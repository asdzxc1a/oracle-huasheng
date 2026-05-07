# Anti-Patterns — Video Analysis Agent

## Patterns the Agent Must Detect and Avoid

### 1. Halo Effect
- **Definition:** One exceptional performance colors assessment of all other capabilities
- **Detection:** Does the agent reference one role repeatedly when discussing unrelated traits?
- **Mitigation:** Force explicit analysis of non-overlapping domains

### 2. Recency Bias
- **Definition:** Overweighting recent work vs. historical pattern
- **Detection:** Are recent roles discussed at 3x the length of breakthrough-era roles?
- **Mitigation:** Weight by career-stage relevance, not calendar proximity

### 3. Source Inflation
- **Definition:** Treating managed/scripted sources as RAW signal
- **Detection:** Are claims from late-night interviews marked Tier A?
- **Mitigation:** Strict tier capping by source type (see source-reliability-matrix.md)

### 4. Confirmation Bias
- **Definition:** Seeking evidence that supports the thesis, ignoring contradictions
- **Detection:** Does the contradiction map have entries? Are they explored or dismissed?
- **Mitigation:** Mandate adversarial analysis section; require ≥2 contradictions

### 5. False Precision
- **Definition:** Claiming certainty where only inference exists
- **Detection:** Are there Tier C claims presented as facts? Is uncertainty quantified?
- **Mitigation:** Every claim must have a tier. Tier C claims must use hedging language.

### 6. Narrative Coherence Bias
- **Definition:** Forcing disparate observations into a single coherent story
- **Detection:** Does the synthesis paper over contradictions for the sake of a clean narrative?
- **Mitigation:** Preserve contradictions. The client's casting question may not have a clean answer.

### 7. Beauty/Charisma Blindness
- **Definition:** Attractive/charismatic actors get graded on a curve
- **Detection:** Is the agent harder on less conventionally attractive actors?
- **Mitigation:** Blind analysis where possible (transcript-only pass before video pass)

## Validation Checklist
Before marking a brief complete, verify:
- [ ] ≥2 contradiction pairs preserved in contradiction map
- [ ] Adversarial section presents a genuine challenge to the thesis
- [ ] No Tier A claims from SCRIPTED sources
- [ ] Uncertainty map lists at least 3 unknowns
- [ ] Anti-patterns section has been reviewed
