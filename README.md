# Enterprise AI Workflow Intelligence Platform

An AI-powered enterprise automation system that helps organizations process business documents, extract insights, automate workflows, and provide intelligent knowledge assistance using modern AI techniques.

This project is built for the msg global AI Intern role requirements, strictly adhering to an enterprise-grade architecture.

## 🌟 Key Features

1. **Intelligent Document Processing**
   - Automatically ingests PDF, DOCX, and TXT files
   - Uses NLP/LLM to classify document types (Invoices, Contracts, POs, etc.)
   - Extracts key entities (Companies, Dates, Amounts, Payment Terms)
   - Performs automated Risk Analysis (identifies missing clauses, unusual amounts)

2. **Enterprise RAG Knowledge Assistant**
   - A semantic search and chat interface built on `ChromaDB` and `SentenceTransformers`
   - Answers questions strictly based on uploaded company documents
   - Provides concrete source citations & relevance scoring for transparency

3. **AI Workflow Automation Engine**
   - Automatically calculates an AI Confidence Score and Risk Level
   - Detects missing mandatory fields
   - Recommends workflow routing (Auto-Approve, Manual Review, Escalate)
   - Allows Managers/Admins to quickly act on AI recommendations

4. **Business Analytics Dashboard**
   - Professional Dark-Mode SAP-style enterprise dashboard
   - Real-time KPIs, historical trends, and risk distribution analysis

5. **Role-Based Access Control (RBAC)**
   - **Admin:** Full access to all documents, workflows, and user management
   - **Manager:** Can view all documents and approve/reject workflows
   - **Employee:** Can upload documents, use the chat assistant, and view only their own documents

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **Framework:** FastAPI (Async, high-performance)
- **Database:** PostgreSQL (with AsyncPG and SQLAlchemy 2.0 ORM)
- **AI/ML:** LangChain, HuggingFace Sentence Transformers (`all-MiniLM-L6-v2`), OpenAI GPT-4o-mini
- **Vector DB:** ChromaDB (Persistent local storage)
- **Security:** JWT Authentication, Bcrypt Password Hashing, RBAC Middleware

### Frontend (React/Vite)
- **Framework:** React 18, React Router DOM v6
- **State Management:** Zustand (with local storage persistence)
- **Styling:** Custom Enterprise Design System (Vanilla CSS with CSS Variables, Dark Mode)
- **Data Visualization:** Recharts
- **HTTP Client:** Axios with response interceptors

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL server running locally

### 1. Database Setup
Create a PostgreSQL database named `enterprise_ai_db`:
```sql
CREATE DATABASE enterprise_ai_db;
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file based on .env.example and add your OpenAI API Key
cp .env.example .env

# Run Alembic migrations or initialize DB on first startup
python main.py
```
> *Note: The application will automatically create the database tables on startup via `init_db()`.*
Start the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend will run on `http://localhost:5173`.

### 4. Sample Users (Automatically seeded if script provided or register via API)
The frontend login page has a "Quick Demo Access" feature that automatically fills in credentials for testing the 3 different roles.
*You will need to manually register these users via the `/api/auth/register` endpoint or database script first.*

## 📁 Folder Structure

```
enterprise-ai-platform/
├── backend/
│   ├── app/
│   │   ├── api/routes/    # FastAPI endpoint definitions
│   │   ├── core/          # Config, Security, Logging
│   │   ├── db/            # SQLAlchemy database setup
│   │   ├── models/        # SQLAlchemy DB Models
│   │   ├── schemas/       # Pydantic validation schemas
│   │   └── services/      # Core business logic
│   │       ├── ai/        # RAG Pipeline, Embeddings
│   │       ├── document/  # NLP Extraction, OCR, Cleaning
│   │       └── workflow/  # Risk Assessment, Routing Rules
│   ├── data/              # Uploads, ChromaDB, FAISS Index
│   └── tests/             # Pytest Unit Tests
└── frontend/
    ├── src/
    │   ├── components/    # Reusable UI elements (Layout)
    │   ├── pages/         # React Route Pages (Dashboard, Chat, etc)
    │   ├── services/      # Axios API Client
    │   ├── store/         # Zustand global state
    │   └── styles/        # Enterprise Design System CSS
    └── package.json
```
