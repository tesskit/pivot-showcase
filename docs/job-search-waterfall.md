# Pivot — Job Data Approaches

This document describes the approaches evaluated for sourcing live job listings in Pivot, with real examples. It serves as both technical documentation and a portfolio artifact demonstrating architectural decision-making.

---

## The Problem

Pivot needs real, current job listings to be useful. Claude's training knowledge is stale — job postings from training data may be months or years old, companies may have changed hiring, and salary ranges shift constantly. A career advocate that shows outdated listings is worse than no listings at all.

---

## Approach 1 — Claude Training Knowledge (Fallback Only)

**Status:** Active as fallback when all live sources fail

**How it works:** Claude generates job titles, company names, and salary ranges from its training data when no live source is available.

**Example output for a nurse in NJ targeting healthcare administration:**
> "Healthcare administration roles in the New Jersey area include positions such as Clinical Operations Manager at RWJBarnabas Health, Director of Patient Services at Hackensack Meridian Health, and Healthcare Administrator at CarePoint Health. Salary ranges typically fall between $85,000 and $130,000 for experienced candidates."

**Problems:**
- Data may be 1-2 years old
- Cannot provide apply links

**When used:** Only when Apify, JSearch, and USAJobs all fail or return no results. The Fact-Check Agent labels all Claude-generated job data as ESTIMATED.

---

## Approach 2 — JSearch via RapidAPI (Active — Fallback Only)

**Status:** Active as fallback when Apify returns fewer than 10 combined results

**API:** https://rapidapi.com/letscrape-6bRB7reou7/api/jsearch
**Free tier:** 200 requests/month
**Data source:** Google for Jobs — aggregates Indeed, LinkedIn, Glassdoor, ZipRecruiter in real time

**Example output for a nurse in NJ targeting healthcare administration:**
```
LIVE JOB LISTINGS (via JSearch):
1. Healthcare Administrator at Atlantic Health System (Morristown, NJ) | $95,000-$118,000 YEAR
   Apply: https://www.indeed.com/viewjob?jk=abc123...
2. Clinical Operations Manager at RWJBarnabas Health (New Brunswick, NJ)
   Apply: https://www.linkedin.com/jobs/view/...
```

**Implementation:** `src/jsearch_client.py`

---

## Approach 3 — Indeed Publisher API (Evaluated — Replaced by Approach 5)

**Status:** Evaluated and replaced by Apify Indeed Scraper

**Why it was not implemented:**
Indeed's OAuth flow requires a browser redirect — it cannot complete in a server-side Python context without a full OAuth callback implementation. Indeed MCP works in Claude.ai because it authenticates via the browser session. From a Python FastAPI backend on Render, there is no browser session.

**Why it was replaced:**
The OAuth complexity was solved a different way. Apify's `misceres/indeed-scraper` actor scrapes Indeed directly without requiring OAuth, delivering equivalent data with zero auth infrastructure.

---

## Approach 4 — USAJobs API (Active — Government Roles)

**Status:** Active, always runs for government roles

**API:** https://developer.usajobs.gov/
**Free tier:** Unlimited

**Example output:**
```
GOVERNMENT JOB LISTINGS (from USAJobs):
1. Health Systems Administrator at Department of Veterans Affairs (East Orange, NJ) | $89,054-$115,766 YEAR
   Apply: https://www.usajobs.gov/job/...
2. Medical Administrative Officer at U.S. Army (Fort Dix, NJ) | $72,553-$94,317 YEAR
   Apply: https://www.usajobs.gov/job/...
```

**Implementation:** `src/usajobs_client.py`

---

## Approach 5 — Apify Direct Scrapers (Active — Primary Source)

**Status:** Active as of April 2026 — primary job data source

**Actors used:**
- `misceres/indeed-scraper` — direct Indeed scraper, 20K+ users, 4.0 rating
- `cryptosignals/linkedin-jobs-scraper` — direct LinkedIn scraper, public guest API, no login required

**Cost:** ~$0.50/1K results (Indeed), ~$10/1K results (LinkedIn). Pay-per-usage from Apify's $5/month free credit.

**Why Apify over Indeed Publisher API:**
Approach 3 required browser-based OAuth impossible from a Python backend. Apify handles all scraping infrastructure — no OAuth, no callback URL, no token storage.

**Example output for an ICU nurse in Dallas targeting Clinical Informaticist:**
```
[Indeed] Clinical Informatics Spec 2 at Baylor Scott & White Health (Dallas, TX)
Apply: https://www.indeed.com/viewjob?jk=...

[LinkedIn] Clinical Informaticist Analyst at White Rock Medical Center (Dallas, TX)
Apply: https://www.linkedin.com/jobs/view/...
```

Each listing is labeled [Indeed] or [LinkedIn] so the user knows exactly where it came from.

**Implementation:** `src/apify_indeed_client.py`, `src/apify_linkedin_client.py`

---

## Current Architecture Decision

Pivot 1.0 uses the following 5-layer waterfall:

```
1. Apify Indeed     -> up to 5 direct Indeed listings
2. Apify LinkedIn   -> up to 5 direct LinkedIn listings
3. Deduplicate      -> merge by company + title key, cap at 10
4. JSearch          -> fallback only if combined Apify < 10 results
5. USAJobs          -> always runs, government roles only
6. Claude fallback  -> silent, prose only, no fabricated postings
```

---

## Interview Talking Points

- **Graceful degradation** — five-layer waterfall means the pipeline never fails due to a job API outage
- **Direct vs aggregator** — Apify scrapes Indeed and LinkedIn directly, eliminating the aggregator layer for better relevance and fresher data
- **OAuth without OAuth** — Indeed Publisher API requires browser-based OAuth impossible from a Python backend; Apify's actor handles all scraping infrastructure with zero auth complexity
- **Source attribution** — each listing is labeled [Indeed] or [LinkedIn] so users know exactly where each job came from
- **URL preservation** — live job URLs bypass the Research Agent's prose summarization by storing directly in state, preventing link loss through LLM rewriting
- **Separation of concerns** — job API clients are standalone modules testable independently of the LangGraph pipeline
- **Cost optimization** — Apify pay-per-usage on $5/month free credit handles portfolio demo load; JSearch free tier preserved as fallback
