"""
LangChain Orchestrator - Main Agent Graph
Coordinates all agents for intelligent registration flow
"""

import os
from typing import Dict
from sqlalchemy.orm import Session
from langchain_groq import ChatGroq
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
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        try:
            self.llm = ChatGroq(
                model=model,
                groq_api_key=api_key,
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
        """Handle eligibility-related queries — LLM interprets ordinances + student context."""
        eligibility = self.eligibility_agent.analyze_eligibility(student_id)

        # RAG — safe, won't crash if vector store is empty
        rag_result = {"context": "", "sources": []}
        try:
            rag_result = retriever.retrieve_context(message, top_k=2)
        except Exception as e:
            print(f"⚠️ RAG retrieval skipped: {e}")

        rag_section = f"\n\nRelevant AMU Ordinances:\n{rag_result['context']}" if rag_result['context'] else ""

        prompt = f"""You are an academic advisor for AMU ZHCET students. Be concise (max 5 sentences).

Student: {student_data['name']} | Sem {student_data['current_semester']} | CGPA {student_data['cgpa']} | Credits {student_data['total_earned_credits']}
Status: {eligibility.get('status')} | Backlogs: {eligibility.get('backlog_count', 0)} | Risk: {eligibility.get('risk_level')}
Allowed registrations: {', '.join(eligibility.get('allowed_registration_types', []))}
{rag_section}

Student question: {message}

Answer directly and helpfully."""

        if not self.llm:
            return {
                "response": f"Status: {eligibility.get('status')}. CGPA: {eligibility['cgpa']}, Credits: {eligibility['total_earned_credits']}, Backlogs: {eligibility.get('backlog_count', 0)}.",
                "context": eligibility,
                "sources": rag_result['sources']
            }

        try:
            response = self.llm.invoke(prompt)
            return {
                "response": response.content,
                "context": eligibility,
                "sources": rag_result['sources']
            }
        except Exception as e:
            print(f"❌ LLM error in eligibility handler: {e}")
            return {
                "response": f"Your status: {eligibility.get('status')}. CGPA: {eligibility['cgpa']}, Credits: {eligibility['total_earned_credits']}, Backlogs: {eligibility.get('backlog_count', 0)}. Check the eligibility page for full details.",
                "context": eligibility,
                "sources": []
            }
    
    def _handle_course_query(self, student_id: int, student_data: Dict, message: str) -> Dict:
        """Handle course-related queries — no LLM, pure data formatting."""
        eligibility = self.eligibility_agent.analyze_eligibility(student_id)
        courses = self.course_selector.recommend_courses(student_id, eligibility)

        current = courses['courses']['current']
        backlogs = courses['courses']['backlogs']
        advance = courses['courses']['advance']

        lines = [f"Here's your course summary for Semester {eligibility['current_semester']}:\n"]
        lines.append(f"Current Semester: {len(current)} course(s) available")
        for c in current[:5]:
            lines.append(f"  - {c.get('course_code','?')} {c.get('course_name','?')} ({c.get('credits','?')} cr)")

        if backlogs:
            lines.append(f"\nBacklogs: {len(backlogs)} course(s) to clear")
            for c in backlogs[:5]:
                lines.append(f"  - {c.get('course_code','?')} {c.get('course_name','?')} ({c.get('credits','?')} cr)")

        if advance:
            lines.append(f"\nAdvancement: {len(advance)} course(s) available (next semester)")
            for c in advance[:3]:
                lines.append(f"  - {c.get('course_code','?')} {c.get('course_name','?')} ({c.get('credits','?')} cr)")

        lines.append(f"\nTotal registerable credits: {courses['total_credits']}/40")

        if eligibility.get('warnings'):
            lines.append("\nWarnings:")
            for w in eligibility['warnings']:
                lines.append(f"  - {w}")

        return {
            "response": "\n".join(lines),
            "context": courses,
            "sources": []
        }
    def _handle_ordinance_query(self, message: str) -> Dict:
        """Handle ordinance/rule queries — RAG + LLM."""
        rag_result = {"context": "", "sources": []}
        try:
            rag_result = retriever.retrieve_context(message, top_k=3)
        except Exception as e:
            print(f"⚠️ RAG retrieval skipped: {e}")

        if not self.llm:
            return {
                "response": rag_result['context'][:600] if rag_result['context'] else "Ordinance retrieval unavailable.",
                "context": None,
                "sources": rag_result['sources']
            }

        rag_section = rag_result['context'] if rag_result['context'] else "No ordinance documents indexed yet."
        prompt = f"""You are an AMU B.Tech academic policy expert. Be concise and cite clauses.

Question: {message}

AMU Ordinances (2023-24):
{rag_section}

Answer in 3-5 sentences max."""

        try:
            response = self.llm.invoke(prompt)
            return {
                "response": response.content,
                "context": None,
                "sources": rag_result['sources']
            }
        except Exception as e:
            print(f"❌ LLM error in ordinance handler: {e}")
            return {
                "response": rag_section[:600] if rag_section else "Unable to retrieve ordinance information.",
                "context": None,
                "sources": rag_result['sources']
            }
    
    def _handle_general_query(self, student_data: Dict, message: str) -> Dict:
        """Handle general queries."""
        if not self.llm:
            return {
                "response": "I can help with eligibility, courses, ordinances, and registration rules. Try asking something specific!",
                "context": None,
                "sources": []
            }

        prompt = f"""You are a helpful academic assistant for AMU ZHCET students. Be concise.

Student: {student_data['name']} | Branch: {student_data['branch']} | Sem {student_data['current_semester']}

Question: {message}

Answer in 3-4 sentences."""

        try:
            response = self.llm.invoke(prompt)
            return {"response": response.content, "context": None, "sources": []}
        except Exception as e:
            print(f"❌ LLM error in general handler: {e}")
            return {
                "response": "I can help with eligibility, courses, ordinances, and registration rules. Try asking something specific!",
                "context": None,
                "sources": []
            }


# Factory function
def create_orchestrator(db: Session) -> RegistrationOrchestrator:
    return RegistrationOrchestrator(db)