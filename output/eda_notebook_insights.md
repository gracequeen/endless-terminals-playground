# EDA Notebook Insights: Complexity Metrics V1 → V3

## Summary Table

| Metric | V1 | V2 | V3 | Trend |
|---|---|---|---|---|
| Description Length (chars) | 629.74 | 593.24 | 629.89 | Flat — V2 dipped slightly, V3 returned to V1 level |
| Test Function Count | 18.30 | 19.06 | 15.50 | Regressed — V3 dropped notably |
| Test Assertion Count | 24.29 | 25.75 | 27.65 | **Improved steadily** across all three versions |
| Structural Score | 0.39 | 0.38 | 0.15 | **Regressed sharply** — V3 tests rely far less on process/stdout checks |
| Description Overlap Score | 0.32 | 0.33 | 0.32 | Flat — essentially unchanged across all versions |

## Complexity Metrics Finding

Across V1 → V2 → V3, only **Test Assertion Count** improved consistently (24.3 → 25.8 → 27.7), suggesting that later dataset versions generate more thorough verifiers with a greater number of individual checks. Everything else either stagnated or regressed. **Description Length** and **Description Overlap Score** remained flat throughout (both hovering around 630 chars and 0.32 respectively), meaning task descriptions are no better aligned with their verifier assertions in V3 than they were in V1. Most strikingly, **Structural Score** collapsed from ~0.39 in V1/V2 to 0.15 in V3 — V3 verifiers shifted heavily toward passive state checks (file existence, content) and away from process/stdout-based outcome verification. **Test Function Count** also declined in V3 (15.5 vs. ~18–19 in V1/V2), indicating fewer distinct test functions despite more total assertions, suggesting V3 tests are denser but shallower in structure.
