---
name: pre-ship-validation
description: |
  Run the 8-item Huasheng pre-ship checklist before any brief ships. 
  Score 0-100. Any critical failure blocks shipment. Use as the final 
  gate before the brief is presented to the human oracle.
---

# Pre-Ship Validation

## Checklist

| # | Item | Severity | Points |
|---|---|---|---|
| 1 | ≥2 contradiction pairs preserved | Critical | 15 |
| 2 | Adversarial section presents genuine challenge | Critical | 15 |
| 3 | No Tier A claims from SCRIPTED sources | Critical | 15 |
| 4 | Uncertainty map lists ≥3 unknowns | Critical | 15 |
| 5 | Anti-patterns section reviewed with findings | High | 10 |
| 6 | Every Tier A/B claim traceable to specific source | High | 10 |
| 7 | Video claims reference specific timestamps | Medium | 10 |
| 8 | Tier C claims use hedging language | Medium | 10 |

## Scoring

- **Score ≥ 60 with zero critical blockers:** PASS
- **Any critical blocker:** FAIL (brief cannot ship)
- **Score < 60:** FAIL (brief needs work)

## Output Format

```markdown
# Pre-Ship Validation Report

**Score:** X/100
**Status:** ✅ PASSED / ❌ BLOCKED

## Blockers
- ❌ [Blocker description]

## Checklist
- ✅ / ❌ **item_name** (severity)
```

## Quality Checklist
- [ ] All 8 items checked
- [ ] Score calculated correctly
- [ ] Blockers listed explicitly
- [ ] Report written to `research/pre-ship-validation.md`
