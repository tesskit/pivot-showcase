# Pivot — Research Foundation

The problem Pivot addresses is not anecdotal. It is documented, peer-reviewed, and published in the most respected academic journals in economics and behavioral science. This page cites the foundational research behind Pivot's core design decisions.

---

## The Articulation Gap

### Study 1 — The Gender Gap in Self-Promotion

> Exley, C. L., & Kessler, J. B. (2022). The gender gap in self-promotion. *The Quarterly Journal of Economics*, *137*(3), 1345–1381. https://doi.org/10.1093/qje/qjac003

**Original working paper:** NBER Working Paper No. 26345 (2019). National Bureau of Economic Research. https://www.nber.org/papers/w26345

**What they found:**

In a series of experiments involving over 4,000 online participants and over 10,000 school-aged youth, researchers found a large and persistent gender gap in self-promotion. When asked to describe their performance on a task to a potential employer:

- Men rated themselves an average of **61 out of 100**
- Women rated themselves an average of **46 out of 100**
- **Both groups had the exact same average score**

Crucially, even when women were told that a potential employer would use their self-evaluation to decide whether to hire them and what to pay them — they still self-promoted less than equally performing men.

The gap was not explained by confidence. It was not explained by actual performance. It was a systemic, documented pattern of women describing their own abilities less favorably than men — even when they knew it was in their direct financial interest not to.

The gender gap in self-promotion appears as early as the sixth grade.

**Why this matters for Pivot:**
This is Pivot's foundational insight. The barrier is not skill. It is articulation. Women cannot be told to "just be more confident" — the research shows confidence alone does not close the gap. They need a tool that translates their real performance into language the market understands on their behalf.

---

### Study 2 — Whether to Apply

> Coffman, K. B., Collis, M. R., & Kulkarni, L. (2024). Whether to apply. *Management Science*, *70*(7), 4649–4669. https://doi.org/10.1287/mnsc.2023.4907

**Funded by:** National Science Foundation (Grant 1713752) and Harvard Business School.

**What they found:**

Harvard Business School Associate Professor Katherine B. Coffman and colleagues ran a series of experiments using the freelance platform UpWork to measure gender differences in willingness to apply for higher-return, more challenging work.

Key findings:

- In male-typed domains, **qualified women were significantly less likely to apply than equally qualified men**
- When ads contained vague language about required qualifications, only **6% of qualified women applied for the expert position**, compared with **22% of qualified men** — a gap of more than 3x
- When job descriptions were made more specific and concrete, the rate at which qualified women applied increased substantially

The research opens with a question a BBC interviewer posed to Donna Strickland, a Canadian Nobel laureate in physics, in 2018: *"Why are you not a full professor — given your eminence?"* Her answer: *"I never applied."*

**Why this matters for Pivot:**
Women are self-selecting out of opportunities they are qualified for — not because they lack skills, but because ambiguous job requirements make it harder to see their own fit. Pivot helps women understand their own qualifications clearly so they can move forward instead of self-selecting out.

---

## The Scale of the Problem

- A 2023 LinkedIn study of workers in 163 countries found that women make up approximately 42% of the workforce but only 32% of senior leadership positions — and just 25% at the C-suite level.
  - Source: LinkedIn Economic Graph, 2023.

- The World Economic Forum's 2026 report estimates that, at the current rate of change, full global gender parity is still **120 years away**.
  - Source: World Economic Forum. (2026). *Global Gender Gap Report 2026*. https://www.weforum.org/publications/global-gender-gap-report-2026/digest/

- In 2024, women in management, professional, and related occupations earned approximately **$0.74 for every dollar earned by men** — an improvement of just three cents over twenty years.
  - Source: Department for Professional Employees, AFL-CIO. (2025). *Women Professionals: Making Gains Despite Persistent Inequality in the U.S. Workforce*. https://www.dpeaflcio.org/factsheets/professional-women-a-gendered-look-at-inequality-in-the-us-workforce

---

## Design Implications

These findings directly shaped Pivot's architecture:

| Research Finding | Pivot Design Decision |
|---|---|
| Women underrate themselves even with identical performance | Narrative Agent translates her real experience into market language — she doesn't have to do it alone |
| Women self-select out due to ambiguous qualifications | Fact-Check Agent verifies what she actually qualifies for against real job requirements |
| The gap appears as early as sixth grade — it is systemic | Intake Agent asks, never assumes — meets her where she is without judgment |
| Telling women to "be more confident" doesn't work | Pivot doesn't coach confidence. It provides evidence. Real data. Real market context. Real proof. |
| The gap is worse in male-typed or analytical domains | RAG pipeline spans all industries — not just tech — so no field is treated as default |
| Hiring processes test for isolated skills, not real applied experience | Narrative Agent bridges the evaluation gap — maps what she's actually done to what interviewers test for, without losing what makes her experience genuine |

---

## A Note on Scope

Pivot is a career advocacy tool, not a therapy tool. The research above documents a systemic, structural problem — one that requires structural solutions. Pivot is one part of that solution: helping individual women navigate a system that was not designed for them, while we collectively work toward a system that is.

For further reading on systemic interventions, see Coffman's recommendation: rather than "change the women" approaches, focus on "change the system" approaches — reducing ambiguity in hiring, eliminating self-evaluation requirements, and proactive recruitment of qualified female candidates.
