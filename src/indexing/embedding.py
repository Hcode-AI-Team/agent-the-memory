"""
Embedding para indexação RAG. Vertex AI via Google Gen AI SDK (google-genai) ou mock quando não configurado.
"""

import hashlib
import logging
import os

logger = logging.getLogger(__name__)


def embed_texts(
    texts: list[str],
    *,
    model: str = "text-multilingual-embedding-002",
    project_id: str | None = None,
    location: str | None = None,
    batch_size: int = 5,
    for_query: bool = False,
) -> list[list[float]]:
    """
    Gera embeddings para uma lista de textos.
    Usa Vertex AI Text Embedding se GOOGLE_CLOUD_PROJECT estiver definido;
    caso contrário, retorna vetores mock (determinísticos por texto) para o pipeline rodar sem Vertex.

    Args:
        texts: lista de strings a embedar.
        model: modelo Vertex (ex.: text-multilingual-embedding-002).
        project_id: projeto GCP (default: GOOGLE_CLOUD_PROJECT).
        location: região (default: GOOGLE_CLOUD_REGION).
        batch_size: tamanho do lote para a API.
        for_query: se True, usa RETRIEVAL_QUERY (consulta); senão RETRIEVAL_DOCUMENT (indexação).

    Returns:
        Lista de vetores (listas de float), um por texto.
    """
    if not texts:
        return []

    project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = location or os.environ.get("GOOGLE_CLOUD_LOCATION")

    if project_id and location:
        return _embed_vertex(
            texts,
            model=model,
            project_id=project_id,
            location=location,
            batch_size=batch_size,
            for_query=for_query,
        )
    logger.warning(
        "Vertex não configurado (GOOGLE_CLOUD_PROJECT/REGION). "
        "Usando embeddings mock — suficiente para o lab com ChromaDB; Vertex é opcional."
    )
    return [_mock_embed(t) for t in texts]


def _mock_embed(text: str, dim: int = 768) -> list[float]:
    """Vetor determinístico por hash do texto (reprodutível para testes). Dimensão 768 para compatibilidade com Vertex (text-multilingual-embedding-002)."""
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    # Repete o padrão para preencher 768 dimensões (hash tem 64 chars hex = 32 bytes)
    base = [(int(h[i : i + 2], 16) / 255.0 - 0.5) for i in range(0, min(64, len(h) - 1), 2)]
    while len(base) < dim:
        base = (base * ((dim // len(base)) + 1))[:dim]
    return base


def _embed_vertex(
    texts: list[str],
    *,
    model: str,
    project_id: str,
    location: str,
    batch_size: int,
    for_query: bool = False,
) -> list[list[float]]:
    """Usa Google Gen AI SDK (google-genai) com Vertex AI para embeddings."""
    from google import genai
    from google.genai.types import EmbedContentConfig

    task_type = "RETRIEVAL_QUERY" if for_query else "RETRIEVAL_DOCUMENT"
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location,
    )
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = [t[:20_000] for t in texts[i : i + batch_size]]
        result = client.models.embed_content(
            model=model,
            contents=batch,
            config=EmbedContentConfig(task_type=task_type),
        )
        if not result.embeddings:
            continue
        for emb in result.embeddings:
            vec = getattr(emb, "values", None) or emb
            if vec is not None:
                all_embeddings.append(list(vec))
    return all_embeddings
