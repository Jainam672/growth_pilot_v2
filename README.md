# 🚀 GrowthPilot — AI-Powered Business Mentor

A full-stack AI SaaS platform that analyzes business ideas using RAG (Retrieval-Augmented Generation) with Phi-3-mini.

---

## 📁 Project Structure

```
growthpilot/
├── backend/                    ← FastAPI Python Backend
│   ├── main.py                 ← App entry point + routes
│   ├── run.py                  ← Quick start script
│   ├── database.py             ← SQLAlchemy + SQLite setup
│   ├── models.py               ← ORM table definitions
│   ├── schemas.py              ← Pydantic request/response models
│   ├── auth.py                 ← JWT tokens + password hashing
│   ├── .env                    ← Environment variables
│   ├── requirements.txt        ← Python dependencies
│   ├── routers/
│   │   ├── auth_routes.py      ← POST /auth/register, /auth/login
│   │   ├── idea_routes.py      ← CRUD for business ideas
│   │   ├── ai_routes.py        ← POST /ai/analyze
│   │   ├── dashboard_routes.py ← GET /dashboard/stats
│   │   └── settings_routes.py  ← GET/PUT /settings/
│   └── ai_engine/
│       ├── llm.py              ← Phi-3-mini model loader + LoRA
│       ├── embeddings.py       ← SentenceTransformer embeddings
│       ├── vector_store.py     ← ChromaDB client
│       ├── rag_pipeline.py     ← Full RAG query pipeline
│       └── ingest_docs.py      ← PDF → ChromaDB ingestion
│
└── frontend/                   ← HTML/CSS/JS + Bootstrap
    ├── index.html              ← Landing page
    ├── js/
    │   └── api.js              ← Central API helper (fetch + auth)
    └── pages/
        ├── login.html          ← Login page
        ├── register.html       ← Registration page
        ├── dashboard.html      ← Main dashboard + stats
        ├── idea.html           ← 3-step idea submission form
        ├── response.html       ← AI analysis results
        ├── history.html        ← All ideas with search/filter
        ├── analytics.html      ← Charts (Chart.js)
        └── settings.html       ← Language, voice, preferences
```

---

## ⚙️ Backend Setup

### 1. Install Python dependencies

For local development:
```bash
cd growthpilot/backend
pip install -r requirements.txt
```

For free Render / dummy AI deployment:
```bash
cd growthpilot/backend
pip install -r requirements
```

### 2. Configure environment

Edit `.env`:
```env
SECRET_KEY=your-secret-key-here
USE_DUMMY_AI=true        # Set false when Phi-3-mini is ready
MODEL_NAME=microsoft/Phi-3-mini-4k-instruct
```

### 3. (Optional) Add business knowledge PDFs

```bash
mkdir -p data/business_guides
# Copy your PDF files there
# Then run:
python -m ai_engine.ingest_docs
```

### 4. Start the server

```bash
python run.py
# OR
uvicorn main:app --reload --port 8000
```

API available at: http://localhost:8000
Swagger docs at: http://localhost:8000/docs

---

## 🌐 Frontend Setup

Open `frontend/index.html` in a browser, OR serve with a local server:

```bash
cd growthpilot/frontend
python -m http.server 3000
# Open: http://localhost:3000
```

**Important:** Make sure the backend is running on port 8000 before using the frontend.


## 🔌 API Endpoints

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/auth/register` | POST | ❌ | Register new user |
| `/auth/login` | POST | ❌ | Login + get JWT |
| `/me` | GET | ✅ | Get current user |
| `/idea/` | POST | ✅ | Submit new idea |
| `/idea/` | GET | ✅ | List all ideas |
| `/idea/{id}` | DELETE | ✅ | Delete idea |
| `/ai/analyze` | POST | ✅ | Analyze idea with AI |
| `/ai/result/{id}` | GET | ✅ | Get analysis result |
| `/dashboard/stats` | GET | ✅ | Dashboard statistics |
| `/settings/` | GET/PUT | ✅ | User preferences |

---

## 🤖 AI Engine

### Development Mode (USE_DUMMY_AI=true)
Returns structured dummy responses instantly — no GPU needed.

### Production Mode (USE_DUMMY_AI=false)
1. Phi-3-mini downloads automatically via HuggingFace
2. LoRA weights applied if `LORA_WEIGHTS_PATH` is set
3. ChromaDB retrieves relevant business knowledge
4. RAG pipeline generates structured JSON responses

---

## 🗄️ Database Schema

**users** → id, name, email, hashed_password, language, is_active, created_at  
**ideas** → id, user_id, title, description, budget, location, category, experience_level, status, created_at  
**ai_responses** → id, idea_id, feasibility, cost_breakdown, roadmap, marketing, risks, competitors, funding, idea_score, stage  
**user_settings** → id, user_id, language, voice_input, voice_output, ai_detail_level, notifications  

---

## 📱 Frontend Features

| Page | Features |
|---|---|
| Landing | Hero, features, how-it-works, CTA |
| Login | JWT auth, password toggle |
| Register | Password strength meter, language select |
| Dashboard | Stats cards, recent ideas grid, skeleton loading |
| New Idea | 3-step form, voice input, category, budget chips |
| Response | Idea score ring, roadmap, risks, marketing, voice read-aloud |
| History | Search, filter by status/category, delete |
| Analytics | Chart.js — donut + bar charts |
| Settings | Language, voice toggles, AI detail level |

---

## 🏗️ Development Phases

- **Phase 1 (Done):** Auth, Dashboard, Idea form, Dummy AI
- **Phase 2:** Connect real Phi-3-mini + ChromaDB RAG
- **Phase 3:** Voice multilingual, PDF report export, Admin panel
