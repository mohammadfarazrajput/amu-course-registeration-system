# 🚀 QUICK START GUIDE
## AMU Course Registration System

### ⚡ Super Quick Setup (5 Minutes)

#### **Step 1: Extract Files**
- Extract the downloaded ZIP file
- Open folder: `college-registration-system`

#### **Step 2: Run Setup**
```
Double-click: setup.bat
```
Wait for installation to complete (2-3 minutes)

#### **Step 3: Start Backend**
```
Open Terminal 1
Double-click: run_backend.bat
```
Wait until you see: "Uvicorn running on http://0.0.0.0:8000"

#### **Step 4: Start Frontend**
```
Open Terminal 2
Double-click: run_frontend.bat
```
Browser will auto-open to: http://localhost:8501

#### **Step 5: Login**
```
Faculty Number: 23AIB001
Enrollment Number: 202300001
```

**Done! 🎉**

---

## 📋 What to Demo

### 1. Login & Dashboard (2 min)
- Show student details
- Check eligibility
- Explain metrics

### 2. Chat Assistant (2 min)
- Type: "Check my eligibility"
- Type: "What courses should I register for?"
- Show AI responses

### 3. Course Selection (2 min)
- Get recommendations
- Show current + backlog + advance courses
- Explain registration types

### 4. Different Student Scenarios (3 min)
Logout and login as:
- **21AIB003** - Student with backlogs
- **21AIB005** - At-risk student
Show warnings and restrictions

### 5. Registration (1 min)
- Select courses
- Choose registration mode
- Submit registration

---

## 🎯 Key Features to Highlight

✅ **AI-Powered:** Multi-agent system with orchestrator
✅ **Real Rules:** Based on actual AMU ordinances 2023-24
✅ **Smart Detection:** Automatic eligibility & risk warnings
✅ **Multi-Mode:** Supports Mode A, B, C registration
✅ **Advancement:** Auto-detects if student can take next sem courses

---

## 🐛 If Something Goes Wrong

### Backend won't start?
```bash
cd backend
python main.py
```
Check error message

### Frontend won't start?
```bash
cd frontend
streamlit run app.py
```
Check error message

### Database error?
```bash
cd backend
python seed_database.py
```
Recreates database

---

## 📊 Project Stats

- **Students:** 15 sample students
- **Courses:** 45 courses (AI branch)
- **Semesters:** 3-8 covered
- **Agents:** 6 AI agents
- **API Endpoints:** 12+ endpoints
- **Lines of Code:** ~3000+

---

## 💡 Tips for Presentation

1. **Start with the problem:** Manual registration is complex
2. **Show the solution:** AI agents automate the process
3. **Demo different scenarios:** Good student, backlog student, at-risk
4. **Highlight AMU-specific rules:** Promotion requirements, name removal
5. **Show chat assistant:** Natural language interaction
6. **Explain architecture:** Multi-agent system diagram
7. **Technical stack:** FastAPI + Streamlit + SQLite

---

## 📞 Emergency Contacts

If demo fails:
1. ✅ Use screenshots (take them beforehand!)
2. ✅ Show architecture diagrams
3. ✅ Walk through code
4. ✅ Explain agents and business rules

---

**Good luck with your demo! 🎓**
