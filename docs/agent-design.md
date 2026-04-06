# Pivot — Agent Design

This document explains the reasoning behind Pivot's seven-agent architecture — why seven agents, what each one does, and the design decisions that shaped them.

---

## Why Seven Agents

The naive approach is one big prompt: send the user's message to Claude, get a response back. That breaks down immediately for Pivot's use case.

A single prompt cannot simultaneously:
- Ask warm, open-ended intake questions without jumping to advice
- Research real salary data and live job listings
- Verify that research before it reaches the user
- Translate her experience into market language
- Build a STAR story grounded in what she actually said
- Produce resume bullets, a cover letter opening, and a quick win
- Deliver all of it in a single coherent voice that feels human

Each of those is a distinct cognitive task with distinct failure modes. Collapsing them into one prompt produces a response that does all of them poorly. Separating them into specialized agents — each with a focused prompt, specific inputs, and specific outputs — produces a response that does each one well.

The seven agents are not arbitrary. Each exists because the task it owns cannot be reliably done by any other agent.

---

## The Agents

### Orchestrator
The traffic controller. Receives the user's message, delegates to Intake, and enforces the pipeline order. Never speaks to the user directly. Never skips Intake — you cannot advocate for someone you don't understand.

### Intake
The first voice she hears. Its only job is to understand her situation before anything else happens. Plain prose only. One question at a time. Never advice, never resources, never next steps — just warm, open listening until her profile is complete.

The PROFILE block is Intake's output — a structured JSON object that every downstream agent reads. It includes her role, target, location, situation archetype, accomplishment, impact, skills, obstacles, and outcome.

**Key design decision:** The profile gates the rest of the pipeline. Research, Fact-Check, Narrative, and Application Coach all wait for `profile_complete: true`. This prevents the pipeline from running on incomplete information.

### Research
Finds real data: live job listings via JSearch and USAJobs, salary ranges from BLS, returnship programs from iRelaunch and Path Forward, women's professional orgs by industry. Never guesses. Never assumes tech. Always anchors salary to her actual experience level — not entry-level, not the median. Women systematically undersell; Pivot corrects for this.

### Fact-Check
Verifies everything before it reaches the user. Flags unverified salary figures, stale job postings, inactive returnship programs. Does not remove flagged items — marks them clearly so the Synthesizer can handle them honestly. Live API results (JSearch, USAJobs) pass through as VERIFIED. Claude training knowledge is marked ESTIMATED.

### Application Coach
Produces the concrete packet: resume bullets tailored to the specific posting, a cover letter opening in first person, skills to highlight with evidence, and one quick win she can act on before she applies. Every output maps to the specific job posting — generic advice is not advocacy.

**Critical rule:** Never take language from the job posting and write it as if she said it. Her profile is the only source of truth about her experience.

### Narrative
Translates her experience into market language without losing her voice. Builds the STAR story (Situation, Task, Action, Result) from her five dimensions. Tailors the story to the specific posting. Tests for specificity — a thin accomplishment gets flagged as "Accomplishment too thin" rather than fabricated into a story.

### Synthesizer
The only voice she hears once her profile is complete. Takes all agent outputs and delivers them as a single coherent response — three paragraphs, warm and direct. Leads with acknowledgment. Delivers her narrative. Lists job listings as structured items with apply links. Ends with one question she hasn't already answered. Always ends with the email nudge.

**Key constraint:** Exactly three paragraphs. Not two, not four. This forces discipline — the Synthesizer cannot dump everything it received. It must choose what matters most.

---

## Composable Skills

Each agent loads shared skill files at runtime rather than duplicating behavior across prompts:

- `empathy.md` — tone rules, acknowledgment-first pattern, used by all agents
- `anxiety.md` — softer approach when she sounds defeated or stuck, used by Intake and Synthesizer
- `limits.md` — when to refer to human resources (988), used by all agents

This keeps individual prompt files focused and short. Shared behavior lives in one place and is updated once.

---

## What This Architecture Demonstrates

- **Separation of concerns** — each agent owns exactly one job
- **Gate-based pipeline** — downstream agents never run on incomplete data
- **Composable prompts** — shared behavior extracted to skill files, not duplicated
- **Equity baked in** — no skills_gap field anywhere, salary anchored to her experience level, informal work treated as real work
- **Honest failure modes** — thin STAR data produces an invitation, not a fabrication; unverified data gets flagged, not hidden
