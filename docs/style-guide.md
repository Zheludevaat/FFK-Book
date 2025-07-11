# Reusable Book Generation Framework Template

*Version 0.1 – Updated 2025-07-09*

> **Voice tag:** `[AUTHOR STYLE]`

---

## Global Constants
| Variable | Value |
|----------|-------|
| Part length | **2 800–3 000 words** (≈ 4 K tokens) |
| Footnote humour ratio | ≈ [HUMOUR RATIO] |
| Hard per-chunk token ceiling | **4 000 tokens** |
| Repository token ceiling | **120 000 tokens** |
| CHUNK markers | `<!-- CHUNK NN START -->` … `<!-- CHUNK NN END -->` |
| 200-word recap | Mandatory at end of each chunk |

All constants appear **only** here and `qa-checklist.md`.

Chapters are produced in **two parts**. Each part must meet the length and token
constraints above so the full chapter totals roughly **5 600 words**.

---

## [AUTHOR STYLE] Tone Rules
Narrator persona: [Narrator persona description].
1. Conversational, first-person plural with occasional self-deprecation.
2. Crisp topic sentences with playful footnote-driven humour.
3. Avoid academic hedging; prefer confident plain speech.
4. Never mention the real-life author by name.

Consult `voice-samples.md` for exemplar passages.

---

## Generation Protocol
1. **Retrieve → Generate**: Only 01-Research may call the web.
2. Drafters use prompts from 02-Prompt-Forge.
3. Insert figure call-outs `[Fig X]` inline; 06-Figure-Build creates assets.
4. 04-QA-Edit must run the full `qa-checklist.md`.

### Agent Roles and Token Budgets

| Agent | 4.1 Variant | **Max output / call** | Rationale |
|-------|-------------|-----------------------|-----------|
| **ResearchAgent** | `gpt-4.1-long-1M` | **2 048 tokens ≈ 1 500 words** | Generates a rich fact bundle, web-sourced citations, and image descriptions while sitting well below the 8 k cap. |
| **PromptBuilder** | `gpt-4.1-code-pro` | **400 tokens ≈ 300 words** | Emits a concise, precise drafting prompt + JSON tool calls; larger output adds no value. |
| **DraftWriter** | `gpt-4.1-long-1M` | **4 096 tokens ≈ 3 000 words** | Delivers robust section prose yet leaves half of allowed output unused to dodge truncation. |
| **ReviewerAgent** | `gpt-4.1-review-64k` | **1 600 tokens ≈ 1 200 words** | Produces `review.diff` plus human-readable rationale without nearing limits. |
| **Rewriter** | `gpt-4.1-long-1M` | **4 096 tokens** | Mirrors DraftWriter to regenerate a full section if required. |
| **UpdaterAgent** | `gpt-4.1-code-pro` | **800 tokens ≈ 600 words** | Enough for YAML/Markdown patches and a change log. |

Loop-guard: Reviewer issues one correction cycle → Rewriter regenerates → Reviewer performs a ≤600-token post-check and returns pass/fail summary only. Further loops need explicit user approval.

### End‑to‑End Flow (Token‑Aware & Web‑Enabled)

1. **Kick‑off** – User seeds `outline.yaml` and `style.md`.
2. **Section cycle**
   1. ResearchAgent gathers facts and updates `_images_plan.yaml`.
   2. PromptBuilder composes the drafting prompt.
   3. DraftWriter writes `drafts/section_###.md`.
   4. ReviewerAgent audits and may produce `reviews/section_###.diff`.
   5. Rewriter applies the diff once.
   6. ReviewerAgent delivers a pass/fail summary.
   7. User approves or requests another correction loop.
   8. UpdaterAgent patches caches and embeds text.
3. **Chapter checkpoint** – Reviewer loads all accepted drafts (64 k context) to flag narrative drift.
4. **Final assembly** – Concatenate drafts, run style pass, and export.

---
