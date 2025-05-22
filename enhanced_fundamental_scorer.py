
import requests
import numpy as np

API_KEY = "682d76fa5c4b17.85025825"
WACC = 0.1  # Assumed average cost of capital (10%)

def get_fundamentals(ticker, section):
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={API_KEY}&fmt=json&filter={section}"
    resp = requests.get(url)
    return resp.json() if resp.status_code == 200 else {}

def score_range(value, thresholds, scores):
    for i, threshold in enumerate(thresholds):
        if value < threshold:
            return scores[i]
    return scores[-1]

def calculate_scores(ticker):
    print(f"\n📊 Scoring fundamentals for {ticker}")
    data_cf = get_fundamentals(ticker, "Financials::Cash_Flow::annual")
    data_bs = get_fundamentals(ticker, "Financials::Balance_Sheet::annual")
    data_is = get_fundamentals(ticker, "Financials::Income_Statement::annual")
    data_highlights = get_fundamentals(ticker, "Highlights")

    try:
        years = sorted(data_cf.keys())[-5:]

        # Get financial arrays
        cfo = [float(data_cf[y]["Operating_Cash_Flow"]) for y in years]
        capex = [float(data_cf[y]["Capital_Expenditures"]) for y in years]
        fcf = [c - abs(x) for c, x in zip(cfo, capex)]
        cfi = [float(data_cf[y]["Investing_Cash_Flow"]) for y in years]
        cff = [float(data_cf[y]["Financing_Cash_Flow"]) for y in years]
        net_income = [float(data_is[y]["Net_Income"]) for y in years]
        revenue = [float(data_is[y]["Total_Revenue"]) for y in years]
        op_income = [float(data_is[y]["Operating_Income"]) for y in years]

        latest_bs = data_bs[years[-1]]
        total_assets = float(latest_bs["Total_Assets"])
        current_liabilities = float(latest_bs["Total_Current_Liabilities"])
        current_assets = float(latest_bs["Total_Current_Assets"])
        total_liabilities = float(latest_bs["Total_Liabilities"])
        total_equity = float(latest_bs["Total_Equity"])
        cash = float(latest_bs.get("Cash_and_Cash_Equivalents", 0))

        roe = float(data_highlights.get("ReturnOnEquity", 0)) / 100
        peg = float(data_highlights.get("PEGRatio", 0))

        scores = []

        # A) Free Cash Flow (FCF)
        delta_fcf = fcf[-1] - fcf[0]
        scores.append(score_range(delta_fcf, [0, np.mean(cfo) * 0.05], [0, 1, 2]))

        # B) CFO / Net Income
        cfo_ni = np.mean(cfo) / np.mean(net_income)
        scores.append(score_range(cfo_ni, [0.8, 1.0], [0, 1, 2]))

        # C) CFI Trend
        cfi_std = np.std(cfi)
        scores.append(score_range(cfi_std, [50000000, 10000000], [0, 1, 2]))

        # D) CFF Pattern
        cff_trend = np.mean(cff)
        scores.append(score_range(abs(cff_trend), [1e9, 1e8], [0, 1, 2]))

        # E) Debt-to-Equity Ratio
        debt_eq = total_liabilities / total_equity
        scores.append(score_range(debt_eq, [1.0, 2.0], [2, 1, 0]))

        # F) Current Ratio
        curr_ratio = current_assets / current_liabilities
        scores.append(score_range(curr_ratio, [1.0, 1.5], [0, 1, 2]))

        # G) ROCE
        roce = op_income[-1] / (total_assets - current_liabilities)
        scores.append(score_range(roce, [WACC * 0.95, WACC * 1.05], [0, 1, 2]))

        # H) Economic Profit
        nopat = op_income[-1] * (1 - 0.21)
        eco_profit = nopat - total_assets * WACC
        scores.append(score_range(eco_profit, [0, 1], [0, 1, 2]))

        # I) Operating Margin
        op_margin = op_income[-1] / revenue[-1]
        scores.append(score_range(op_margin, [0.10, 0.15], [0, 1, 2]))

        # J) Revenue Growth (3–5 yr CAGR)
        cagr = (revenue[-1] / revenue[0]) ** (1 / (len(revenue) - 1)) - 1
        scores.append(score_range(cagr, [0.05, 0.10], [0, 1, 2]))

        # K) Earnings Quality (Net Profit / Operating Profit)
        earn_quality = net_income[-1] / op_income[-1]
        scores.append(score_range(earn_quality, [0.6, 0.85], [0, 1, 2]))

        # L) ROE
        scores.append(score_range(roe, [0.10, 0.15], [0, 1, 2]))

        # M) ROIC
        invested_cap = total_equity + total_liabilities - cash
        roic = nopat / invested_cap
        scores.append(score_range(roic, [WACC * 0.95, WACC * 1.05], [0, 1, 2]))

        # N) PEG Ratio
        scores.append(score_range(peg, [1.0, 2.0], [2, 1, 0]))

        # O) CFO / Operating Profit
        cf_op_ratio = np.mean(cfo) / np.mean(op_income)
        scores.append(score_range(cf_op_ratio, [0, 0.5, 0.9, 1.2], [0, 0.5, 1, 2]))

        total_score = sum(scores)
        print(f"\n🧮 Total Score: {total_score}/30")

        if total_score >= 25:
            print("✅ Fundamentally Strong – Investable for long-term holding")
        elif total_score >= 17:
            print("⚠️ Moderately Strong – Further analysis needed")
        else:
            print("❌ Weak Fundamentals – Avoid or proceed with caution")

    except Exception as e:
        print(f"Error processing data: {e}")

# Example
calculate_scores("AAPL.US")
