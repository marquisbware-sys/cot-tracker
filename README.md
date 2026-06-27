# COT Tracker (per-index)

Per-index Commitments of Traders dashboard mirroring Tradingster's layout.
Pulls directly from the CFTC's free public reporting API (no key, official),
with a dropdown to switch between indexes and both reports (Legacy +
Disaggregated) shown per index.

Indexes: S&P 500, Nasdaq-100, Russell 2000, VIX.

Live: `https://marquisbware-sys.github.io/cot-tracker/dashboard.html`

## What you get (per index)

- Legacy raw data table: non-commercial / commercial / non-reportable,
  long/short/spreads, color-coded W/W changes, % of open interest, trader counts.
- Key-numbers cards: large-spec net, leveraged-funds net, OI W/W, commercials.
- Disaggregated institutional breakdown: leveraged funds, asset managers,
  dealers, other reportables, with net and net W/W.
- Multi-week comparison showing how positioning shifted.
- "Copy this index for Claude" button — packages the full picture so you can
  paste it into chat and get the written "what this means for my trades" read.

## Setup

1. Create a **public** repo `cot-tracker`.
2. Upload `calculate_cot.py`, `dashboard.html`, `cot_data.json`, this README;
   create `.github/workflows/update-cot.yml` via Add file -> Create new file.
3. Settings -> Actions -> General -> **Read and write permissions** -> Save.
4. Settings -> Pages -> Deploy from branch -> **main** / root -> Save.
5. Actions -> update-cot -> Run workflow, then hard-refresh.

Runs automatically Fridays 21:00 UTC (4pm CT), after the 3pm CT release.

## How to use it

COT reflects each **Tuesday's** positioning, released **Friday ~3pm CT** — a
**weekly, lagged bias** tool, not an intraday signal. Read the data here, then
hit "Copy for Claude" and paste it into chat to get the written bias breakdown
(flip-signal watch, OI interpretation, trade-this-week framing).

## Files

| File | Purpose |
|---|---|
| `calculate_cot.py` | Pulls CFTC data (4 indexes, full fields, 6 wks), writes JSON |
| `dashboard.html` | Per-index dropdown dashboard |
| `.github/workflows/update-cot.yml` | Friday + manual runner |
| `cot_data.json` | Generated output |
