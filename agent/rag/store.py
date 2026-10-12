from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from agent.app.config import Settings

_vectorstore: PGVector | None = None


def get_vectorstore(settings: Settings | None = None) -> PGVector:
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore
    if settings is None:
        raise RuntimeError("Vector store not initialized")
    _vectorstore = PGVector(
        embeddings=OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key,
        ),
        collection_name="documents",
        connection=settings.postgres_url,
        use_jsonb=True,
    )
    return _vectorstore


def init_vectorstore(settings: Settings) -> PGVector:
    return get_vectorstore(settings)
