# Pivot — Job Data Approaches

This document describes the approaches evaluated for sourcing live job listings in Pivot, with real examples. It serves as both technical documentation and a portfolio artifact demonstrating architectural decision-making.

---

## The Problem

Pivot needs real, current job listings to be useful. Claude's training knowledge is stale — job postings from training data may be months or years old, companies may have changed hiring, and salary ranges shift constantly. A career advocate that shows outdated listings is worse than no listings at all.

---

## Approach 1 — Claude Training Knowledge (Fallback Only)

**Status:** Active as fallback when live APIs are unavailable

**How it works:** Claude generates job titles, company names, and salary ranges from its training data when no live source is available.

**Example output for a nurse in NJ targeting healthcare administration:**
> "Healthcare administration roles in the New Jersey area include positions such as Clinical Operations Manager at RWJBarnabas Health, Director of Patient Services at Hackensack Meridian Health, and Healthcare Administrator at CarePoint Health. Salary ranges typically fall between $85,000 and $130,000 for experienced candidates."

**When used:** Only when JSearch and USAJobs both fail or return no results. The Fact-Check Agent labels all Claude-generated job data as ESTIMATED.

---

## Approach 2 — JSearch via RapidAPI (Active — Primary Source)

**Status:** Active, primary job data source

**API:** Available via RapidAPI (https://rapidapi.com)
**Free tier:** 200 requests/month
**Data source:** Google for Jobs — aggregates Indeed, LinkedIn, Glassdoor, ZipRecruiter in real time

**Example output for a nurse in NJ targeting healthcare administration:**
```
LIVE JOB LISTINGS (from Indeed/LinkedIn via JSearch):
1. Healthcare Administrator at Atlantic Health System (Morristown, NJ) | $95,000–$118,000 YEAR
   Apply: https://www.indeed.com/viewjob?jk=abc123...
2. Clinical Operations Manager at RWJBarnabas Health (New Brunswick, NJ)
   Apply: https://www.linkedin.com/jobs/view/...
3. Director of Care Coordination at Hackensack Meridian Health (Hackensack, NJ) | $110,000–$135,000 YEAR
   Apply: https://careers.hackensackmeridianhealth.org/...
```

**Implementation:** `src/jsearch_client.py`

---

## Approach 3 — Indeed Publisher API (Documented — Pivot 1.1)

**Status:** Documented only — cannot authenticate from Python backend

**Why it was not implemented:**
Indeed's OAuth flow requires a browser redirect — it cannot complete in a server-side Python context without a full OAuth callback implementation. Indeed MCP works in Claude.ai because it authenticates via the browser session. From a Python FastAPI backend on Render, there is no browser session.

**Path to implementation in Pivot 1.1:**
- Implement OAuth 2.0 callback endpoint in FastAPI
- Store tokens in PostgreSQL (already planned for Pivot 1.1)
- Swap or supplement JSearch with Indeed Publisher API calls

---

## Approach 4 — USAJobs API (Active — Government Roles)

**Status:** Active, secondary source for government roles

**API:** https://developer.usajobs.gov/
**Free tier:** Unlimited

**Example output:**
```
GOVERNMENT JOB LISTINGS (from USAJobs):
1. Health Systems Administrator at Department of Veterans Affairs (East Orange, NJ) | $89,054–$115,766 YEAR
   Apply: https://www.usajobs.gov/job/...
2. Medical Administrative Officer at U.S. Army (Fort Dix, NJ) | $72,553–$94,317 YEAR
   Apply: https://www.usajobs.gov/job/...
```

**Implementation:** `src/usajobs_client.py`

---

## Current Architecture Decision

Pivot 1.0 uses **JSearch + USAJobs** in parallel, with **Claude training knowledge** as a silent fallback when both APIs return empty results.

---

## Interview Talking Points

- **Graceful degradation** — the pipeline never fails due to a job API outage; it falls back silently
- **Source attribution** — the Fact-Check Agent labels data differently by source (JSearch = VERIFIED, Claude knowledge = ESTIMATED)
- **URL preservation** — live job URLs bypass the Research Agent's prose summarization by storing directly in state, preventing link loss through LLM rewriting
- **Separation of concerns** — job API clients are standalone modules testable independently of the LangGraph pipeline
- **Cost optimization** — free tier APIs handle portfolio demo load; documented upgrade path for production scale
