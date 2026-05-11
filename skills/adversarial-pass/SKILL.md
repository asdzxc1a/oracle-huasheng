---
name: adversarial-pass
description: |
  Run a devil's advocate pass against the main thesis. Spend ≥20% of 
  analysis effort arguing AGAINST the conclusion. Use after generating 
  the main analysis and before final validation. If the adversarial case 
  is stronger, the main case is wrong.
---

# Adversarial Pass

## Quick Start
After generating the main analysis:
1. Identify the main thesis from the executive summary
2. Generate the strongest possible challenges
3. Find evidence that points the opposite direction
4. Identify blind spots in the main analysis
5. Formulate a counter-thesis
6. Assess confidence in the challenge

## Workflow

1. Identify the main thesis from the executive summary
2. Generate the strongest possible challenges
3. Find evidence that points the opposite direction
4. Identify blind spots in the main analysis
5. Formulate a counter-thesis
6. Assess confidence in the challenge

## Output Format

```markdown
### Challenge: [What you're arguing against]

- **Evidence Against Thesis:** [Specific evidence]
- **Blind Spot in Main Analysis:** [What was missed]
- **Counter-Thesis:** [Alternative conclusion]
- **Confidence:** [high / moderate / low]
```

## Quality Checklist
- [ ] ≥2 genuine challenges generated
- [ ] Evidence is specific, not vague
- [ ] Blind spots are real (not strawmen)
- [ ] Counter-thesis is defensible
- [ ] Confidence honestly rated

## Scripts
- Devil's advocate: `scripts/devil_advocate.py`
