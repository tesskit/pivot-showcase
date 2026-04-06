# Pivot — RAG Pipeline

Pivot uses Retrieval-Augmented Generation to ground its responses in real data — salary figures, returnship programs, transferable skills research — rather than relying on Claude's training knowledge alone.

---

## The Problem RAG Solves

Claude's training knowledge includes general career information, but it has two limitations for Pivot's use case:

1. **Staleness** — salary data, returnship programs, and workforce statistics change. Training data may be 1-2 years old.
2. **Generality** — Pivot serves women across every industry, including service workers, domestic workers, clinical workers, and educators. Generic career data skews toward tech and white-collar roles.

RAG lets Pivot retrieve specific, curated, up-to-date content at query time and inject it into the Research Agent's context before generating a response.

---

## Data Sources

9 source files in `src/rag/data/`, purpose-built for Pivot's user base:

| File | Source | Content |
|---|---|---|
| bls_occupational.txt | Bureau of Labor Statistics | Occupational salary data by role |
| bls_women_workforce.txt | BLS | Women's workforce participation and wage data |
| bls_regional.txt | BLS | Regional salary variations |
| aauw_pay_equity.txt | AAUW | Pay equity research including race intersectionality |
| irelaunch.txt | iRelaunch | Return-to-work programs and returnship data |
| path_forward.txt | Path Forward | Returnship program listings |
| transferable_clinical.txt | Custom | Transferable skills for clinical workers |
| transferable_service.txt | Custom | Transferable skills for service, gig, and domestic workers |
| transferable_teachers.txt | Custom | Transferable skills for educators |

The transferable skills files are custom-built — they don't exist anywhere else. They map informal, gig, caregiving, and service work to the language employers use in job postings. This is core to Pivot's equity mission: the RAG data itself was designed to serve women the hiring system was built to overlook.

---

## The OOM Problem — And How We Fixed It

**The original approach** ran HuggingFace `all-MiniLM-L6-v2` directly on Render at query time. The model requires ~450MB RAM to load plus PyTorch, and produced a ~350MB inference spike per request. Combined with FastAPI, LangGraph, and the Anthropic SDK, the baseline exceeded Render Standard's 2GB RAM limit mid-conversation — causing silent OOM restarts that killed active sessions.

**The insight:** Pivot's RAG corpus is 43KB of static text across 9 files. It doesn't change between deploys. There is no reason to run a 450MB ML model on the server to embed a 10-word query at runtime.

**The fix:** Pre-compute the embeddings once locally and ship them as a flat file.

`src/rag/export_embeddings.py` reads the local ChromaDB and exports all 366 chunk vectors + text + metadata to `src/rag/embeddings.npz` (690KB). At query time, `main.py` loads this file once into a module-level cache, builds a lightweight keyword query vector, and runs cosine similarity in pure numpy — microseconds, zero model loading, zero memory spike.

This also eliminated `langchain-huggingface`, `langchain-chroma`, `chromadb`, and `sentence-transformers` from `requirements.txt` — the packages that pulled in PyTorch and caused Render's memory pressure and slow cold starts.

---

## Embeddings Stack

| Stage | Where | Tool |
|---|---|---|
| Ingest | Local only | HuggingFace `all-MiniLM-L6-v2` via `ingest.py` |
| Export | Local only | `export_embeddings.py` → `src/rag/embeddings.npz` |
| Runtime retrieval | Render | numpy cosine similarity — no model, no vector DB |

**Memory footprint at runtime:** ~2MB for the vectors in RAM, loaded once on startup.

---

## Query Construction

The Research Agent builds a query from the user's profile:

```
"Career resources for {situation} transitioning from {role} to {target}"
```

A keyword-hash vector (384-dim float32) is computed from this string and compared against all 366 pre-computed chunk vectors. Top-5 chunks by cosine score are injected into the Research Agent's context.

---

## Local Workflow

When adding new RAG data:

```
1. Add .txt file to src/rag/data/
2. pip install -r requirements-dev.txt   # HuggingFace etc — local only
3. python src/rag/ingest.py              # writes ChromaDB locally
4. python src/rag/export_embeddings.py   # exports to src/rag/embeddings.npz
5. git add src/rag/embeddings.npz
6. git commit -m "update RAG embeddings"
7. git push → Render picks it up on next deploy
```

HuggingFace, ChromaDB, and sentence-transformers never touch Render. They live in `requirements-dev.txt` and run locally only.

---

## Upgrade Path — Pivot 1.1

The keyword-hash vector is a lightweight approximation. For a larger corpus (more occupations, more metro areas, more industries), swap it for a real embedding via Anthropic's `voyage-3-lite` API. That's a 10-line change in `query_embeddings_file()` — the rest of the pipeline is unchanged.
