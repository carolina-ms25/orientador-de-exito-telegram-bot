import pandas as pd
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from loguru import logger

from telegram_agent_aws.config import settings
from telegram_agent_aws.infrastructure.clients.qdrant import get_qdrant_client


def generate_course_documents():
    """Load courses from Excel and convert to LangChain Documents."""
    df = pd.read_excel("./data/knowledge_base_2025.xlsx")
    
    documents = []
    for _, row in df.iterrows():
        # Create rich text content for each course
        content = f"""
Curso: {row['Nombre del curso']}
Formato: {row['Formato']}
Costo: S/ {row['Costo (soles)']} soles
Objetivo: {row['Objetivo']}
Link de inscripción: {row['Link para inscripcion']}

Este curso ofrece {row['Objetivo'].lower()}
El formato de este curso es {row['Formato'].lower()}.
El precio del curso es {row['Costo (soles)']} soles.
Para inscribirse, visita: {row['Link para inscripcion']}
""".strip()
        
        metadata = {
            "course_name": row['Nombre del curso'],
            "format": row['Formato'],
            "price": row['Costo (soles)'],
            "enrollment_link": row['Link para inscripcion']
        }
        
        documents.append(Document(page_content=content, metadata=metadata))
    
    logger.info(f"Generated {len(documents)} course documents from Excel")
    return documents


def index_documents():
    """Index course documents into Qdrant vector store, replacing existing collection."""
    documents = generate_course_documents()
    embeddings = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)

    # This will recreate the collection with new data
    QdrantVectorStore.from_documents(
        documents=documents,
        embedding=embeddings,
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        collection_name="telegram_agent_aws_collection",
        force_recreate=True,  # This ensures old data is replaced
    )

    logger.info(f"Successfully indexed {len(documents)} course documents to Qdrant.")
