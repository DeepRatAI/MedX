"""Initial MedeX V2 schema - users, conversations, messages, patient contexts, tool executions

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-06

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================================================
    # Users Table
    # ==========================================================================
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column(
            "detected_type", sa.String(20), nullable=False, server_default="unknown"
        ),
        sa.Column("preferences", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column(
            "request_count_today", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("last_request_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "is_deleted", sa.Boolean, nullable=False, server_default="false", index=True
        ),
    )

    op.create_index("ix_users_created_at", "users", ["created_at"])
    op.create_index("ix_users_type_active", "users", ["detected_type", "is_deleted"])

    # ==========================================================================
    # Conversations Table
    # ==========================================================================
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "title", sa.String(255), nullable=False, server_default="Nueva conversación"
        ),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("message_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("detected_specialty", sa.String(100), nullable=True, index=True),
        sa.Column(
            "emergency_detected",
            sa.Boolean,
            nullable=False,
            server_default="false",
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            index=True,
        ),
        sa.Column(
            "is_deleted", sa.Boolean, nullable=False, server_default="false", index=True
        ),
        sa.CheckConstraint("message_count >= 0", name="ck_conversations_message_count"),
    )

    op.create_index(
        "ix_conversations_user_updated", "conversations", ["user_id", "updated_at"]
    )
    op.create_index(
        "ix_conversations_active",
        "conversations",
        ["user_id", "is_deleted", "updated_at"],
    )

    # ==========================================================================
    # Messages Table
    # ==========================================================================
    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("sequence_number", sa.Integer, nullable=False),
        sa.Column("role", sa.String(20), nullable=False, index=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tool_executions", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            index=True,
        ),
        sa.UniqueConstraint(
            "conversation_id", "sequence_number", name="uq_messages_conv_seq"
        ),
        sa.CheckConstraint("sequence_number > 0", name="ck_messages_seq_positive"),
        sa.CheckConstraint("token_count >= 0", name="ck_messages_tokens_positive"),
    )

    op.create_index(
        "ix_messages_conv_seq", "messages", ["conversation_id", "sequence_number"]
    )
    op.create_index("ix_messages_role_created", "messages", ["role", "created_at"])

    # ==========================================================================
    # Patient Contexts Table
    # ==========================================================================
    op.create_table(
        "patient_contexts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "patient_reference",
            sa.String(50),
            nullable=False,
            server_default="patient_1",
        ),
        sa.Column("age_years", sa.Integer, nullable=True),
        sa.Column("sex", sa.String(20), nullable=True),
        sa.Column("chief_complaint", sa.Text, nullable=True),
        sa.Column("symptoms", postgresql.JSONB, nullable=True, server_default="[]"),
        sa.Column("vital_signs", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column(
            "medical_history", postgresql.JSONB, nullable=True, server_default="{}"
        ),
        sa.Column("current_medications", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("allergies", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("lab_results", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column(
            "emergency_level",
            sa.String(20),
            nullable=False,
            server_default="none",
            index=True,
        ),
        sa.Column("emergency_indicators", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint(
            "conversation_id",
            "patient_reference",
            "version",
            name="uq_patient_context_version",
        ),
        sa.CheckConstraint(
            "age_years >= 0 AND age_years <= 150", name="ck_patient_age_range"
        ),
        sa.CheckConstraint("version > 0", name="ck_patient_version_positive"),
    )

    op.create_index(
        "ix_patient_contexts_conv_ref",
        "patient_contexts",
        ["conversation_id", "patient_reference"],
    )
    op.create_index(
        "ix_patient_contexts_emergency", "patient_contexts", ["emergency_level"]
    )

    # ==========================================================================
    # Tool Executions Table
    # ==========================================================================
    op.create_table(
        "tool_executions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("tool_name", sa.String(100), nullable=False, index=True),
        sa.Column("tool_category", sa.String(50), nullable=False, index=True),
        sa.Column("input_params", postgresql.JSONB, nullable=False),
        sa.Column("output_result", postgresql.JSONB, nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("error_traceback", sa.Text, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("cache_hit", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            index=True,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("latency_ms >= 0", name="ck_tool_latency_positive"),
    )

    op.create_index(
        "ix_tool_exec_conv_tool", "tool_executions", ["conversation_id", "tool_name"]
    )
    op.create_index(
        "ix_tool_exec_status_time", "tool_executions", ["status", "started_at"]
    )
    op.create_index(
        "ix_tool_exec_category", "tool_executions", ["tool_category", "status"]
    )

    # ==========================================================================
    # Knowledge Base Index Table
    # ==========================================================================
    op.create_table(
        "kb_index",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("qdrant_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("collection_name", sa.String(100), nullable=False, index=True),
        sa.Column("source_type", sa.String(50), nullable=False, index=True),
        sa.Column("source_id", sa.String(100), nullable=False, index=True),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column(
            "embedding_model",
            sa.String(100),
            nullable=False,
            server_default="all-MiniLM-L6-v2",
        ),
        sa.Column(
            "embedding_dimension", sa.Integer, nullable=False, server_default="384"
        ),
        sa.Column(
            "indexed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            index=True,
        ),
        sa.CheckConstraint("chunk_index >= 0", name="ck_kb_chunk_index_positive"),
        sa.CheckConstraint("embedding_dimension > 0", name="ck_kb_embed_dim_positive"),
    )

    op.create_index("ix_kb_source_type_id", "kb_index", ["source_type", "source_id"])
    op.create_index(
        "ix_kb_collection_indexed", "kb_index", ["collection_name", "indexed_at"]
    )

    # ==========================================================================
    # Triggers for updated_at
    # ==========================================================================
    # Create trigger function (should already exist from init-db.sql)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Apply triggers to tables with updated_at
    for table in ["users", "conversations", "patient_contexts"]:
        op.execute(f"""
            CREATE TRIGGER tr_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers
    for table in ["users", "conversations", "patient_contexts"]:
        op.execute(f"DROP TRIGGER IF EXISTS tr_{table}_updated_at ON {table};")

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("kb_index")
    op.drop_table("tool_executions")
    op.drop_table("patient_contexts")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("users")
