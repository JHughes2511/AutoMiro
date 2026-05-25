"""
Free financial data via yfinance — no API key required.
"""

import json
import yfinance as yf
from ..utils.logger import get_logger

logger = get_logger("tools.financial")


def get_stock_info(ticker: str) -> dict:
    """Fetch key fundamentals and metadata for a ticker."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "ticker": ticker.upper(),
            "name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "analyst_target": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey"),
            "short_ratio": info.get("shortRatio"),
            "description": (info.get("longBusinessSummary") or "")[:500],
        }
    except Exception as e:
        logger.warning(f"[financial] get_stock_info({ticker}) failed: {e}")
        return {"ticker": ticker, "error": str(e)}


def get_ticker_history(ticker: str, period: str = "1y") -> dict:
    """Fetch price history. Period: 1mo, 3mo, 6mo, 1y, 2y, 5y."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        if hist.empty:
            return {"ticker": ticker, "error": "No history data"}

        start_price = float(hist["Close"].iloc[0])
        end_price = float(hist["Close"].iloc[-1])
        pct_change = ((end_price - start_price) / start_price) * 100

        return {
            "ticker": ticker.upper(),
            "period": period,
            "start_price": round(start_price, 2),
            "end_price": round(end_price, 2),
            "pct_change": round(pct_change, 2),
            "high": round(float(hist["High"].max()), 2),
            "low": round(float(hist["Low"].min()), 2),
            "avg_volume": int(hist["Volume"].mean()),
        }
    except Exception as e:
        logger.warning(f"[financial] get_ticker_history({ticker}) failed: {e}")
        return {"ticker": ticker, "error": str(e)}


def search_tickers(query: str) -> list[dict]:
    """Basic ticker search — returns candidates for a company/sector query."""
    try:
        results = yf.Search(query, max_results=10)
        quotes = results.quotes if hasattr(results, "quotes") else []
        return [
            {
                "ticker": q.get("symbol", ""),
                "name": q.get("longname") or q.get("shortname", ""),
                "type": q.get("quoteType", ""),
                "exchange": q.get("exchDisp", ""),
            }
            for q in quotes
            if q.get("symbol")
        ]
    except Exception as e:
        logger.warning(f"[financial] search_tickers({query}) failed: {e}")
        return []


def format_stock_info(ticker: str) -> str:
    """Returns stock info as formatted string for agent consumption."""
    info = get_stock_info(ticker)
    if "error" in info:
        return f"Could not fetch data for {ticker}: {info['error']}"

    hist = get_ticker_history(ticker, "1y")
    change_str = f"{hist.get('pct_change', 'N/A')}%" if "pct_change" in hist else "N/A"

    def fmt(val, prefix="$", suffix="", is_int=False):
        if val is None:
            return "N/A"
        if is_int:
            return f"{prefix}{int(val):,}{suffix}"
        return f"{prefix}{val}{suffix}"

    return f"""
{info['ticker']} — {info['name']}
Sector: {info['sector']} | Industry: {info['industry']}
Price: {fmt(info['price'])} | 52w: {fmt(info['52w_low'])} – {fmt(info['52w_high'])}
Market Cap: {fmt(info['market_cap'], is_int=True)} | P/E: {fmt(info['pe_ratio'], prefix='')} | Fwd P/E: {fmt(info['forward_pe'], prefix='')}
Revenue Growth: {fmt(info['revenue_growth'], prefix='')} | Earnings Growth: {fmt(info['earnings_growth'], prefix='')}
Analyst Target: {fmt(info['analyst_target'])} | Recommendation: {fmt(info['recommendation'], prefix='')}
1Y Price Change: {change_str}
Business: {info['description']}
""".strip()
