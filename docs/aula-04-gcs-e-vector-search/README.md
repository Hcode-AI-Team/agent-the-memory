# Aula 4 — GCS, manuais e Vector Search

| # | Arquivo | Conteúdo |
|---|---------|----------|
| 1 | [01-tutorial-gcs-upload-manuais.md](01-tutorial-gcs-upload-manuais.md) | Mapa do GCP, conferir índice/endpoint/deploy, upload manual no Cloud Storage |
| 2 | [02-tutorial-agente-local-depois-vertex.md](02-tutorial-agente-local-depois-vertex.md) | RAG no Chroma, **correções de código** (vector_store / memory_gateway / score), depois `--push` + Vector Search |

Material visual (raiz do repo): [`vector_search.html`](../../vector_search.html)

Como o índice foi criado (referência): [02-tutorial-vertex-vector-search.md](../aula-02-retrieval-e-vector-search/02-tutorial-vertex-vector-search.md)

Autenticação da turma: **Google ADC** (`gcloud auth application-default login`), sem `GOOGLE_API_KEY`. Sufixo `grupo-0` = professor.

Antes da Parte B do Tutorial 2, os alunos **editam** `src/indexing/vector_store.py`, `src/memory_gateway.py` e `config/memory_policy.yaml` conforme a seção “Correções obrigatórias no código”.
