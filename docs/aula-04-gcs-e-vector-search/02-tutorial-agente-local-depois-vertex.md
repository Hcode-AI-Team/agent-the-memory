# Aula 4 · Tutorial 2 — Chroma local e depois Vector Search

Como testar o `agent-the-memory` **sem** Vector Search (RAG no Chroma) e, em seguida, indexar os manuais no índice da sua letra e consultar pela nuvem.

**Duração sugerida:** 60–75 min (a espera do deploy/rebuild do índice não conta como “digitação”)  
**Pré-requisitos:** [Tutorial 1](01-tutorial-gcs-upload-manuais.md) (folha de IDs + pasta `manuais/` no bucket); venv da Aula 1; ADC.

Visual: [`vector_search.html`](../../vector_search.html).

---

## Objetivo

1. Rodar indexação + `rag_query.py` com **Chroma** e embedding **local** (384 dimensões).
2. Rodar `python -m src.main` autenticado por **ADC** (Gemini no Vertex), ainda sem Vector Search.
3. Trocar configs para embedding **768** + backend **vertex**.
4. Empurrar os manuais para o **seu** índice e consultar de novo com `rag_query.py` e com o agente.

Autenticação desta turma: **Google ADC**, nunca `GOOGLE_API_KEY`.

---

## 0. Ligar o terminal no projeto

Na raiz do repositório `agent-the-memory`:

**Git Bash / Linux / macOS**

```bash
cd /caminho/para/agent-the-memory
source venv/Scripts/activate          # Git Bash no Windows
# source venv/bin/activate            # Linux / macOS
```

**PowerShell**

```powershell
cd C:\caminho\para\agent-the-memory
.\venv\Scripts\Activate.ps1
```

Confira:

```bash
python --version
# 3.11 ou 3.12
```

Se `sentence-transformers` não estiver instalado (Aula 1):

```bash
pip install -e ".[lab]"
```

### ADC (obrigatório para o agente e para o Tutorial 2B)

```bash
gcloud auth application-default login
gcloud config set project spartan-setting-485114-e3
gcloud config get-value project
```

O segundo comando deve imprimir `spartan-setting-485114-e3`.  
Não cole chave de API em lugar nenhum.

---

## Parte A — RAG local (sem Vector Search)

Aqui o LLM pode estar no Vertex (ADC). O que **não** usamos ainda é o índice da nuvem. Memória longa = **Chroma** em `data/chroma`. Embedding = MiniLM **384**.

### A.1 Arquivo `.env` mínimo

Na raiz, copie o exemplo e edite:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Deixe **comentadas** (ou apague) as linhas `VECTOR_SEARCH_*` nesta parte. O arquivo deve ter, no mínimo:

```env
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=spartan-setting-485114-e3
GOOGLE_CLOUD_LOCATION=us-east1
```

Não defina `USE_VERTEX_SESSION=1`. A sessão da demo fica **em memória** ([`src/session_gateway.py`](../../src/session_gateway.py)).

Não defina `VECTOR_SEARCH_ENDPOINT_ID`. Sem esse ID, o gateway de memória longa não tenta o Vertex (e, com `backend: chroma`, usa o disco local).

### A.2 Conferir os YAMLs (valores default do repo)

[`config/indexing.yaml`](../../config/indexing.yaml):

```yaml
embedding:
  backend: local
  model: paraphrase-multilingual-MiniLM-L12-v2
```

[`config/memory_policy.yaml`](../../config/memory_policy.yaml):

```yaml
vector_search:
  backend: chroma
  max_documents: 3
  min_similarity_score: 0.35
  chroma:
    persist_directory: data/chroma
    collection_name: customer_insights
```

Se alguém da dupla já tinha mudado isso para `vertex`, **volte** para `local` + `chroma` agora. Misturar MiniLM (384) com índice Vertex (768) é o erro número 1 da aula.

### A.3 Indexar no Chroma

```bash
python -m src.indexing --config config/indexing.yaml -i data/lab data/sample_insights.csv data/sample_policies.json --output out/chunks_local.json --push
```

O que o comando faz, nesta ordem ([`src/indexing/__main__.py`](../../src/indexing/__main__.py)):

1. Lê CSV / TXT / PDF / JSON (`data/lab` entra como pasta: todos os `.csv`, `.json`, `.pdf`, `.txt`).
2. Parte em chunks (`chunk_size_chars: 512`, overlap 64).
3. Gera embeddings **locais** (384).
4. Grava no Chroma (`data/chroma`) porque `backend: chroma`.
5. Escreve `out/chunks_local.json` para você inspecionar.

Saída esperada (trechos):

```text
INFO: Chunks gravados: out/chunks_local.json (...)
INFO: Vector store ChromaDB: N documentos gravados em data/chroma
INFO: Push concluído: N documentos.
```

Se aparecer “embeddings mock (hash)”, o extra `[lab]` não está instalado. Rode `pip install -e ".[lab]"` e indexe de novo.

### A.4 Consultar sem abrir o agente

`scripts/rag_query.py` chama o mesmo [`LongTermMemoryGateway`](../../src/memory_gateway.py) que o agente usa. Não precisa do Gemini.

```bash
python scripts/rag_query.py "Quais são as tarifas da conta premium e as condições para empréstimo pessoal?"
```

**Sucesso:** vários trechos em português (conta premium, empréstimo, taxas).  
**Falha típica:** `(nenhum trecho recuperado)` — Chroma vazio, `backend` errado, ou `min_similarity_score` alto demais para MiniLM (o default `0.35` costuma funcionar).

Outra pergunta de fumaça:

```bash
python scripts/rag_query.py "Qual a margem máxima de desconto para cliente premium?"
```

Deve puxar a política de `0,3 p.p.` (do JSON ou do TXT).

### A.5 Rodar o agente (ainda sem Vector Search)

```bash
python -m src.main
```

O que acontece ([`src/main.py`](../../src/main.py)):

- Três turnos de um cliente premium recusando taxa.
- Sessão em memória (`sessao_premium_998877`).
- Gemini via Vertex (**ADC** + `GOOGLE_GENAI_USE_VERTEXAI=1`).
- RAG só entra quando a FSM está em `rate_proposed` ou `analyzing_credit` ([`src/agent_router.py`](../../src/agent_router.py)). Nos primeiros turnos a memória longa pode nem ser consultada. Por isso o teste **honesto** do RAG é o `rag_query.py` do passo A.4.

Saída esperada: três respostas do negociador e um relatório FinOps no final.

Se o LLM falhar com erro de credencial: refaça `gcloud auth application-default login`. Não adicione `GOOGLE_API_KEY`.

**Checkpoint da Parte A:** `rag_query.py` devolve texto do lab **e** `python -m src.main` completa os três turnos. Só então passe para a Parte B.

---

## Parte B — Ligar o Vector Search da sua letra

Agora o embedding e o vector store passam a ser os da nuvem. O índice já existe (Tutorial 1); você só **alimenta** vetores e consulta.

### B.1 Completar o `.env`

Descomente / preencha com a **folha de IDs** do Tutorial 1. Substitua `X` e os números:

```env
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=spartan-setting-485114-e3
GOOGLE_CLOUD_LOCATION=us-east1

VECTOR_SEARCH_GCS_BUCKET=rag-spartan-bv2-grupo-X
VECTOR_SEARCH_INDEX_ID=cole_o_id_numerico_do_indice
VECTOR_SEARCH_ENDPOINT_ID=cole_o_id_numerico_do_endpoint
VECTOR_SEARCH_DEPLOYED_INDEX_ID=endpoint-ap-index-rag-grupo-X
```

Deixe `USE_VERTEX_SESSION` desligado (ausente ou `0`). Nesta aula só a **memória longa** vai para a nuvem.

O código de upsert e de busca lê `GOOGLE_CLOUD_LOCATION` ([`src/indexing/vector_store.py`](../../src/indexing/vector_store.py), [`src/memory_gateway.py`](../../src/memory_gateway.py)). Use `us-east1`, não `us-central1`.

### B.2 Trocar os YAMLs (dimensão 768)

Em [`config/indexing.yaml`](../../config/indexing.yaml):

```yaml
embedding:
  backend: vertex
  model: text-multilingual-embedding-002
  batch_size: 5
```

Em [`config/memory_policy.yaml`](../../config/memory_policy.yaml):

```yaml
vector_search:
  backend: vertex
  max_documents: 3
  min_similarity_score: 0.60
  vertex:
    index_id: ""
    gcs_bucket: ""
    deployed_index_id: ""
    content_store_path: data/vertex_content_store.jsonl
    gcs_prefix: vertex_batch
    is_complete_overwrite: false
```

Os três campos vazios em `vertex:` são preenchidos pelas **env** do `.env`. Não precisa colar os IDs duas vezes.

Por que `0.60` e não `0.35`: o comentário no YAML já avisa — embeddings Vertex multilingual costumam ter scores mais altos. Se a consulta voltar vazia com trechos “obviamente” certos, baixe para `0.50` e teste de novo. Não copie o limiar do MiniLM sem pensar.

**Não apague** `data/chroma`. Ele é o baseline da Parte A. O Vertex usa outro arquivo: `data/vertex_content_store.jsonl`.

### B.3 Ter os manuais no disco local

O CLI **não** lê `gs://.../manuais/` sozinho. Precisa de arquivos locais.

**Opção 1 — já tem os mesmos arquivos no repo** (o mais simples se você subiu os exemplos do Tutorial 1):

```bash
mkdir -p data/manuais
cp data/sample_insights.csv data/manuais/
cp data/lab/lab_emprestimo.txt data/manuais/
cp data/lab/lab_conta_premium.pdf data/manuais/
cp data/sample_policies.json data/manuais/
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path data\manuais | Out-Null
Copy-Item data\sample_insights.csv data\manuais\
Copy-Item data\lab\lab_emprestimo.txt data\manuais\
Copy-Item data\lab\lab_conta_premium.pdf data\manuais\
Copy-Item data\sample_policies.json data\manuais\
```

**Opção 2 — baixar o que está no bucket** (o que o grupo realmente enviou):

```bash
mkdir -p data/manuais
gsutil cp gs://rag-spartan-bv2-grupo-X/manuais/* data/manuais/
ls data/manuais
```

PowerShell (gsutil igual; `ls` → `Get-ChildItem data\manuais`).

Substitua `X`. Se `gsutil` disser que não achou objetos, volte ao Tutorial 1: a pasta `manuais/` está vazia ou o bucket é o errado.

### B.4 Empurrar vetores para o índice (`--push`)

Confira de novo: `embedding.backend` é `vertex` e `vector_search.backend` é `vertex`.

```bash
python -m src.indexing --config config/indexing.yaml -i data/manuais --output out/chunks_vertex.json --push
```

O que o Vertex faz ([`_upsert_vertex`](../../src/indexing/vector_store.py)):

1. Gera um JSONL `{"id": "...", "embedding": [768 floats]}`.
2. Sobe para `gs://rag-spartan-bv2-grupo-X/vertex_batch/update_<timestamp>.jsonl`.
3. Dispara **update** do índice (`contentsDeltaUri`). Rebuild **batch** leva minutos.
4. Acrescenta id → texto em `data/vertex_content_store.jsonl`.

Esse último arquivo é obrigatório na consulta: o Vector Search devolve **IDs**, não o parágrafo. Sem content store local, `rag_query.py` acha vizinhos e imprime vazio.

Saída esperada:

```text
INFO: Vertex Vector Search: batch enviado para gs://.../vertex_batch/update_....jsonl (N documentos). Rebuild pode levar minutos.
INFO: Vector store Vertex: content store atualizado em data/vertex_content_store.jsonl
INFO: Push concluído: N documentos.
```

Se cair em mock (`Vector store mock: ... jsonl`):

- `.env` sem algum `VECTOR_SEARCH_*` ou sem `GOOGLE_CLOUD_LOCATION`
- ADC inválido
- Falha de permissão no bucket / índice

Leia o `WARNING` imediatamente acima. Não siga em frente no mock.

No Console: **Cloud Storage → seu bucket → `vertex_batch/`**. Deve existir pelo menos um `.jsonl`. Isso **não** é o PDF: é o alimento do índice.

### B.5 Esperar o rebuild

Índice **batch** não fica consultável no segundo seguinte.

1. Vector Search → **Índices** → o seu → status volta a **Pronto**.
2. (Quando a UI mostrar) contagem de vetores densos deixa de ser `--`.
3. Endpoint continua com o deployed index **Pronto** (não **Implantando**).

Se o deployed index ainda estiver **Implantando** (Tutorial 1 incompleto), a consulta falha mesmo com JSONL no bucket. Espere.

### B.6 Consultar no Vector Search

```bash
python scripts/rag_query.py "Quais são as tarifas da conta premium e as condições para empréstimo pessoal?"
```

**Sucesso:** trechos dos manuais (os mesmos temas da Parte A, agora via `find_neighbors`).  
Logs úteis: `Long-Term Memory: Vertex AI Vector Search (find_neighbors)`.

Se vier `(nenhum trecho recuperado)`:

1. Content store existe e tem linhas? `data/vertex_content_store.jsonl`
2. Rebuild terminou?
3. `VECTOR_SEARCH_DEPLOYED_INDEX_ID` é **exatamente** o nome na coluna “Índices implantados”?
4. `min_similarity_score` alto demais? Teste `0.50` no YAML.
5. Embedding da **query** também precisa ser Vertex 768. Se `indexing.yaml` ainda estiver `local`, a query tem 384 dimensões e o endpoint rejeita ou devolve lixo.

### B.7 Agente falando com a nuvem

```bash
python -m src.main
```

Mesmos três turnos. Diferença: quando a FSM pedir memória longa, o gateway chama o **seu** endpoint. Sessão continua em memória.

Não espere o agente citar o PDF em **todos** os turnos. Confirme o RAG com `rag_query.py`.

---

## Fluxo mental (guarde isso)

```text
Parte A
  TXT/CSV/PDF local → chunk → MiniLM 384 → Chroma (data/chroma)
  rag_query.py  →  embed local  →  Chroma.query

Parte B
  mesmos arquivos → chunk → Vertex embed 768 → JSONL no GCS → update índice
                 → content store local (id → texto)
  rag_query.py  →  embed Vertex 768  →  endpoint.find_neighbors  →  texto no content store
```

Os dois mundos **não** compartilham vetores. Reindexar no Vertex não apaga o Chroma; consultar o Vertex não lê `data/chroma`.

---

## Checklist final

- [ ] ADC ok (`gcloud config get-value project` = `spartan-setting-485114-e3`)
- [ ] Parte A: `rag_query.py` com Chroma devolve trechos
- [ ] Parte A: `python -m src.main` termina os 3 turnos
- [ ] `.env` com IDs da **minha** letra (não `grupo-0`)
- [ ] `indexing.yaml` = `vertex` + `text-multilingual-embedding-002`
- [ ] `memory_policy.yaml` = `backend: vertex`
- [ ] `data/manuais/` tem os arquivos
- [ ] `--push` criou `vertex_batch/` no meu bucket e `data/vertex_content_store.jsonl`
- [ ] Índice Pronto depois do rebuild; deployed index Pronto
- [ ] `rag_query.py` devolve trechos **com backend vertex**

---

## Problemas comuns

| Sintoma | Causa | Correção |
|---------|-------|----------|
| `DefaultCredentialsError` / 401 / 403 | ADC ausente ou conta sem papel | `gcloud auth application-default login`; peça IAM ao professor (Vertex AI User + acesso ao bucket) |
| Alguém colou `GOOGLE_API_KEY` | Fora do padrão da turma | Apague a chave. Use ADC + `GOOGLE_GENAI_USE_VERTEXAI=1` |
| `Vector store mock` no `--push` | Env incompleta ou exceção no Vertex | Confira as 4 variáveis `VECTOR_SEARCH_*` e `GOOGLE_CLOUD_LOCATION=us-east1` |
| Erro de dimensão / consulta vazia depois do push | MiniLM 384 no índice 768 | `embedding.backend: vertex` na indexação **e** na query |
| `rag_query` vazio, JSONL no bucket | Rebuild incompleto ou content store vazio | Espere o índice; confira `data/vertex_content_store.jsonl` |
| `find_neighbors` falha | Índice não implantado ou `DEPLOYED_INDEX_ID` errado | Tutorial 1, passo 3.4; copie o nome da UI |
| Upload no `grupo-0` | Recurso do professor | Pare. Use `grupo-X` |
| Usei Mecanismo RAG | Outro produto | Ignore esse menu. Este repo = Vector Search + CLI |
| Região `us-central1` no `.env` | Docs antigos do README | Troque para `us-east1` |
| Agente responde, `rag_query` vazio | LLM não prova o RAG | Conserte `rag_query.py` primeiro |

Voltar ao Chroma (Parte A) depois da Parte B: restaure `backend: local` / `backend: chroma` nos YAMLs e **comente** `VECTOR_SEARCH_ENDPOINT_ID` no `.env`. Não é preciso apagar o content store do Vertex.
