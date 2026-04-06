# Pivot 🔄
### An Agentic AI Career Advocate for Women

> *"When a woman opens Pivot, she shouldn't feel like she's filling out a form or being evaluated. She should feel like she finally found someone in her corner."*

> *In basketball, a pivot isn't starting over. You keep one foot planted while you change direction. Your experience is the anchor, not the obstacle. That's exactly what Pivot helps you do.*

---

## Live Demo
🔄 [pivotforwomen.com](https://pivotforwomen.com)
▶ [Watch a 2-minute demo](https://youtu.be/01qlKzlBgJA)

Access is token-gated during soft launch. Request your preview token directly in the app — a confirmation email will be sent to you via Resend.


## The Problem

The hiring system was built to evaluate a very specific kind of career: linear, uninterrupted, and already fluent in self-promotion. Job postings, resume screeners, applicant tracking software, interview processes, salary benchmarks — all of it. Most women didn't have that career.

Two Harvard studies — published in *The Quarterly Journal of Economics* and *Management Science* — confirm what many women already feel: the barrier is rarely skill. It is articulation. Women consistently underrate and underdescribe their own performance, even when they know an employer is evaluating them, even when they know it costs them money. See [docs/RESEARCH_APPROACHES.md](./docs/RESEARCH_APPROACHES.md) for the full academic foundation.

Existing tools like LinkedIn, Indeed, and resume builders fail her — and they fail her for the same reason. They assume she already knows how to talk about herself.

They fail her whether she is:
- **The Pivoter** — changing industries with more transferable skills than she realizes
- **The Loyalist** — built her career at one company and has the results to prove it
- **The Returner** — stepped away for a reason that mattered and is ready to come back
- **The Starter** — entering the workforce with more to offer than she's been told
- **The Escaper** — outgrown where she is and knows she's worth more
- **The Laid-Off** — didn't lose her value, lost a job

**Pivot doesn't fail her. It starts where she is.**

---

## What Pivot Does

Pivot is a multi-agent AI system that acts as a personal career advocate — not a job board, not a resume builder, not a chatbot.

A woman comes to Pivot and says things like:
- *"I want to change industries but I don't know how to translate what I know"*
- *"I took 5 years off for my kids and don't know how to explain that gap"*
- *"I was laid off and I don't know what I'm worth anymore"*
- *"I've spent years doing caregiving or gig work — does that even count?"*

Pivot doesn't assume her industry, her background, or her fears. It asks. It listens. It understands her specific situation. Then it autonomously researches, fact-checks, builds her narrative, and produces a concrete application packet — delivered in language that feels like a trusted friend who also happens to know exactly how the hiring system works.

Specifically, Pivot helps her:
- **Translate her real experience** into language job postings and ATS systems recognize — including informal, gig, caregiving, and domestic work
- **Bridge the evaluation gap** — mapping what she's actually done to what the hiring process tests for
- **Build her STAR story** — turning real work experiences into interview-ready format without losing what makes them genuine
- **Know her worth** — real salary data for her specific role, industry, and geography
- **Apply with confidence** — resume bullets, cover letter angle, and one quick win tailored to a specific posting
- **Move at her pace** — one small next step at a time, never the whole mountain

She leaves feeling **seen, heard, and capable.**

---

## The Core Insight

Fear doesn't go away because someone gives you information. It goes away through feeling understood, breaking the overwhelming into small steps, and evidence that you're more ready than you think.

Every agent in Pivot is designed around this. Empathy first. Strategy second.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph |
| LLM | Anthropic Claude API (claude-sonnet-4-20250514) |
| Embeddings (ingest) | HuggingFace `all-MiniLM-L6-v2` — runs locally only, never on Render |
| RAG Runtime | Pre-computed `embeddings.npz` + numpy cosine similarity — no model on server |
| Vector Database | ChromaDB — local ingest only, not deployed to Render |
| Backend | Python 3.11 + FastAPI |
| Frontend | React / Next.js |
| Job Data | JSearch via RapidAPI (Google for Jobs) + USAJobs. Claude normalizes job titles ("maid" → "Housekeeper"). Nominatim geocodes locations ("Monmouth County" → "Monmouth County, NJ"). Free sources tried and removed — garbage. |
| Session DB | PostgreSQL (Render) + psycopg2 — primary session store with blob fallback |
| Deployment | Vercel (frontend) + Render Standard (backend) |
| Data Sources | BLS, AAUW, iRelaunch, Path Forward, custom transferable skills corpus |

---

## Seven-Agent Pipeline
```
User Input
    ↓
Orchestrator → Intake → Research → Fact-Check → Application Coach → Narrative → Synthesizer
                                                                                    ↓
                                                                             Her Response
```

| Agent | Job |
|---|---|
| Orchestrator | Routes to Intake, manages state |
| Intake | Builds her profile through warm conversation |
| Research | Finds salary data, job listings, situation-specific resources |
| Fact-Check | Verifies everything before it reaches her |
| Application Coach | Resume bullets, cover letter angle, skills to highlight, quick win |
| Narrative | Translates her experience into market language, builds her STAR story |
| Synthesizer | The only voice she hears — warm, coherent, one question at the end |

---

## Privacy by Design

- RAG embeddings are pre-computed locally from curated source files only — never user data
- At runtime, no embedding model runs on the server and no user query is sent to a third-party embedding API
- Session state is stored in PostgreSQL with a 2-hour inactivity TTL — automatically deleted after the session ends. A full state blob is also held client-side as a fallback so no conversation is ever lost.
- Pivot can email you your career summary at any time during your session via Resend — your email address is used only to deliver that message and is never stored

---

## Learn More

- 📐 [ARCHITECTURE.md](./ARCHITECTURE.md) — full technical deep dive: agent diagram, RAG pipeline, skill/prompt structure, tradeoffs, equity design decisions
- 📋 [docs/JOB_DATA_APPROACHES.md](./docs/JOB_DATA_APPROACHES.md) — job data source documentation and architectural decisions

---

## Project Status

🚧 Active development — Step 5 complete

- ✅ Step 1: Project scaffold, LangGraph graph, basic agent stubs
- ✅ Step 2: Intake Agent, profile extraction, PROFILE block
- ✅ Step 3: Research, Fact-Check, Narrative agents wired
- ✅ Step 4: RAG pipeline (366 chunks, ChromaDB local), Application Coach agent, equity audit, all prompt/skill files load from disk
- ✅ Step 5: React/Next.js frontend, FastAPI, JSearch + USAJobs, Resend email, deploy to Vercel + Render, lightweight numpy RAG (no HuggingFace/ChromaDB on server)
- ⬜ Step 6: Expand RAG corpus, Indeed Publisher API integration, Google OAuth + PostgreSQL user accounts

---

## Why I Built This

I'm a software engineer specializing in agentic AI systems and full-stack development. I also played and coached basketball — and the most important thing about a pivot is this: you don't start over. You keep one foot planted, change your angle, and find the open path. Your experience is the anchor.

The research is clear and the problem is real. Women across every industry consistently underdescribe their own performance — not because they lack capability, but because the hiring system was never built to recognize how they work.

So I built the tool that should have existed already.

---

> This repository contains architecture docs, agent design files, and a demo script. The full implementation is private.
