# PakYield Lab — Research Publication Source Packet

**Status:** FROZEN-SOURCE PUBLICATION INPUT

This document is generated deterministically from the frozen Phase 6D research evidence map.

It is a publication-writing source packet, not a new empirical-analysis layer.

## Frozen source

- Artifact: `data/interim/research_evidence_map.csv`
- Evidence rows: 24
- SHA-256: `50f0ca2f897c6a986e908854f7a75d8186ed07bc2f5fcab7ead83bf7d087f002`

## Publication evidence boundary

The publication layer must preserve the evidentiary status of the frozen research outputs.

It must not:

- manufacture missing observations;
- bypass frozen analytical eligibility rules;
- convert descriptive evidence into inferential evidence;
- reinterpret MPC announcement-window results as policy surprise;
- convert numerical PKISRV-PKRV differences into structural, Islamic, Sukuk, Shariah, liquidity, credit, tax, or other premia without separate supporting evidence;
- create causal monetary-policy claims from observational comparisons;
- report statistical conclusions not supported by the frozen research artifacts.

## Evidence-map schema

1. `target_id`
2. `target_type`
3. `research_theme`
4. `evidence_class`
5. `source_family`
6. `source_artifact`
7. `evidence_role`
8. `priority`
9. `diagnostic_requirement`
10. `diagnostic_status`
11. `interpretation_boundary`

## Complete frozen evidence register

## Evidence Row 01

- **target_id:** RQ1
- **target_type:** RESEARCH_QUESTION
- **research_theme:** CONVENTIONAL_YIELD_CURVE
- **evidence_class:** DESCRIPTIVE
- **source_family:** yield_levels
- **source_artifact:** data/interim/descriptive_yield_levels.csv
- **evidence_role:** describes PKRV yield levels by regime and tenor
- **priority:** PRIMARY
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** descriptive regime comparison; not causal

## Evidence Row 02

- **target_id:** RQ1
- **target_type:** RESEARCH_QUESTION
- **research_theme:** CONVENTIONAL_YIELD_CURVE
- **evidence_class:** DESCRIPTIVE
- **source_family:** yield_changes
- **source_artifact:** data/interim/descriptive_yield_changes.csv
- **evidence_role:** describes PKRV yield changes by regime and tenor
- **priority:** PRIMARY
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** descriptive regime comparison; not causal

## Evidence Row 03

- **target_id:** RQ1
- **target_type:** RESEARCH_QUESTION
- **research_theme:** CONVENTIONAL_YIELD_CURVE
- **evidence_class:** DESCRIPTIVE
- **source_family:** term_spreads
- **source_artifact:** data/interim/descriptive_term_spreads.csv
- **evidence_role:** describes PKRV curve-shape spreads by regime
- **priority:** PRIMARY
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** spread sign or magnitude has no automatic causal interpretation

## Evidence Row 04

- **target_id:** RQ1
- **target_type:** RESEARCH_QUESTION
- **research_theme:** CONVENTIONAL_YIELD_CURVE
- **evidence_class:** INFERENTIAL
- **source_family:** yield_level_regime
- **source_artifact:** data/interim/inferential_yield_level_regime.csv
- **evidence_role:** tests directional-regime differences in yield levels
- **priority:** PRIMARY
- **diagnostic_requirement:** PASS_REQUIRED
- **diagnostic_status:** PASS
- **interpretation_boundary:** observational regime difference; not causal transmission

## Evidence Row 05

- **target_id:** RQ1
- **target_type:** RESEARCH_QUESTION
- **research_theme:** CONVENTIONAL_YIELD_CURVE
- **evidence_class:** INFERENTIAL
- **source_family:** yield_change_regime
- **source_artifact:** data/interim/inferential_yield_change_regime.csv
- **evidence_role:** tests directional-regime differences in yield changes
- **priority:** PRIMARY
- **diagnostic_requirement:** PASS_REQUIRED
- **diagnostic_status:** PASS
- **interpretation_boundary:** observational regime difference; not causal transmission

## Evidence Row 06

- **target_id:** RQ1
- **target_type:** RESEARCH_QUESTION
- **research_theme:** CONVENTIONAL_YIELD_CURVE
- **evidence_class:** INFERENTIAL
- **source_family:** term_spread_regime
- **source_artifact:** data/interim/inferential_term_spread_regime.csv
- **evidence_role:** tests directional-regime differences in selected PKRV term spreads
- **priority:** PRIMARY
- **diagnostic_requirement:** PASS_REQUIRED
- **diagnostic_status:** PASS
- **interpretation_boundary:** observational regime difference; not causal transmission

## Evidence Row 07

- **target_id:** RQ2
- **target_type:** RESEARCH_QUESTION
- **research_theme:** MPC_ANNOUNCEMENT_WINDOWS
- **evidence_class:** DESCRIPTIVE
- **source_family:** mpc_event_windows
- **source_artifact:** data/interim/descriptive_mpc_event_windows.csv
- **evidence_role:** describes yield movements around MPC observation windows
- **priority:** PRIMARY
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** announcement-window movement is not a policy-surprise estimate

## Evidence Row 08

- **target_id:** RQ2
- **target_type:** RESEARCH_QUESTION
- **research_theme:** MPC_ANNOUNCEMENT_WINDOWS
- **evidence_class:** INFERENTIAL
- **source_family:** mpc_event_window
- **source_artifact:** data/interim/inferential_mpc_event_windows.csv
- **evidence_role:** tests eligible event-window group means against zero
- **priority:** PRIMARY
- **diagnostic_requirement:** PASS_REQUIRED
- **diagnostic_status:** PASS
- **interpretation_boundary:** not causal; groups with insufficient n remain descriptive-only

## Evidence Row 09

- **target_id:** RQ2
- **target_type:** RESEARCH_QUESTION
- **research_theme:** MPC_ANNOUNCEMENT_WINDOWS
- **evidence_class:** DATA_LIMITATION
- **source_family:** market_expectations
- **source_artifact:** _blank_
- **evidence_role:** no market-expectations series exists for policy-surprise identification
- **priority:** CRITICAL
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** policy-rate change must not be called policy surprise

## Evidence Row 10

- **target_id:** RQ3
- **target_type:** RESEARCH_QUESTION
- **research_theme:** CROSS_CURVE_COMPARISON
- **evidence_class:** DESCRIPTIVE
- **source_family:** cross_curve_differences
- **source_artifact:** data/interim/descriptive_cross_curve_differences.csv
- **evidence_role:** describes exact-date PKISRV minus PKRV benchmark differences
- **priority:** PRIMARY
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** numerical difference is not a structural premium or discount

## Evidence Row 11

- **target_id:** RQ3
- **target_type:** RESEARCH_QUESTION
- **research_theme:** CROSS_CURVE_COMPARISON
- **evidence_class:** INFERENTIAL
- **source_family:** cross_curve_zero
- **source_artifact:** data/interim/inferential_cross_curve_zero.csv
- **evidence_role:** tests whether numerical benchmark differences have zero mean
- **priority:** PRIMARY
- **diagnostic_requirement:** PASS_REQUIRED
- **diagnostic_status:** PASS
- **interpretation_boundary:** does not identify why a benchmark difference exists

## Evidence Row 12

- **target_id:** RQ3
- **target_type:** RESEARCH_QUESTION
- **research_theme:** CROSS_CURVE_COMPARISON
- **evidence_class:** INFERENTIAL
- **source_family:** cross_curve_regime
- **source_artifact:** data/interim/inferential_cross_curve_regime.csv
- **evidence_role:** tests directional-regime differences in numerical benchmark differences
- **priority:** PRIMARY
- **diagnostic_requirement:** PASS_REQUIRED
- **diagnostic_status:** PASS
- **interpretation_boundary:** does not identify structural Islamic-finance pricing mechanisms

## Evidence Row 13

- **target_id:** RQ4
- **target_type:** RESEARCH_QUESTION
- **research_theme:** MACRO_RELATIONSHIPS
- **evidence_class:** DESCRIPTIVE
- **source_family:** monthly_sample_census
- **source_artifact:** data/interim/descriptive_monthly_sample_census.csv
- **evidence_role:** documents monthly CPI/yield sample availability
- **priority:** CONTEXTUAL
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** sample census is not a macroeconomic regression

## Evidence Row 14

- **target_id:** RQ4
- **target_type:** RESEARCH_QUESTION
- **research_theme:** MACRO_RELATIONSHIPS
- **evidence_class:** DATA_LIMITATION
- **source_family:** monthly_cpi_yield
- **source_artifact:** data/interim/monthly_cpi_yield_panel.csv
- **evidence_role:** monthly CPI/yield family remains descriptive-only in Phase 6B
- **priority:** CRITICAL
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** no macroeconomic inferential relationship has been estimated

## Evidence Row 15

- **target_id:** H1
- **target_type:** HYPOTHESIS
- **research_theme:** MATURITY_SENSITIVITY
- **evidence_class:** DESCRIPTIVE
- **source_family:** mpc_event_windows
- **source_artifact:** data/interim/descriptive_mpc_event_windows.csv
- **evidence_role:** provides maturity-specific announcement-window movement distributions
- **priority:** PRIMARY
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** support requires relative short-versus-long maturity evidence

## Evidence Row 16

- **target_id:** H1
- **target_type:** HYPOTHESIS
- **research_theme:** MATURITY_SENSITIVITY
- **evidence_class:** INFERENTIAL
- **source_family:** mpc_event_window
- **source_artifact:** data/interim/inferential_mpc_event_windows.csv
- **evidence_role:** provides maturity-specific non-zero event-window tests
- **priority:** CONTEXTUAL
- **diagnostic_requirement:** PASS_REQUIRED
- **diagnostic_status:** PASS
- **interpretation_boundary:** individual significance does not directly test short-versus-long differences

## Evidence Row 17

- **target_id:** H1
- **target_type:** HYPOTHESIS
- **research_theme:** MATURITY_SENSITIVITY
- **evidence_class:** DATA_LIMITATION
- **source_family:** direct_maturity_contrast
- **source_artifact:** _blank_
- **evidence_role:** no dedicated short-minus-long event-response contrast is frozen
- **priority:** CRITICAL
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** H1 cannot be declared supported solely from individual maturity tests

## Evidence Row 18

- **target_id:** H2
- **target_type:** HYPOTHESIS
- **research_theme:** CROSS_CURVE_COMOVEMENT
- **evidence_class:** DESCRIPTIVE
- **source_family:** cross_curve_differences
- **source_artifact:** data/interim/descriptive_cross_curve_differences.csv
- **evidence_role:** provides paired exact-date conventional/Shariah-compliant benchmark observations
- **priority:** CONTEXTUAL
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** difference distributions are not a direct co-movement statistic

## Evidence Row 19

- **target_id:** H2
- **target_type:** HYPOTHESIS
- **research_theme:** CROSS_CURVE_COMOVEMENT
- **evidence_class:** DATA_LIMITATION
- **source_family:** direct_comovement_test
- **source_artifact:** _blank_
- **evidence_role:** no dedicated correlation or co-movement inferential family is frozen
- **priority:** CRITICAL
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** H2 direct inferential status remains unresolved without a co-movement test

## Evidence Row 20

- **target_id:** H3
- **target_type:** HYPOTHESIS
- **research_theme:** CROSS_CURVE_SPREAD_VARIATION
- **evidence_class:** DESCRIPTIVE
- **source_family:** cross_curve_differences
- **source_artifact:** data/interim/descriptive_cross_curve_differences.csv
- **evidence_role:** describes numerical benchmark-difference variation across maturity and regime
- **priority:** PRIMARY
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** numerical difference is not a structural premium or discount

## Evidence Row 21

- **target_id:** H3
- **target_type:** HYPOTHESIS
- **research_theme:** CROSS_CURVE_SPREAD_VARIATION
- **evidence_class:** INFERENTIAL
- **source_family:** cross_curve_regime
- **source_artifact:** data/interim/inferential_cross_curve_regime.csv
- **evidence_role:** tests whether numerical benchmark differences vary by directional regime
- **priority:** PRIMARY
- **diagnostic_requirement:** PASS_REQUIRED
- **diagnostic_status:** PASS
- **interpretation_boundary:** regime variation does not identify the economic cause of the difference

## Evidence Row 22

- **target_id:** H3
- **target_type:** HYPOTHESIS
- **research_theme:** CROSS_CURVE_SPREAD_VARIATION
- **evidence_class:** INFERENTIAL
- **source_family:** cross_curve_zero
- **source_artifact:** data/interim/inferential_cross_curve_zero.csv
- **evidence_role:** tests whether maturity-specific mean numerical differences equal zero
- **priority:** CONTEXTUAL
- **diagnostic_requirement:** PASS_REQUIRED
- **diagnostic_status:** PASS
- **interpretation_boundary:** non-zero mean is not proof of time variation or a structural premium

## Evidence Row 23

- **target_id:** H4
- **target_type:** HYPOTHESIS
- **research_theme:** TERM_SPREAD_REGIME_VARIATION
- **evidence_class:** DESCRIPTIVE
- **source_family:** term_spreads
- **source_artifact:** data/interim/descriptive_term_spreads.csv
- **evidence_role:** describes selected PKRV term spreads across directional regimes
- **priority:** PRIMARY
- **diagnostic_requirement:** NOT_APPLICABLE
- **diagnostic_status:** NOT_APPLICABLE
- **interpretation_boundary:** regime association is observational

## Evidence Row 24

- **target_id:** H4
- **target_type:** HYPOTHESIS
- **research_theme:** TERM_SPREAD_REGIME_VARIATION
- **evidence_class:** INFERENTIAL
- **source_family:** term_spread_regime
- **source_artifact:** data/interim/inferential_term_spread_regime.csv
- **evidence_role:** tests directional-regime differences in selected PKRV term spreads
- **priority:** PRIMARY
- **diagnostic_requirement:** PASS_REQUIRED
- **diagnostic_status:** PASS
- **interpretation_boundary:** does not establish causal monetary-policy effects

## Publication-use rule

Every substantive result statement in the research paper or research brief must be traceable to this packet or to another explicitly identified frozen project artifact.

Interpretation must remain narrower than or equal to the evidence recorded here.
