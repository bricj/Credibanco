"""
Utilidades para interactuar con la base de datos vectorial PgVector.
"""
import os
from sqlalchemy import create_engine
from langchain.vectorstores import PGVector
from langchain.embeddings.openai import OpenAIEmbeddings

# Obtener URL de la base de datos desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://ai:ai@pgvector:5432/ai")

def get_embeddings_model():
    """Crear y retornar el modelo de embeddings de OpenAI."""
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

def get_vector_store(collection_name="documents"):
    """Obtener una instancia de PGVector para una colección específica."""
    return PGVector(
        collection_name=collection_name,
        connection_string=DATABASE_URL,
        embedding_function=get_embeddings_model()
    )