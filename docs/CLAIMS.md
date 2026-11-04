# Claims audit: SCAPS-1D solar cell README and live page

Every number in `README.md` and `docs/index.html` traced to the SCAPS-1D batch export and script that produce it, re-run on
2026-11-04 on a clean clone (`./reproduce.sh`; Python 3.13, numpy 2.5, openpyxl 3.1, matplotlib 3.11). Metrics are the
`Voc = / Jsc = / FF = / eta =` rows SCAPS writes into each export, cross-checked by `scripts/make_figures.py` against P_max
from the J-V sweep (within 0.05 points in every case). `docs/build_assets.py` uses the same sheet parser.

| Claim | Where it is computed | Reproduced value | Status |
|---|---|---|---|
| FTO / ZnSe / CdTe heterojunction with a screened ETL and metal back contact | README device table; sheets in `data/Cs2BiAgI6 DATA POINTS.xlsx` (CdTe, ZnSe, FTO sweeps) | as described | matches |
| Ten electron-transport layers screened | `data/*DATA POINTS.xlsx` (one workbook per ETL) | 10 workbooks: Cs2BiAgI6, C60, PC16BM, Cu2O, CuO, Sb2Se3, TiO2, WO3, PCBM, WS2 | matches |
| Best simulated efficiency 27.99 % with Cs2BiAgI6 (V_OC 1.21 V, J_SC 25.96 mA cm⁻², FF 89.3 %) | `Cs2BiAgI6 DATA POINTS.xlsx`, sheet ETL VARY at 2.0 µm | PCE 27.988 %, V_OC 1.2075 V, J_SC 25.962 mA cm⁻², FF 89.281 % | matches |
| ETL ranking at best swept thickness: C60 27.50, PC16BM 23.41, Cu2O 22.63, CuO 20.56, Sb2Se3 20.50, TiO2 13.99, WO3 8.11, PCBM 0.25, WS2 0.25 % | `data/scaps_metrics.json` `etl_thickness` | identical to two decimals | matches |
| Layer sweeps: ETL 27.81 → 27.99 %, CdTe 27.23 → 27.85 %, ZnSe flat at 27.80 to 27.82 %, FTO 27.89 → 26.96 % | `scaps_metrics.json` `layers` | identical | matches |
| Temperature 300 → 400 K: PCE 27.99 → 23.07 %, V_OC slope −1.66 mV K⁻¹, −0.049 points K⁻¹ | `Cs2BiAgI6_Temperature_Data.xlsx`; `scaps_metrics.json` `voc_slope_mV_per_K`, `pce_slope_per_K` | −1.661 mV K⁻¹, −0.0492 points K⁻¹ | matches |
| Nine back-contact metals; Ni (5.55 eV) 27.99 %, Pt 28.44 %, Se 28.45 %, Al 5.26 % | `scripts/make_figures.py` lines 100-103 (table transcribed from the report, Project_Report.pdf); nine metals were screened in the report, the gold row is omitted in the README because its recorded work function does not match literature values, leaving eight plotted | values as tabulated | from the report, not from an export in `data/` |
| Six-parameter DOE | README: ETL material, ETL / CdTe / ZnSe / FTO thickness, temperature, back-contact metal swept one at a time in batch mode | six swept parameters across the workbooks and the report | matches the count; one-at-a-time sweeps, not a factorial design |
| Spiral PV architecture with 17.9 % more active area; two granted Indian design registrations (434427-001, 459195-001); one utility application under review | `PATENT 1.pdf`, `PATENT 2.pdf` (certificates); the 17.9 % figure is from the CV and the report's concept description, not computable from any file here | certificates present | registrations verified; area figure not verifiable here |
| Best Poster Award, 61st Annual Convention of Chemists (ACC 2024) | `Conference_Poster.pdf` | poster present; award not evidenced by a file | from the CV |

## Changes made in this pass

| Old | New | Reason |
|---|---|---|
| hero was a static banner | hero block linking to the live page, banner retained below | requested structure |
| "about 18 % more active area" | "17.9 % more active area" | the figure in the CV; the README's rounding is dropped |
| "Reproduce the figures" with a bare pip line | `requirements.txt`, `./reproduce.sh`, How to run verified from a clean clone | hygiene |
| no LICENSE, .gitignore | MIT, .gitignore | hygiene |
| no results table or citation | results table with source sheets; citation block | requested structure |

No numeric claim read from the exports needed correction; `scripts/make_figures.py` regenerates `data/scaps_metrics.json` identically (differences only in the 15th decimal of the two fitted slopes).

## Not verifiable from the repository

- The back-contact table and the material-parameter table come from the capstone report (`Project_Report.pdf`), not from an export in `data/`.
- The 17.9 % active-area figure for the spiral panel and the Best Poster Award are stated on the CV; the repository holds the design-registration certificates and the poster, not a derivation of the area or an award certificate.
- Simulated efficiencies are a ceiling for this one-dimensional parameter set, as the README's scope section says; no fabricated cell exists.
