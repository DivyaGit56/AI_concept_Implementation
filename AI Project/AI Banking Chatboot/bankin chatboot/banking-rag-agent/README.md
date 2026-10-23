# Banking RAG Agent

An enterprise-grade **AI-Powered Banking Customer Support Agent** built with Retrieval-Augmented Generation (RAG). DemoBank AI answers customer questions by retrieving relevant information from official banking policy documents — never inventing fees, rates, or regulations.

![Architecture](docs/architecture.png)

## Problem Statement

Banking customers frequently need answers about policies, eligibility, charges, and procedures. Traditional FAQ pages are hard to navigate, and generic chatbots hallucinate incorrect financial information. This project solves that by grounding every answer in verified banking documents with source citations.

## Features

- **RAG-Powered Q&A** — Retrieves from 13+ banking policy documents before generating answers
- **Source Citations** — Every answer includes document name, section, and page references
- **Hallucination Prevention** — Strict grounding with relevance thresholds; refuses to answer when context is insufficient
- **Query Classification** — Routes queries to Account, KYC, Loan, Cards, Charges, etc.
- **Conversational Query Rewriting** — Resolves pronouns using chat history ("What documents for it?" → "What documents for home loan?")
- **Cross-Encoder Reranking** — Improves retrieval accuracy with ms-marco-MiniLM reranker
- **AI Agent Layer** — Routes account-data queries to mock banking tools (balance, transactions, loan status)
- **Support Tickets** — Auto-creates tickets for unresolved issues
- **Admin Dashboard** — Upload/delete/re-index documents, view analytics, tickets, and FAQs
- **JWT Authentication** — Customer and Admin roles with role-based access
- **Feedback System** — Thumbs up/down on AI responses
- **RAG Evaluation Module** — Measures retrieval accuracy, faithfulness, and hallucination rate

## Architecture

```
┌──────────────┐     REST/JWT     ┌──────────────────────────────────┐
│  React UI    │ ◄──────────────► │  FastAPI Backend                 │
│  Chat/Admin  │                  │  ┌────────────┐  ┌────────────┐ │
└──────────────┘                  │  │ RAG Pipeline│  │ AI Agent   │ │
                                  │  │ Retrieve   │  │ Tools/API  │ │
                                  │  │ Rerank     │  │ Tickets    │ │
                                  │  │ Generate   │  └────────────┘ │
                                  │  └─────┬──────┘                  │
                                  └────────┼─────────────────────────┘
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                         ChromaDB      MongoDB      LLM API
                        (Vectors)    (Users/Chats)  (OpenAI)
```

## RAG Pipeline

```
Document (PDF/TXT)
    → Document Loader (PyPDF/TextLoader)
    → Text Cleaning
    → Chunking (800 tokens, 150 overlap)
    → HuggingFace Embeddings (all-MiniLM-L6-v2)
    → ChromaDB Vector Store
    → Query Classification
    → Query Rewriting (conversational context)
    → Similarity Search (Top-K=10)
    → Cross-Encoder Reranking (Top-K=5)
    → Relevance Threshold Check (0.35)
    → Grounded LLM Generation
    → Answer + Source Citations
```

## Technology Stack & Rationale

| Technology | Why |
|---|---|
| **FastAPI** | High-performance async Python framework with automatic OpenAPI docs |
| **React + Vite** | Modern, fast frontend with component-based architecture |
| **LangChain** | Modular document loading, splitting, and vector store integration |
| **ChromaDB** | Lightweight, persistent vector database — no external server needed |
| **HuggingFace Embeddings** | Free, local `all-MiniLM-L6-v2` model — no API cost for embeddings |
| **Cross-Encoder Reranker** | Significantly improves retrieval precision over bi-encoder alone |
| **MongoDB** | Flexible document store for users, chats, tickets, and metadata |
| **JWT + bcrypt** | Industry-standard authentication with role-based authorization |
| **OpenAI-compatible LLM** | Works with OpenAI, Groq, or local Ollama for answer generation |

## Project Structure

```
banking-rag-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment configuration
│   │   ├── api/                 # REST API routes
│   │   ├── auth/                # JWT & password hashing
│   │   ├── rag/                 # RAG pipeline components
│   │   ├── agents/              # AI agent & mock banking tools
│   │   ├── services/            # Business logic
│   │   ├── schemas/             # Pydantic models
│   │   └── database/            # MongoDB connection
│   └── scripts/seed.py          # Seed users & ingest documents
├── frontend/
│   └── src/
│       ├── components/          # Chat UI components
│       ├── pages/               # Login, Dashboard, Admin
│       ├── services/            # API client
│       └── hooks/               # Auth context
├── data/documents/              # Sample banking policy documents
├── vector_store/                # ChromaDB persistence
├── tests/                       # API & evaluation tests
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)

### 1. Clone and Setup Backend

```bash
cd banking-rag-agent

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env    # Windows
# cp .env.example .env    # macOS/Linux

# Edit .env and set your LLM_API_KEY
```

### 2. Setup Frontend

```bash
cd frontend
npm install
```

### 3. Start MongoDB

Ensure MongoDB is running on `mongodb://localhost:27017` (default).

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DB` | Database name | `banking_rag` |
| `JWT_SECRET_KEY` | Secret for JWT signing | (change in production) |
| `LLM_API_KEY` | OpenAI/Groq API key | (required for LLM answers) |
| `LLM_BASE_URL` | LLM API endpoint | `https://api.openai.com/v1` |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | HuggingFace embedding model | `all-MiniLM-L6-v2` |
| `RELEVANCE_THRESHOLD` | Min score for answering | `0.35` |

## How to Run

### Step 1: Seed Database & Index Documents

```bash
cd backend
python scripts/seed.py
```

This creates demo users and ingests all 13 banking policy documents into ChromaDB.

### Step 2: Start Backend

```bash
cd backend
python run.py
```

API available at: http://localhost:8000
Swagger docs at: http://localhost:8000/docs

### Step 3: Start Frontend

```bash
cd frontend
npm run dev
```

UI available at: http://localhost:5173

### Step 4: Login & Test

| Role | Email | Password |
|---|---|---|
| Customer | demo@customer.com | demo123 |
| Admin | admin@demobank.com | admin123 |

## API Documentation

Full interactive docs at `/docs` (Swagger) and `/redoc`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | Public | Register new user |
| POST | `/auth/login` | Public | Login, receive JWT |
| POST | `/chat` | Customer | Send message, get RAG answer |
| GET | `/chat/history` | Customer | List chat sessions |
| GET | `/chat/sessions/{id}/messages` | Customer | Get session messages |
| DELETE | `/chat/sessions/{id}` | Customer | Clear conversation |
| POST | `/documents/upload` | Admin | Upload & index document |
| GET | `/documents` | Auth | List all documents |
| DELETE | `/documents/{id}` | Admin | Delete document |
| POST | `/documents/{id}/reindex` | Admin | Re-index document |
| POST | `/tickets` | Customer | Create support ticket |
| GET | `/tickets` | Auth | List tickets |
| POST | `/feedback` | Customer | Submit thumbs up/down |
| GET | `/admin/analytics` | Admin | Dashboard analytics |
| GET | `/health` | Public | System health check |

## Example Questions

**Policy Questions (RAG):**
- "What documents are required for a personal loan?"
- "What is the minimum balance for a savings account?"
- "What are the home loan interest rates?"
- "How do I block my debit card?"
- "What are NEFT charges via internet banking?"
- "What is the KYC update frequency?"

**Account Data (Mock Tools):**
- "Show my recent transactions"
- "What is my account balance?"
- "What is my loan status?"

**Conversational (Query Rewriting):**
- User: "What is the eligibility for a home loan?"
- User: "What documents do I need for it?" → Rewritten to include home loan context

**Support Tickets:**
- "My debit card isn't working and I've tried everything"

## RAG Evaluation

Run the evaluation module:

```bash
cd backend
python -m app.rag.evaluation
```

Metrics measured:
- **Retrieval Accuracy** — Did the correct source document appear in results?
- **Context Relevance** — Average reranker score of retrieved chunks
- **Answer Relevance** — Does the answer contain expected key terms?
- **Faithfulness** — Are numeric claims grounded in retrieved context?
- **Hallucination Rate** — Percentage of answers with ungrounded claims

## Screenshots

> Placeholder: Add screenshots of the chat interface, admin dashboard, and source citations here.

## Security

- JWT tokens with configurable expiry
- bcrypt password hashing
- Role-based authorization (customer vs admin)
- Rate limiting (30 requests/minute)
- Input validation via Pydantic
- No hardcoded secrets — all via environment variables
- Synthetic demo data only — no real financial information

## Future Improvements

- [ ] Streaming responses for real-time answer generation
- [ ] Multi-language support (Hindi, regional languages)
- [ ] Voice input/output integration
- [ ] Advanced analytics with conversation clustering
- [ ] A/B testing for prompt variations
- [ ] Redis caching for frequent queries
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline with automated RAG evaluation
- [ ] PDF page-level citation with bounding boxes
- [ ] Human-in-the-loop review for low-confidence answers

## License

MIT — For educational and demonstration purposes only. Not for production banking use.
