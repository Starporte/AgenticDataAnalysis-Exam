"""Modeles SQLAlchemy pour la base de donnees."""

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.db.database import Base


class User(Base):
    """Modele utilisateur avec authentification."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    mot_de_passe_hash = Column(String(255), nullable=False)
    nom = Column(String(255), nullable=True)
    est_actif = Column(Boolean, default=True)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())
    mis_a_jour_le = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    sessions = relationship("AnalysisSession", back_populates="utilisateur", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="utilisateur", cascade="all, delete-orphan")


class AnalysisSession(Base):
    """Session d'analyse regroupant messages et visualisations."""
    __tablename__ = "analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    nom = Column(String(255), nullable=False, default="Nouvelle analyse")
    description = Column(Text, nullable=True)
    nom_dataset = Column(String(255), nullable=True)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())
    mis_a_jour_le = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relations
    utilisateur = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan",
                            order_by="Message.cree_le")
    visualisations = relationship("Visualization", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """Message dans une session d'analyse (utilisateur ou agent)."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" ou "assistant"
    contenu = Column(Text, nullable=False)
    metadata_msg = Column(JSON, nullable=True)  # donnees supplementaires (pensee agent, code, etc.)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    session = relationship("AnalysisSession", back_populates="messages")
    visualisations = relationship("Visualization", back_populates="message", cascade="all, delete-orphan")


class Dataset(Base):
    """Dataset uploade par un utilisateur."""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    nom_fichier = Column(String(255), nullable=False)
    chemin_fichier = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    taille_octets = Column(Integer, nullable=True)
    nombre_lignes = Column(Integer, nullable=True)
    nombre_colonnes = Column(Integer, nullable=True)
    noms_colonnes = Column(JSON, nullable=True)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    utilisateur = relationship("User", back_populates="datasets")


class Visualization(Base):
    """Visualisation Plotly generee par l'agent."""
    __tablename__ = "visualizations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, index=True)
    titre = Column(String(255), nullable=True)
    figure_json = Column(JSON, nullable=False)  # Figure Plotly serialisee en JSON
    cree_le = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    session = relationship("AnalysisSession", back_populates="visualisations")
    message = relationship("Message", back_populates="visualisations")
