"""Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class DocumentCategory(str, Enum):
    FAQ = "General FAQ"
    ACCOUNT = "Account"
    KYC = "KYC"
    LOAN = "Loan"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    BANKING_CHARGES = "Banking Charges"
    FUND_TRANSFER = "Fund Transfer"
    INTEREST_RATES = "Interest Rates"
    COMPLAINTS = "Complaints"
    OTHER = "Other"


class QueryCategory(str, Enum):
    ACCOUNT = "Account"
    KYC = "KYC"
    LOAN = "Loan"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    BANKING_CHARGES = "Banking Charges"
    FUND_TRANSFER = "Fund Transfer"
    INTEREST_RATES = "Interest Rates"
    COMPLAINTS = "Complaints"
    GENERAL_FAQ = "General FAQ"
    ACCOUNT_DATA = "Account Data"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


# Auth
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole


# Chat
class SourceCitation(BaseModel):
    filename: str
    section: Optional[str] = None
    page: Optional[int] = None
    relevance_score: Optional[float] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    regenerate: bool = False


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    answer: str
    sources: List[SourceCitation] = []
    query_category: Optional[str] = None
    route: str = "rag"
    confidence: Optional[float] = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: List[SourceCitation] = []
    timestamp: datetime
    feedback: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


# Documents
class DocumentResponse(BaseModel):
    id: str
    filename: str
    category: str
    upload_date: datetime
    chunk_count: int
    status: str
    file_size: Optional[int] = None


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    category: str
    chunk_count: int
    status: str
    message: str


# Tickets
class TicketCreate(BaseModel):
    issue: str = Field(..., min_length=10, max_length=2000)
    category: Optional[str] = None


class TicketResponse(BaseModel):
    ticket_id: str
    issue: str
    status: TicketStatus
    created_at: datetime
    resolution: Optional[str] = None


# Feedback
class FeedbackCreate(BaseModel):
    message_id: str
    rating: str = Field(..., pattern="^(up|down)$")
    comment: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    id: str
    message_id: str
    rating: str
    comment: Optional[str] = None


# Admin
class AnalyticsResponse(BaseModel):
    total_users: int
    total_sessions: int
    total_messages: int
    total_documents: int
    total_tickets: int
    open_tickets: int
    feedback_positive: int
    feedback_negative: int
    top_categories: List[dict[str, Any]] = []
    frequent_questions: List[dict[str, Any]] = []


class HealthResponse(BaseModel):
    status: str
    database: str
    vector_store: str
    llm: str


TokenResponse.model_rebuild()
