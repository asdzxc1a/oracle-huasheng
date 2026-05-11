---
name: anti-pattern-enforcement
description: |
  Check brief output against seven cognitive biases that corrupt casting 
  analysis: Halo Effect, Recency Bias, Source Inflation, Confirmation Bias, 
  False Precision, Narrative Coherence Bias, and Beauty/Charisma Blindness. 
  Use as a quality gate before shipping any brief.
---

# Anti-Pattern Enforcement

## The Seven Anti-Patterns

| Pattern | Description | Detection Method |
|---|---|---|
| **Halo Effect** | One great role doesn't make a great actor | Count role-specific praise vs. behavioral analysis |
| **Recency Bias** | Recent work overweighted vs. historical pattern | Check if breakthrough-era work is equally weighted |
| **Source Inflation** | Managed appearances treated as RAW signal | Verify access-level assignments match source type |
| **Confirmation Bias** | Thesis not challenged by contradictory evidence | Confirm ≥2 contradiction pairs are preserved |
| **False Precision** | Certainty claimed where only inference exists | Check for absolute language ("definitely", "proves") |
| **Narrative Coherence Bias** | Story too clean, no tensions acknowledged | Verify contradictions and unknowns are present |
| **Beauty/Charisma Blindness** | Appearance-based assessments substitute for behavioral analysis | Count appearance mentions vs. behavior mentions |

## Enforcement Rule
Any critical detection blocks brief shipment. Warnings must be documented
with evidence and mitigation strategy.

## Quality Checklist
- [ ] All 7 patterns checked
- [ ] Critical detections documented with evidence
- [ ] Mitigation strategies provided
- [ ] Report written to `references/anti-patterns.md`

## References
- Pattern definitions: `references/patterns.md`
