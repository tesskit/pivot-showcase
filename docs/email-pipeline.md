# Pivot — Email Pipeline

The email is Pivot's primary deliverable — not the chat. The conversation is how she gets there. The email is what she walks away with.

---

## Why Email

A chat response disappears the moment the session ends. A career packet in her inbox is something she can open the night before an interview, forward to a friend, or refer back to whenever she needs it. The email is the artifact that makes Pivot useful beyond the conversation.

Every full pipeline run — once her profile is complete and the pipeline has fired — produces a formatted HTML email she can send to herself with one tap.

---

## What's In the Email

The email contains everything the pipeline produced, converted to second person (you/your) so it reads as hers:

- **STAR story** — Situation, Task, Action, Result — with each label bolded and clearly marked
- **Resume bullets** — tailored to her target role, ready to drop into her resume
- **Cover letter opening** — one paragraph in first person, the strongest reason she's right for the role
- **Strongest angle** — her single best bridge to the target role, highlighted in a gold callout box
- **Quick win** — one concrete action she can take before she applies
- **Live job listings** — every listing from the pipeline with Apply Now buttons linking directly to the posting

---

## How It's Built

The `/email` endpoint in FastAPI builds two versions of every email:

- **HTML** — rich formatted email with Pivot ✦ header, bold STAR labels (Situation / Task / Action / Result), purple section headers, gold callout box for strongest angle, and Apply Now ✦ buttons
- **Plain text** — fallback for email clients that don't render HTML

All narrative content passes through `to_you()` before delivery — a converter that replaces third-person pronouns (she/her/hers) with second-person (you/your/yours) throughout the STAR story, resume bullets, lead strength, and quick win. The Narrative and Application Coach agents write in third person for pipeline processing; the email is the first place she sees it in her own voice.

The raw research summary is never shown in the email. Only live job listings appear — if no live listings were found, the job section is omitted rather than filled with Claude's training knowledge.

---

## Delivery

Email is delivered via **Resend** — a transactional email API with a free tier of 3,000 emails/month. Resend was chosen over Gmail MCP because Gmail MCP authenticates via browser session and cannot authenticate from a Python backend on Render.

Her email address is used solely to deliver the packet. It is never stored, logged, or associated with her conversation data.

---

## Email Bar UX

The email bar is always visible in the chat interface after the first message — not hidden behind a button, not shown only at the end. This keeps the deliverable top of mind throughout the conversation.

When the full pipeline completes (`profile_complete` + narrative present in session state), the email bar upgrades:

1. A GSAP glow sweep animates across the bar
2. The label updates to "✦ Your career packet is ready — Email my career packet"
3. The Synthesizer's response always ends with an explicit nudge: "I've also put together your complete career packet..."

After the email is sent, the bar resets to its default state. The packet has been delivered.

---

## Mid-Session Email

The email bar is available at any point during the session — not just after the full pipeline runs. If she sends her email before the pipeline has completed, Pivot sends what it has: her conversation history, any profile data collected so far, and a warm note explaining the packet will be more complete after the full conversation.

This ensures she always leaves with something, even if she ends the session early.
