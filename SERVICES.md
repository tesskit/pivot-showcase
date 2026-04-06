# Pivot — Services & Dependencies

A quick reference for every external service Pivot uses, what it costs, and where to manage it.

---

## Paying / Could Be Paying

| Service | URL | Cost | Notes |
|---|---|---|---|
| Render | dashboard.render.com | $25/month (Standard) + ~$5-15/month build pipeline | Backend + PostgreSQL. Standard required for 2GB RAM. |
| Anthropic Claude API | console.anthropic.com | Pay per token | Every Pivot conversation calls the API. Monitor usage in Console. |
| RapidAPI / JSearch | rapidapi.com | Free up to 200 requests/month | Billing cycle started March 18. Resets April 18. Check Console for usage. |
| Claude.ai Pro | claude.ai | Monthly subscription | Development and planning use. |

---

## Free Tiers — Monitor Limits

| Service | URL | Limit | Notes |
|---|---|---|---|
| Resend | resend.com | 3,000 emails/month free | Email delivery for career packets. |
| Vercel | vercel.com | Free hobby tier | Frontend deployment. |
| UptimeRobot | uptimerobot.com | Free tier | Pings Render every 5 minutes to keep service warm. Status: stats.uptimerobot.com/Bmxvrr5eIH |
| Namecheap | namecheap.com | Annual renewal | Domain registration for pivotforwomen.com. |
| Proton Mail | proton.me | Free tier | Demo inbox: pivotdemo@proton.me. Used for demo recordings only. |

---

## Free — No Limits

| Service | URL | Notes |
|---|---|---|
| USAJobs API | developer.usajobs.gov | Government job listings. Free, unlimited, no rate limits. |
| Nominatim | nominatim.openstreetmap.org | Location geocoding. Free, no API key required. |
| GitHub | github.com/tesskit | Source control. Private repo: tesskit/pivot. Public showcase: tesskit/pivot-showcase. |

---

## Open Source — No Account Needed

| Package | URL | Notes |
|---|---|---|
| FastAPI | fastapi.tiangolo.com | Python web framework. Backend routing layer. |
| LangGraph | langchain-ai.github.io/langgraph | Agent orchestration framework. |
| numpy | numpy.org | RAG cosine similarity at runtime. |
| psycopg2 | psycopg.org | PostgreSQL adapter for Python. |

---

## Notes

- The two services that cost real money every month are **Render** and the **Claude API**.
- Everything else is free at current soft-launch scale.
- If Pivot goes to production scale, RapidAPI and Resend are the first free tiers likely to need upgrading.
