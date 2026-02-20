# =============================================================================
# MedeX - SQLAlchemy ORM Models
# =============================================================================
"""
Database models for MedeX V2 persistence layer.

This module defines all SQLAlchemy ORM models for:
- User management and session tracking
- Conversation history with hierarchical structure
- Message storage with role-based typing
- Patient clinical context extraction
- Tool execution audit trail
- Knowledge base indexing metadata

Design Principles:
- Async-first with asyncpg driver
- UUID primary keys for distributed safety
- Soft deletes for audit compliance
- JSONB for flexible medical metadata
- Proper indexing for query performance
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any

from sqlalchemy import (
    String,
    Text,
    Boolean,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


# =============================================================================
# Base Configuration
# =============================================================================


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Provides:
    - UUID primary key generation
    - Created/updated timestamps
    - Soft delete support
    - Type annotation support
    """

    type_annotation_map = {
        dict[str, Any]: JSONB,
        list[str]: ARRAY(String),
    }


# =============================================================================
# Enums
# =============================================================================


class UserType(str, Enum):
    """User classification for response formatting."""

    PROFESSIONAL = "professional"
    EDUCATIONAL = "educational"
    UNKNOWN = "unknown"


class MessageRole(str, Enum):
    """Message sender role in conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ToolStatus(str, Enum):
    """Tool execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class EmergencyLevel(str, Enum):
    """Clinical emergency classification."""

    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# User Model
# =============================================================================


class User(Base):
    """
    User entity for session and preference management.

    Supports:
    - Anonymous session tracking (no auth required)
    - Detected user type (professional/educational)
    - Preference persistence
    - Rate limiting tracking
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique user identifier",
    )

    # Session tracking
    session_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, comment="Browser/client session identifier"
    )

    # User classification
    detected_type: Mapped[UserType] = mapped_column(
        String(20),
        default=UserType.UNKNOWN,
        comment="Auto-detected user type based on query patterns",
    )

    # Preferences (JSONB for flexibility)
    preferences: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, default=dict, comment="User preferences: language, specialty, etc."
    )

    # Rate limiting
    request_count_today: Mapped[int] = mapped_column(
        Integer, default=0, comment="API requests made today"
    )
    last_request_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Timestamp of last API request"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="User creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp",
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, comment="Soft delete flag"
    )

    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        lazy="selectin",
        order_by="desc(Conversation.updated_at)",
    )

    # Indexes
    __table_args__ = (
        Index("ix_users_created_at", "created_at"),
        Index("ix_users_type_active", "detected_type", "is_deleted"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, type={self.detected_type})>"


# =============================================================================
# Conversation Model
# =============================================================================


class Conversation(Base):
    """
    Conversation entity for chat history persistence.

    Features:
    - Auto-generated titles from first user message
    - Patient context association
    - Message count tracking
    - Soft delete with cascade
    """

    __tablename__ = "conversations"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique conversation identifier",
    )

    # Foreign key
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="Owner user ID",
    )

    # Conversation metadata
    title: Mapped[str] = mapped_column(
        String(255),
        default="Nueva conversación",
        comment="Conversation title (auto-generated or user-defined)",
    )

    summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="AI-generated conversation summary"
    )

    # Message statistics
    message_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Total messages in conversation"
    )

    # Clinical metadata
    detected_specialty: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Detected medical specialty from conversation",
    )

    emergency_detected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        comment="Whether emergency was detected in conversation",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="Conversation creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        index=True,
        comment="Last activity timestamp",
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, comment="Soft delete flag"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        lazy="selectin",
        order_by="Message.sequence_number",
    )

    patient_contexts: Mapped[list["PatientContext"]] = relationship(
        "PatientContext", back_populates="conversation", lazy="selectin"
    )

    # Indexes and constraints
    __table_args__ = (
        Index("ix_conversations_user_updated", "user_id", "updated_at"),
        Index("ix_conversations_active", "user_id", "is_deleted", "updated_at"),
        CheckConstraint("message_count >= 0", name="ck_conversations_message_count"),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title[:30]}...')>"


# =============================================================================
# Message Model
# =============================================================================


class Message(Base):
    """
    Message entity for conversation content storage.

    Features:
    - Role-based typing (user/assistant/system/tool)
    - Token counting for context window management
    - Tool execution references
    - Metadata for debugging/audit
    """

    __tablename__ = "messages"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique message identifier",
    )

    # Foreign key
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        comment="Parent conversation ID",
    )

    # Message ordering
    sequence_number: Mapped[int] = mapped_column(
        Integer, comment="Message order within conversation (1-indexed)"
    )

    # Content
    role: Mapped[MessageRole] = mapped_column(
        String(20), index=True, comment="Message sender role"
    )

    content: Mapped[str] = mapped_column(
        Text, comment="Message content (markdown supported)"
    )

    # Token metrics
    token_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Estimated token count for context window"
    )

    # Tool execution reference
    tool_executions: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String), nullable=True, comment="Associated tool execution IDs"
    )

    # Metadata
    metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, default=dict, comment="Additional message metadata"
    )

    # Model information
    model_used: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="LLM model used for response"
    )

    latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Response generation time in milliseconds"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        comment="Message creation timestamp",
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    # Indexes and constraints
    __table_args__ = (
        Index("ix_messages_conv_seq", "conversation_id", "sequence_number"),
        Index("ix_messages_role_created", "role", "created_at"),
        UniqueConstraint(
            "conversation_id", "sequence_number", name="uq_messages_conv_seq"
        ),
        CheckConstraint("sequence_number > 0", name="ck_messages_seq_positive"),
        CheckConstraint("token_count >= 0", name="ck_messages_tokens_positive"),
    )

    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(role={self.role}, content='{preview}')>"


# =============================================================================
# Patient Context Model
# =============================================================================


class PatientContext(Base):
    """
    Patient clinical context extracted from conversation.

    Features:
    - Structured clinical data extraction
    - Multi-patient support per conversation
    - Version tracking for context updates
    - HIPAA-compliant metadata only (no PII stored)
    """

    __tablename__ = "patient_contexts"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique context identifier",
    )

    # Foreign key
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        comment="Parent conversation ID",
    )

    # Patient identifier (anonymous)
    patient_reference: Mapped[str] = mapped_column(
        String(50),
        default="patient_1",
        comment="Anonymous patient reference within conversation",
    )

    # Demographics (non-identifying)
    age_years: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Patient age in years"
    )

    sex: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Biological sex: male/female/other"
    )

    # Clinical data (JSONB for flexibility)
    chief_complaint: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Primary reason for consultation"
    )

    symptoms: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, default=list, comment="List of symptoms with duration/severity"
    )

    vital_signs: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, default=dict, comment="Vital signs: BP, HR, RR, Temp, SpO2"
    )

    medical_history: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, default=dict, comment="Relevant past medical history"
    )

    current_medications: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String), nullable=True, comment="Current medication list"
    )

    allergies: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String), nullable=True, comment="Known allergies"
    )

    lab_results: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, default=dict, comment="Laboratory results mentioned"
    )

    # Emergency classification
    emergency_level: Mapped[EmergencyLevel] = mapped_column(
        String(20),
        default=EmergencyLevel.NONE,
        index=True,
        comment="Detected emergency level",
    )

    emergency_indicators: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String), nullable=True, comment="Specific emergency indicators found"
    )

    # Version tracking
    version: Mapped[int] = mapped_column(
        Integer, default=1, comment="Context version (incremented on update)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="Context creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp",
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="patient_contexts"
    )

    # Indexes
    __table_args__ = (
        Index("ix_patient_contexts_conv_ref", "conversation_id", "patient_reference"),
        Index("ix_patient_contexts_emergency", "emergency_level"),
        UniqueConstraint(
            "conversation_id",
            "patient_reference",
            "version",
            name="uq_patient_context_version",
        ),
        CheckConstraint(
            "age_years >= 0 AND age_years <= 150", name="ck_patient_age_range"
        ),
        CheckConstraint("version > 0", name="ck_patient_version_positive"),
    )

    def __repr__(self) -> str:
        return f"<PatientContext(id={self.id}, ref={self.patient_reference}, emergency={self.emergency_level})>"


# =============================================================================
# Tool Execution Model
# =============================================================================


class ToolExecution(Base):
    """
    Tool execution audit trail for traceability.

    Features:
    - Full request/response logging
    - Performance metrics
    - Error tracking
    - Cache hit tracking
    """

    __tablename__ = "tool_executions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique execution identifier",
    )

    # Foreign keys
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        comment="Parent conversation ID",
    )

    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        comment="Associated message ID",
    )

    # Tool identification
    tool_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        comment="Tool identifier (e.g., 'icd10_search', 'drug_interactions')",
    )

    tool_category: Mapped[str] = mapped_column(
        String(50),
        index=True,
        comment="Tool category (kb_wrapper, external_api, calculator)",
    )

    # Execution data
    input_params: Mapped[dict[str, Any]] = mapped_column(
        JSONB, comment="Tool input parameters"
    )

    output_result: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, comment="Tool output result"
    )

    # Status tracking
    status: Mapped[ToolStatus] = mapped_column(
        String(20), default=ToolStatus.PENDING, index=True, comment="Execution status"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Error message if failed"
    )

    error_traceback: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Full traceback for debugging"
    )

    # Performance metrics
    latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Execution time in milliseconds"
    )

    cache_hit: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether result was served from cache"
    )

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        comment="Execution start timestamp",
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Execution completion timestamp"
    )

    # Indexes
    __table_args__ = (
        Index("ix_tool_exec_conv_tool", "conversation_id", "tool_name"),
        Index("ix_tool_exec_status_time", "status", "started_at"),
        Index("ix_tool_exec_category", "tool_category", "status"),
        CheckConstraint("latency_ms >= 0", name="ck_tool_latency_positive"),
    )

    def __repr__(self) -> str:
        return f"<ToolExecution(tool={self.tool_name}, status={self.status})>"


# =============================================================================
# Knowledge Base Index Model
# =============================================================================


class KnowledgeBaseIndex(Base):
    """
    Knowledge base indexing metadata for RAG.

    Tracks:
    - Indexed documents/chunks
    - Embedding vectors (stored in Qdrant, referenced here)
    - Source mapping for citations
    """

    __tablename__ = "kb_index"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique index entry identifier",
    )

    # Vector reference
    qdrant_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, comment="Qdrant point ID for vector lookup"
    )

    collection_name: Mapped[str] = mapped_column(
        String(100), index=True, comment="Qdrant collection name"
    )

    # Source information
    source_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        comment="Source type: condition, medication, procedure, etc.",
    )

    source_id: Mapped[str] = mapped_column(
        String(100),
        index=True,
        comment="Original source identifier (e.g., ICD-10 code)",
    )

    source_name: Mapped[str] = mapped_column(
        String(255), comment="Human-readable source name"
    )

    # Chunk information
    chunk_index: Mapped[int] = mapped_column(
        Integer, default=0, comment="Chunk index within source document"
    )

    chunk_text: Mapped[str] = mapped_column(
        Text, comment="Original text chunk (for verification)"
    )

    # Metadata
    metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, default=dict, comment="Additional metadata: category, specialty, etc."
    )

    # Embedding info
    embedding_model: Mapped[str] = mapped_column(
        String(100), default="all-MiniLM-L6-v2", comment="Embedding model used"
    )

    embedding_dimension: Mapped[int] = mapped_column(
        Integer, default=384, comment="Embedding vector dimension"
    )

    # Timestamps
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        comment="Indexing timestamp",
    )

    # Indexes
    __table_args__ = (
        Index("ix_kb_source_type_id", "source_type", "source_id"),
        Index("ix_kb_collection_indexed", "collection_name", "indexed_at"),
        CheckConstraint("chunk_index >= 0", name="ck_kb_chunk_index_positive"),
        CheckConstraint("embedding_dimension > 0", name="ck_kb_embed_dim_positive"),
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBaseIndex(source={self.source_type}:{self.source_id})>"
