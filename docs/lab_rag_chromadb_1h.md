# Lab guiado: RAG com ChromaDB (1 hora)

**Este lab usa apenas ChromaDB** (vector store local). Vertex AI não é necessário; a mensagem "Vertex não configurado. Usando embeddings mock" é esperada e indica que o ChromaDB está em uso.

Este documento descreve um lab prático de **1 hora** em que você vai:

1. Fazer uma **consulta RAG** com o vector store vazio (ou mock).
2. **Indexar** três arquivos (PDF, CSV e TXT) no ChromaDB.
3. Repetir a **mesma consulta** e ver o RAG retornar trechos dos documentos.
4. Entender que o **agente** já usa essa mesma base; não é preciso alterar código.

Ao final, você terá visto o ciclo completo **consulta sem dados → indexação → mesma consulta com RAG**.

---

## Pré-requisitos

- **Python 3.11+** instalado.
- Repositório clonado e dependências instaladas na raiz do projeto:
  ```bash
  cd /caminho/para/agente-3-the-memory
  pip install -e .
  ```
- Para **gerar o PDF** do lab (passo 2): dependência opcional do lab:
  ```bash
  pip install -e ".[lab]"
  ```
  Ou apenas: `pip install fpdf2`
- **ChromaDB** é o vector store do lab (pasta `data/chroma`); não é necessário Vertex AI nem servidor externo.
- **Vertex AI é opcional:** o script `scripts/rag_query.py` e o pipeline de indexação **carregam o `.env`** da raiz do projeto (se existir). Se você tiver `GOOGLE_CLOUD_PROJECT` e `GOOGLE_CLOUD_LOCATION` (ou `GOOGLE_CLOUD_REGION`) no `.env`, serão usados embeddings do Vertex AI; caso contrário, embeddings mock (suficiente para o lab). A mensagem _"Vertex não configurado. Usando embeddings mock..."_ é **esperada** quando não há `.env` ou variáveis de Vertex configuradas.

---

## Cronograma (1 hora)

| Tempo     | Bloco               | O que fazer                                                                                                 |
| --------- | ------------------- | ----------------------------------------------------------------------------------------------------------- |
| 0–5 min   | Intro               | Ler objetivo e pré-requisitos; garantir que está na raiz do projeto; criar pasta `scripts` e arquivos se não existirem (ver seção abaixo). |
| 5–10 min  | Contexto            | Conhecer os 3 arquivos em `data/lab/` e o pipeline (loaders → chunking → embedding → ChromaDB).             |
| 10–15 min | **Consulta ANTES**  | Garantir `backend: chroma` em `config/memory_policy.yaml`. Rodar o script de consulta RAG e anotar a saída. |
| 15–35 min | **Indexação**       | Gerar o PDF (se necessário), limpar Chroma, indexar os 3 arquivos com `--push`, verificar chunks.           |
| 35–40 min | Sistema             | Entender que o agente já acessa a base RAG; opcional: um turno de conversa com o agente.                    |
| 40–55 min | **Consulta DEPOIS** | Rodar de novo o script com a mesma pergunta; comparar com a saída “antes”.                                  |
| 55–60 min | Recap               | Resumir o fluxo e onde o RAG entra no agente.                                                               |
| Opcional  | Desafios extras     | Pegadas: agente antes/depois, sources, config, chunk size (seção no final).                                 |

Todos os comandos abaixo devem ser executados **na raiz do repositório** (`agente-3-the-memory`).

---

## Passo 0: Preparar o ambiente (0–5 min)

1. Abra um terminal e vá para a raiz do projeto:
   ```bash
   cd c:\projects\fiap\bv\agentes\agente-3-the-memory
   ```
2. Confirme que o ambiente está ok:
   ```bash
   pip install -e .
   python -c "from src.memory_gateway import LongTermMemoryGateway; print('OK')"
   ```
   Saída esperada: `OK`
3. Se a pasta **`scripts`** ou os arquivos **`scripts/generate_lab_pdf.py`** e **`scripts/rag_query.py`** não existirem, siga a seção **"Criação da pasta scripts e dos arquivos do lab"** abaixo (criar pasta, depois os dois arquivos com o código pronto).

---

## Criação da pasta `scripts` e dos arquivos do lab

Se a pasta **`scripts`** ou os arquivos **`scripts/generate_lab_pdf.py`** e **`scripts/rag_query.py`** ainda não existirem no repositório, crie-os conforme abaixo.

1. **Criar a pasta `scripts`** (na raiz do projeto), se não existir:
   ```bash
   mkdir scripts
   ```
   No Windows, se já existir, o comando não gera erro.

2. **Criar o arquivo `scripts/generate_lab_pdf.py`** com o conteúdo abaixo (permite gerar o PDF do lab):

```python
"""
Gera o PDF do lab RAG (Conta Premium) em data/lab/lab_conta_premium.pdf.
Uso: python scripts/generate_lab_pdf.py
Requer: pip install fpdf2  ou  pip install -e ".[lab]"
"""

from pathlib import Path


def main() -> None:
    try:
        from fpdf import FPDF
    except ImportError as e:
        raise SystemExit(
            "fpdf2 não instalado. Rode: pip install fpdf2  ou  pip install -e \".[lab]\""
        ) from e

    out_dir = Path(__file__).resolve().parent.parent / "data" / "lab"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lab_conta_premium.pdf"

    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=14)
    w = pdf.epw  # effective page width
    pdf.cell(w, 10, "Conta Premium - Produto Banco (Lab RAG)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", size=11)

    # Texto em ASCII para evitar problemas de encoding com fpdf2/Helvetica
    body = """
A Conta Premium e um produto para clientes com maior relacionamento e renda. Beneficios:

- Isencao de taxa de manutencao mensal.
- TEDs: ate 5 gratuitos por mes; apos isso, R$ 15,00 por TED.
- Saques em rede propria: ilimitados. Saques em rede 24h: R$ 10,00 cada.
- Cartao de debito e credito sem anuidade no primeiro ano; segunda via a R$ 35,00.
- Linha de credito pre-aprovada e taxas diferenciadas em emprestimo pessoal (a partir de 0,85% a.m.).

Requisitos para adesao:
- Renda mensal comprovada minima: R$ 5.000.
- Manter saldo medio de R$ 10.000 ou aplicacoes equivalentes no trimestre.

Canais de atendimento:
- App, internet banking, agencia e central de relacionamento (telefone). Proposta de emprestimo pode ser feita pelo agente virtual; condicoes sujeitas a analise de credito.
"""
    for line in body.strip().split("\n"):
        line = line.strip()
        if not line:
            pdf.ln(5)
            continue
        pdf.multi_cell(w, 6, line)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(w, 6, "Documento gerado por scripts/generate_lab_pdf.py para o lab RAG ChromaDB.", new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(out_path))
    print(f"PDF gerado: {out_path}")


if __name__ == "__main__":
    main()
```

3. **Criar o arquivo `scripts/rag_query.py`** com o conteúdo abaixo (consulta RAG e imprime o contexto recuperado):

```python
"""
Consulta RAG (memória de longo prazo): envia uma pergunta e imprime o contexto recuperado.
Uso: python scripts/rag_query.py "Qual a tarifa da conta premium e condições de empréstimo?"
Requer que o projeto esteja instalado (pip install -e .) e config/memory_policy.yaml com backend (chroma | vertex | mock).
Carrega variáveis do .env da raiz do projeto (GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION) se existir.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Raiz do repositório
repo_root = Path(__file__).resolve().parent.parent

# Carregar .env da raiz (GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, etc.) antes de importar src
try:
    from dotenv import load_dotenv
    load_dotenv(repo_root / ".env", override=True)
except ImportError:
    pass

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.memory_gateway import LongTermMemoryGateway


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Consulta o vector store (RAG) e imprime o contexto recuperado para uma pergunta."
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        default="Quais são as tarifas da conta premium e as condições para empréstimo pessoal?",
        help="Pergunta para buscar no RAG (default: pergunta padrão do lab)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=repo_root / "config" / "memory_policy.yaml",
        help="Caminho do memory_policy.yaml",
    )
    args = parser.parse_args()

    if not args.config.exists():
        print(f"Erro: arquivo de config não encontrado: {args.config}", file=sys.stderr)
        return 1

    gateway = LongTermMemoryGateway(config_path=args.config)
    result = asyncio.run(gateway.search_customer_insights(args.query))

    print(result if result else "(nenhum trecho recuperado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

4. Confirme que os arquivos existem:
   ```bash
   dir scripts
   ```
   Você deve ver: `generate_lab_pdf.py` e `rag_query.py`.

---

## Passo 1: Conhecer os arquivos do lab (5–10 min)

Os arquivos do lab ficam em **`data/lab/`**:

| Arquivo                 | Formato | Conteúdo                                                                                 |
| ----------------------- | ------- | ---------------------------------------------------------------------------------------- |
| `lab_conta_premium.pdf` | PDF     | Produto Conta Premium: benefícios, tarifas, requisitos (renda mínima), canais.           |
| `lab_tarifas.csv`       | CSV     | Tarifas (manutenção, TED, saque, segunda via, empréstimo); coluna `content` com o texto. |
| `lab_emprestimo.txt`    | TXT     | Políticas de empréstimo: taxas por perfil, documentação, handoff após 3 recusas.         |

- O **PDF** é gerado por um script (próximo passo); o **CSV** e o **TXT** já estão no repositório.
- Os três tratam do mesmo domínio (banco: tarifas, conta premium, empréstimo), para que **uma única pergunta** possa recuperar trechos dos três.

**Pergunta padrão do lab** (use sempre a mesma para comparar antes/depois):

```text
Quais são as tarifas da conta premium e as condições para empréstimo pessoal?
```

---

## Passo 2: Gerar o PDF do lab (se ainda não existir)

O PDF não é commitado; ele é gerado por um script.

1. Instale a dependência do lab (se ainda não tiver):
   ```bash
   pip install fpdf2
   ```
   Ou: `pip install -e ".[lab]"`
2. Gere o PDF:
   ```bash
   python scripts/generate_lab_pdf.py
   ```
   Saída esperada: `PDF gerado: ...\data\lab\lab_conta_premium.pdf`
3. Confira se o arquivo existe:
   ```bash
   dir data\lab
   ```
   Você deve ver: `lab_conta_premium.pdf`, `lab_tarifas.csv`, `lab_emprestimo.txt`.

---

## Passo 3: Consulta RAG **ANTES** da indexação (10–15 min)

Aqui você roda a mesma pergunta que usará depois. Com o Chroma vazio (ou só com dados antigos), a resposta do RAG será vazia ou mínima.

1. **Garantir que o backend é Chroma**  
   Abra `config/memory_policy.yaml` e confira:

   ```yaml
   vector_search:
     backend: chroma
   ```

   Se estiver `mock`, altere para `chroma` e salve.

2. **(Opcional) Limpar o Chroma** para ver claramente o “antes” vazio:
   - No Windows:
     ```bash
     rmdir /s /q data\chroma
     ```
   - No Linux/macOS:
     ```bash
     rm -rf data/chroma
     ```
     Na primeira execução do script abaixo, o Chroma será recriado vazio.

3. **Rodar o script de consulta RAG** com a pergunta padrão:

   ```bash
   python scripts/rag_query.py "Quais são as tarifas da conta premium e as condições para empréstimo pessoal?"
   ```

4. **Anotar a saída**
   - O script carrega automaticamente o **`.env`** da raiz do projeto; se houver `GOOGLE_CLOUD_PROJECT` e `GOOGLE_CLOUD_LOCATION` (ou `GOOGLE_CLOUD_REGION`), serão usados embeddings do Vertex. Caso contrário, a mensagem "Vertex não configurado. Usando embeddings mock..." é **normal**.
   - Com Chroma vazio e `backend: chroma`: a saída deve ser **vazia** ou `(nenhum trecho recuperado)`.
   - Se ainda estiver em `backend: mock`: você pode ver uma resposta fixa do mock (ex.: “Nenhum histórico prévio encontrado...” ou texto genérico). Nesse caso, mude para `chroma`, limpe `data/chroma` e rode de novo.

Guarde essa saída para comparar no **Passo 6**.

---

## Passo 4: Indexar os três arquivos no ChromaDB (15–35 min)

Agora você vai carregar o PDF, o CSV e o TXT, fatiar em chunks, gerar embeddings e enviar ao ChromaDB.

1. **Garantir que o PDF existe**  
   Se não rodou o Passo 2, rode:

   ```bash
   python scripts/generate_lab_pdf.py
   ```

2. **Limpar o Chroma** (recomendado para um lab “limpo”):
   - Windows: `rmdir /s /q data\chroma`
   - Linux/macOS: `rm -rf data/chroma`

3. **Rodar o pipeline de indexação** com os três arquivos e `--push`:

   ```bash
   python -m src.indexing --config config/indexing.yaml --input data/lab/lab_conta_premium.pdf data/lab/lab_tarifas.csv data/lab/lab_emprestimo.txt --output out/chunks_lab.json --push
   ```

4. **Verificar o resultado**
   - Nos logs você deve ver algo como:
     - `Chunks gravados: out\chunks_lab.json (N)`
     - `Vector store ChromaDB: N documentos gravados em data/chroma`
   - Abra `out/chunks_lab.json`: deve haver uma lista de objetos com `content`, `source` (nome do arquivo) e `metadata`.
   - O número de chunks depende do tamanho dos arquivos e de `chunk_size_chars` em `config/indexing.yaml` (ex.: 512). Esperado: pelo menos alguns chunks por arquivo.

5. **Possíveis erros**
   - “Arquivo não encontrado”: confira os caminhos; o PDF deve ter sido gerado no Passo 2.
   - “Formato não suportado”: o loader aceita `.csv`, `.json`, `.pdf` e `.txt`.
   - Chroma/NumPy: se aparecer erro de `np.float_` ou `np.int_`, o projeto já inclui workaround no código; atualize o repositório.

---

## Passo 5: O agente já usa a base RAG (35–40 min)

Não é necessário **adicionar** nenhum recurso ao agente para ele consultar o ChromaDB.

- O **`main.py`** já instancia o `LongTermMemoryGateway` e injeta no agente.
- O **`agent_router`** chama `search_customer_insights` nas fases em que o RAG é usado (ex.: proposta de taxa, análise de crédito).
- O mesmo `config/memory_policy.yaml` que você usou na indexação e no script `rag_query.py` é usado pelo agente em runtime.

Ou seja: **depois de indexar**, o agente já passa a “enxergar” os documentos que você colocou no Chroma. Você pode (opcional) iniciar o agente e fazer uma pergunta relacionada a tarifas ou empréstimo para ver a resposta enriquecida pelo RAG.

---

## Passo 6: Consulta RAG **DEPOIS** da indexação (40–55 min)

Repita exatamente o mesmo comando do Passo 3:

```bash
python scripts/rag_query.py "Quais são as tarifas da conta premium e as condições para empréstimo pessoal?"
```

- **Saída esperada:** um ou mais trechos de texto concatenados, vindos dos três arquivos (PDF, CSV, TXT), com informações como:
  - Isenção de manutenção para conta premium, TEDs gratuitos, saques, taxas de empréstimo (ex.: 0,85% a.m. premium).
  - Handoff após 3 recusas, documentação, prazos.

Compare com a saída que você anotou no **Passo 3**: antes vazia ou genérica; depois, preenchida com trechos dos documentos. Essa diferença é o **RAG em ação**.

---

## Passo 7: Recap (55–60 min)

- Você fez **uma consulta** antes de indexar (saída vazia ou mock).
- **Indexou** três formatos (PDF, CSV, TXT) no ChromaDB via `python -m src.indexing ... --push`.
- Fez a **mesma consulta** depois e viu o RAG retornar trechos dos documentos.
- O **agente** já usa esse mesmo vector store; nenhuma alteração de código foi necessária.

Fluxo resumido: **loaders (CSV, JSON, PDF, TXT) → chunking → embedding → ChromaDB** na indexação; **query → embedding da query → busca no Chroma → texto injetado no prompt** na consulta (e no agente).

---

## Desafios opcionais (pegadas)

Se sobrar tempo ou quiser aprofundar, use estes desafios.

### Pegada 1 – Agente antes vs depois (recomendada)

- **Antes** de indexar: inicie o agente e faça uma pergunta como: “Quais as tarifas da conta premium e condições de empréstimo?” Anote a resposta (tende a ser genérica).
- **Depois** de indexar: repita a mesma pergunta no agente. A resposta deve trazer valores e condições baseados nos documentos (RAG).

### Pegada 2 – De onde veio cada trecho?

O Chroma guarda o campo `source` (nome do arquivo) nos metadados. Você pode inspecionar `out/chunks_lab.json` e ver qual chunk veio de qual arquivo. Proponha três perguntas: uma que puxe mais do PDF, uma do CSV, uma do TXT, e confira se os trechos retornados batem com a fonte esperada.

### Pegada 3 – Brincar com a config

Em `config/memory_policy.yaml` altere:

- `max_documents`: 3 → 5. Rode de novo o script de consulta: tende a retornar mais trechos.
- `min_similarity_score`: 0,70 → 0,50. Rode de novo: pode aparecer mais contexto, com possível ruído.

Discuta o efeito de cada parâmetro.

### Pegada 4 – Chunk size importa

Em `config/indexing.yaml` altere `chunk_size_chars` (ex.: 512 → 256). Apague `data/chroma`, reindexe os 3 arquivos e rode a mesma pergunta. Compare a qualidade dos trechos (mais fragmentado vs mais contexto por chunk).

### Pegada 5 – E se um arquivo não existisse?

Indexe só o PDF e o CSV (sem o TXT). Faça uma pergunta que depende do conteúdo do TXT (ex.: “Quantas recusas de taxa disparam handoff?”). Veja a resposta incompleta. Reindexe com os 3 arquivos e compare.

---

## Troubleshooting

| Problema                                                               | O que verificar                                                                                                                                                                                                                                                                  |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Script `rag_query.py` não encontra o módulo `src`                      | Execute sempre na **raiz** do projeto. Rode `pip install -e .`.                                                                                                                                                                                                                  |
| Saída do RAG sempre vazia após indexar                                 | Confirme `backend: chroma` em `memory_policy.yaml`. Confira se o comando de indexação terminou com “Vector store ChromaDB: N documentos gravados”. Veja se `data/chroma` existe e foi atualizado.                                                                                |
| “Formato não suportado” ao indexar                                     | Extensões aceitas: `.csv`, `.json`, `.pdf`, `.txt`. Verifique o caminho e a extensão do arquivo.                                                                                                                                                                                 |
| PDF não encontrado                                                     | Rode `python scripts/generate_lab_pdf.py` antes da indexação.                                                                                                                                                                                                                    |
| Erro de NumPy/Chroma (np.float\_, "object of type 'int' has no len()") | O código em `vector_store.py` trata compatibilidade NumPy 2. Em alguns ambientes (Chroma 0.5 + NumPy 2), a consulta pode falhar; a indexação costuma funcionar. Se a consulta retornar vazio mesmo com documentos: apague `data/chroma`, reindexe; ou use um venv com `numpy<2`. |
| TypeError: metadata key None                                           | Metadados com chave `None` são filtrados pelo vector_store. Se persistir, confira loaders (ex.: CSV com coluna sem nome).                                                                                                                                                        |
| Mock em vez de Chroma                                                  | Se `backend` estiver `mock`, a consulta usa respostas fixas. Altere para `chroma` e limpe `data/chroma` para testar com o banco real.                                                                                                                                            |
| Quero usar Vertex embeddings mas aparece "Vertex não configurado"       | O script `rag_query.py` e o CLI de indexação carregam o **`.env`** da raiz. Confira que existe `.env` com `GOOGLE_CLOUD_PROJECT` e `GOOGLE_CLOUD_LOCATION` (ou `GOOGLE_CLOUD_REGION`). Rode a partir da raiz.                                                                                                                                 |
| "Collection expecting embedding with dimension of X, got 768" (incompatibilidade) | Index e consulta devem usar a mesma dimensão. O **mock** e o **Vertex** (text-multilingual-embedding-002) usam **768** dimensões. Se a collection foi criada com dados antigos (ex.: mock em 128 dim), **apague `data/chroma`** e reindexe; assim index e consulta ficam em 768. |

---

## Validação rápida do lab (instrutor)

Para validar que o lab está correto, execute na raiz do projeto, na ordem:

1. `python scripts/generate_lab_pdf.py` → deve imprimir "PDF gerado: ... lab_conta_premium.pdf".
2. `python scripts/rag_query.py "Quais são as tarifas da conta premium e as condições para empréstimo pessoal?"` → com Chroma vazio: "(nenhum trecho recuperado)" ou saída vazia.
3. Apagar `data/chroma` (se existir); depois:  
   `python -m src.indexing --config config/indexing.yaml --input data/lab/lab_conta_premium.pdf data/lab/lab_tarifas.csv data/lab/lab_emprestimo.txt --output out/chunks_lab.json --push`  
   → deve mostrar "Chunks gravados", "Vector store ChromaDB: N documentos gravados", "Push concluído".
4. Repetir o comando do passo 2 → esperado: trechos de texto recuperados (em ambientes onde a consulta Chroma funciona; em alguns setups com NumPy 2 a consulta pode falhar — ver Troubleshooting).

Confirme também que existem: `data/lab/lab_tarifas.csv`, `data/lab/lab_emprestimo.txt`, `scripts/rag_query.py`, `scripts/generate_lab_pdf.py` e que `config/memory_policy.yaml` tem `vector_search.backend: chroma`.

---

## Referências

- [Tutorial: Memória de Longo Prazo e RAG](tutorial_rag_memoria_longo_prazo.md) – visão geral do pipeline e arquivos.
- [config/indexing.yaml](../config/indexing.yaml) – chunking, coluna de texto, embedding.
- [config/memory_policy.yaml](../config/memory_policy.yaml) – backend do vector store (chroma | vertex | mock), max_documents, min_similarity_score.
