"""initial schema

Creates every PersonaTwin table. On PostgreSQL it also enables the pgvector
extension and adds HNSW cosine indexes on the three embedding columns.

Revision ID: 0001_initial
Revises: 
Create Date: 2026-10-01 09:23:17.196255
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.config import EMBEDDING_DIM
from app.db.types import EmbeddingVector


revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


VECTOR_INDEXES = (
    ("ix_knowledge_chunks_embedding_hnsw", "knowledge_chunks"),
    ("ix_experience_memories_embedding_hnsw", "experience_memories"),
    ("ix_conversation_memories_embedding_hnsw", "conversation_memories"),
)


def upgrade() -> None:
    is_pg = op.get_bind().dialect.name == "postgresql"
    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('full_name', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('token_version', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    op.create_table('conversations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('topic', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_conversations_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conversations'))
    )
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_conversations_user_id'), ['user_id'], unique=False)

    op.create_table('experience_memories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('experience_type', sa.String(length=24), nullable=False),
    sa.Column('situation', sa.Text(), nullable=False),
    sa.Column('what_happened', sa.Text(), nullable=False),
    sa.Column('lesson_learned', sa.Text(), nullable=False),
    sa.Column('do_differently', sa.Text(), nullable=False),
    sa.Column('context', sa.String(length=200), nullable=False),
    sa.Column('occurred_on', sa.Date(), nullable=True),
    sa.Column('importance', sa.Integer(), nullable=False),
    sa.Column('embedding', EmbeddingVector(EMBEDDING_DIM), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_experience_memories_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_experience_memories'))
    )
    with op.batch_alter_table('experience_memories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_experience_memories_experience_type'), ['experience_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_experience_memories_user_id'), ['user_id'], unique=False)

    op.create_table('knowledge_documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('category', sa.String(length=40), nullable=False),
    sa.Column('source_type', sa.String(length=16), nullable=False),
    sa.Column('source', sa.String(length=500), nullable=False),
    sa.Column('char_count', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_knowledge_documents_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_knowledge_documents'))
    )
    with op.batch_alter_table('knowledge_documents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_knowledge_documents_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_knowledge_documents_user_id'), ['user_id'], unique=False)

    op.create_table('mentor_profiles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('mentor_name', sa.String(length=80), nullable=False),
    sa.Column('bio', sa.Text(), nullable=False),
    sa.Column('expertise_areas', sa.JSON(), nullable=False),
    sa.Column('mentoring_domains', sa.JSON(), nullable=False),
    sa.Column('onboarding_completed', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_mentor_profiles_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_mentor_profiles')),
    sa.UniqueConstraint('user_id', name=op.f('uq_mentor_profiles_user_id'))
    )
    op.create_table('personality_profiles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('communication_style', sa.String(length=32), nullable=False),
    sa.Column('tone', sa.String(length=32), nullable=False),
    sa.Column('teaching_approach', sa.String(length=32), nullable=False),
    sa.Column('decision_style', sa.String(length=32), nullable=False),
    sa.Column('encouragement_style', sa.String(length=32), nullable=False),
    sa.Column('response_length', sa.String(length=16), nullable=False),
    sa.Column('formality', sa.Integer(), nullable=False),
    sa.Column('directness', sa.Integer(), nullable=False),
    sa.Column('warmth', sa.Integer(), nullable=False),
    sa.Column('humor', sa.Integer(), nullable=False),
    sa.Column('values', sa.JSON(), nullable=False),
    sa.Column('signature_phrases', sa.JSON(), nullable=False),
    sa.Column('philosophy_encouragement', sa.Text(), nullable=False),
    sa.Column('philosophy_mistakes', sa.Text(), nullable=False),
    sa.Column('philosophy_decisions', sa.Text(), nullable=False),
    sa.Column('philosophy_teaching', sa.Text(), nullable=False),
    sa.Column('boundaries', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_personality_profiles_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_personality_profiles')),
    sa.UniqueConstraint('user_id', name=op.f('uq_personality_profiles_user_id'))
    )
    op.create_table('tags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_tags_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tags')),
    sa.UniqueConstraint('user_id', 'name', name='uq_tags_user_id_name')
    )
    with op.batch_alter_table('tags', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tags_user_id'), ['user_id'], unique=False)

    op.create_table('user_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('save_conversations', sa.Boolean(), nullable=False),
    sa.Column('use_conversation_memory', sa.Boolean(), nullable=False),
    sa.Column('auto_remember', sa.Boolean(), nullable=False),
    sa.Column('retrieval_top_k', sa.Integer(), nullable=False),
    sa.Column('min_relevance', sa.Float(), nullable=False),
    sa.Column('creativity', sa.Float(), nullable=False),
    sa.Column('show_sources', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_settings_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_settings')),
    sa.UniqueConstraint('user_id', name=op.f('uq_user_settings_user_id'))
    )
    op.create_table('experience_tags',
    sa.Column('experience_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['experience_id'], ['experience_memories.id'], name=op.f('fk_experience_tags_experience_id_experience_memories'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name=op.f('fk_experience_tags_tag_id_tags'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('experience_id', 'tag_id', name=op.f('pk_experience_tags'))
    )
    op.create_table('knowledge_chunks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', EmbeddingVector(EMBEDDING_DIM), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], name=op.f('fk_knowledge_chunks_document_id_knowledge_documents'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_knowledge_chunks_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_knowledge_chunks'))
    )
    with op.batch_alter_table('knowledge_chunks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_knowledge_chunks_document_id'), ['document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_knowledge_chunks_user_id'), ['user_id'], unique=False)

    op.create_table('knowledge_document_tags',
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], name=op.f('fk_knowledge_document_tags_document_id_knowledge_documents'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name=op.f('fk_knowledge_document_tags_tag_id_tags'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('document_id', 'tag_id', name=op.f('pk_knowledge_document_tags'))
    )
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=16), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('topic', sa.String(length=32), nullable=False),
    sa.Column('feedback', sa.String(length=8), nullable=True),
    sa.Column('grounding', sa.String(length=16), nullable=True),
    sa.Column('provider', sa.String(length=32), nullable=True),
    sa.Column('model', sa.String(length=80), nullable=True),
    sa.Column('latency_ms', sa.Integer(), nullable=True),
    sa.Column('trace', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name=op.f('fk_messages_conversation_id_conversations'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_messages_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_messages'))
    )
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_messages_conversation_id'), ['conversation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_messages_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_messages_topic'), ['topic'], unique=False)
        batch_op.create_index(batch_op.f('ix_messages_user_id'), ['user_id'], unique=False)

    op.create_table('conversation_memories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=True),
    sa.Column('message_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('topic', sa.String(length=32), nullable=False),
    sa.Column('embedding', EmbeddingVector(EMBEDDING_DIM), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name=op.f('fk_conversation_memories_conversation_id_conversations'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['message_id'], ['messages.id'], name=op.f('fk_conversation_memories_message_id_messages'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_conversation_memories_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conversation_memories'))
    )
    with op.batch_alter_table('conversation_memories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_conversation_memories_user_id'), ['user_id'], unique=False)

    op.create_table('message_sources',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('message_id', sa.Integer(), nullable=False),
    sa.Column('label', sa.String(length=8), nullable=False),
    sa.Column('source_type', sa.String(length=16), nullable=False),
    sa.Column('source_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('snippet', sa.Text(), nullable=False),
    sa.Column('score', sa.Float(), nullable=False),
    sa.Column('cited', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['message_id'], ['messages.id'], name=op.f('fk_message_sources_message_id_messages'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_message_sources'))
    )
    with op.batch_alter_table('message_sources', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_message_sources_message_id'), ['message_id'], unique=False)

    op.create_table('conversation_memory_tags',
    sa.Column('memory_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['memory_id'], ['conversation_memories.id'], name=op.f('fk_conversation_memory_tags_memory_id_conversation_memories'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name=op.f('fk_conversation_memory_tags_tag_id_tags'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('memory_id', 'tag_id', name=op.f('pk_conversation_memory_tags'))
    )

    if is_pg:
        for name, table in VECTOR_INDEXES:
            op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for name, _ in VECTOR_INDEXES:
            op.execute(f"DROP INDEX IF EXISTS {name}")
    op.drop_table('conversation_memory_tags')
    with op.batch_alter_table('message_sources', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_message_sources_message_id'))

    op.drop_table('message_sources')
    with op.batch_alter_table('conversation_memories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_conversation_memories_user_id'))

    op.drop_table('conversation_memories')
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_messages_user_id'))
        batch_op.drop_index(batch_op.f('ix_messages_topic'))
        batch_op.drop_index(batch_op.f('ix_messages_created_at'))
        batch_op.drop_index(batch_op.f('ix_messages_conversation_id'))

    op.drop_table('messages')
    op.drop_table('knowledge_document_tags')
    with op.batch_alter_table('knowledge_chunks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_knowledge_chunks_user_id'))
        batch_op.drop_index(batch_op.f('ix_knowledge_chunks_document_id'))

    op.drop_table('knowledge_chunks')
    op.drop_table('experience_tags')
    op.drop_table('user_settings')
    with op.batch_alter_table('tags', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tags_user_id'))

    op.drop_table('tags')
    op.drop_table('personality_profiles')
    op.drop_table('mentor_profiles')
    with op.batch_alter_table('knowledge_documents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_knowledge_documents_user_id'))
        batch_op.drop_index(batch_op.f('ix_knowledge_documents_category'))

    op.drop_table('knowledge_documents')
    with op.batch_alter_table('experience_memories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_experience_memories_user_id'))
        batch_op.drop_index(batch_op.f('ix_experience_memories_experience_type'))

    op.drop_table('experience_memories')
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_conversations_user_id'))

    op.drop_table('conversations')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
