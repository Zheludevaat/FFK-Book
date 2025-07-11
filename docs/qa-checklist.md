# QA Checklist
*Updated: 2025-07-09*

## 1 · Structural Integrity
| Check | Pass criteria |
|-------|---------------|
| **Word-count** | Each part including footnotes is **2 800–3 000 words** |
| CHUNK markers | `<!-- CHUNK NN START -->` and `<!-- CHUNK NN END -->` present |
| YAML front-matter | Contains `length_target` = "2 800–3 000 words" |
| Figures | All figure call-outs resolved in `resources.md` |

Each chapter is generated in **two parts**. Ensure the closing story appears only in the final part and that both parts meet the word-count requirement.

## 2 · Research Compliance
| Check | Pass criteria |
|-------|---------------|
| Sources per focus | ≥2 post‑2022 scholarly or primary sources |
| Citation IDs | All IDs present in `sources.json` |
| Link health | URLs HTTP 200 at research time |

## 3 · Token & Context Safety
| Check | Pass criteria |
|-------|---------------|
| Per-part tokens | ≤4 000 |
| Repo total | <120 000 tokens at merge |

## 4 · Voice & Style Fidelity
| Check | Pass criteria |
|-------|---------------|
| Tone | Matches `style-guide.md` samples |
| Humour ratio | ≈ [HUMOUR RATIO] |

## 5 · Model / Tool Selection Log
Record models used in `research-log.md`.

## 6 · Sign-off
Add at end of chunk QA pass:
```
QA Verdict
✓ All checks passed
QA-Editor: _______
Date: [DATE]
```
