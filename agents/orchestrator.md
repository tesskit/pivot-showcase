# Orchestrator

> Simplified design-level description. The running prompts are kept private and may differ in wording.

The Orchestrator is not an LLM agent. It is rule-based Python inside the LangGraph pipeline and makes no Claude call for routing.

## What it does on every turn
- If her profile is not complete, it routes to the Intake Agent.
- If her profile is complete and the pipeline has already run, it routes follow-up conversation to the Synthesizer.
- If she asks for a new kind of job after the pipeline has run, it clears the previous research and live listings and routes to the Research Agent. A small Claude call (`detect_job_search_intent`) decides whether a message is a new job search and what the new target is.
- It records employers she asks to exclude (for example, "not the Navy") so they are filtered out of later listings.

## After Intake
Once the profile is complete, the graph continues on its own: Research, then Fact-Check, then Narrative and Application Coach in parallel, then the Synthesizer.

## Never
- Never speaks to the user directly. The Intake Agent and the Synthesizer are the only voices she hears.
- Never skips Intake while her profile is incomplete.
