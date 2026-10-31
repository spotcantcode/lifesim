# Implementation checklist

- [x] Foundation: navigation, fictional profile, profile editor, migrations
- [x] Engine: monthly ledgers, workload, deterministic and seeded Monte Carlo
- [x] Game: monthly decisions, events, five-year campaign, independent rewind
- [x] Narratives: grounded domain reports, three modeled trajectories
- [x] Comparison: branch tree, side-by-side futures, sensitivity assumptions
- [x] Verification: engine/API tests, frontend unit tests, browser walkthrough, reconciliation, restart, runtime request inspection

Explicitly deferred: full workspace restore, multi-user authentication, business sales/valuation, multiple independently actionable businesses, tax jurisdictions, external narrative providers.

These checks mark the implemented MVP scope, not every feature in the long-term product vision. Business/account/assumption lists currently use validated JSON editors; everyday profile fields use regular controls. Decision interpretation uses explicit keyword rules. Scheduled challenges are synthetic, and individual businesses share one aggregate model. The UI primitives are local native controls in a shadcn-style component layer, rather than the full shadcn registry.

## Milestone results

| Milestone | Implemented | Verified | Remaining |
| --- | --- | --- | --- |
| 1 · Foundation | Seven views, digital twin, fictional campaign, SQL migration, SQLite entities | Profile API validation, startup, reload and database reopening | Richer editors for lists; per-field provenance |
| 2 · Engine | Monthly business/cash/investment/debt ledgers, time constraints, eight actions, deterministic and 100/1,000/10,000-run ensembles | Monthly reconciliation, repeatable seeds, aligned shocks, maximum-size ensemble | Sales, valuations, richer tax and manager execution models |
| 3 · Game | 60 monthly turns, synthetic disruption events, journal, snapshots, independent branch at saved months | Full 60-turn API campaign; browser expansion → 12 months → rewind → hiring → 12 months | More event variety and campaign objectives |
| 4 · Narratives | Eleven domains, provider interface, computed metrics separated from illustrative routines, three whole-path representatives | Grounded report assertions; browser central and unfavorable views | More narrative variety and user-authored templates |
| 5 · Comparison | React Flow branch tree, side-by-side narratives for two or three futures, financial chart and sensitivity deltas | Browser comparison shows 57 vs 30 work hours and distinct finances; tree links preserved | Comparison of arbitrary historical segments |
| 6 · Refinement | Local request guards, validated import/export, deletion, separate actual observations, package lock files | 21 Pytest tests; 4 Vitest tests; TypeScript/build; desktop and 390px browser inspection; server restart; no external resource requests in tested flows | Full automated browser regression suite; authentication before any public use; full backup restore |

## Try every milestone

Run `./start.sh` from `lifesim/`, then open http://127.0.0.1:5173.

1. Open **My digital twin** to edit/export the fictional profile or create your own copy.
2. Enter **Freedom by 50**, select an expansion decision, then **Simulate 12 months**.
3. Read the future report. Return to **Strategy game**, rewind to month 0, and choose hiring.
4. Open **Compare futures** and select both month-12 timelines. Inspect the tree under **Timelines**.
5. Use **Simulation studio** for 1/5/10/20-year projections, editable assumptions and seeded ensembles.

Browser screenshots are in `output/playwright/` (ignored from version control). A 10,000-run, 240-month engine benchmark took approximately 0.2 seconds in this environment; timing will vary. Tests currently emit one upstream Starlette TestClient deprecation warning; they pass. The tested application made only localhost resource requests. This does not establish a complete independent privacy or security audit.
