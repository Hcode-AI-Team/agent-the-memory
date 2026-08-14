# Aula 4 · Tutorial 1 — Do arquivo no computador ao Vector Search

Como subir manuais (PDF, TXT, CSV) no **Cloud Storage** e o que cada peça do Google Cloud faz neste projeto.

**Duração sugerida:** 40–50 min  
**Formato:** individual ou dupla (um piloto no console, um conferindo a checklist)  
**Pré-requisitos:** Aulas 1–3; índice e endpoint do grupo já criados; região **`us-east1`**.

Material visual (abra no navegador, na raiz do repositório):

- [`vector_search.html`](../../vector_search.html) — o que é índice, endpoint, deploy, bucket e consulta

Não recrie índice nem endpoint. Quem quiser rever *como* eles foram criados: [Tutorial Vertex da Aula 2](../aula-02-retrieval-e-vector-search/02-tutorial-vertex-vector-search.md).

---

## Objetivo

Ao final deste tutorial você consegue:

1. Explicar, em uma frase cada, **projeto**, **bucket**, **índice**, **endpoint** e **índice implantado**.
2. Identificar **os recursos da sua letra** (e nunca mexer no `grupo-0`).
3. Conferir se o índice está **Pronto** e **implantado** no endpoint.
4. Subir PDF, TXT e CSV na pasta `manuais/` do **seu** bucket.

---

## 0. Autenticação desta turma

Esta turma usa **Google ADC** (Application Default Credentials), **não** `GOOGLE_API_KEY`.

No console do GCP você entra com a conta da organização `fiapconsulting.com`. No computador, o SDK Python usa a mesma identidade depois de:

```bash
gcloud auth application-default login
gcloud config set project spartan-setting-485114-e3
```

Neste tutorial 1 quase tudo é **clique no Console**. O `gcloud` acima entra de verdade no Tutorial 2, quando o `agent-the-memory` for falar com a nuvem.

---

## 1. Mapa da plataforma (o que é cada peça)

Imagine um depósito de manuais (os arquivos) e um **catálogo inteligente** (os vetores). São coisas diferentes.

```text
  Seu computador                Google Cloud (projeto compartilhado)
  ──────────────                ────────────────────────────────────
  PDF / TXT / CSV  ──upload──►  Cloud Storage (bucket da sua letra)
                                      │
                                      │  (ainda NÃO é busca)
                                      ▼
                                Vector Search
                                      ├── Índice     → guarda os vetores (768 números cada)
                                      ├── Endpoint   → “porta” que recebe a pergunta
                                      └── Índice implantado → liga o índice à porta
```

### 1.1 Projeto GCP

**O que é:** a “conta-mãe” onde todos os recursos desta turma vivem.

| Campo no console | Valor desta turma |
|------------------|-------------------|
| Nome de exibição | My First Project |
| ID do projeto | `spartan-setting-485114-e3` |
| Organização | `fiapconsulting.com` |
| Região usada aqui | `us-east1` (Carolina do Sul) |

Todo mundo trabalha **no mesmo projeto**. O isolamento entre grupos é pelo **nome do recurso** (`grupo-a`, `grupo-b`, …), não por projeto separado.

No topo do Console, confira se o seletor mostra **My First Project**. Se estiver em outro projeto, nada do que você criar ou listar vai bater com a aula.

### 1.2 Cloud Storage (bucket)

**O que é:** um “disco na nuvem” para arquivos. Cada arquivo é um objeto; pastas são só prefixos no nome (`manuais/tarifas.pdf`).

Nesta turma o bucket do grupo `X` se chama:

```text
rag-spartan-bv2-grupo-X
```

Exemplo do professor: `rag-spartan-bv2-grupo-0`.  
Exemplo do grupo F: `rag-spartan-bv2-grupo-f`.

O que você vai ver na lista de buckets:

- **Localização:** `us-east1` (quase todos; não use buckets de outra região)
- **Classe:** Standard
- **Acesso público:** Não público
- **Controle de acesso:** Uniforme (permissão no bucket inteiro, não arquivo a arquivo)

O **mesmo bucket** terá duas pastas com papéis diferentes:

| Pasta | Quem cria | O que tem |
|-------|-----------|-----------|
| `manuais/` | Você, neste tutorial, pelo Console | PDF, TXT, CSV originais |
| `vertex_batch/` | O pipeline Python, no Tutorial 2 | JSONL de **vetores** (não abra isso como “o manual”) |

### 1.3 Agent Platform → Vector Search

No menu esquerdo: **Agentes → Escala → Vector Search**.

Há duas abas:

| Aba | O que lista |
|-----|-------------|
| **Índices** | O “catálogo” de vetores |
| **Endpoints de índice** | A “porta” pela qual a aplicação pergunta |

Não use **Mecanismo RAG** (menu Criar) neste projeto. O `agent-the-memory` fala com **Vector Search** + o CLI `python -m src.indexing`, não com o RAG Engine automático do Google.

### 1.4 Índice (Index)

**O que é:** a estrutura que guarda os embeddings e permite busca por similaridade. Sozinho, ele **não recebe** a pergunta do agente.

Configuração que o professor usou no `grupo-0` (a sua deve ser igual):

| Campo | Valor | Por que importa |
|-------|-------|-----------------|
| Dimensões | **768** | Tem que ser o mesmo do modelo `text-multilingual-embedding-002` |
| Tipo de algoritmo | `tree-AH` | Busca aproximada (vizinhos mais próximos) |
| Método de atualização | **Lote** (batch) | Novos vetores entram por arquivo no GCS, não um a um |
| Tipo de distância | Produto escalar | Tem que combinar com o embedding |
| Tamanho do fragmento | Pequeno | Volume de lab |
| Status | Pronto | Criação terminou — ainda pode estar **vazio** |

A coluna **Contagem densos** pode aparecer como `--`. Isso significa: o índice existe, mas **ainda não há vetores**. Subir PDF no bucket **não** preenche essa coluna. Quem preenche é o `--push` do Tutorial 2.

### 1.5 Endpoint de índice

**O que é:** o endereço que a aplicação chama. Analogia: o índice é o fichário; o endpoint é o balcão de atendimento.

No `grupo-0` o endpoint é público (`Tipo de acesso: Público`) e fica em `us-east1`. A aplicação não usa o “nome de domínio público” direto: ela usa o **ID numérico** do endpoint + ADC.

### 1.6 Índice implantado (Deployed Index)

**O que é:** a **ligação** entre um índice e um endpoint. Sem essa ligação, o endpoint está “Pronto” mas não tem o que consultar.

O professor nomeou o deployed index assim:

```text
endpoint-ap-index-rag-grupo-0
```

Siga o mesmo padrão com a **sua letra**. Esse nome é o valor de `VECTOR_SEARCH_DEPLOYED_INDEX_ID` no Tutorial 2.

Três estados comuns:

| O que você vê | Significado | O que fazer |
|---------------|-------------|-------------|
| Link azul **Implantar** na lista de índices | Índice criado, **ainda não** está no endpoint | Clique em Implantar e espere |
| Status **Implantando** (círculo azul) | Deploy em andamento | Espere. Pode levar dezenas de minutos na primeira vez |
| Nome do deployed index + **Pronto** | Pode receber `find_neighbors` | Anote o ID e siga |

**Mito a matar agora:** índice “Pronto” ≠ busca funcionando. Falta (1) implantar e (2) ter vetores.

---

## 2. A regra da letra (leia antes de clicar em qualquer coisa)

| Quem | Sufixo | Exemplo de bucket |
|------|--------|-------------------|
| Professor (demo da aula) | `0` | `rag-spartan-bv2-grupo-0` |
| Seu grupo | uma letra (`a` … `l`, etc.) | `rag-spartan-bv2-grupo-f` |

**Nunca** edite, apague, faça upload ou clique em Implantar em recurso que termine em `-grupo-0`. Esse é o material da demonstração.

Substitua `X` pela **sua** letra em tudo que segue.

| Recurso | Nome |
|---------|------|
| Bucket | `rag-spartan-bv2-grupo-X` |
| Índice | `agent-platform-index-rag-grupo-X` |
| Endpoint | `rag-endpoint-ap-grupo-X` |
| Deployed index (padrão) | `endpoint-ap-index-rag-grupo-X` |

Se o seu grupo criou o deployed index com outro nome, **use o nome que está no console**, não invente.

---

## 3. Conferir o que já existe

Faça nesta ordem. Não pule a região.

### Passo 3.1 — Projeto e região

1. Abra [console.cloud.google.com](https://console.cloud.google.com/).
2. No seletor de projeto (topo), confirme **My First Project** / `spartan-setting-485114-e3`.
3. Em **Vector Search**, o dropdown **Região** deve estar em **`us-east1 (Carolina do Sul)`**.  
   Se estiver em `us-central1` ou outra, a lista vai parecer vazia ou mostrar recursos de outra aula.

### Passo 3.2 — Índice

1. Menu: **Agentes → Escala → Vector Search → aba Índices**.
2. Ache **somente** `agent-platform-index-rag-grupo-X`.
3. Confira **Status = Pronto**.
4. Clique no nome e copie para um bloco de notas:

```text
Letra do grupo:           X
Nome do índice:           agent-platform-index-rag-grupo-X
ID do índice:             (número longo, ex. 8600340370045272064)
Dimensões:                768
```

O ID do professor (`grupo-0`) é só exemplo. **O seu número é outro.**

### Passo 3.3 — Endpoint

1. Aba **Endpoints de índice**, mesma região `us-east1`.
2. Ache `rag-endpoint-ap-grupo-X`.
3. Status **Pronto**.
4. Abra o endpoint e copie:

```text
Nome do endpoint:         rag-endpoint-ap-grupo-X
ID do endpoint:           (número longo)
Tipo de acesso:           Público
```

### Passo 3.4 — Implantar, se ainda não implantou

Na lista de **Índices**, coluna **Índices implantados**:

- Se já aparece um nome (ex. `endpoint-ap-index-rag-grupo-X`): anote esse nome. Pule para 3.5.
- Se aparece o link **Implantar**:
  1. Clique em **Implantar**.
  2. Escolha o endpoint `rag-endpoint-ap-grupo-X`.
  3. **ID do índice implantado:** `endpoint-ap-index-rag-grupo-X` (letras, números e hífen/underscore; sem espaços).
  4. Confirme e **espere** o status sair de **Implantando**. Não feche a aula e não rode o agente ainda.

Na aba **Endpoints**, a coluna **Índices implantados** do seu endpoint deve deixar de ser `-`.

### Passo 3.5 — Folha de IDs (você vai colar no `.env` no Tutorial 2)

```text
GOOGLE_CLOUD_PROJECT=spartan-setting-485114-e3
GOOGLE_CLOUD_LOCATION=us-east1
VECTOR_SEARCH_GCS_BUCKET=rag-spartan-bv2-grupo-X
VECTOR_SEARCH_INDEX_ID=________________
VECTOR_SEARCH_ENDPOINT_ID=________________
VECTOR_SEARCH_DEPLOYED_INDEX_ID=endpoint-ap-index-rag-grupo-X
```

Guarde esse bloco. Sem esses números o Python não acha o **seu** índice (e pode, no pior caso, apontar para o lugar errado).

---

## 4. Preparar os arquivos no computador

O loader do projeto ([`src/indexing/loaders.py`](../../src/indexing/loaders.py)) aceita:

| Extensão | Como o texto é lido | Dica |
|----------|---------------------|------|
| `.csv` | Coluna `content` (fallback: `text`). Outras colunas viram metadados | Use o CSV de exemplo da aula |
| `.txt` | Arquivo inteiro, UTF-8 | Evite encoding “Windows-1252” se houver acento |
| `.pdf` | Texto extraído com `pypdf` (páginas concatenadas por padrão) | PDF escaneado (só imagem) **não** funciona |
| `.json` | Campo `content` (ou o path em `indexing.yaml`) | Opcional neste tutorial |

Arquivos prontos no repositório (na raiz do projeto):

| Arquivo | Tipo | Conteúdo |
|---------|------|----------|
| [`data/sample_insights.csv`](../../data/sample_insights.csv) | CSV | Insights de cliente (inclui `session_id`, `tier`, `content`) |
| [`data/lab/lab_emprestimo.txt`](../../data/lab/lab_emprestimo.txt) | TXT | Políticas de empréstimo pessoal |
| [`data/sample_policies.json`](../../data/sample_policies.json) | JSON | Políticas / handoff |
| `data/lab/lab_conta_premium.pdf` | PDF | Gerado pelo script abaixo |

Se o PDF ainda não existir:

```bash
# venv ativo; extra [lab] instalado (Aula 1)
python scripts/generate_lab_pdf.py
```

Isso grava `data/lab/lab_conta_premium.pdf`.

Você **pode** usar manuais do próprio grupo (tarifas, política de crédito, FAQ). Mantenha extensão `.pdf`, `.txt` ou `.csv` e texto selecionável.

---

## 5. Upload manual no Console

Objetivo: deixar uma cópia dos manuais em `gs://rag-spartan-bv2-grupo-X/manuais/`. Isso é a **fonte da turma** (o professor consegue ver o que o grupo indexou). A busca em si só acontece no Tutorial 2.

### Passo 5.1 — Abrir o bucket certo

1. No Console, busque **Cloud Storage** (ou **Buckets**).
2. Abra **somente** `rag-spartan-bv2-grupo-X`.
3. Confira de novo: nome termina na **sua** letra, localização `us-east1`, **Não público**.

### Passo 5.2 — Criar a pasta `manuais`

1. Clique em **Criar pasta** (ou equivalente).
2. Nome: `manuais` (minúsculo, sem acento, sem espaço).
3. Entre na pasta. A barra de endereço / breadcrumbs deve mostrar `.../manuais/`.

Se a pasta já existir, entre nela. Não crie `Manuais` nem `manual`.

### Passo 5.3 — Enviar os arquivos

1. **Fazer upload** / **Upload files**.
2. Selecione pelo menos:
   - `data/sample_insights.csv`
   - `data/lab/lab_emprestimo.txt`
   - `data/lab/lab_conta_premium.pdf` (depois de gerar)
3. Espere o upload terminar. Os três nomes devem aparecer na tabela.

Não marque o objeto como público. O bucket já é uniforme e não público; o Python entra com ADC.

### Passo 5.4 — Conferir

Checklist:

- [ ] Estou no bucket `rag-spartan-bv2-grupo-X` (não no `grupo-0`)
- [ ] Pasta `manuais/` existe
- [ ] CSV, TXT e PDF visíveis
- [ ] Região do bucket = `us-east1`

Opcional, no Cloud Shell ou no terminal com `gcloud` (substitua `X`):

```bash
gsutil ls gs://rag-spartan-bv2-grupo-X/manuais/
```

Você deve ver os três (ou mais) arquivos. Se `CommandException: One or more URLs matched no objects`, a pasta está vazia ou o nome do bucket está errado.

---

## 6. Checklist final deste tutorial

- [ ] Sei a diferença entre bucket, índice, endpoint e índice implantado.
- [ ] Folha de IDs preenchida com a **minha** letra.
- [ ] Índice Pronto **e** implantado no meu endpoint (não “Implantando”).
- [ ] `manuais/` no meu bucket tem PDF, TXT e CSV.
- [ ] Não toquei em `grupo-0`.
- [ ] Abri [`vector_search.html`](../../vector_search.html) e cliquei em cada peça do diagrama.

Quando isso estiver verde, vá para o [Tutorial 2](02-tutorial-agente-local-depois-vertex.md): testar o agente com Chroma local e depois ligar o Vector Search.

---

## 7. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| Lista de índices vazia | Região errada | Troque para `us-east1` |
| Achei `grupo-0` e fiz upload lá | Recurso do professor | Pare. Apague só se o professor pedir. Use a sua letra |
| **Implantar** ainda visível | Deploy nunca feito | Faça o Passo 3.4 e espere |
| PDF no bucket mas busca vazia | Esperado neste tutorial | Tutorial 2: indexar com `--push` |
| `gsutil` pede login | ADC / gcloud não configurado | `gcloud auth login` e `gcloud auth application-default login` |
| Bucket “não público” e achei que precisa abrir | Permissão IAM, não link público | O Python usa ADC; não torne o bucket público |
