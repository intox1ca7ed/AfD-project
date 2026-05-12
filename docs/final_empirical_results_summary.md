# Final Empirical Results Summary (Descriptive)

Last updated: 2026-05-11

## Data Basis
- Core panel: `data/panel/monthly_full_analysis_panel_2013_2025.parquet`
- Coverage: `2013-09` to `2025-12` (148 monthly rows)
- Construction: combined polling + Nexis volume panel merged with monthly text/content indicators
- Shock summary source: `data/panel/final_descriptive_diagnostics.csv`
- Lag snapshot source (descriptive only): `data/panel/lag_diagnostics_descriptive_summary.csv`

## Key Indicators
- Polling: `afd_poll_support_mean`
- Media volume: `nexis_total_results`
- Text indicators (monthly means per 1000 words):
  - `migration_terms_per_1000_mean`
  - `security_terms_per_1000_mean`
  - `afd_far_right_terms_per_1000_mean`
  - `remigration_democracy_terms_per_1000_mean`
  - `negative_threat_terms_per_1000_mean`

## Shock Summary Table (Descriptive)

| Shock | Expected mechanism | AfD Δ (±3/±6) | Migration Δ (±3/±6) | Security Δ (±3/±6) | AfD/Far-right Δ (±3/±6) | Remigration/Democracy Δ (±3/±6) | Negative/Threat Δ (±3/±6) | Interpretation label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Cologne (2016-01) | AfD support up with stronger security/public-order framing | +3.978 / +6.494 | +1.561 / -1.698 | +0.342 / +0.562 | +0.034 / +0.138 | +0.304 / +0.151 | -0.614 / -0.392 | Pattern-consistent: polling increase with stronger security framing. |
| Chemnitz (2018-08) | Strong security + far-right framing surge, limited net polling movement | +0.446 / +0.067 | -6.891 / -1.849 | +2.217 / +0.456 | +2.336 / +0.867 | +1.049 / +0.460 | -0.202 / -0.634 | Pattern-consistent: strong framing movement with limited net polling shift. |
| Correctiv (2024-01) | AfD support down with remigration/democracy-threat + far-right spike | -3.280 / -3.653 | -10.669 / -7.477 | +3.162 / +2.495 | +4.103 / +1.724 | +3.479 / +1.838 | +0.188 / -0.204 | Pattern-consistent: polling decline with remigration/far-right content surge. |

## Concise Interpretation
- The descriptive panel aligns with the project’s mechanism framing at a pattern level for all three shocks.
- Cologne shows a positive polling shift with modestly stronger security framing in local windows.
- Chemnitz shows large security/far-right framing movement with weak net polling change.
- Correctiv shows a negative polling movement with strong remigration/far-right framing spikes.

## Descriptive Lag Snapshot (Existing Diagnostics)
- In the combined sample, strongest absolute correlations in the existing lag summary are small-to-moderate and include:
  - `media_salience_z_lag0` with `afd_poll_support_mean`: `-0.245`
  - `media_salience_z_lag1` with `afd_poll_support_change`: `+0.244`
- These are descriptive correlations only and should not be interpreted causally.

## Caveats
- Results are descriptive co-movement diagnostics, not causal identification.
- Shock-window contrasts are local summaries, not event-study estimators.
- Interpretation is sensitive to dictionary-based content measurement and monthly aggregation choices.
- Source-boundary differences (historical manual block vs DAWUM period) remain relevant for cross-period comparisons.

## Suggested Thesis Results Wording
- “Across the combined monthly panel (2013-09 to 2025-12), descriptive shock-window diagnostics show pattern-consistent co-movements between AfD polling and mechanism-relevant media content indicators. Around Cologne (2016-01), AfD support increases alongside stronger security/public-order framing. Around Chemnitz (2018-08), security and far-right framing intensifies while net polling movement is limited. Around the Correctiv revelation (2024-01), AfD support declines as remigration/democracy-threat and far-right content indicators spike. These findings are descriptive and do not establish causal effects.”
