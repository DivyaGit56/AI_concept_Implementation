# Banking RAG Agent - System Design

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React + Vite)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Login/Reg   │  │  Chat UI     │  │  Admin Dash  │  │  Support Tickets│ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────────┘ │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ REST API (JWT)
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                         BACKEND (FastAPI)                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Auth (JWT)  │  │ Chat API    │  │ Admin API   │  │ Tickets API         │ │
│  └─────────────┘  └──────┬──────┘  └─────────────┘  └─────────────────────┘ │
│                            │                                                 │
│  ┌─────────────────────────▼──────────────────────────────────────────────┐ │
│  │                    AI AGENT ORCHESTRATOR                                │ │
│  │  Query Classifier → Query Rewriter → Route (RAG | Tools) → Response    │ │
│  └────────────┬───────────────────────────────┬───────────────────────────┘ │
│               │                               │                              │
│  ┌────────────▼────────────┐    ┌─────────────▼─────────────┐               │
│  │      RAG PIPELINE       │    │    MOCK BANKING TOOLS     │               │
│  │  Retrieve→Rerank→LLM    │    │  balance, transactions,   │               │
│  └────────────┬────────────┘    │  profile, loan, tickets   │               │
│               │                 └───────────────────────────┘               │
└───────────────┼─────────────────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────────────────────────────┐
│  ChromaDB (Vector Store)  │  MongoDB (Users, Chats, Docs, Tickets, Feedback)│
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Folder Structure

```
banking-rag-agent/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── api/
│       │   ├── auth.py
│       │   ├── chat.py
│       │   ├── documents.py
│       │   ├── tickets.py
│       │   └── admin.py
│       ├── models/
│       ├── schemas/
│       ├── services/
│       ├── rag/
│       │   ├── loader.py
│       │   ├── chunker.py
│       │   ├── embeddings.py
│       │   ├── vector_store.py
│       │   ├── retriever.py
│       │   ├── reranker.py
│       │   ├── query_classifier.py
│       │   ├── query_rewriter.py
│       │   └── generator.py
│       ├── agents/
│       │   ├── orchestrator.py
│       │   └── tools.py
│       ├── database/
│       ├── auth/
│       └── utils/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       └── hooks/
├── data/documents/
├── vector_store/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## 3. Database Schema (MongoDB)

- **users**: id, name, email, password_hash, role, created_at
- **chat_sessions**: id, user_id, title, created_at, updated_at
- **messages**: session_id, role, content, sources[], timestamp, feedback
- **documents**: filename, category, upload_date, chunk_count, status, file_path
- **support_tickets**: ticket_id, user_id, issue, status, created_at, resolution
- **feedback**: message_id, user_id, rating, comment, timestamp

## 4. RAG Workflow

Document → Loader → Clean → Chunk → Embed → ChromaDB
Query → Classify → Rewrite → Embed → Similarity Search → Rerank → Threshold Check → LLM (grounded) → Answer + Sources

## 5. API Design

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register user |
| POST | /auth/login | Login, get JWT |
| POST | /chat | Send message, get RAG response |
| GET | /chat/history | Get chat sessions |
| GET | /chat/sessions/{id}/messages | Get session messages |
| POST | /documents/upload | Admin upload document |
| GET | /documents | List documents |
| DELETE | /documents/{id} | Delete document |
| POST | /tickets | Create support ticket |
| GET | /tickets | List user tickets |
| GET | /admin/analytics | Admin analytics |
| POST | /feedback | Submit feedback |
| GET | /health | Health check |

## 6. Development Phases

1. **Phase 1**: Backend foundation (config, MongoDB, auth, schemas)
2. **Phase 2**: RAG pipeline (loader, chunker, embeddings, vector store, retriever, reranker)
3. **Phase 3**: Agent layer + mock banking tools
4. **Phase 4**: API endpoints (chat, documents, tickets, admin)
5. **Phase 5**: Sample banking documents + seed data
6. **Phase 6**: React frontend (auth, chat, admin)
7. **Phase 7**: Evaluation module + tests + README
