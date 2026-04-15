"""
LangChain Orchestrator - Main Agent Graph
Coordinates all agents for intelligent registration flow
"""

import os
from typing import Dict
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from services.retriever import retriever
from agents.verification_agent import VerificationAgent
from agents.eligibility_agent import create_eligibility_agent
from agents.course_selector import create_course_selector_agent
from agents.registration_agent import create_registration_agent


class RegistrationOrchestrator:
    """
    Main orchestrator for the registration system
    Coordinates agents and handles chat interactions
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize agents
        self.verification_agent = VerificationAgent(db)
        self.eligibility_agent = create_eligibility_agent(db)
        self.course_selector = create_course_selector_agent(db)
        self.registration_agent = create_registration_agent(db)
        
        # Initialize LLM for chat
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=0.3
            )
        except Exception as e:
            print(f"⚠️ Failed to initialize Orchestrator LLM: {e}")
            self.llm = None
    
    def handle_chat(self, student_id: int, message: str) -> Dict:
        """
        Handle chat message with RAG-powered response
        
        Args:
            student_id: Student ID
            message: User message
        
        Returns:
            Dict with response and context
        """
        # Get student data
        student_result = self.verification_agent.get_student_by_id(student_id)
        if not student_result.get("found"):
            return {
                "response": "Student not found. Please log in again.",
                "context": None,
                "sources": []
            }
        
        student_data = student_result["student"]
        
        # Classify query intent
        intent = self._classify_intent(message)
        
        # Route to appropriate handler
        if intent == "eligibility":
            return self._handle_eligibility_query(student_id, student_data, message)
        elif intent == "courses":
            return self._handle_course_query(student_id, student_data, message)
        elif intent == "ordinance":
            return self._handle_ordinance_query(message)
        else:
            return self._handle_general_query(student_data, message)
    
    def _classify_intent(self, message: str) -> str:
        """Classify user intent"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["eligib", "can i", "promotion", "advance", "backlog"]):
            return "eligibility"
        elif any(word in message_lower for word in ["course", "register", "recommend", "select"]):
            return "courses"
        elif any(word in message_lower for word in ["rule", "ordinance", "regulation", "policy", "clause"]):
            return "ordinance"
        else:
            return "general"
    
    def _handle_eligibility_query(self, student_id: int, student_data: Dict, message: str) -> Dict:
        """Handle eligibility-related queries"""
        # Get eligibility analysis
        eligibility = self.eligibility_agent.analyze_eligibility(student_id)
        
        # Retrieve relevant ordinances
        rag_result = retriever.retrieve_context(message, top_k=2)
        
        # Generate response using LLM
        prompt = f"""You are an academic advisor for AMU students.

Student: {student_data['name']}
Semester: {student_data['current_semester']}
CGPA: {student_data['cgpa']}
Credits: {student_data['total_earned_credits']}

Eligibility Status:
{eligibility}

Relevant AMU Ordinances:
{rag_result['context']}

Student Question: {message}

Provide a clear, helpful answer based on the student's eligibility and AMU ordinances.
Be concise and supportive."""
        
        try:
            response = self.llm.invoke(prompt)
            return {
                "response": response.content,
                "context": eligibility,
                "sources": rag_result['sources']
            }
        except:
            return {
                "response": f"Based on your current status, you have {eligibility['total_earned_credits']} credits and CGPA {eligibility['cgpa']}. Check the eligibility page for details.",
                "context": eligibility,
                "sources": []
            }
    
    def _handle_course_query(self, student_id: int, student_data: Dict, message: str) -> Dict:
        """Handle course-related queries"""
        # Get eligibility first
        eligibility = self.eligibility_agent.analyze_eligibility(student_id)
        
        # Get course recommendations
        courses = self.course_selector.recommend_courses(student_id, eligibility)
        
        # Generate response
        current_count = len(courses['courses']['current'])
        backlog_count = len(courses['courses']['backlogs'])
        advance_count = len(courses['courses']['advance'])
        
        response_text = f"""Based on your current status:

📚 Current Semester Courses: {current_count} available
"""
        
        if backlog_count > 0:
            response_text += f"⚠️ Backlog Courses: {backlog_count} to clear\n"
        
        if advance_count > 0:
            response_text += f"🚀 Advancement Courses: {advance_count} available\n"
        
        response_text += f"\nTotal Credits: {courses['total_credits']}/40"
        
        return {
            "response": response_text,
            "context": courses,
            "sources": []
        }
    
    def _handle_ordinance_query(self, message: str) -> Dict:
        """Handle ordinance/rule queries"""
        # Retrieve relevant ordinances
        rag_result = retriever.retrieve_context(message, top_k=3)
        
        # Generate response
        prompt = f"""You are an AMU academic policy expert.

Student Question: {message}

Relevant AMU B.Tech Ordinances (2023-24):
{rag_result['context']}

Provide a clear explanation based on the ordinances above.
Cite specific clauses when relevant."""
        
        try:
            response = self.llm.invoke(prompt)
            return {
                "response": response.content,
                "context": None,
                "sources": rag_result['sources']
            }
        except:
            return {
                "response": rag_result['context'][:500] + "...",
                "context": None,
                "sources": rag_result['sources']
            }
    
    def _handle_general_query(self, student_data: Dict, message: str) -> Dict:
        """Handle general queries"""
        prompt = f"""You are a helpful academic assistant for AMU students.

Student: {student_data['name']}
Branch: {student_data['branch']}
Semester: {student_data['current_semester']}

Question: {message}

Provide a helpful response."""
        
        try:
            response = self.llm.invoke(prompt)
            return {
                "response": response.content,
                "context": None,
                "sources": []
            }
        except:
            return {
                "response": "I'm here to help with course registration and AMU ordinances. Ask me about eligibility, courses, or registration rules!",
                "context": None,
                "sources": []
            }


# Factory function
def create_orchestrator(db: Session) -> RegistrationOrchestrator:
    return RegistrationOrchestrator(db)