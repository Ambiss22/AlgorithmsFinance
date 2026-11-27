# Class 3: PriceAmericanPut - Stephane Martin Ambassa

This submission corresponds to **Lab: PriceAmericanPut on market data** in
`AlgorithmsFinance_Slides3.pdf` (PDF pages 29-32; printed lab slides 29/31-31/31).
`Submissions/AmbassaStéphaneMartin/Class3/` is the canonical working folder.
This consolidation uses `Ambiss22:class3-price-american-put-ambassa` at
`9765746` and retains the useful local reference inspector. The complete course
checkout keeps shared data and profiling code in the top-level `Class3/` folder.

## Current stage: scalar pricing and market calibration implemented

The scalar American put pricer and hourly market calibration are implemented.
Exercise-boundary construction and observed-exercise decisions remain
`NotImplementedError` stubs.
No market-data option value or pricing benchmark has been invented.
Assignment 1 is unchanged.

| Lab work | Included | Remaining |
|---|---|---|
| Acquire/inspect all 40 assets | preparation code, hashes, coverage/quality tables | none for this preparation snapshot |
| Verify small trees and financial properties | production one-row scalar pricer, exact references, property and numerical tests | complete for scalar stage |
| Calibrate hourly data | production log returns, hourly sample volatility and binomial factors; existing contracts pass | complete for this stage |
| Exercise boundary and observed decision | exact node, tie, indexing and path tests | production exercise logic |
| Bitcoin one-year/full-history and all-asset experiments | actual Bitcoin one-year calibration report; reproducible windows and data-readiness tables | pricing runs, other-asset calibration and an explicit full-history gap decision |
| Runtime/peak memory | opt-in integration and benchmark procedure | actual measurements after implementation |

## Reproduce from this repository

Python 3.10+ and its standard library are sufficient. From the repository root:

```powershell
cd "Submissions/AmbassaStéphaneMartin/Class3"
python prepare_data.py --source-repo ../../..
python run_tests.py
```

The first command acquires the supplied course snapshot and regenerates the
80 window CSVs and audit files in ignored `output/`. In a full course checkout,
inputs are copied once from the shared `Class3/data/hourly/` folder into ignored
`data/raw/`; they are not duplicated in this submission's Git history. A local
consolidated workspace that already contains `data/hourly/` reuses those files
without copying them. Preparation does not fetch or fill missing hours. Later runs need only
`python prepare_data.py`. Reviewed snapshots stay in `results/`; consumers use
fresh `output/` tables when present and otherwise the reviewed tables.
The reviewed `results/source_manifest.json` records the source commit and measured file hashes.
The local data/source_manifest.json is generated during the first bootstrap and
then preserves that local snapshot. On subsequent runs use python prepare_data.py
(without reacquiring). Git checkout line endings can change byte hashes across
platforms; the reviewed manifest records the measured Windows snapshot. Course
data stay unchanged. The course PDF is referenced, not redistributed, and is
not needed for preparation.

`run_tests.py` currently runs 107 methods: **86 pass**. The remaining 21
exercise-policy methods have 33 pending cases (16 boundary, 17 observed-decision
cases); unexpected assertion failures and unittest errors are zero. The runner
intentionally exits **1** until those functions are implemented. The historical
105-method pre-calibration snapshot remains in `results/test_summary.json`.
The existing calibration and scalar-pricing test files are unchanged.

Run only the implemented scalar/reference/data checks:

```powershell
python -B -m unittest -v test_market_calibration test_american_put test_american_put_numerics test_american_put_properties
python -m unittest -v test_prepare_data test_prepared_market test_exercise_policy.BoundaryReferenceTests
```

Reconcile every regenerated window directly with the raw source:

```powershell
python reference/check_outputs.py
```

## Reviewed tables and provenance

`results/bitcoin_calibration.json` is the reproducible report for the implemented
market-calibration stage. `results/` also contains `asset_summary.csv`, `window_summary.csv`, `gaps.csv`,
`exclusions.csv`, `REPORT.txt`, `test_summary.json`, `scalar_validation.json`, `source_manifest.json`, `verification.json` and
`run_metadata.json`. These are the preparation/test snapshot; fresh results
are regenerated under `output/`.

All 40 assets are USDT-quoted; PAXG represents tokenized gold. Bitcoin's one-year
window has 8,761 closes, N=8,760 and S0=K=109608.01 USDT from its FIRST selected
close. Full history contains 43,823 closes and is missing
`2023-03-24T13:00:00Z`. All 40 assets share that gap and their full-history windows
are flagged for explicit treatment before equal-hour calibration. S&P 500 retrieval
is documented separately in the report and has not been run.

The 40 input files are already versioned in the course's `Class3/data/hourly/`.
Local snapshot copies and generated window rows stay ignored. The snapshot includes no market-data pricing
table or benchmark measurement; those experiments are deferred.

## Interfaces, tests and opt-in performance work

- `PRICING_TESTS.txt`: scalar interface, exact values, invalid inputs and tolerances.
- `FINANCIAL_CALIBRATION_TESTS.txt`: financial properties and calibration contracts.
- `EXERCISE_TESTS.txt`: boundary/path interfaces, ties, settlement and gap gates.
- `BENCHMARKS.txt`: explicit elapsed-time/peak-memory protocol and run commands.

After boundary implementation, explicitly run the expensive market check:

```powershell
python bitcoin_integration_check.py --run
```

Large-tree runs stay outside the default fast suite. Benchmark output distinguishes
untraced elapsed time, peak traced Python allocations and whole-process peak
resident memory. There are no machine-dependent timing pass/fail thresholds.

## Market calibration and Bitcoin result

```powershell
python -B calibrate_bitcoin.py
```

This reuses `load_prepared_window`, `require_hourly_window` and
`calibrate_prepared_window`; elapsed years come from the timestamps using
ACT/365F. The one-year window runs from **2025-10-31 23:00 UTC** to
**2026-10-31 23:00 UTC**: 8,761 closes, 8,760 periods, T=1 year and
S0=K=P0=109608.01 USDT. At the default continuously compounded annual rate 0.04:

| Parameter | Actual value |
|---|---:|
| Hourly sample volatility s | 0.00460739514049591 |
| u = exp(s) | 1.004618025505313 |
| d = 1/u | 0.9954032026222204 |
| R = exp(annual_rate*T/N) | 1.0000045662204708 |
| q = (R-d)/(u-d) | 0.49934368317518857 |

`log_returns` calculates adjacent natural-log returns. `sample_hourly_volatility`
uses sample standard deviation with denominator N-1, without annualization.
Near-equal prices use `log1p`; extreme ratios use log differences; accurate
sample sums avoid unnecessary overflow or underflow. Inputs are preserved.
Invalid or insufficient inputs, zero volatility, nonfinite/degenerate factors
and violations of 0<d<R<u or 0<q<1 raise `ValueError`. No volatility floor or
probability clipping is used. The `Calibration` dataclass and public signatures
are preserved.

The report includes input and implementation hashes and the full-history gap
rejection. Full history still misses **2023-03-24 13:00 UTC** and is not
calibrated. No exercise boundary or 8,760-period pricing run is performed.

## Scalar algorithm and numerical scope

`price_american_put(S0, K, u, d, R, N) -> float` validates inputs before shortcuts
and applies backward induction in O(N^2) time with one O(N) value row. Ascending
node indices preserve both successors during each in-place row update.
Stock/strike ratios use compensated log sums and `expm1`; a separately computed
complementary probability preserves small branches. General valid factors and
negative rates are supported. Binary64 precision/range and resource limits are
documented in `PRICING_TESTS.txt`. Valid but unrepresentable option values raise
`OverflowError`. The independent full-tree evaluator remains in the tests.

## Local data preparation and Windows Python

After the first bootstrap, `python prepare_data.py` regenerates preparation
outputs from the local snapshot without internet. SHA-256 integrity checks run
before and after preparation; raw files, course files and source PDFs are not
modified. Existing raw bytes/manifests cannot be silently replaced. Create a
separate snapshot/project when deliberately changing the data version.

If Python is not on PATH, the Codex bundled interpreter can be used from the
project folder (no pip packages are needed):

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\prepare_data.py
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest -v test_prepare_data
```

For a separate standalone project, acquire from an existing checkout; preserving
an optional local copy of the supplied course PDF is supported:

```powershell
python prepare_data.py --source-repo "C:\path\to\AlgorithmsFinance" --reference-pdf "C:\path\to\AlgorithmsFinance_Slides3.pdf"
```

If needed, first clone the course repository into a new folder with
`git clone https://github.com/cogeorg/AlgorithmsFinance.git "C:\path\to\course-checkout"`.
Acquisition reuses `data/hourly/` when that local consolidated dataset exists.
Otherwise it copies the external course snapshot into ignored `data/raw/` and
reference scripts into ignored `reference/course_data/`. It does not pull into
the checkout. Shared course files are not copied into this submission's Git history.

| Local generated path | Meaning |
|---|---|
| `data/raw/<ASSET>.csv` | Ignored local snapshot of the shared course inputs |
| `data/hourly/<ASSET>.csv` | Existing dataset reused by a local consolidated workspace |
| `data/source_manifest.json` | Local source URL, commit, hashes and optional PDF provenance |
| `reference/course_data/` | Ignored reference scripts copied with an external snapshot |
| `reference/AlgorithmsFinance_Slides3.pdf` | Optional supplied PDF, preserved locally and not committed |
| `output/REPORT.txt` | Regenerated cleaning decisions and Bitcoin readiness |
| `output/gaps.csv`, `output/exclusions.csv` | Missing intervals and excluded source rows |
| `output/windows/<ASSET>/<window>.csv` | Indexed one-year and full-history selections |
| `output/run_metadata.json` | Interpreter, scope and raw-integrity result |

## Window conventions

- One year: last 8,761 valid observed closes. N=8,760. This is an observation
  selection, not a 365-day filter. Elapsed time and gaps are checked separately.
- Full history: all available closes in (last timestamp - 5 calendar years,
  last timestamp]. The strict lower bound caps hourly bar labels to five years;
  leap days are included. It does not force a 5*8,760 observation count.
- Row index i labels P_i; P_0 is the FIRST selected close. S_0=K=P_0 in USDT.
- Each window CSV retains UTC labels, exact close text, source file line, and
  elapsed_hours_from_previous/missing_hours_before. The first elapsed value is
  blank because there is no prior selected observation.
- A two-hour jump remains a two-hour jump. No fills, interpolation, synthetic
  rows, or contiguous-subwindow substitutions occur.
- sufficient_observations tests count only. ready_for_hourly_pricing additionally
  requires consecutive one-hour timestamps. A partial available history may be
  usable for a shorter experiment; complete_course_five_year_grid separately
  tests the full advertised November 2021-October 2026 inclusive grid.

## Audit field definitions

raw_observations: parsed CSV records before exclusions, excluding the header.
usable_observations: unique valid hourly closes after the documented policy.
duplicate_timestamp_rows: extra rows beyond one at each parseable UTC timestamp.
duplicate_timestamp_groups: distinct timestamps with more than one raw row.
invalid_prices: empty, nonnumeric, nonfinite or nonpositive closes.
invalid_timestamps: unparseable timestamps or timestamps without a timezone.
off_hour_timestamps: UTC minute/second/subsecond component is nonzero.
ordering_violations: adjacent parseable RAW timestamps decrease.
missing_hours: absent internal hours between first and last usable timestamp.
missing_course_hours: absent hours on the expected 43,824-label course grid,
  including missing endpoints. Observations outside it are reported separately.
Excluded-row count is distinct: invalid issue counts can overlap on a row.
An identical-price duplicate keeps its first valid source row; conflicting
valid closes for one hour exclude that entire conflicting group.

## S&P 500 retrieval

The supplied fetch_sp500.py is documented separately in output/REPORT.txt and
has NOT been run. It requests ^GSPC from Yahoo for range=730d&interval=1h and
writes hourly/SP500.csv relative to the script. It returns index points during
New York market sessions, not a USDT series on a 24/7 clock. Do not combine its
nontrading periods with crypto missing-hour counts. Use a separate exchange
calendar and period convention if the later lab stage includes it.

## Optional course profiling and reference inspection

The shared `Class3/class3_evidence.py` preserves course demonstrations for
`FillMarketSell`, `PriceAmericanPut`, `RandomizedQuickSort` and `EstimateMeanLoss`.
From this submission folder in a full checkout:

```powershell
python ../../../Class3/class3_evidence.py --validate-only
# Optional figures require matplotlib:
python ../../../Class3/class3_evidence.py
```

A local consolidated workspace may keep that script as `class3_evidence.py`;
run it there directly. Profiling outputs stay ignored.
`reference/inspect_reference.py` preserves the local lab-reference helper:

```powershell
python reference/inspect_reference.py reference/AlgorithmsFinance_Slides3.pdf
```

Reference text extraction needs `pypdf`; optional `--render` also needs
`pypdfium2` and Pillow. The reference PDF and rendered pages stay local.
