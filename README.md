# 🧠 CHATLAW — Agentic Legal AI System

A fully-fledged **agentic, retrieval-augmented, multi-domain legal analysis system** built inside a single Colab notebook.

ChatLaw behaves like a **junior advocate**, **legal researcher**, and **senior counsel** all chained together into one intelligent pipeline.

This README explains **EVERYTHING** — the architecture, models, theory, agents, and the full pipeline.

---

# 🚀 What This System Actually Does

ChatLaw is an **end-to-end AI legal assistant** that:

* Understands any legal query (civil, family, property, criminal, contract)
* Classifies the case domain
* Asks targeted follow-up questions like a real lawyer
* Extracts structured facts from answers
* Builds a knowledge graph from the conversation
* Performs legal search using FAISS + SBERT
* Runs deep structured analysis using a 4-bit quantized LLM
* Produces a **6-section professional legal report**
* Avoids hallucination + avoids repeating reports
* Supports Indian legal datasets + IPC-style reasoning

---

# 🏗️ High-Level Architecture

```
User Query
   ↓
SmartClassifierAgent  →  (family, property, contract, criminal)
   ↓
KnowledgeGraph (initial memory)
   ↓
AdaptiveQuestionGenerator (multi-turn lawyer-style questioning)
   ↓
EntityExtractionAgent (NER + regex)
   ↓
KnowledgeGraph updated
   ↓
ResearchAgent (SBERT embeddings → FAISS search)
   ↓
AnalysisAgent (Mistral 7B → 6-section legal report)
   ↓
Final Output
```

This is **RAG + Agents + KG + LLM** all working in a feedback loop.

---

# 🧩 Components Explained (In Depth)

## 1️⃣ SmartClassifierAgent — *Case Type Detection*

Uses keyword scoring across 4 domains:

* **family** (divorce, custody, maintenance…)
* **property** (land, encroachment, possession…)
* **contract** (agreement, payment, breach…)
* **criminal** (theft, assault, robbery, FIR…)

This ensures every query is routed correctly.

---

## 2️⃣ AdaptiveQuestionGenerator — *Domain-Specific Lawyer Questions*

This agent asks **different** questions depending on `case_type`.

### Family cases:

* How long have you been married?
* Any children?
* Notices exchanged?
* Domestic violence involved?

### Property cases:

* What property type?
* Title ownership?
* Encroachment?
* Boundary dispute timeline?

### Contract cases:

* What was the agreement?
* Written/oral?
* Payment amount & breach date?

### Criminal cases:

Subtype-based:

* theft → item last seen, CCTV
* assault → injuries, witnesses
* robbery → force, weapons
* murder → location, weapon, relationship

---

## 3️⃣ EntityExtractionAgent — *Information Extraction*

Uses:

* **InLegalBERT** (domain NER)
* Regex
* Keyword heuristics

Extracts:

* dates
* values
* parties
* locations
* items

Everything goes into the **KnowledgeGraph**.

---

## 4️⃣ KnowledgeGraph — *Memory System*

Stores:

* `entities` (structured facts)
* `relations` (optional logic links)
* `context` (case_type, situation, subtype)

Produces a compact summary used in retrieval & LLM analysis.

---

## 5️⃣ ResearchAgent — *RAG Retrieval with FAISS*

Uses:

* **InLegal-SBERT** to encode KG summary
* **FAISS (L2 index)** for similarity search
* Searches **Indian legal dataset (~50k Q&A)**
* Extracts top relevant legal documents

This gives the LLM real legal grounding → **fewer hallucinations**.

---

## 6️⃣ AnalysisAgent — *Structured Legal Reasoning*

Builds a structured prompt:

```
CLIENT STATEMENT
FACTS
RELEVANT MATERIAL
CASE TYPE
SUBTYPE
SECTIONS 1–6 TEMPLATE
```

Uses:

* **Mistral-7B-Instruct (4-bit quantized)**
* Temperature 0.3 + top_p 0.85
* max_new_tokens 650 (stable)

Outputs:

### Final Report Structure:

1. Summary of Incident
2. Legal Characterization
3. Legal Reasoning
4. Prosecution & Defence
5. Evidence & Strategy
6. Conclusion

### Anti-Repetition Fix

Ensures the LLM cannot output the report twice.

---

## 7️⃣ AgenticLegalSystem — *The Orchestrator*

This agent controls:

* classification
* questioning loop
* KG enrichment
* retrieval
* analysis generation

Acts like a **real lawyer-client interview + research + opinion writing workflow**.

---

# 📦 Tech Stack (Full, No Bullshit)

### 🧠 Machine Learning

* **Mistral-7B-Instruct v0.2 (4-bit)** — main LLM
* **InLegal-SBERT** — embeddings
* **InLegalBERT** — NER
* **InCaseLawBERT** — zero-shot classification

### 📚 Libraries

* `transformers`
* `sentence-transformers`
* `faiss-cpu`
* `huggingface-hub`
* `bitsandbytes`
* `accelerate`
* `numpy`, `pandas`

### 🔎 Retrieval System

* FAISS L2 vector database
* SBERT embeddings (~768 dimensions)
* Top-k semantic search

### 💾 Storage & Memory

* Knowledge Graph (custom class)
* Document embeddings cached

### 🖥️ Runtime

* Google Colab T4 GPU
* Python 3.x
* 4-bit quantized LLM to fit in 12GB VRAM

---

# 📄 Folder/Code Structure (Colab Notebook)

```
1. Install dependencies
2. Imports + device setup
3. Model configuration
4. Load Mistral 7B
5. Load legal dataset
6. Build FAISS index
7. KnowledgeGraph
8. EntityExtractionAgent
9. ResearchAgent
10. AnalysisAgent (LLM reasoning)
11. SmartClassifier + QGen
12. AgenticLegalSystem
13. Main Loop
```

---

# 🧪 How It Works (End-to-End)

## User:

```
"My husband is abusive. I need a divorce."
```

### Step 1 → Classification:

```
case_type = "family"
```

### Step 2 → Questions:

```
“How long have you been married?”
“Any children involved?”
“What relief do you want?”
```

### Step 3 → Entity Extraction:

```
PARTIES: husband
DURATION: 7 years
FACTS: domestic violence
```

### Step 4 → Retrieval (FAISS):

Finds similar legal Q&A regarding:

* domestic abuse
* divorce
* maintenance

### Step 5 → Analysis:

Mistral outputs:

```
<SECTION 1: SUMMARY OF INCIDENT>
<SECTION 2: LEGAL CHARACTERIZATION>
...
<SECTION 6: CONCLUSION>
```

### Step 6 → Cleaned & delivered.

---

# 🛠️ How to Run (Local Dev)

This repo has a React/Vite frontend (`src/`) and a Python backend (`backend/`). Run them in two terminals for local development.

## Prerequisites
- Node.js 18+ and a package manager (`npm`, `pnpm`, or `yarn`)
- Python 3.10+

## Backend (Python)

1. Create a virtual environment and install deps:

```zsh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Set environment variables (copy the example and fill values):

```zsh
cp .env.example .env
# edit .env to set keys and config
```

3. Run the backend API:

```zsh
# Option A: start script
./start.sh

# Option B: run app directly
python app.py
```

By default it usually serves on `http://127.0.0.1:8000` or `http://127.0.0.1:5000` depending on the app. Check `backend/app.py` or `start.sh` for the exact port.

## Frontend (React + Vite)

1. Install dependencies:

```zsh
cd ..
npm install
```

2. Configure API base URL for local dev (if required):

Edit `src/services/api.js` or `.env` variables used by the frontend to point to the backend (e.g., `http://127.0.0.1:8000`). If using Vite envs, create `.env.local` with:

```zsh
echo 'VITE_API_BASE_URL=http://127.0.0.1:8000' >> .env.local
```

3. Start the dev server:

```zsh
npm run dev
```

Vite will print a local URL like `http://localhost:5173`.

## Run Both Together

Open two terminals:

- Terminal A (backend): `cd backend && source .venv/bin/activate && ./start.sh`
- Terminal B (frontend): `npm run dev`

Ensure the frontend `API_BASE_URL` points to the backend port.

## Production Builds

Frontend build:

```zsh
npm run build
```

The static assets will be in `dist/`.

Backend can be run with any WSGI/ASGI server depending on the framework (e.g., `uvicorn`, `gunicorn`). Check `backend/README.md` for details if present.

## Common Issues
- Backend not reachable: verify port and CORS settings in `backend/app.py`.
- 404 from frontend API calls: confirm `VITE_API_BASE_URL` and routes in `src/services/api.js`.
- Python package errors: re-activate venv and re-run `pip install -r requirements.txt`.
- Node version mismatch: use Node 18+ (`node -v`).

---

# 🛠️ How to Run (Colab Notebook)

If you prefer the original notebook workflow:

1. Open the notebook in Google Colab
2. Run **Cell 1 → 14** sequentially
3. Start entering queries
4. Answer follow-up questions
5. Receive full legal report
6. Save as `.txt` if needed

---

# 🚨 Limitations

* Not legal advice
* Dependent on dataset quality
* Mistral may hallucinate outside controlled prompts
* Extraction accuracy depends on NER model
* Not a replacement for a licensed lawyer

---

# 🎯 Roadmap / Future Work

* Add multi-lingual support
* Add more IPC modules
* Add civil procedure logic
* Improve KG with relation extraction
* Add embedding caching
* Deploy as web app (FastAPI + React)

---

# 🔥 Final Note

This notebook isn’t a toy — it’s a **miniature legal AI platform**:

* RAG
* Multi-agent
* KG memory
* 4-bit LLM inference
* Domain-specific NER
* IPC reasoning
* Automatic legal drafting

All inside a single Colab file.

This README is now **GitHub-ready**.

Paste it → Commit → Flex.
