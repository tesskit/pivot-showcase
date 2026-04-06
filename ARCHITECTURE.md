# Pivot — Architecture Document

**Version:** 0.9 (Session table, mid-session job re-routing, relevance filter improvements)
**Status:** Active development

---

## 1. Problem Statement

Existing career tools are built for linear careers. They reward continuous employment, single-industry experience, and people who already know how to market themselves. They systematically disadvantage women who have career gaps, pivoted industries, spent decades building expertise in ways that don't map cleanly to a job description, or whose work history includes informal, gig, caregiving, or domestic labor that the system doesn't recognize.

The core problem is not skill — it is articulation. Women know what they've done. The system just wasn't built to recognize it.

Pivot is an agentic AI system that closes that gap — across every industry, every background, every situation.

---

## 2. Design Philosophy

### 2.1 Empathy Before Strategy
Every agent response leads with acknowledgment before information. This is not a UX nicety — it is a core architectural decision. The articulation gap is the primary blocker for the target user, not capability, not readiness. Addressing it directly in every interaction is what makes Pivot different from every other career tool.

### 2.2 Never Assume
Pivot makes zero assumptions about a user's industry, background, technical level, or situation. The intake agent asks before the system acts. Informal, gig, caregiving, and domestic work is treated as real work from the first message.

### 2.3 Advocacy Lens Only
Pivot never frames what she lacks. Every output — resume bullets, cover letter angles, skills to highlight — frames what she brings. There is no skills_gap field anywhere in the system. This is an intentional equity design decision.

### 2.4 Lean Instructions, Composable Skills
Prompt files are minimal and pointed. Shared behaviors (empathy, anxiety response, limits) live in composable skill files used across multiple agents. This keeps the system maintainable and testable without touching agent logic.

### 2.5 Privacy by Design
RAG embeddings are pre-computed locally from curated source files only — never user data. At runtime, no embedding model runs on the server and no user query text is sent to a third-party embedding API. Cosine similarity runs in numpy against static pre-computed vectors. User session state lives in PivotState (in-memory only). PostgreSQL (Pivot 1.1) will store user accounts separately.

### 2.6 Know the Limits
Pivot is a career advocate, not a therapist. When a user's situation appears to exceed what a career tool can address, Pivot acknowledges it warmly and points to appropriate human resources. This is a deliberate ethical design decision, not an afterthought.

### 2.7 Email as the Primary Deliverable
The Synthesizer response in the chat is the conversation. The emailed career packet is the deliverable. Every full pipeline run produces a formatted HTML email containing the user's STAR story, resume bullets, strongest angle, quick win, and live job listings with Apply Now buttons — all converted to second person (you/your) before delivery. The Synthesizer always nudges the user to send it to herself.

---

## 3. Multi-Agent Architecture

Pivot uses LangGraph to orchestrate seven specialized agents. The user only ever hears from the Synthesizer.
```
User Input
    ↓
Orchestrator
    ↓
Intake Agent          ← builds her profile through warm conversation
    ↓ (profile_complete gate)
Research Agent        ← salary data, job listings, situation-specific resources
    ↓
Fact-Check Agent      ← verifies everything, flags unverified claims
    ↓
Application Coach     ← resume bullets, cover letter angle, quick win
    ↓
Narrative Agent       ← STAR story, market language translation
    ↓
Synthesizer Agent     ← the only voice she hears after her profile is complete
    ↓
Her Response
```

---

## 4. Agent Responsibilities

| Agent | Input | Output | Gate |
|---|---|---|---|
| Orchestrator | User message | Routes to Intake | None |
| Intake | Conversation history | Profile JSON + PROFILE block | None |
| Research | profile_complete=True | Salary data, job listings, RAG context | profile_complete |
| Fact-Check | Research summary | Verified research with labels | research exists |
| Application Coach | Verified research + narrative | Resume bullets, quick win | profile_complete + verified_research |
| Narrative | Profile + verified research | STAR story, market language | profile_complete + verified_research |
| Synthesizer | All agent outputs + live_jobs | Final user-facing response | verified_research or research |

---

## 5. State Management

PivotState is the baton passed between every agent:

```python
class PivotState(TypedDict):
    messages: List[dict]        # full conversation history
    user_input: str             # her most recent message
    profile: dict               # what we know about her
    research: dict              # Research Agent output
    verified_research: dict     # Fact-Check Agent output
    narrative: dict             # STAR story + resume bullets
    application_coach: dict     # resume bullets, cover letter angle, quick win
    live_jobs: str              # raw job listings with apply links — bypasses summarization
    response: str               # the final response she sees
    turn_count: int
    profile_complete: bool
```

The `live_jobs` field is critical — it bypasses the Research and Narrative agents' prose summarization that would strip apply links. Raw listings are stored directly in state and passed to the Synthesizer as structured text.

**Session persistence** uses a two-layer approach:
- **Primary:** PostgreSQL session table (`sessions`) stores the full `PivotState` blob keyed by UUID. The frontend stores `session_id` in `localStorage` and sends it with every request. The backend loads state from the DB, runs the pipeline, and writes the result back.
- **Fallback:** The full `session_state` blob is also returned in every response and sent back with the next request. If the DB is unavailable or the session has expired, the blob carries the conversation forward without any data loss.
- **TTL:** Sessions are automatically deleted after 2 hours of inactivity. A `/ping` endpoint resets the clock without changing state — called when the user clicks "Keep it going" on the timeout warning banner.
- **Cleanup:** Expired sessions are purged three ways: on startup via `cleanup_expired_sessions()`, on every `/session/load` call, and every 30 minutes via UptimeRobot pinging the `/cleanup` endpoint. This guarantees sessions are deleted within 2.5 hours of expiry at most.

**Session timeout UX flow:**
After 1h45m of inactivity, a modal overlay appears (not an inline banner — it's impossible to miss):
- **Screen 1:** "Still there? ✦" — Keep it open or End my session
- **Screen 2a (if packet is ready):** "Before you go ✦" — inline email input to send career packet before session ends. Auto-advances to Screen 3 after sending.
- **Screen 2b (no packet):** Skips straight to Screen 3
- **Screen 3:** "All done? ✦" — final confirmation before ending
- **After confirmation:** Shows "You've got this. ✦" for 3 seconds then redirects to the access page for a clean restart

---

## 6. RAG Pipeline

### 6.1 Data Sources
9 source files make up the RAG knowledge base in `src/rag/data/`:

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

### 6.2 Embeddings Stack
- **Ingest (local only):** HuggingFace `all-MiniLM-L6-v2` via `ingest.py` + `export_embeddings.py`
- **Runtime (Render):** Pre-computed vectors in `src/rag/embeddings.npz` (366 chunks, 690KB flat file)
- **Retrieval:** Cosine similarity via numpy — no model, no vector DB, no API calls at query time
- **Memory footprint:** ~2MB for the vectors in RAM (loaded once into a module-level cache)

### 6.3 Why We Moved Away From HuggingFace + ChromaDB at Runtime

**The original approach** ran HuggingFace `all-MiniLM-L6-v2` directly on Render. The model requires ~450MB RAM to load plus PyTorch, and produced a ~350MB inference spike per request. Combined with FastAPI, LangGraph, and the Anthropic SDK, the baseline exceeded Render Standard's 2GB limit mid-conversation — causing OOM restarts that silently killed active sessions.

**The insight:** The RAG knowledge base is 43KB of static text across 9 files. It doesn't change between deploys. There is no reason to run a 450MB ML model on the server to embed a 10-word query at runtime. The embeddings can be pre-computed once locally and committed to the repo as a flat file.

**The fix:** `src/rag/export_embeddings.py` reads the local ChromaDB and exports all 366 chunk vectors + text + metadata to `src/rag/embeddings.npz`. At query time, `main.py` loads this file once (module-level cache), builds a lightweight keyword query vector, and runs cosine similarity in pure numpy — microseconds, zero model loading.

This also eliminated `langchain-huggingface`, `langchain-chroma`, `chromadb`, and `sentence-transformers` from `requirements.txt` — packages that pulled in PyTorch and were the primary source of Render's memory pressure and slow cold starts.

### 6.4 Local RAG Workflow
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

### 6.5 Query Construction
Query is constructed from profile fields:
```
"Career resources for {situation} transitioning from {role} to {target}"
```
A keyword-hash vector (384-dim float32) is computed from this string and compared against all 366 pre-computed chunk vectors. Top-5 by cosine score are returned as context to the Research Agent.

**Pass 2 upgrade path:** For a larger knowledge base (more occupations, more metros), swap the keyword hash vector for a real embedding via Anthropic's voyage-3-lite API. That's a 10-line change in `query_embeddings_file()`.

---

## 7. Job Data Sources

| Source | Type | Cost | Notes |
|---|---|---|---|
| JSearch via RapidAPI | Live (Google for Jobs) | 200 req/month free | Aggregates Indeed, LinkedIn, Glassdoor, ZipRecruiter |
| USAJobs.gov | Live (government only) | Free, unlimited | Federal and VA roles, strong for healthcare |
| Indeed Publisher API | Live (direct) | Free with OAuth | Next priority — replaces removed multi-source waterfall |
| Claude training knowledge | Static fallback | Included in API cost | Used when live sources return 0 results |

**Removed: Free multi-source waterfall (Himalayas, The Muse, Adzuna, Jooble)**
These sources were free and unlimited but proved useless in production. They skew heavily toward tech and remote roles — a search for "housekeeper in New Jersey" returned Relationship Bankers, LPNs, and Senior Product Managers regardless of query. Removed entirely in favor of an honest Claude fallback that describes the real market landscape in prose rather than showing irrelevant listings with Apply Now buttons.

See `docs/JOB_DATA_APPROACHES.md` for full documentation including architectural decisions and NJ nurse examples.

### 7.1 Job Title Normalization — Claude

Women describe their work in human language, not HR language. A woman who has cleaned rooms at the Waldorf Astoria for 15 years calls herself a "maid." Employers post jobs titled "Housekeeper" or "Room Attendant." Searching for "maid" on Google for Jobs returns almost nothing.

The fix: one small Claude API call before the job search. `normalize_job_title()` sends the raw title to Claude: "What is the standard job title employers use when posting '{title}' jobs? Return only the title, nothing else." No list to maintain. Works for any title in any industry forever.

Real results:
- `"maid"` → `"Housekeeper"`
- `"waitress"` → `"Server"`
- `"cleaning lady"` → `"Housekeeper"`
- `"stewardess"` → `"Flight Attendant"`

### 7.2 Location Normalization — Nominatim Geocoding

Women describe where they live in human terms. "Monmouth County." "Central NJ." "Near Princeton." JSearch works on city + state format. The fix: Nominatim (OpenStreetMap's free geocoding API) converts any location format to clean city/state that JSearch understands. Free, no API key required.

Real results:
- `"Monmouth County NJ"` → `"Monmouth County, NJ"`
- `"central NJ"` → `"Trenton, NJ"`
- `"near Princeton"` → `"Princeton, NJ"`
- `"remote"` → `"remote"` (unchanged)

### 7.3 Zero Results Fallback
When both JSearch and USAJobs return 0 results, the Research Agent describes the job market landscape using Claude's training knowledge — 2-3 representative titles, typical employers, and salary ranges in prose. It does not fabricate specific postings.

---

## 8. Frontend

### 8.1 Stack
React/Next.js deployed on Vercel. Communicates with FastAPI backend via HTTP.

### 8.2 Key Features
- Token gate (access page) with GSAP stagger animation on load
- Chat interface with CSS fadeUp animation on message bubbles
- Inline Apply Now ✦ buttons rendered from `Apply: https://...` lines in Synthesizer output
- Email bar — always visible after first message, upgrades to `packetReady` state when full pipeline completes
- `packetReady` state triggers GSAP glow sweep on email bar and updates label text to "✦ Your career packet is ready"
- Status messages cycle during pipeline wait
- 180 second timeout on both frontend (AbortController) and backend (asyncio.wait_for)

### 8.3 Email Bar UX
The email is the primary deliverable — not the chat:
1. Email bar is always visible after the first message
2. When `packetReady` fires, the bar pulses with a GSAP glow sweep
3. Label updates to "✦ Your career packet is ready — Email my career packet"
4. Synthesizer always ends with an explicit nudge to send it
5. After sending, `packetReady` resets and the bar returns to its default state

---

## 9. Backend

### 9.1 FastAPI Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| / | GET, HEAD | Health check — UptimeRobot pings this |
| /chat | POST | Run the full LangGraph pipeline |
| /email | POST | Send formatted career packet via Resend |
| /ping | POST | Reset session TTL clock — called by "Keep it going" button |
| /session | DELETE | Explicit session cleanup — called by "No thanks" button |

### 9.2 Email Architecture
The `/email` endpoint builds two versions of the career packet:
- **Plain text** — fallback for email clients without HTML support
- **HTML** — rich formatted email with Pivot ✦ header, bold STAR labels (Situation/Task/Action/Result), purple section headers, gold callout box for strongest angle, Apply Now ✦ buttons, and a restart block

All narrative content passes through `to_you()` — a converter that replaces third-person pronouns (she/her) with second-person (you/your) for user-facing delivery.

### 9.3 Render Deployment Configuration

| Component | What It Controls | Correct Setting | Cost |
|---|---|---|---|
| Workspace Plan | Team/org features, collaboration | Hobby | Free |
| Build Pipeline | Build minutes per deploy | Starter + $15 spend limit | ~$5-15/month |
| Service Instance | Running application — RAM, CPU, performance | Standard | $25/month |

**Why Standard:** The pre-computed embeddings file loads into RAM on startup. Combined with FastAPI, LangGraph, and the Anthropic SDK, the baseline requires 2GB RAM. Anything below Standard causes OOM crashes mid-conversation.

### 9.4 UptimeRobot Keep-Alive
UptimeRobot pings the health endpoint every 5 minutes to keep the Render service warm and prevent the 15-minute spin-down.

---

## 10. Tradeoffs

| Decision | Considered | Chose | Why |
|---|---|---|---|
| Agent framework | LangChain vs LangGraph | LangGraph | Better state management for sequential multi-agent flows |
| LLM | OpenAI vs Anthropic | Anthropic Claude | Superior instruction following, empathetic tone, Constitutional AI alignment |
| Vector DB | Pinecone vs ChromaDB | ChromaDB (local ingest only) | Zero cost for portfolio; ChromaDB no longer runs on Render — see RAG runtime row |
| Embeddings | Anthropic vs HuggingFace | HuggingFace all-MiniLM-L6-v2 | Runs locally during ingest, no API key, no user data leaves the machine |
| RAG runtime | HuggingFace model on Render vs flat file + numpy | Pre-computed embeddings.npz + numpy | Eliminated PyTorch and related packages — removed ~450MB from Render memory footprint |
| Job data | Six sources evaluated | JSearch + USAJobs active; multi-source removed; Indeed next | Free sources returned garbage for service and hospitality roles regardless of query |
| Email delivery | Gmail MCP vs Resend | Resend | Gmail MCP authenticates via browser session — cannot auth from Python backend |
| Session state | Client-side blob vs PostgreSQL | PostgreSQL primary + blob fallback | DB enables TTL, debugging, and future resume-session UX |
| Job title normalization | Hard-coded synonym map vs Claude API call | Claude API call (20 tokens) | Synonym maps need thousands of entries; Claude knows the full vocabulary of work |
| Location normalization | Regex county stripping vs Nominatim | Nominatim (free, no API key) | 3,000+ US counties can't be hard-coded; Nominatim handles any format |
| Skills gap framing | Standard career tool approach | No skills_gap field | Advocacy lens — frame what she brings, never what she lacks |

---

## 11. Ethical Considerations

- **Advocacy lens only.** No skills_gap field anywhere. Pivot frames what she brings.
- **Informal work is real work.** Gig, caregiving, domestic, and service work treated as valid experience throughout.
- **No hallucination tolerance.** Fact-Check Agent validates all research outputs. RAG grounds responses in real sources.
- **Privacy by design.** Embeddings are pre-computed locally — never user data. No embedding model runs on the server at runtime.
- **Race intersectionality.** RAG knowledge base explicitly includes wage gap data by race and ethnicity, not just gender.
- **Not a therapist.** When a situation exceeds career tool scope, Pivot refers warmly to human resources (988).
- **No industry assumptions.** Intake never defaults to tech. Every profile is built from her answers.
- **Loyalist protection.** If a user says she loves her field, Pivot never suggests leaving it.

---

## 12. Pivot 1.1 Roadmap

| Priority | Feature | Description |
|---|---|---|
| High | Google OAuth + PostgreSQL | User accounts, persistent conversation history, saved profiles |
| High | Indeed Publisher API | Direct Indeed job listings via OAuth — requires PostgreSQL for token storage |
| Medium | Google Calendar MCP | Schedule interviews, set follow-up reminders directly from Pivot |
| Medium | Expanded RAG knowledge base — Pass 2 | More occupations, more metro areas; swap keyword hash vector for voyage-3-lite embeddings API |
| Medium | Immigrant workforce | Credential recognition, language support, non-linear career history |
| Low | Spanish language support | First non-English language expansion |
| Low | Rate limiting + guest mode | Turn limits for unauthenticated users |
| Medium | Real-time Fact-Check verification | Replace Claude-based reasoning verification with actual web search calls — verify job postings are still active, confirm returnship programs are running, validate org activity in real time |
