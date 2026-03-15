"""
services/embeddings.py
Google Gemini Embeddings using the NEW google-genai SDK (google-genai package).
Switched from google-generativeai to google-genai which uses stable v1 API.
"""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY is not set in .env")

# Try new SDK first, fall back to old SDK
try:
    from google import genai
    from google.genai import types

    _client = genai.Client(api_key=GEMINI_API_KEY)
    _USE_NEW_SDK = True
    EMBEDDING_MODEL = "gemini-embedding-001"
    EMBED_DIMENSION = 768

    def embed_text(text: str) -> list[float]:
        response = _client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return response.embeddings[0].values

    def embed_query(query: str) -> list[float]:
        response = _client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        return response.embeddings[0].values

except ImportError:
    # Fall back to google-generativeai (old SDK)
    import google.generativeai as genai_old
    genai_old.configure(api_key=GEMINI_API_KEY)
    _USE_NEW_SDK = False
    # FIX: use gemini-embedding-001
    EMBEDDING_MODEL = "models/gemini-embedding-001"
    EMBED_DIMENSION = 768

    def embed_text(text: str) -> list[float]:
        result = genai_old.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']

    def embed_query(query: str) -> list[float]:
        result = genai_old.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
            task_type="retrieval_query"
        )
        return result['embedding']


BATCH_SIZE = 50


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed all chunks in batches of 50."""
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        for text in batch:
            all_embeddings.append(embed_text(text))
        print(f"[Embeddings] Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")
    return all_embeddings
