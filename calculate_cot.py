"""
Commitments of Traders (COT) Calculator — per-index detailed version
====================================================================
Pulls weekly COT data from the CFTC's free public reporting API (Socrata,
no key, works from GitHub Actions) for four index futures and captures the
FULL table breakdown so the dashboard can mirror Tradingster's layout.

For each index we keep the latest report plus several prior weeks (for the
week-over-week changes and the multi-week comparison), from BOTH reports:

  LEGACY (jun7-fc8e): Non-commercial (long/short/spreads), Commercial
    (long/short), Non-reportable (long/short), open interest, trader counts.

  DISAGGREGATED (72hh-3qpy): Leveraged Funds, Asset Managers, Dealers,
    Other Reportables (long/short), for the finer institutional read.

COT reflects each TUESDAY's positioning, released Friday ~3pm CT. Weekly,
lagged bias tool — not an intraday signal.

Output: cot_data.json
"""

import json
import time
from datetime import datetime, timezone

import requests

LEGACY_URL = "https://publicreporting.cftc.gov/resource/jun7-fc8e.json"
DISAGG_URL = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"

CONTRACTS = [
    {"name": "S&P 500 E-Mini",     "code": "SP",  "match": "E-MINI S&P 500"},
    {"name": "Nasdaq-100 E-Mini",  "code": "NQ",  "match": "NASDAQ-100 STOCK INDEX"},
    {"name": "Russell 2000 E-Mini","code": "RTY", "match": "RUSSELL 2000"},
    {"name": "VIX Futures",        "code": "VX",  "match": "VIX FUTURES"},
]

WEEKS_KEPT = 6  # latest + 5 prior, enough for W/W + comparison
HEADERS = {"User-Agent": "cot-tracker/1.0"}


def fetch_dataset(url):
    params = {"$order": "report_date_as_yyyy_mm_dd DESC", "$limit": "5000"}
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=40)
            if r.status_code == 200:
                return r.json()
            print(f"  HTTP {r.status_code} from {url}")
        except requests.RequestException as e:
            print(f"  attempt {attempt+1} failed: {e}")
        time.sleep(3)
    return None


def n(row, key):
    v = row.get(key)
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def rows_for(rows, match):
    m = match.upper()
    return [r for r in rows if m in (r.get("market_and_exchange_names") or "").upper()]


def legacy_week(row):
    """Full legacy breakdown for one report week."""
    return {
        "date": (row.get("report_date_as_yyyy_mm_dd") or "")[:10],
        "oi": n(row, "open_interest_all"),
        "noncomm_long": n(row, "noncomm_positions_long_all"),
        "noncomm_short": n(row, "noncomm_positions_short_all"),
        "noncomm_spread": n(row, "noncomm_postions_spread_all") or n(row, "noncomm_positions_spread_all"),
        "comm_long": n(row, "comm_positions_long_all"),
        "comm_short": n(row, "comm_positions_short_all"),
        "nonrept_long": n(row, "nonrept_positions_long_all"),
        "nonrept_short": n(row, "nonrept_positions_short_all"),
        "traders_total": n(row, "traders_tot_all"),
        "traders_noncomm_long": n(row, "traders_noncomm_long_all"),
        "traders_noncomm_short": n(row, "traders_noncomm_short_all"),
        "traders_comm_long": n(row, "traders_comm_long_all"),
        "traders_comm_short": n(row, "traders_comm_short_all"),
    }


def disagg_week(row):
    """Disaggregated institutional breakdown for one week."""
    return {
        "date": (row.get("report_date_as_yyyy_mm_dd") or "")[:10],
        "oi": n(row, "open_interest_all"),
        "lev_long": n(row, "lev_money_positions_long") or n(row, "m_money_positions_long_all"),
        "lev_short": n(row, "lev_money_positions_short") or n(row, "m_money_positions_short_all"),
        "am_long": n(row, "asset_mgr_positions_long") or n(row, "prod_merc_positions_long_all"),
        "am_short": n(row, "asset_mgr_positions_short") or n(row, "prod_merc_positions_short_all"),
        "dealer_long": n(row, "dealer_positions_long") or n(row, "swap_positions_long_all"),
        "dealer_short": n(row, "dealer_positions_short") or n(row, "swap__positions_short_all"),
        "other_long": n(row, "other_rept_positions_long") or n(row, "other_rept_positions_long_all"),
        "other_short": n(row, "other_rept_positions_short") or n(row, "other_rept_positions_short_all"),
    }


def build(legacy_rows, disagg_rows, c):
    leg = rows_for(legacy_rows, c["match"])[:WEEKS_KEPT]
    dis = rows_for(disagg_rows, c["match"])[:WEEKS_KEPT]
    out = {"name": c["name"], "code": c["code"]}
    if leg:
        out["legacy"] = [legacy_week(r) for r in leg]
    if dis:
        out["disagg"] = [disagg_week(r) for r in dis]
    return out if ("legacy" in out or "disagg" in out) else None


def main():
    print("Fetching Legacy ...")
    legacy_rows = fetch_dataset(LEGACY_URL) or []
    print(f"  {len(legacy_rows)} rows")
    print("Fetching Disaggregated ...")
    disagg_rows = fetch_dataset(DISAGG_URL) or []
    print(f"  {len(disagg_rows)} rows")

    results, errors = [], []
    for c in CONTRACTS:
        b = build(legacy_rows, disagg_rows, c)
        if b:
            results.append(b)
            lw = b.get("legacy", [{}])[0]
            print(f"  [{c['code']}] {lw.get('date')} noncomm "
                  f"{lw.get('noncomm_long')}L/{lw.get('noncomm_short')}S")
        else:
            errors.append(c["code"])
            print(f"  [{c['code']}] not found")

    report_date = None
    for r in results:
        report_date = (r.get("legacy") or r.get("disagg") or [{}])[0].get("date")
        if report_date:
            break

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "report_date": report_date,
        "note": "COT reflects each Tuesday's positioning, released Fri ~3pm CT. "
                "Weekly, lagged bias tool — not an intraday signal.",
        "errors": errors,
        "contracts": results,
    }
    with open("cot_data.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote cot_data.json: {len(results)} indexes, week {report_date}.")


if __name__ == "__main__":
    main()
