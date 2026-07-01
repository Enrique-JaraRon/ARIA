"""
Guided AI portfolio generation utilities for ARIA.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from app_config import get_runtime_setting
from portfolio_analytics import PROFESSIONAL_COLUMNS

REQUIRED_GENERATED_COLUMNS = [
    "ticker",
    "name",
    "weight",
    "asset_class",
    "sector",
]

DISCLAIMER = (
    "Ce portefeuille est une simulation éducative générée à partir des "
    "préférences indiquées. Il ne constitue pas un conseil en investissement. "
    "Les performances passées ou estimées ne préjugent pas des performances "
    "futures."
)

PRICE_FALLBACKS = {
    "SPY": 500.0,
    "QQQ": 455.0,
    "VTI": 285.0,
    "VT": 118.0,
    "BND": 72.0,
    "AGG": 100.0,
    "BNDX": 49.0,
    "SHV": 110.0,
    "SHY": 82.0,
    "GLD": 220.0,
    "VNQ": 88.0,
    "VIG": 190.0,
    "SCHD": 80.0,
    "USMV": 85.0,
    "XLV": 145.0,
    "XLP": 77.0,
    "XLE": 93.0,
    "IXUS": 70.0,
    "VWO": 44.0,
    "NOBL": 105.0,
    "TIP": 108.0,
    "DBC": 23.0,
    "ESGU": 123.0,
    "ESGD": 86.0,
    "ICLN": 14.0,
    "SMH": 260.0,
    "NVDA": 125.0,
    "MSFT": 430.0,
    "AAPL": 195.0,
    "GOOGL": 180.0,
    "AVGO": 170.0,
    "BRK-B": 410.0,
    "COST": 850.0,
    "LLY": 880.0,
    "JPM": 205.0,
    "JNJ": 155.0,
    "PG": 165.0,
}


def _clean_ticker(value: Any) -> str:
    return str(value or "").strip().upper()


def _normalize_weight_series(weights: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(
        weights,
        errors="coerce",
    ).fillna(0.0)
    numeric = numeric.clip(lower=0.0)
    total = float(numeric.sum())

    if total <= 0:
        return pd.Series(
            [100.0 / max(len(numeric), 1)] * len(numeric),
            index=numeric.index,
        )

    return numeric / total * 100.0


def validate_generated_portfolio(
    portfolio_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Validate and normalize a generated portfolio before loading it into ARIA.

    The output uses lowercase advisory columns:
    ticker, name, weight, asset_class, sector, rationale.
    """

    warnings = []
    data = portfolio_df.copy()
    data.columns = [str(column).strip().lower() for column in data.columns]

    for column in REQUIRED_GENERATED_COLUMNS:
        if column not in data.columns:
            data[column] = ""
            warnings.append(f"Colonne manquante remplie automatiquement : {column}")

    if "rationale" not in data.columns:
        data["rationale"] = ""

    data["ticker"] = data["ticker"].map(_clean_ticker)
    data = data[data["ticker"] != ""].copy()

    if data.empty:
        data = fallback_portfolio({})["portfolio"]
        warnings.append(
            "La génération était vide : ARIA a utilisé un portefeuille diversifié de secours."
        )

    data["weight"] = pd.to_numeric(
        data["weight"],
        errors="coerce",
    ).fillna(0.0)

    data["name"] = data["name"].fillna(data["ticker"])
    data["asset_class"] = data["asset_class"].replace("", "Equity / ETF")
    data["sector"] = data["sector"].replace("", "Diversified")
    data["rationale"] = data["rationale"].fillna("")

    duplicated_tickers = data[data["ticker"].duplicated()]["ticker"].unique().tolist()
    if duplicated_tickers:
        warnings.append(
            "Tickers en double fusionnés : "
            + ", ".join(sorted(duplicated_tickers))
        )

    data = (
        data.groupby("ticker", as_index=False)
        .agg(
            {
                "name": "first",
                "weight": "sum",
                "asset_class": "first",
                "sector": "first",
                "rationale": "first",
            }
        )
        .sort_values("weight", ascending=False)
        .reset_index(drop=True)
    )

    if float(data["weight"].max()) > 80.0:
        warnings.append(
            "Une position trop concentrée a été réduite pendant la validation."
        )
        excess_index = data["weight"].idxmax()
        excess = float(data.loc[excess_index, "weight"] - 45.0)
        data.loc[excess_index, "weight"] = 45.0
        if len(data) > 1 and excess > 0:
            other_index = data.index != excess_index
            data.loc[other_index, "weight"] += excess / int(other_index.sum())

    data["weight"] = _normalize_weight_series(data["weight"]).round(4)

    rounding_gap = 100.0 - float(data["weight"].sum())
    if not data.empty and abs(rounding_gap) > 0:
        data.loc[data.index[0], "weight"] = round(
            float(data.loc[data.index[0], "weight"]) + rounding_gap,
            4,
        )

    return data[REQUIRED_GENERATED_COLUMNS + ["rationale"]], warnings


def fallback_portfolio(preferences: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic, diversified portfolio when no LLM is available."""

    risk_level = str(preferences.get("risk_level", "Moderate")).lower()
    style = str(preferences.get("style", "")).lower()
    sectors = str(preferences.get("preferred_sectors", "")).lower()

    if "ai" in sectors or "semi" in sectors or "tech" in style:
        rows = [
            ("QQQ", "Nasdaq 100 ETF", 28, "Equity ETF", "Growth equities"),
            ("SMH", "VanEck Semiconductor ETF", 18, "Equity ETF", "Semiconductors"),
            ("MSFT", "Microsoft", 10, "Stock", "Software"),
            ("NVDA", "NVIDIA", 8, "Stock", "AI chips"),
            ("VTI", "Vanguard Total Stock Market ETF", 18, "Equity ETF", "US equities"),
            ("BND", "Vanguard Total Bond Market ETF", 12, "Bond ETF", "Core bonds"),
            ("GLD", "SPDR Gold Shares", 6, "Commodity ETF", "Gold"),
        ]
        strategy = "Allocation croissance avec biais IA et semi-conducteurs."
    elif "low" in risk_level or "faible" in risk_level or "defensive" in style:
        rows = [
            ("BND", "Vanguard Total Bond Market ETF", 32, "Bond ETF", "Core bonds"),
            ("SHV", "iShares Short Treasury Bond ETF", 18, "Cash/Bond ETF", "Cash"),
            ("USMV", "iShares MSCI USA Min Vol ETF", 18, "Equity ETF", "Low volatility"),
            ("VIG", "Vanguard Dividend Appreciation ETF", 12, "Equity ETF", "Dividend equities"),
            ("GLD", "SPDR Gold Shares", 12, "Commodity ETF", "Gold"),
            ("VTI", "Vanguard Total Stock Market ETF", 8, "Equity ETF", "US equities"),
        ]
        strategy = "Allocation défensive centrée sur la maîtrise du drawdown."
    elif "esg" in style or "sustainable" in style:
        rows = [
            ("ESGU", "iShares ESG Aware MSCI USA ETF", 34, "Equity ETF", "US ESG"),
            ("ESGD", "iShares ESG Aware MSCI EAFE ETF", 18, "Equity ETF", "Developed ESG"),
            ("VTI", "Vanguard Total Stock Market ETF", 16, "Equity ETF", "US equities"),
            ("BND", "Vanguard Total Bond Market ETF", 20, "Bond ETF", "Core bonds"),
            ("ICLN", "iShares Global Clean Energy ETF", 6, "Equity ETF", "Clean energy"),
            ("GLD", "SPDR Gold Shares", 6, "Commodity ETF", "Gold"),
        ]
        strategy = "Allocation ESG diversifiée avec une poche obligataire stabilisatrice."
    else:
        rows = [
            ("VT", "Vanguard Total World Stock ETF", 42, "Equity ETF", "Global equities"),
            ("BND", "Vanguard Total Bond Market ETF", 24, "Bond ETF", "Core bonds"),
            ("VTI", "Vanguard Total Stock Market ETF", 14, "Equity ETF", "US equities"),
            ("VEA", "Vanguard Developed Markets ETF", 8, "Equity ETF", "Developed equities"),
            ("GLD", "SPDR Gold Shares", 7, "Commodity ETF", "Gold"),
            ("SHY", "iShares 1-3 Year Treasury Bond ETF", 5, "Cash/Bond ETF", "Short bonds"),
        ]
        strategy = "Allocation mondiale équilibrée coeur-satellite."

    portfolio = pd.DataFrame(
        [
            {
                "ticker": ticker,
                "name": name,
                "weight": weight,
                "asset_class": asset_class,
                "sector": sector,
                "rationale": (
                    "Sélectionné pour respecter le profil de risque tout en "
                    "préservant la diversification."
                ),
            }
            for ticker, name, weight, asset_class, sector in rows
        ]
    )
    portfolio, warnings = validate_generated_portfolio(portfolio)

    return {
        "portfolio": portfolio,
        "warnings": warnings,
        "risk_level": preferences.get("risk_level", "Moderate"),
        "horizon": preferences.get("horizon", "Long term"),
        "strategy": strategy,
        "limits": [
            "Les hypothèses du modèle sont simplifiées.",
            "Les prix sont indicatifs lorsque la donnée de marché n'est pas disponible.",
            "Aucun rendement n'est garanti.",
        ],
        "disclaimer": DISCLAIMER,
        "used_llm": False,
    }


def _extract_json_payload(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(
            r"\{.*\}",
            text,
            flags=re.DOTALL,
        )
        if not match:
            raise
        return json.loads(match.group(0))


def generate_ai_portfolio(preferences: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a portfolio proposal with the configured LLM, then validate it.

    Falls back to a deterministic portfolio when the API is not configured or
    the LLM returns invalid data.
    """

    model = get_runtime_setting("ARIA_LLM_MODEL")
    api_key = get_runtime_setting("OPENAI_API_KEY")

    if not model or not api_key:
        return fallback_portfolio(preferences)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = {
            "role": "user",
            "content": (
                "Create an educational investment portfolio proposal for ARIA. "
                "Réponds en français. Return only valid JSON with keys: "
                "portfolio, risk_level, horizon, strategy, limits. portfolio "
                "must be a list of objects with ticker, name, weight, "
                "asset_class, sector, rationale. Rules: weights sum to 100, "
                "no negative weights, no guaranteed returns, no personalized "
                "financial advice, use liquid listed tickers or broad ETFs. "
                "Preferences: "
                + json.dumps(preferences, ensure_ascii=True)
            ),
        }
        response = client.responses.create(
            model=model,
            input=[prompt],
        )
        payload = _extract_json_payload(response.output_text)
        portfolio = pd.DataFrame(payload.get("portfolio", []))
        clean_portfolio, warnings = validate_generated_portfolio(portfolio)

        return {
            "portfolio": clean_portfolio,
            "warnings": warnings,
            "risk_level": payload.get("risk_level", preferences.get("risk_level", "")),
            "horizon": payload.get("horizon", preferences.get("horizon", "")),
            "strategy": payload.get("strategy", ""),
            "limits": payload.get("limits", []),
            "disclaimer": DISCLAIMER,
            "used_llm": True,
        }

    except Exception as error:
        result = fallback_portfolio(preferences)
        result["warnings"].append(
            f"Génération LLM indisponible, portefeuille de secours utilisé : {error}"
        )
        return result


def generated_portfolio_to_aria_table(
    generated_df: pd.DataFrame,
    total_value: float = 100_000.0,
) -> pd.DataFrame:
    """Convert a validated generated allocation to the ARIA table schema."""

    clean_df, _ = validate_generated_portfolio(generated_df)
    rows = []

    for _, row in clean_df.iterrows():
        ticker = _clean_ticker(row["ticker"])
        price = PRICE_FALLBACKS.get(ticker, 100.0)
        quantity = round(total_value * float(row["weight"]) / 100.0 / price, 4)
        rows.append(
            {
                "Asset type": "stock",
                "Asset class": row["asset_class"],
                "Ticker": ticker,
                "Sous-jacent": ticker,
                "Nom": row["name"],
                "Sector": row["sector"],
                "Currency": "USD",
                "Weight": round(float(row["weight"]), 4),
                "Value": round(total_value * float(row["weight"]) / 100.0, 2),
                "Quantity": quantity,
                "Price": price,
                "Data source": "IA ARIA",
                "Commentaire": row["rationale"],
                "Option type": "",
                "Strike": None,
                "Maturity": None,
                "Volatility": None,
                "Rate": None,
                "Contract size": 1,
                "Instrument": "Action",
                "Type option": "",
                "Quantite": quantity,
                "Multiplicateur": 1,
                "Spot": price,
                "Volatilite": None,
                "Maturite": None,
            }
        )

    return pd.DataFrame(
        rows,
        columns=PROFESSIONAL_COLUMNS,
    )
