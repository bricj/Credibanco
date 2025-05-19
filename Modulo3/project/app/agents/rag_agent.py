import os
import requests
from io import BytesIO
from pypdf import PdfReader
from pypdf import PdfReader
from langchain.vectorstores import PGVector
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

def create_rag_agent(
    pdf_url: str,
    pg_connection_string: str = "postgresql+psycopg2://ai:ai@pgvector:5432/ai",
    collection_name: str = "financial_documents",
    embedding_model: str = "text-embedding-3-small",
    llm_model: str = "gpt-4o-mini",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    k_retrieval: int = 5,
    temperature: float = 0.2
):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY no está definido en las variables de entorno")

    # Descargar el PDF desde la URL
    response = requests.get(pdf_url)
    response.raise_for_status()
    pdf_bytes = BytesIO(response.content)

    # Leer texto plano del PDF con pypdf
    reader = PdfReader(pdf_bytes)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() or ""

    # Dividir el texto en fragmentos
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts = text_splitter.split_text(full_text)

    # Configurar embeddings
    embeddings = OpenAIEmbeddings(
        model=embedding_model,
        openai_api_key=openai_api_key
    )

    # Crear o conectar con la base de datos vectorial PostgreSQL
    db = PGVector.from_texts(
        texts,
        embedding=embeddings,
        collection_name=collection_name,
        connection_string=pg_connection_string,
    )

    # Configurar modelo LLM
    llm = ChatOpenAI(
        model=llm_model,
        temperature=temperature,
        openai_api_key=openai_api_key
    )

    # Crear cadena RAG para preguntas y respuestas
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": k_retrieval})
    )
    return qa

# if __name__ == "__main__":
#     pdf_url = "https://www.apple.com/environment/pdf/Apple_Environmental_Progress_Report_2024.pdf"  # Cambia por tu PDF
#     agent = create_rag_agent(pdf_url)
#     query = "¿Cuál es el objetivo principal del documento?"
#     result = agent.run(query)
#     print("Respuesta:", result)
