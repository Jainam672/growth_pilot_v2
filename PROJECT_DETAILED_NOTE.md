# GrowthPilot Detailed Project Note

## 1. Project Overview

GrowthPilot is a full-stack AI business mentoring application. A user can:

- register and log in
- submit a business idea
- trigger AI analysis for that idea
- view the result in dashboard/history/chat screens
- ask follow-up questions in the chat page
- manage preferences from the settings page

At a high level, the system has three major layers:

1. `frontend/`
   Static HTML/CSS/JavaScript pages that run in the browser.
2. `backend/`
   FastAPI API server, authentication, data storage, AI analysis pipeline, and chat proxy.
3. `backend/vector_store/chroma_db/`
   Persistent ChromaDB vector database containing embedded business knowledge chunks used for retrieval.

The application is designed around a typical flow:

1. User signs up or logs in.
2. Frontend stores JWT token in `localStorage`.
3. User submits an idea from the form page.
4. Backend saves the idea to SQLite.
5. User triggers AI analysis.
6. Backend runs the RAG pipeline:
   embed query -> search ChromaDB -> build prompt -> call local LLM through Ollama -> parse JSON -> save structured result.
7. Frontend loads the saved result and lets the user continue the discussion in chat.

One important implementation detail:

- The app has two SQLite files:
  - `growthpilot.db` at repo root
  - `backend/growthpilot.db`
- The active backend data is currently in `backend/growthpilot.db`, because `DATABASE_URL` defaults to `sqlite:///./growthpilot.db` and the backend is typically started from inside `backend/`.
- The root `growthpilot.db` currently exists but is empty.

## 2. Real Project Structure

```text
growthpilot_v2_fixed/
├─ backend/
│  ├─ ai_engine/
│  │  ├─ embeddings.py
│  │  ├─ ingest_docs.py
│  │  ├─ llm.py
│  │  ├─ rag_pipeline.py
│  │  └─ vector_store.py
│  ├─ data/
│  │  └─ business_guides/
│  │     └─ many PDF business documents
│  ├─ routers/
│  │  ├─ ai_routes.py
│  │  ├─ auth_routes.py
│  │  ├─ chat_routes.py
│  │  ├─ dashboard_routes.py
│  │  ├─ idea_routes.py
│  │  └─ settings_routes.py
│  ├─ vector_store/
│  │  └─ chroma_db/
│  │     ├─ chroma.sqlite3
│  │     └─ HNSW index binary files
│  ├─ auth.py
│  ├─ database.py
│  ├─ growthpilot.db
│  ├─ growthpilot.log
│  ├─ main.py
│  ├─ models.py
│  ├─ requirements.txt
│  ├─ run.py
│  ├─ runtime.txt
│  └─ schemas.py
├─ frontend/
│  ├─ index.html
│  ├─ js/
│  │  └─ api.js
│  └─ pages/
│     ├─ analytics.html
│     ├─ chat.html
│     ├─ dashboard.html
│     ├─ form.html
│     ├─ history.html
│     ├─ login.html
│     ├─ register.html
│     └─ settings.html
├─ growthpilot.db
├─ growthpilot.log
└─ README.md
```

## 3. How the System Works End to End

### 3.1 Frontend to backend communication

All browser requests are centralized through `frontend/js/api.js`.

This file does the following:

- sets `API_BASE = "http://localhost:8000"`
- reads the JWT token from `localStorage`
- adds `Authorization: Bearer <token>` for protected routes
- handles `401` by clearing storage and redirecting to login
- exposes helper methods like:
  - `register`
  - `login`
  - `getMe`
  - `createIdea`
  - `listIdeas`
  - `analyzeIdea`
  - `getResult`
  - `getDashboard`
  - `getSettings`
  - `saveSettings`
  - `sendChat`

So the frontend pages themselves are thin UI layers, and `api.js` is the shared request layer.

### 3.2 Backend startup flow

`backend/main.py` is the FastAPI entry point.

On startup it:

- loads environment variables with `dotenv`
- configures logging to console and `growthpilot.log`
- imports database and router modules
- runs `Base.metadata.create_all(bind=engine)` to ensure tables exist
- creates the FastAPI app
- enables permissive CORS using `allow_origins=["*"]`
- mounts all API routers
- exposes:
  - `/`
  - `/health`
  - `/me`

### 3.3 FastAPI routers

The backend routes are split by responsibility:

- `auth_routes.py`
  register and login
- `idea_routes.py`
  create/list/get/delete ideas
- `ai_routes.py`
  analyze ideas and fetch saved AI results
- `dashboard_routes.py`
  summary statistics for dashboard/analytics
- `settings_routes.py`
  get/update user preferences and profile data
- `chat_routes.py`
  chat follow-up route for the AI mentor experience

This keeps the backend modular and easier to maintain.

## 4. Authentication Flow

Authentication is handled in `backend/auth.py`.

It uses:

- password hashing via `passlib` + `bcrypt`
- JWT tokens via `python-jose`
- FastAPI OAuth2 bearer token extraction via `OAuth2PasswordBearer`

### 4.1 Register

`POST /auth/register`

Flow:

1. validate password length
2. check if email already exists
3. hash password
4. create `users` row
5. create default `user_settings` row
6. create JWT token with `sub = user.id`
7. return token + user info

### 4.2 Login

`POST /auth/login`

Flow:

1. find user by email
2. verify hashed password
3. ensure account is active
4. create JWT
5. return token + user info

### 4.3 Protected user lookup

`get_current_user()`:

1. reads bearer token
2. decodes JWT
3. extracts `sub`
4. loads matching user from DB
5. rejects missing/inactive users

This dependency is reused in almost every protected route.

## 5. Database Layer

### 5.1 Main relational DB

The relational database is SQLite through SQLAlchemy.

Configured in `backend/database.py`:

- default URL: `sqlite:///./growthpilot.db`
- `check_same_thread=False` to allow FastAPI request handling with SQLite
- `SessionLocal` gives one SQLAlchemy session per request

### 5.2 Actual database files found

Current files:

- `growthpilot.db`
  empty database at repo root
- `backend/growthpilot.db`
  active database with application data

Current observed counts in `backend/growthpilot.db`:

- `users`: 18
- `user_settings`: 18
- `ideas`: 12
- `ai_responses`: 12

This tells us the backend has already been used with real/sample records.

### 5.3 Tables

Defined in `backend/models.py`.

#### `users`

Stores:

- basic auth data
- profile details
- language
- activity state
- created date

Important columns:

- `id`
- `name`
- `email`
- `hashed_password`
- `language`
- `age`
- `city`
- `profession`
- `experience_level`
- `business_interest`
- `income`
- `birthdate`
- `state`
- `country`
- `mobile_number`
- `gender`
- `usage_purpose`
- `is_active`
- `created_at`

#### `ideas`

Stores one business idea per submission.

Important columns:

- `id`
- `user_id`
- `title`
- `description`
- `budget`
- `location`
- `category`
- `experience_level`
- `status`
- `created_at`

`status` is used heavily in the UI and is typically:

- `pending`
- `analyzed`

#### `ai_responses`

Stores the structured AI output for an idea.

Important columns:

- `idea_id`
- `feasibility`
- `cost_breakdown`
- `roadmap`
- `marketing`
- `risks`
- `competitors`
- `funding`
- `idea_score`
- `stage`
- `created_at`

List-like fields are stored as JSON strings in SQLite and converted back to arrays on read.

#### `user_settings`

Stores per-user preferences:

- `language`
- `voice_input`
- `voice_output`
- `ai_detail_level`
- `notifications`

### 5.4 Relationships

Model relationships:

- one `User` -> many `Idea`
- one `Idea` -> one `AIResponse`
- one `User` -> one `UserSettings`

Cascade delete is enabled, so deleting an idea also deletes its AI response.

### 5.5 Sample data found

Recent example ideas in `backend/growthpilot.db` include:

- laptop shop idea in Ahmedabad
- mobile shop idea
- clothing brand
- cafe
- tea business

This is useful as testing/sample data for the current build.



### 6.1 Idea submission workflow

Frontend page:

- `frontend/pages/form.html`

Backend route:

- `POST /idea/`

Flow:

1. user fills multi-step form
2. frontend creates payload with title, description, category, budget, location, and stage-like experience level
3. `api.createIdea()` sends POST request
4. backend inserts row into `ideas`
5. status defaults to `pending`
6. frontend then calls AI analysis

### 6.2 AI analysis workflow

Backend route:

- `POST /ai/analyze`

This is the core business feature.

Flow:

1. backend verifies idea belongs to logged-in user
2. `_run_analysis()` loads the idea
3. `ai_engine.rag_pipeline.analyze_idea()` is called
4. the AI result dict is returned
5. backend inserts or updates `ai_responses`
6. idea status is changed to `analyzed`
7. frontend can then open `chat.html?idea_id=<id>`

### 6.3 Dashboard workflow

Frontend page:

- `frontend/pages/dashboard.html`

Backend route:

- `GET /dashboard/stats`

Flow:

1. frontend loads stats after auth
2. backend fetches all user ideas
3. computes:
   - total ideas
   - analyzed ideas
   - pending ideas
   - recent ideas
   - category distribution
4. frontend renders cards, recent idea cards, bar visuals, and activity list

### 6.4 History workflow

Frontend page:

- `frontend/pages/history.html`

Backend routes:

- `GET /idea/`
- `DELETE /idea/{id}`
- `POST /ai/analyze`

Flow:

1. frontend loads all ideas for user
2. browser-side search and filter is applied
3. user can:
   - view analyzed report
   - trigger pending analysis
   - delete idea

### 6.5 Settings workflow

Frontend page:

- `frontend/pages/settings.html`

Backend routes:

- `GET /me`
- `GET /settings/`
- `PUT /settings/`

Flow:

1. page loads user profile and settings separately
2. form is populated from both endpoints
3. save requires current password
4. backend verifies password
5. backend updates both `user_settings` and selected `users` columns

### 6.6 Chat workflow

Frontend page:

- `frontend/pages/chat.html`

Backend route:

- `POST /chat/message`

Flow:

1. page optionally loads an existing idea result via `idea_id`
2. frontend builds local chat history array
3. frontend sends last messages plus optional `idea_context`
4. backend either:
   - returns dummy business mentor response
   - or proxies to local Ollama `/api/chat`
5. frontend renders formatted response bubbles

This chat is not writing chat history into SQLite. It is session-oriented in browser memory.

## 7. Local LLM Working

### 7.1 Important correction

The code comments and README mention Phi-3-mini and optional LoRA style wording, but the current implementation does not directly load a Hugging Face transformer model in Python.

The real current implementation is:

- local LLM access through `Ollama`
- model name from:
  - `OLLAMA_MODEL`
  - else `MODEL_NAME`
  - else fallback `phi3.5:latest`

So the current "local LLM" design is not:

- `transformers` model loaded directly in `torch`

It is:

- FastAPI -> `httpx` -> local Ollama server -> local model response

### 7.2 LLM file

Implemented in `backend/ai_engine/llm.py`.

Main functions:

- `generate_response(prompt)`
- `repair_json_response(raw_text)`
- `_dummy_response()`

### 7.3 How `generate_response()` works

If `USE_DUMMY_AI=true`:

- it immediately returns fixed structured JSON
- this is used for development/testing without real inference

If `USE_DUMMY_AI=false`:

1. build JSON payload for Ollama
2. call `POST {OLLAMA_BASE_URL}/api/generate`
3. ask Ollama to return JSON format
4. return response text

Ollama parameters used:

- `temperature: 0.2`
- `num_predict: 512`
- `stream: false`
- `format: "json"`

### 7.4 JSON repair logic

Sometimes LLMs return malformed JSON.

`repair_json_response()` handles that by:

1. creating a second repair prompt
2. forcing valid JSON-only output
3. calling the same local model again

This improves reliability of structured AI responses.

### 7.5 Dummy mode behavior

Dummy mode returns a hardcoded response with:

- feasibility
- cost breakdown
- roadmap
- marketing
- risks
- competitors
- funding
- score
- stage

This is extremely useful for frontend development because:

- the UI can be fully tested
- no Ollama dependency is needed
- no vector retrieval is required

## 8. RAG Pipeline Working

Implemented in `backend/ai_engine/rag_pipeline.py`.

This is the heart of the analysis engine.

### 8.1 RAG meaning here

RAG = Retrieval-Augmented Generation.

That means the LLM does not answer only from its own internal weights. Before generation, the app first retrieves relevant business knowledge from a vector store and injects that retrieved content into the prompt.

### 8.2 Actual pipeline steps

`analyze_idea()` does this:

1. combine idea title + description into one query string
2. embed the query using sentence-transformers
3. search ChromaDB for top 5 relevant document chunks
4. build a strict JSON-output prompt using the retrieved context
5. send prompt to local LLM through Ollama
6. parse the model output
7. repair malformed JSON if needed
8. normalize the output to app schema

### 8.3 Prompt structure

`build_prompt()` includes:

- role: expert business mentor
- required output keys
- formatting rules
- retrieved business knowledge context
- business title
- description
- budget
- location
- category
- founder experience

This prompt is strongly schema-driven so the backend can safely store the result.

### 8.4 Output normalization

`_normalize_output()` ensures:

- string fields always become strings
- list fields always become arrays of strings
- score becomes integer from 0 to 100
- stage always has a fallback

This protects the frontend from model inconsistency.

### 8.5 Fallback behavior

If parsing and repair both fail:

- backend logs error
- returns a generic fallback structured response

That means the app almost always produces something usable instead of crashing.

## 9. Sentence Transformer Working

Implemented in `backend/ai_engine/embeddings.py`.

### 9.1 Model used

The embedding model is:

- `all-MiniLM-L6-v2`

This is loaded from the `sentence-transformers` library.

### 9.2 How it works here

`get_embedding_model()` lazily loads the model only once and caches it in `_embed_model`.

This means:

- first request may be slower
- later requests reuse the same loaded model

Functions:

- `embed_text(text)`
  returns embedding vector for one string
- `embed_batch(texts)`
  returns embeddings for many strings

### 9.3 Vector size

The active Chroma collection reports dimension:

- `384`

That matches the embedding output size for `all-MiniLM-L6-v2`.

### 9.4 Practical role in the system

Sentence transformer is used in two places:

1. document ingestion
   converting business guide chunks into vectors
2. user analysis queries
   converting idea text into a query vector

Without this layer, ChromaDB similarity search would not work.

## 10. ChromaDB Working

Implemented in `backend/ai_engine/vector_store.py`.

### 10.1 What ChromaDB is doing in this project

ChromaDB is the persistent vector database for business knowledge.

Its job is:

- store document chunks
- store embeddings for those chunks
- retrieve semantically similar chunks when a new idea is analyzed

### 10.2 Storage location

Configured default path:

- `./vector_store/chroma_db`

Actual files found:

- `backend/vector_store/chroma_db/chroma.sqlite3`
- HNSW segment/index files in subfolder

This means Chroma uses:

- SQLite metadata storage
- binary ANN/HNSW index files for retrieval

### 10.3 Collection

Collection name:

- `business_knowledge`

Metadata:

- `{"hnsw:space": "cosine"}`

So similarity is cosine distance based.

### 10.4 Current observed vector DB state

In the current repo:

- `collections`: 1
- `segments`: 2
- `embeddings`: 10,350
- `embedding_metadata`: 20,700

That means the vector store is already populated and usable.

### 10.5 Query process

`query_similar(query_embedding, n_results=5)`:

1. loads collection
2. calls Chroma `query(...)`
3. asks for top `n_results`
4. returns only document texts

These texts become prompt context for the LLM.

### 10.6 Add document process

`add_documents(...)`:

1. receives ids, texts, embeddings, metadata
2. inserts in batches of 5000
3. stores documents + vectors + metadata in collection

This is used by the ingestion script.

## 11. Document Ingestion Working

Implemented in `backend/ai_engine/ingest_docs.py`.

### 11.1 Source knowledge base

Business PDFs are stored in:

- `backend/data/business_guides/`

The repo already contains many PDFs about:

- startup planning
- marketing
- budgeting
- lean startup
- HR
- sales
- strategy
- entrepreneurship books

### 11.2 Ingestion flow

When `ingest_all()` runs:

1. scan `DOCS_PATH` for `.pdf` files
2. extract text from each PDF
3. split text into chunks
4. create UUIDs per chunk
5. embed chunks in batch
6. add chunks to ChromaDB

### 11.3 PDF extraction behavior

Preferred:

- `fitz` from PyMuPDF

Fallback:

- `pdfminer.high_level.extract_text`

Important note:

- neither `pymupdf` nor `pdfminer` is present in current `backend/requirements.txt`
- so ingestion may depend on separately installed packages in the environment

### 11.4 Chunking strategy

Defaults:

- chunk size: `500` characters
- overlap: `50` characters

Why overlap matters:

- keeps continuity between chunk boundaries
- improves retrieval quality when meaning spans chunk edges

### 11.5 Sample fallback knowledge

If no PDFs exist, the script inserts built-in startup/business sample chunks.

This is a good backup path for testing.

### 11.6 First-run behavior

`backend/run.py` checks whether `./vector_store/chroma_db` exists.

If missing, it tries to run:

- `python -m ai_engine.ingest_docs`

Then it starts FastAPI with Uvicorn.

## 12. Frontend Working by Page

### 12.1 `frontend/index.html`

Landing page only.

Purpose:

- marketing/home page
- shows features and process
- links to analysis/chat/dashboard

It is static and does not call backend APIs directly.

### 12.2 `frontend/pages/login.html`

Purpose:

- authenticate existing users

Expected behavior:

- submit email/password
- call `api.login()`
- save auth token
- redirect to dashboard or app page

### 12.3 `frontend/pages/register.html`

Purpose:

- create new user account with extended profile fields

Calls:

- `api.register(...)`

### 12.4 `frontend/pages/dashboard.html`

Purpose:

- main signed-in summary screen

Calls:

- `api.getDashboard()`
- `api.deleteIdea()`
- `api.analyzeIdea()`

Shows:

- total analyses
- analyzed count
- pending count
- categories explored
- recent ideas
- pseudo visual score bars
- activity list

Note:

- it uses a hardcoded score visual for cards when analyzed, not the real stored `idea_score`
- the real detailed score is used more clearly in the chat result view

### 12.5 `frontend/pages/form.html`

Purpose:

- multi-step idea submission form

Form sections:

- business idea
- category
- stage
- location
- budget slider
- target market
- report preferences

Behavior:

1. validate required inputs
2. build idea payload
3. call `api.createIdea()`
4. immediately call `api.analyzeIdea()`
5. show success screen
6. link to chat result page

### 12.6 `frontend/pages/chat.html`

Purpose:

- follow-up conversational AI interface
- display previously generated analysis

Behavior:

1. if `idea_id` exists in URL, call `api.getResult(idea_id)`
2. render saved analysis summary
3. keep a browser-side `conversationHistory`
4. send follow-up messages through `api.sendChat(...)`
5. receive AI response from backend chat route

Voice input:

- uses browser Web Speech API
- this part is frontend/browser-native, not Python-based STT

### 12.7 `frontend/pages/history.html`

Purpose:

- tabular listing of all saved ideas

Behavior:

- loads ideas with `api.listIdeas()`
- filters in browser by search, category, status
- allows delete or analyze

### 12.8 `frontend/pages/analytics.html`

Purpose:

- visual charts using Chart.js

Calls:

- `api.getDashboard()`
- `api.listIdeas()`

Shows:

- category distribution doughnut
- analyzed vs pending doughnut
- ideas over time bar chart

### 12.9 `frontend/pages/settings.html`

Purpose:

- profile + app preferences

Behavior:

- loads `/me`
- loads `/settings/`
- saves via `PUT /settings/`
- requires current password

## 13. What Queries Are Happening

There are two kinds of "queries" in this project.

### 13.1 SQL queries

SQLAlchemy generates relational database queries such as:

- find user by email
- find user by id from JWT
- list user ideas ordered by date
- get one idea by user ownership
- insert new idea
- insert/update AI response
- count/dashboard statistics
- fetch/update settings

Common patterns seen:

- `db.query(models.User).filter(models.User.email == payload.email).first()`
- `db.query(models.Idea).filter(models.Idea.user_id == current_user.id).all()`
- `db.query(models.AIResponse).filter(models.AIResponse.idea_id == idea_id).first()`

### 13.2 Vector similarity queries

ChromaDB vector query:

- embed current idea text
- `col.query(query_embeddings=[query_embedding], n_results=5)`

This returns the nearest business knowledge chunks.

Those chunks are not shown directly to the user. They are inserted into the prompt as background context.

## 14. Logging and Runtime Behavior

Logging is enabled in `backend/main.py`.

Outputs go to:

- console
- `backend/growthpilot.log` when backend runs from `backend/`

Observed runtime details in logs:

- sentence-transformer model was loaded successfully
- ChromaDB started successfully
- retrieval returned 5 chunks
- Ollama calls were attempted
- some chat route timeouts occurred
- Chroma telemetry produced harmless-looking PostHog errors

Important operational note:

- the logs show the embedding model running on CPU
- so this setup currently appears CPU-friendly, though slower than GPU inference

## 15. Testing Data and Current State Check

### 15.1 Found sample/real stored data

Yes, there is existing data in:

- `backend/growthpilot.db`

This includes:

- 18 users
- 12 ideas
- 12 AI responses

So there is already useful testing/demo data available.

### 15.2 Found vector knowledge data

Yes, vector knowledge is already stored in:

- `backend/vector_store/chroma_db/`

With:

- 1 collection
- 10,350 embeddings

So RAG retrieval has data to work with.

### 15.3 Automated tests

No dedicated automated test suite directory was found in the repo scan.

That means current testing seems to be mainly:

- manual UI testing
- manual API testing
- using dummy AI mode
- using stored sample records

## 16. Library-by-Library Usage From `backend/requirements.txt`

Below is exactly where the listed libraries are used or intended to be used.

### `fastapi==0.111.0`

Used for:

- API app creation
- route definitions
- dependency injection
- request/response handling

Files:

- `backend/main.py`
- all files in `backend/routers/`
- `backend/auth.py`

### `uvicorn[standard]==0.29.0`

Used for:

- running the FastAPI server

Files:

- `backend/run.py`

### `sqlalchemy==2.0.30`

Used for:

- ORM models
- DB sessions
- queries
- relationships

Files:

- `backend/database.py`
- `backend/models.py`
- router files

### `pydantic[email]==2.7.1`

Used for:

- request validation
- response schemas
- email validation

Files:

- `backend/schemas.py`

### `python-jose[cryptography]==3.3.0`

Used for:

- JWT encode/decode

Files:

- `backend/auth.py`

### `passlib[bcrypt]>=1.7.4`

Used for:

- password hashing context

Files:

- `backend/auth.py`

### `bcrypt==4.1.2`

Used indirectly by passlib for:

- actual bcrypt password hashing backend

Files:

- consumed through `backend/auth.py`

### `numpy<2.0`

Used indirectly by:

- sentence-transformers
- embeddings/model math stack

No direct project import was found.

### `python-multipart==0.0.9`

Usually required by FastAPI for:

- form/multipart handling

No explicit direct use was found in current routes, but it is commonly installed with FastAPI projects and may support future file or form-post handling.

### `sentence-transformers==2.7.0`

Used directly for:

- loading `all-MiniLM-L6-v2`
- generating embeddings

Files:

- `backend/ai_engine/embeddings.py`

### `chromadb==0.5.0`

Used directly for:

- persistent vector store
- similarity search
- document collection management

Files:

- `backend/ai_engine/vector_store.py`

### `transformers==4.41.2`

Currently not directly imported in the inspected code.

This looks like a leftover or future-facing dependency from an earlier design where the model may have been loaded directly in Python.

### `torch==2.3.0`

Currently not directly imported in the inspected code.

Likely present because:

- sentence-transformers depends on PyTorch
- or for a future direct local model pipeline

### `peft==0.11.1`

Currently not directly imported in the inspected code.

Likely intended for:

- LoRA/adapter support in an earlier or planned direct-transformer design

### `accelerate==0.30.1`

Currently not directly imported in the inspected code.

Likely intended for:

- future direct HF model loading / acceleration

### `python-dotenv==1.0.1`

Used directly for:

- loading environment variables from `.env`

Files:

- `backend/main.py`
- `backend/database.py`
- `backend/ai_engine/llm.py`
- `backend/ai_engine/rag_pipeline.py`
- `backend/routers/chat_routes.py`

### `aiofiles==23.2.1`

No direct import was found in the inspected code.

Potentially leftover or reserved for future async file handling.

### `httpx==0.27.0`

Used directly for:

- calling local Ollama HTTP APIs

Files:

- `backend/ai_engine/llm.py`
- `backend/routers/chat_routes.py`

## 17. Important Design Observations

### 17.1 Strengths

- clean separation between frontend, backend, and AI engine
- easy local development with dummy mode
- persistent relational storage + persistent vector storage
- good modular route structure
- RAG pipeline has parsing, normalization, and fallback safety
- frontend has a coherent user journey

### 17.2 Mismatches / caveats

- README/comments still mention Phi-3-mini and LoRA-style design, but current runtime path is Ollama-based
- `transformers`, `torch`, `peft`, `accelerate`, and `aiofiles` are not directly used in the inspected code
- ingestion script expects PDF extraction libraries not declared in current requirements
- two SQLite files can confuse developers
- chat history is not persisted in DB
- dashboard cards use some placeholder score visuals

### 17.3 Current architecture summary in one line

The actual working architecture is:

- static frontend -> FastAPI backend -> SQLite for app data -> SentenceTransformer embeddings -> ChromaDB retrieval -> Ollama local LLM -> structured JSON result -> frontend dashboard/chat rendering

## 18. Recommended Mental Model of the Whole App

If you want to explain this project simply:

1. Frontend collects idea and displays outputs.
2. FastAPI handles auth, CRUD, settings, and AI routes.
3. SQLite stores users, ideas, settings, and AI analysis results.
4. Business PDFs are chunked and embedded into ChromaDB.
5. When a user analyzes an idea, the app embeds the idea text.
6. ChromaDB returns the most relevant business knowledge chunks.
7. Those chunks are added into the prompt.
8. Ollama runs the local LLM and returns structured JSON.
9. Backend stores that JSON-derived result in SQLite.
10. Frontend renders the result and enables follow-up chat.

## 19. Files Most Important to Understand First

If someone wants to understand the project quickly, these are the most important files:

- `backend/main.py`
- `backend/database.py`
- `backend/models.py`
- `backend/schemas.py`
- `backend/auth.py`
- `backend/routers/ai_routes.py`
- `backend/ai_engine/rag_pipeline.py`
- `backend/ai_engine/llm.py`
- `backend/ai_engine/embeddings.py`
- `backend/ai_engine/vector_store.py`
- `backend/ai_engine/ingest_docs.py`
- `frontend/js/api.js`
- `frontend/pages/form.html`
- `frontend/pages/chat.html`
- `frontend/pages/dashboard.html`

## 20. Final Conclusion

GrowthPilot is a business-idea analysis SaaS app with:

- browser-based frontend
- FastAPI backend
- JWT authentication
- SQLite relational persistence
- ChromaDB vector retrieval
- sentence-transformers embedding model
- local LLM inference through Ollama
- RAG-based structured business analysis output

The project is already functional with existing sample data and a populated vector store. The most important thing to understand is that the application is not using only a plain chat model. It uses a retrieval pipeline: user idea -> embeddings -> vector search -> prompt construction -> local LLM -> parsed JSON -> stored analysis -> frontend rendering.
