
"""
Financial Health Scoring Script using EODHD API

Calculates 14 key financial metrics for a given stock ticker.
Each metric is scored (0 to 2), with an overall score determining fundamental strength.

Scoring categories:
- 24–28: ✅ Fundamentally Strong – Investable for long-term holding
- 18–23: ⚠️ Moderately Strong – Further analysis needed
- <18: ❌ Weak Fundamentals – Avoid or proceed with caution
"""

import requests
import numpy as np

API_KEY = "682d76fa5c4b17.85025825"
WACC = 0.10  # Assumed cost of capital (10%)

def get_fundamentals(ticker, section):
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={API_KEY}&fmt=json&filter={section}"
    resp = requests.get(url)
    return resp.json() if resp.status_code == 200 else {}

def score_range(value, thresholds, scores):
    for i, threshold in enumerate(thresholds):
        if value < threshold:
            return scores[i]
    return scores[-1]

def calculate_score(ticker):
    print(f"📊 Evaluating {ticker}...
")
    data_cf = get_fundamentals(ticker, "Financials::Cash_Flow::annual")
    data_bs = get_fundamentals(ticker, "Financials::Balance_Sheet::annual")
    data_is = get_fundamentals(ticker, "Financials::Income_Statement::annual")
    data_highlights = get_fundamentals(ticker, "Highlights")

    try:
        years = sorted(data_cf.keys())[-5:]
        # Prepare data arrays
        cfo = [float(data_cf[y]["Operating_Cash_Flow"]) for y in years]
        capex = [float(data_cf[y]["Capital_Expenditures"]) for y in years]
        fcf = [c - abs(x) for c, x in zip(cfo, capex)]
        cfi = [float(data_cf[y]["Investing_Cash_Flow"]) for y in years]
        cff = [float(data_cf[y]["Financing_Cash_Flow"]) for y in years]

        net_income = [float(data_is[y]["Net_Income"]) for y in years]
        revenue = [float(data_is[y]["Total_Revenue"]) for y in years]
        op_income = [float(data_is[y]["Operating_Income"]) for y in years]

        year_latest = years[-1]
        total_assets = float(data_bs[year_latest]["Total_Assets"])
        current_liabilities = float(data_bs[year_latest]["Total_Current_Liabilities"])
        current_assets = float(data_bs[year_latest]["Total_Current_Assets"])
        total_liabilities = float(data_bs[year_latest]["Total_Liabilities"])
        total_equity = float(data_bs[year_latest]["Total_Equity"])
        cash = float(data_bs[year_latest].get("Cash_and_Cash_Equivalents", 0))

        pe_ratio = float(data_highlights.get("PERatio", 0))
        roe = float(data_highlights.get("ReturnOnEquity", 0))
        peg = float(data_highlights.get("PEGRatio", 0))

        # Scoring
        scores = {}

        # A) Free Cash Flow (FCF)
        scores["FCF"] = score_range(np.mean(fcf), [0, np.mean(cfo)*0.05], [0, 1, 2])

        # B) CFO / Net Income
        cfo_ni_ratio = np.mean(cfo) / np.mean(net_income)
        scores["CFO/NetIncome"] = score_range(cfo_ni_ratio, [0.8, 1.0], [0, 1, 2])

        # C) CFI Trend
        scores["CFI Trend"] = score_range(np.std(cfi), [5e7, 1e7], [0, 1, 2])

        # D) CFF Pattern
        scores["CFF Pattern"] = score_range(abs(np.mean(cff)), [1e9, 1e8], [0, 1, 2])

        # E) Debt-to-Equity Ratio
        debt_equity = total_liabilities / total_equity
        scores["Debt/Equity"] = score_range(debt_equity, [1.0, 2.0], [2, 1, 0])

        # F) Current Ratio
        curr_ratio = current_assets / current_liabilities
        scores["Current Ratio"] = score_range(curr_ratio, [1.0, 1.5], [0, 1, 2])

        # G) ROCE
        roce = op_income[-1] / (total_assets - current_liabilities)
        scores["ROCE"] = score_range(roce, [WACC*0.95, WACC*1.05], [0, 1, 2])

        # H) Economic Profit
        nopat = op_income[-1] * (1 - 0.21)
        capital_charge = total_assets * WACC
        eco_profit = nopat - capital_charge
        scores["Econ Profit"] = score_range(eco_profit, [0, 1], [0, 1, 2])

        # I) Operating Margin
        op_margin = op_income[-1] / revenue[-1]
        scores["Op Margin"] = score_range(op_margin, [0.10, 0.15], [0, 1, 2])

        # J) Revenue Growth
        cagr = (revenue[-1] / revenue[0])**(1/4) - 1
        scores["Revenue Growth"] = score_range(cagr, [0.05, 0.10], [0, 1, 2])

        # K) Earnings Quality
        eq = net_income[-1] / op_income[-1]
        scores["Earnings Quality"] = score_range(eq, [0.6, 0.85], [0, 1, 2])

        # L) ROE
        scores["ROE"] = score_range(roe / 100, [0.10, 0.15], [0, 1, 2])

        # M) ROIC
        invested_capital = total_equity + total_liabilities - cash
        roic = nopat / invested_capital
        scores["ROIC"] = score_range(roic, [WACC*0.95, WACC*1.05], [0, 1, 2])

        # N) PEG
        scores["PEG"] = score_range(peg, [1.0, 2.0], [2, 1, 0])

        # Total Score
        total_score = sum(scores.values())
        print(f"🔢 Total Score: {total_score}/28")

        # Verdict
        if total_score >= 24:
            print("✅ Fundamentally Strong – Investable for long-term holding")
        elif total_score >= 18:
            print("⚠️ Moderately Strong – Further analysis needed")
        else:
            print("❌ Weak Fundamentals – Avoid or proceed with caution")

        # Detailed Output
        print("\n📋 Detailed Scores:")
        for k, v in scores.items():
            print(f"{k}: {v}/2")

    except Exception as e:
        print(f"⚠️ Error in processing: {e}")

# Example
calculate_score("AAPL.US")
