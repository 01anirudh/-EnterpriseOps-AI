# 🚀 EnterpriseOps AI

![EnterpriseOps AI Banner](https://img.shields.io/badge/EnterpriseOps%20AI-Autonomous%20Agents-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-20+-blue.svg?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_AI-FF9900.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?logo=postgresql&logoColor=white)

**EnterpriseOps AI** is a production-style Autonomous Multi-Agent Enterprise Operations Platform. It automates routine corporate tasks by combining several specialized AI agents into a single, cohesive workflow coordinated by **LangGraph**.

Instead of interacting with a single LLM, users submit complex prompts, and a team of specialized agents collaborate to understand the request, retrieve enterprise knowledge (RAG), execute SQL analytics, generate professional reports, and dispatch notifications via Email, Slack, or GitHub.

---

## ✨ Features

- **🤖 Multi-Agent Orchestration**: Built with LangGraph. Agents include a Planner, SQL Analyst, RAG Knowledge Retriever, Data Analyst, Report Writer, and Action Dispatchers.
- **📚 Local RAG Pipeline**: Upload company PDFs/Documents. They are chunked, vectorized using local SentenceTransformers, and stored in a **Qdrant** Vector DB.
- **📊 Text-to-SQL Analytics**: The AI autonomously queries a PostgreSQL database to extract insights from raw corporate data (e.g., Sales, HR).
- **🛑 Human-in-the-Loop (HITL)**: Workflows pause before executing irreversible actions (like sending emails) so a human manager can approve or reject the action.
- **📡 Real-Time SSE Streaming**: The React frontend uses Server-Sent Events to stream live agent logs, thought processes, and status updates directly to the dashboard.

---

## 🛠️ Technology Stack

### Frontend
- **React 18** + **Vite**
- **Tailwind CSS** for modern, responsive styling
- **Zustand** for state management
- **Axios** & **SSE (Server-Sent Events)** for real-time API communication

### Backend
- **FastAPI** (Async Python web framework)
- **LangGraph** & **LangChain** (Multi-Agent framework)
- **Celery** + **Redis** (Background task queues for long-running workflows)
- **SQLAlchemy** + **asyncpg** (Async Database ORM)

### Infrastructure
- **PostgreSQL**: Relational database for structured data and user state.
- **Qdrant**: Vector Database for RAG and semantic search.
- **Redis**: Message broker for Celery and SSE Pub/Sub.
- **Docker Compose**: Containerized infrastructure orchestration.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### 1. Start Infrastructure (Databases)
Run PostgreSQL, Redis, and Qdrant in the background via Docker:
```bash
docker-compose up -d
```

### 2. Setup Backend
Open a terminal in the root directory:
```bash
# Create and activate virtual environment
python -m venv backend/venv
# On Windows:
.\backend\venv\Scripts\activate
# On Mac/Linux:
source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure Environment Variables (Requires Gemini API Key)
cp backend/.env.example backend/.env

# Seed the database with mock sales data and a default admin user
python -m backend.scripts.seed_db

# Seed the Qdrant vector database with mock company documents
python -m backend.scripts.seed_documents
```

### 3. Start Backend Services
You need two separate terminals for the backend processes.

**Terminal 1 (FastAPI Server):**
```bash
# Ensure venv is activated!
uvicorn backend.main:app --reload
```

**Terminal 2 (Celery Worker):**
```bash
# Ensure venv is activated!
# Note: On Windows, use the --pool=solo flag
celery -A backend.workers.celery_worker worker --loglevel=info --pool=solo
```

### 4. Start Frontend
**Terminal 3 (Vite React App):**
```bash
cd frontend
npm install
npm run dev
```

---

## 🎮 Usage Guide

1. Open your browser and navigate to `http://localhost:5173`.
2. **Login** using the seeded admin credentials:
   - **Email:** `admin@demo.com`
   - **Password:** `admin123`
3. **Trigger a Workflow:** Go to the Workflow page and enter a complex task such as:
   > *"Analyze Q2 sales, check our discount policy, generate an executive report, and email the finance team."*
4. **Monitor:** Watch the agents plan and execute in real-time in the Agent Logs window.
5. **Approve:** Navigate to the **Approval Requests** tab to review the generated report and approve the final email dispatch.
6. **Review Reports:** Go to the **Reports** page to view or download the generated Markdown executive summaries.

---

## 🔒 Environment Configuration (`.env`)

The application supports real integrations with external services. If you leave these blank, the app runs in **Mock Mode** (logging actions to the console instead of actually sending them).

- **`GOOGLE_API_KEY`**: Required. Your Gemini API key for the LLM.
- **`GMAIL_CREDENTIALS_FILE`**: (Optional) Path to OAuth 2.0 credentials for sending emails.
- **`SLACK_BOT_TOKEN`**: (Optional) Slack API token to dispatch messages.
- **`GITHUB_TOKEN`**: (Optional) PAT to automate issue creation.

---

*Built for advanced Agentic AI orchestration and practical enterprise automation.*
