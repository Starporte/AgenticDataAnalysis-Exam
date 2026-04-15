"""Schema initial : tables users, sessions, messages, datasets, visualizations

Revision ID: 001
Revises: None
Create Date: 2025-01-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Table users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("mot_de_passe_hash", sa.String(255), nullable=False),
        sa.Column("nom", sa.String(255), nullable=True),
        sa.Column("est_actif", sa.Boolean(), default=True),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("mis_a_jour_le", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Table analysis_sessions
    op.create_table(
        "analysis_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("nom", sa.String(255), nullable=False, server_default="Nouvelle analyse"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("nom_dataset", sa.String(255), nullable=True),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("mis_a_jour_le", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Table messages
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("contenu", sa.Text(), nullable=False),
        sa.Column("metadata_msg", sa.JSON(), nullable=True),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Table datasets
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("nom_fichier", sa.String(255), nullable=False),
        sa.Column("chemin_fichier", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("taille_octets", sa.Integer(), nullable=True),
        sa.Column("nombre_lignes", sa.Integer(), nullable=True),
        sa.Column("nombre_colonnes", sa.Integer(), nullable=True),
        sa.Column("noms_colonnes", sa.JSON(), nullable=True),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Table visualizations
    op.create_table(
        "visualizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("titre", sa.String(255), nullable=True),
        sa.Column("figure_json", sa.JSON(), nullable=False),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("visualizations")
    op.drop_table("datasets")
    op.drop_table("messages")
    op.drop_table("analysis_sessions")
    op.drop_table("users")
