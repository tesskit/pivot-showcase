# Pivot — Architecture Document

**Version:** 1.0 (Apify Indeed + LinkedIn direct integration, Courses subagent, two-phase pipeline, session reliability)
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
RAG embeddings are pre-computed locally from curated source files only, never user data. At runtime, no embedding model runs on the server and no user query text is sent to a third-party embedding API. Cosine similarity runs in numpy against static pre-computed vectors. User session state lives in PivotState while a request runs and in the user's browser between requests. Server-side storage in PostgreSQL (sessions and email recipients) is built but switched off by default behind the `PERSIST_USER_DATA_IN_DB` flag (see Section 5). Her email address is held in memory only for the single send request and is not written to the database. User accounts in PostgreSQL are planned for Pivot 1.1.

### 2.6 Know the Limits
Pivot is a career advocate, not a therapist. When a user's situation appears to exceed what a career tool can address, Pivot acknowledges it warmly and points to appropriate human resources. This is a deliberate ethical design decision, not an afterthought.

### 2.7 Email as the Primary Deliverable
The Synthesizer response in the chat is the conversation. The emailed career packet is the deliverable. Every full pipeline run produces a formatted HTML email containing the user's STAR story, resume bullets, strongest angle, quick win, and live job listings with Apply Now buttons — all converted to second person (you/your) before delivery. The Synthesizer always nudges the user to send it to herself.

---

## 3. Multi-Agent Architecture

Pivot uses LangGraph to orchestrate seven agents plus one subagent (the Courses Subagent, which runs inside Research). The user hears from the Intake Agent while her profile is being built and from the Synthesizer after that.
```
User Input
    ↓
Orchestrator          ← rule-based routing, no LLM call
    ↓
Intake Agent          ← builds her profile through warm conversation
    ↓ (profile_complete)
Research Agent        ← salary data, RAG context, live job listings
    │  └─ Courses Subagent   ← background thread, runs while jobs are fetched
    ↓
Fact-Check Agent      ← verifies everything, flags unverified claims
    ↓
Narrative Agent  +  Application Coach    ← run in parallel (one graph node)
    ↓
Synthesizer Agent     ← her voice after her profile is complete
    ↓
Her Response
```

### 3.1 Parallel execution

Parallel threads are used in two places:

1. **Research Agent and the Courses Subagent.** The Courses Subagent starts in a background thread (a ThreadPoolExecutor with one worker) at the beginning of the Research Agent and runs while the job search runs. The Research Agent collects its result after the job waterfall finishes, waiting up to 30 seconds. If it fails or times out, courses are simply empty and the rest of the pipeline continues. This is the only subagent in the system.
2. **Narrative Agent and Application Coach.** Both run side by side inside one graph node (`narrative_and_coach`) using a two-worker ThreadPoolExecutor. They are full agents, not subagents. Neither waits for the other; both read the profile and the verified research summary.

Job search is not a separate agent. It is a sequence of steps inside the Research Agent (Apify Indeed, then Apify LinkedIn, deduplication, JSearch fallback, USAJobs, Claude fallback). See Section 7.

### 3.2 Three compiled graphs

The same agents are wired into three LangGraph graphs in `src/main.py`:

| Graph | Endpoint | Nodes |
|---|---|---|
| Full (`pivot`) | `/chat` | Orchestrator, Intake, Research, Fact-Check, narrative_and_coach, Synthesizer |
| Fast (`pivot_fast`), Phase 1 | `/chat/fast` | Orchestrator, Intake, Research, Fact-Check, fast_responder |
| Finish (`pivot_finish`), Phase 2 | `/chat/finish` | narrative_and_coach, Synthesizer |

`fast_responder` builds a quick, jobs-focused reply without calling Claude. The fast graph returns the job listings and courses first. The finish graph then builds the STAR story, resume bullets, and the final response, and the email button activates when it returns.

### 3.3 Routing and gates

- **Orchestrator** runs on every turn and makes no LLM call. It routes to Intake while her profile is incomplete, to Research when she asks for a new job search after the pipeline has run (it clears the previous research and live jobs first), or to the Synthesizer only for follow-up conversation (to `fast_responder` in the fast graph). It also records employers she asks to exclude.
- **`profile_complete`** is the gate that starts the pipeline. Intake sets it in one of two ways: the PROFILE block from Claude, which is only honored once an accomplishment and an outcome have been captured (or she explicitly asks for jobs), or the Python profile extractor firing when all required fields are present.
- **Each downstream agent skips itself when its input is missing.** Research skips unless `profile_complete` is true. Fact-Check skips if there is no research. `narrative_and_coach` skips unless `profile_complete` and `verified_research` both exist. The Synthesizer skips if there is no research.
- **`_pipeline_complete`** is set after Fact-Check produces verified research and is never cleared. The Orchestrator uses it to treat later turns as follow-ups.

### 3.4 Why LangGraph, and where LangChain fits

LangGraph was chosen over LangChain as the agent framework because Pivot is a multi-agent flow with shared state and gates, and LangGraph is built for state management in sequential multi-agent flows. LangChain is used only in the local RAG ingestion script (`src/rag/ingest.py`), which loads documents, splits them into chunks, and creates embeddings. Those packages live in `requirements-dev.txt` and are not installed on the production server. At runtime, retrieval is a pre-computed embeddings file plus numpy cosine similarity (see Section 6).

---

## 4. Agent Responsibilities

| Agent | Model | Input | Output | Runs when |
|---|---|---|---|---|
| Orchestrator | None (Python and regex) | User message and state | Route: Intake, Research, or Synthesizer only | Every turn |
| Intake | Claude Sonnet | Conversation history | Profile JSON, PROFILE block, `profile_complete` | Until profile is complete |
| Research | Claude Sonnet | Profile | Salary data, RAG context, live job listings, courses | `profile_complete` |
| Courses Subagent | Claude Haiku | Target role | 3 to 5 courses (name, platform, cost, link) | Inside Research, in parallel with the job search |
| Fact-Check | Claude Haiku | Research summary | Verified research with labels | Research exists |
| Narrative | Claude Sonnet | Profile and verified research | STAR story, market language | `profile_complete` and `verified_research`; parallel with Application Coach |
| Application Coach | Claude Haiku | Profile and verified research | Resume bullets, cover letter angle, quick win | Same as Narrative; parallel with Narrative |
| Synthesizer | Claude Sonnet | All agent outputs and `live_jobs` | Final user-facing response | Research or verified research exists |

Small Claude Haiku helper calls such as `normalize_job_title`, `infer_industry`, `extract_profile_fields`, and `detect_job_search_intent` are plain functions in `main.py`, not agents.

---

## 5. State Management

PivotState is the baton passed between every agent:

```python
class PivotState(TypedDict):
    messages: List[dict]           # full conversation history
    user_input: str                # her most recent message
    profile: dict                  # what we know about her
    extracted_profile: dict        # accumulated by the Python extractor across turns
    work_arrangement: str          # remote / hybrid / in-person / any
    research: dict                 # Research Agent output
    verified_research: dict        # Fact-Check Agent output
    narrative: dict                # STAR story + resume bullets
    application_coach: dict        # resume bullets, cover letter angle, quick win
    live_jobs: str                 # raw job listings with apply links, bypasses summarization
    courses: str                   # Courses Subagent output
    response: str                  # the final response she sees
    turn_count: int
    profile_complete: bool
    excluded_employers: List[str]  # employers she has explicitly rejected
    _pipeline_complete: bool       # set after the first full pipeline run, never cleared
    _is_resarch: bool              # set by the Orchestrator on a re-search
    _resarch_target: str           # new job target for a re-search, set by the Orchestrator
    target_industry: str           # industry qualifier for the job search
```

The `live_jobs` field is critical — it bypasses the Research and Narrative agents' prose summarization that would strip apply links. Raw listings are stored directly in state and passed to the Synthesizer as structured text.

**Session persistence** uses a two-layer approach, with the database layer switched off by default:
- **Primary (only when the flag is on):** PostgreSQL session table (`sessions`) stores the full `PivotState` blob keyed by UUID. The frontend stores `session_id` in `localStorage` and sends it with every request. The backend loads state from the DB, runs the pipeline, and writes the result back.
- **Fallback:** The full `session_state` blob is also returned in every response and sent back with the next request. If the DB is unavailable or the session has expired, the blob carries the conversation forward without any data loss.
- **TTL (when the flag is on):** Sessions are automatically deleted after 2 hours of inactivity. A `/ping` endpoint resets the clock without changing state, and is called when the user clicks "Keep it going" on the timeout warning banner.
- **Feature flag:** `PERSIST_USER_DATA_IN_DB` (default off, in local and production). With it off, nothing about a conversation or an email address is written to PostgreSQL: `get_session` returns nothing, `update_session` does nothing, `/ping` reports success, and the `session_state` blob from the browser carries the conversation on every request. Resuming a conversation then works only in the same browser, within the 2-hour limit the frontend enforces. Deleting a session and purging expired rows still run. With the flag on, the Primary layer and TTL behavior above apply and `email_log` also stores the recipient address. A count row in `email_log` (time and status, no address) is written either way, for the monthly send count.
- **Cleanup:** Expired sessions are purged three ways: on startup via `cleanup_expired_sessions()`, on every `/session/load` call, and every 30 minutes via a background thread running inside the server process. A second UptimeRobot monitor hits `/cleanup` every 5 minutes as additional redundancy. Sessions are guaranteed to be deleted within 2.5 hours of expiry regardless of server restarts or user traffic.

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
| Apify Indeed Scraper | Live (direct Indeed) | ~$0.50/1K results | Primary. `misceres/indeed-scraper`, 20K users, 4.0 rating |
| Apify LinkedIn Scraper | Live (direct LinkedIn) | ~$10/1K results | Primary. `cryptosignals/linkedin-jobs-scraper`, public guest API, no login required |
| JSearch via RapidAPI | Live (Google for Jobs aggregator) | 200 req/month free | Fallback only — fires when Apify returns fewer than 10 combined results |
| USAJobs.gov | Live (government only) | Free, unlimited | Always runs — federal and VA roles |
| Claude training knowledge | Static fallback | Included in API cost | Silent fallback when all live sources fail |

**Job data waterfall — every pipeline run:**
```
1. Apify Indeed     -> up to 5 direct Indeed listings
2. Apify LinkedIn   -> up to 5 direct LinkedIn listings
3. Deduplicate      -> merge by company + title key, cap at 10
4. JSearch          -> fallback only if combined Apify < 10 results
5. USAJobs          -> always runs, government roles only
6. Claude fallback  -> silent, prose description only, no fabricated postings
```

Each listing is labeled [Indeed] or [LinkedIn] in the Synthesizer output. JSearch fallback listings carry no source label.

**Removed: Free multi-source waterfall (Himalayas, The Muse, Adzuna, Jooble)**
These sources skewed heavily toward tech and remote roles and returned garbage for service and hospitality roles regardless of query. Removed entirely.

**Removed: Indeed Publisher API path**
Requires browser-based OAuth that cannot complete from a server-side Python context on Render. Replaced by the Apify Indeed scraper which delivers direct Indeed data without OAuth complexity. The status of the public Publisher API has not been re-verified against Indeed's own documentation.

See `docs/JOB_DATA_APPROACHES.md` for full documentation including real Dallas nurse examples.

### 7.1 Job Title Normalization — Claude

Women describe their work in human language, not HR language. A woman who has cleaned rooms at the Waldorf Astoria for 15 years calls herself a "maid." Employers post jobs titled "Housekeeper" or "Room Attendant." Searching for "maid" on Google for Jobs returns almost nothing.

The fix: one small Claude API call before the job search. `normalize_job_title()` sends the raw title to Claude: "What is the standard job title employers use when posting '{title}' jobs? Return only the title, nothing else." No list to maintain. Works for any title in any industry forever.

Real results:
- `"maid"` → `"Housekeeper"`
- `"waitress"` → `"Server"`
- `"cleaning lady"` → `"Housekeeper"`
- `"stewardess"` → `"Flight Attendant"`

### 7.2 Location Normalization — Nominatim Geocoding

Women describe where they live in human terms. "Monmouth County." "Central NJ." "Near Princeton." The job sources (Indeed, LinkedIn, JSearch) work best with a city and state. The fix: Nominatim (OpenStreetMap's free geocoding API) converts any location format to a clean city and state. That cleaned location is used for the Apify Indeed and LinkedIn searches and for the JSearch fallback. Free, no API key required.

Real results:
- `"Monmouth County NJ"` → `"Monmouth County, NJ"`
- `"central NJ"` → `"Trenton, NJ"`
- `"near Princeton"` → `"Princeton, NJ"`
- `"remote"` → `"remote"` (unchanged)

### 7.3 Zero Results Fallback
When all live sources (Apify Indeed and LinkedIn, JSearch, and USAJobs) return 0 results, the Research Agent describes the job market landscape using Claude's training knowledge — 2-3 representative titles, typical employers, and salary ranges in prose. It does not fabricate specific postings.

---

## 8. Frontend

### 8.1 Stack
React/Next.js deployed on Vercel. Communicates with FastAPI backend via HTTP.

### 8.2 Key Features
- Token gate (access page) with GSAP stagger animation on load. The backend checks the typed token (`/token/check`), and several tokens can be active at once through the `PREVIEW_TOKENS` setting
- Chat interface with CSS fadeUp animation on message bubbles
- Inline Apply Now ✦ buttons rendered from `Apply: https://...` lines in Synthesizer output
- Recommended courses card: in the sidebar on desktop, inside the chat message area on phones (the sidebar is hidden at 768px and under)
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
| /token/check | POST | Check whether a typed access token is valid |
| /chat | POST | Run the full LangGraph pipeline |
| /email | POST | Send formatted career packet via Resend |
| /ping | POST | Reset session TTL clock — called by "Keep it going" button |
| /chat/fast | POST | Phase 1: Intake + Research + Jobs + Courses. Returns in ~30-45s |
| /chat/finish | POST | Phase 2: Narrative + App Coach + Synthesizer. Called after fast returns |
| /session/load | POST | Load session state for session restore on return banner |
| /session | DELETE | Explicit session cleanup — called by "No thanks" button |
| /cleanup | GET, POST, HEAD | Delete expired sessions. UptimeRobot and a background thread both trigger this |

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

**Why Standard for the Service Instance:**
The Service Instance is currently Standard (2GB RAM, $25/month). That size was chosen when HuggingFace and PyTorch ran on the server (see Section 6.3), and the original out-of-memory crashes happened on that setup. With the pre-computed embeddings file, the vectors need roughly 2MB of RAM. Smaller instances (512MB on Free or Starter) crashed with the old setup. This document does not record a test of a smaller instance with the current, lighter setup, so the 2GB figure has not been re-measured.

**Storing sessions and emails (environment variable):** `PERSIST_USER_DATA_IN_DB` does not need to be set on Render. When it is missing, the app treats it as off, so production stores no sessions or email addresses by default. To turn storage on later, add `PERSIST_USER_DATA_IN_DB` with the value `true` in the Render service's environment settings and redeploy. Setting it to `false` is allowed but has the same effect as leaving it unset. See Section 5.

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
| Job data | Six+ sources evaluated | Apify Indeed + LinkedIn primary; JSearch fallback; USAJobs always | Apify direct scrapers replaced JSearch as primary — better relevance, source-labeled results, no aggregator layer |
| Email delivery | Gmail MCP vs Resend | Resend | Gmail MCP authenticates via browser session — cannot auth from Python backend |
| Session state | Client-side blob vs PostgreSQL | PostgreSQL primary + blob fallback, built but off by default (`PERSIST_USER_DATA_IN_DB`) | DB enables TTL, debugging, and future resume-session UX. For now no sessions or emails are stored server-side and the browser blob carries the conversation. |
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
| Medium | Google Calendar MCP | Schedule interviews, set follow-up reminders directly from Pivot |
| Medium | Expanded RAG knowledge base — Pass 2 | More occupations, more metro areas; swap keyword hash vector for voyage-3-lite embeddings API |
| Medium | Immigrant workforce | Credential recognition, language support, non-linear career history |
| Low | Spanish language support | First non-English language expansion |
| Low | Rate limiting + guest mode | Turn limits for unauthenticated users |
| Medium | Real-time Fact-Check verification | Replace Claude-based reasoning verification with actual web search calls — verify job postings are still active, confirm returnship programs are running, validate org activity in real time |
| Done | Suggested Courses subagent | The Research Agent starts a Courses Subagent in a background thread while the job search runs, so it adds no pipeline time. It is a Claude Haiku call that uses training knowledge to return 3 to 5 courses with name, platform, cost, and link. When it is not certain of a course URL it returns the platform search page instead. Courses appear in the email packet after the job listings and as a card next to the chat (in the sidebar on desktop, inside the chat on mobile). Upgrade path: a live course data source, such as the Udemy Affiliate API, for current availability and pricing. |
