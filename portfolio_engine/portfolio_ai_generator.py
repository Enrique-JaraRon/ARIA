"""
Guided AI portfolio generation utilities for ARIA.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from app.app_config import get_runtime_setting
from portfolio_engine.portfolio_analytics import PROFESSIONAL_COLUMNS

REQUIRED_GENERATED_COLUMNS = [
    "ticker",
    "name",
    "weight",
    "asset_class",
    "sector",
]

OPTION_GENERATED_COLUMNS = [
    "instrument_type",
    "underlying",
    "option_type",
    "position",
    "spot",
    "strike",
    "maturity",
    "premium",
    "implied_volatility",
    "contract_size",
    "quantity",
    "currency",
    "notional_exposure",
    "delta",
    "option_objective",
]

NUMERIC_GENERATED_COLUMNS = [
    "spot",
    "strike",
    "maturity",
    "premium",
    "implied_volatility",
    "contract_size",
    "quantity",
    "notional_exposure",
    "delta",
]

GENERATED_COLUMNS = REQUIRED_GENERATED_COLUMNS + OPTION_GENERATED_COLUMNS + ["rationale"]

DISCLAIMER = (
    "Ce portefeuille est une simulation educative generee a partir des preferences "
    "indiquees. Il ne constitue pas un conseil en investissement. Les performances "
    "passees ou estimees ne prejugent pas des performances futures."
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

GENERATED_COLUMN_ALIASES = {
    "symbol": "ticker",
    "underlying_ticker": "underlying",
    "asset_type": "instrument_type",
    "instrument": "instrument_type",
    "type": "instrument_type",
    "call_put": "option_type",
    "option": "option_type",
    "side": "position",
    "sens": "position",
    "objective": "option_objective",
    "objectif": "option_objective",
    "iv": "implied_volatility",
    "volatility": "implied_volatility",
    "contractsize": "contract_size",
    "notional": "notional_exposure",
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


def _wants_options(preferences: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(preferences.get("instruments", "")),
            str(preferences.get("style", "")),
            str(preferences.get("objective", "")),
        ]
    ).lower()
    return any(
        keyword in text
        for keyword in [
            "option",
            "options",
            "call",
            "put",
            "couverture",
            "hedge",
            "protection",
            "covered call",
            "collar",
        ]
    )


def _normalize_generated_column_names(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    data = portfolio_df.copy()
    cleaned_columns = []
    for column in data.columns:
        clean = str(column).strip().lower().replace(" ", "_").replace("-", "_")
        cleaned_columns.append(GENERATED_COLUMN_ALIASES.get(clean, clean))
    data.columns = cleaned_columns
    return data


def _safe_text(value: Any, default: str = "") -> str:
    if pd.isna(value):
        return default
    return str(value)


def _complete_option_fields(data: pd.DataFrame) -> pd.DataFrame:
    option_mask = data["instrument_type"].eq("option")

    for index, row in data.loc[option_mask].iterrows():
        underlying = _clean_ticker(_safe_text(row.get("underlying"), row.get("ticker")))
        spot = pd.to_numeric(row.get("spot"), errors="coerce")
        if pd.isna(spot) or float(spot) <= 0:
            spot = PRICE_FALLBACKS.get(underlying, 100.0)
            data.loc[index, "spot"] = spot

        option_type = _safe_text(row.get("option_type")).lower()
        if option_type not in {"call", "put"}:
            option_type = "put"
            data.loc[index, "option_type"] = option_type

        strike = pd.to_numeric(row.get("strike"), errors="coerce")
        if pd.isna(strike) or float(strike) <= 0:
            data.loc[index, "strike"] = round(
                float(spot) * (0.95 if option_type == "put" else 1.05),
                2,
            )

        maturity = pd.to_numeric(row.get("maturity"), errors="coerce")
        if pd.isna(maturity) or float(maturity) <= 0:
            data.loc[index, "maturity"] = 0.25

        volatility = pd.to_numeric(row.get("implied_volatility"), errors="coerce")
        if pd.isna(volatility) or float(volatility) <= 0:
            data.loc[index, "implied_volatility"] = 0.24

        contract_size = pd.to_numeric(row.get("contract_size"), errors="coerce")
        if pd.isna(contract_size) or float(contract_size) <= 0:
            data.loc[index, "contract_size"] = 100

        premium = pd.to_numeric(row.get("premium"), errors="coerce")
        if pd.isna(premium) or float(premium) <= 0:
            data.loc[index, "premium"] = round(float(spot) * 0.018, 2)

        if _safe_text(row.get("option_objective")).strip() == "":
            data.loc[index, "option_objective"] = (
                "Simulation d'option pour couverture ou rendement"
            )

    return data


def validate_generated_portfolio(
    portfolio_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Validate and normalize a generated portfolio before loading it into ARIA.
    """

    warnings = []
    data = _normalize_generated_column_names(portfolio_df)

    for column in REQUIRED_GENERATED_COLUMNS:
        if column not in data.columns:
            data[column] = ""
            warnings.append(f"Colonne manquante remplie automatiquement : {column}")

    for column in OPTION_GENERATED_COLUMNS + ["rationale"]:
        if column not in data.columns:
            data[column] = pd.NA

    for column in NUMERIC_GENERATED_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["ticker"] = data["ticker"].map(_clean_ticker)
    data = data[data["ticker"] != ""].copy()

    if data.empty:
        data = fallback_portfolio({})["portfolio"]
        warnings.append(
            "La generation etait vide : ARIA a utilise un portefeuille diversifie de secours."
        )

    data["weight"] = pd.to_numeric(
        data["weight"],
        errors="coerce",
    ).fillna(0.0)

    data["name"] = data["name"].fillna(data["ticker"])
    data["asset_class"] = data["asset_class"].replace("", "ETF / action")
    data["sector"] = data["sector"].replace("", "Diversifie")
    data["rationale"] = data["rationale"].fillna("")
    data["instrument_type"] = (
        data["instrument_type"]
        .fillna("")
        .astype(str)
        .str.lower()
        .replace(
            {
                "": "stock",
                "equity": "stock",
                "action": "stock",
                "etf": "stock",
                "option": "option",
                "options": "option",
            }
        )
    )
    data["underlying"] = data["underlying"].fillna("").astype(str)
    data.loc[data["underlying"].str.strip().eq(""), "underlying"] = data.loc[
        data["underlying"].str.strip().eq(""),
        "ticker",
    ]
    data["option_type"] = data["option_type"].fillna("").astype(str).str.lower()
    data["position"] = (
        data["position"]
        .fillna("long")
        .astype(str)
        .str.lower()
        .replace(
            {
                "achete": "long",
                "acheté": "long",
                "achetee": "long",
                "vendu": "short",
                "vendue": "short",
                "sell": "short",
            }
        )
    )
    data["currency"] = data["currency"].replace("", "USD").fillna("USD")

    identity_columns = [
        "ticker",
        "instrument_type",
        "option_type",
        "position",
        "strike",
        "maturity",
    ]
    duplicated_assets = data[data.duplicated(identity_columns)]["ticker"].unique().tolist()
    if duplicated_assets:
        warnings.append(
            "Tickers en double fusionnes : " + ", ".join(sorted(duplicated_assets))
        )

    data = (
        data.groupby(identity_columns, as_index=False, dropna=False)
        .agg(
            {
                "underlying": "first",
                "name": "first",
                "weight": "sum",
                "asset_class": "first",
                "sector": "first",
                "spot": "first",
                "premium": "first",
                "implied_volatility": "first",
                "contract_size": "first",
                "quantity": "first",
                "currency": "first",
                "notional_exposure": "first",
                "delta": "first",
                "option_objective": "first",
                "rationale": "first",
            }
        )
        .sort_values("weight", ascending=False)
        .reset_index(drop=True)
    )

    if float(data["weight"].max()) > 80.0:
        warnings.append("Une position trop concentree a ete reduite pendant la validation.")
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

    data = _complete_option_fields(data)
    return data[GENERATED_COLUMNS], warnings


def _option_strategy_rows(preferences: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    risk_level = str(preferences.get("risk_level", "Equilibre")).lower()
    objective = str(preferences.get("objective", "")).lower()
    base_ticker = "SPY"
    spot = PRICE_FALLBACKS[base_ticker]

    if "agressif" in risk_level or "speculation" in objective:
        return (
            [
                _generated_row("SPY", "SPDR S&P 500 ETF", 55, "ETF / action", "US equities"),
                _generated_row("QQQ", "Nasdaq 100 ETF", 25, "ETF / action", "Growth equities"),
                _generated_row(
                    "SPY",
                    "SPY call 3 mois 105%",
                    12,
                    "Option",
                    "Index options",
                    instrument_type="option",
                    underlying=base_ticker,
                    option_type="call",
                    position="long",
                    spot=spot,
                    strike=spot * 1.05,
                    maturity=0.25,
                    premium=12.5,
                    implied_volatility=0.26,
                    contract_size=100,
                    delta=0.52,
                    option_objective="Participation haussiere avec risque limite a la prime",
                ),
                _generated_row(
                    "SPY",
                    "SPY put 3 mois 95%",
                    8,
                    "Option",
                    "Index options",
                    instrument_type="option",
                    underlying=base_ticker,
                    option_type="put",
                    position="long",
                    spot=spot,
                    strike=spot * 0.95,
                    maturity=0.25,
                    premium=9.0,
                    implied_volatility=0.28,
                    contract_size=100,
                    delta=-0.34,
                    option_objective="Protection partielle en cas de baisse rapide",
                ),
            ],
            "Portefeuille offensif avec options listees simulees : participation actions, calls achetes et puts de protection.",
        )

    return (
        [
            _generated_row("SPY", "SPDR S&P 500 ETF", 60, "ETF / action", "US equities"),
            _generated_row("BND", "Vanguard Total Bond Market ETF", 20, "ETF / action", "Core bonds"),
            _generated_row("GLD", "SPDR Gold Shares", 8, "ETF / action", "Gold"),
            _generated_row(
                "SPY",
                "SPY put protecteur 3 mois 95%",
                7,
                "Option",
                "Index options",
                instrument_type="option",
                underlying=base_ticker,
                option_type="put",
                position="long",
                spot=spot,
                strike=spot * 0.95,
                maturity=0.25,
                premium=9.0,
                implied_volatility=0.25,
                contract_size=100,
                delta=-0.35,
                option_objective="Protection contre une baisse marquee",
            ),
            _generated_row(
                "SPY",
                "SPY call couvert 3 mois 108%",
                5,
                "Option",
                "Index options",
                instrument_type="option",
                underlying=base_ticker,
                option_type="call",
                position="short",
                spot=spot,
                strike=spot * 1.08,
                maturity=0.25,
                premium=7.0,
                implied_volatility=0.23,
                contract_size=100,
                delta=0.28,
                option_objective="Financement partiel de la protection via prime encaissee",
            ),
        ],
        "Portefeuille couvert de type collar : exposition actions, poche defensive et options simulees avec hypotheses visibles.",
    )


def _generated_row(
    ticker: str,
    name: str,
    weight: float,
    asset_class: str,
    sector: str,
    **kwargs: Any,
) -> dict[str, Any]:
    row = {
        "ticker": ticker,
        "name": name,
        "weight": weight,
        "asset_class": asset_class,
        "sector": sector,
        "rationale": (
            "Selectionne pour respecter le profil de risque tout en preservant la diversification."
        ),
        "instrument_type": "stock",
        "underlying": ticker,
        "option_type": "",
        "position": "long",
        "spot": PRICE_FALLBACKS.get(ticker, 100.0),
        "strike": "",
        "maturity": "",
        "premium": "",
        "implied_volatility": "",
        "contract_size": 1,
        "quantity": "",
        "currency": "USD",
        "notional_exposure": "",
        "delta": "",
        "option_objective": "",
    }
    row.update(kwargs)
    return row


def fallback_portfolio(preferences: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic, diversified portfolio when no LLM is available."""

    risk_level = str(preferences.get("risk_level", "Moderate")).lower()
    style = str(preferences.get("style", "")).lower()
    sectors = str(preferences.get("preferred_sectors", "")).lower()

    if _wants_options(preferences):
        rows, strategy = _option_strategy_rows(preferences)
    elif (
        "ai" in sectors
        or "ia" in sectors
        or "semi" in sectors
        or "tech" in style
        or "croissance" in style
        or "dynamique" in risk_level
    ):
        rows = [
            _generated_row("QQQ", "Nasdaq 100 ETF", 28, "Equity ETF", "Growth equities"),
            _generated_row("SMH", "VanEck Semiconductor ETF", 18, "Equity ETF", "Semiconductors"),
            _generated_row("MSFT", "Microsoft", 10, "Stock", "Software"),
            _generated_row("NVDA", "NVIDIA", 8, "Stock", "AI chips"),
            _generated_row("VTI", "Vanguard Total Stock Market ETF", 18, "Equity ETF", "US equities"),
            _generated_row("BND", "Vanguard Total Bond Market ETF", 12, "Bond ETF", "Core bonds"),
            _generated_row("GLD", "SPDR Gold Shares", 6, "Commodity ETF", "Gold"),
        ]
        strategy = "Allocation croissance avec biais IA et semi-conducteurs."
    elif (
        "low" in risk_level
        or "faible" in risk_level
        or "prudent" in risk_level
        or "defensive" in style
        or "defensif" in style
    ):
        rows = [
            _generated_row("BND", "Vanguard Total Bond Market ETF", 32, "Bond ETF", "Core bonds"),
            _generated_row("SHV", "iShares Short Treasury Bond ETF", 18, "Cash/Bond ETF", "Cash"),
            _generated_row("USMV", "iShares MSCI USA Min Vol ETF", 18, "Equity ETF", "Low volatility"),
            _generated_row("VIG", "Vanguard Dividend Appreciation ETF", 12, "Equity ETF", "Dividend equities"),
            _generated_row("GLD", "SPDR Gold Shares", 12, "Commodity ETF", "Gold"),
            _generated_row("VTI", "Vanguard Total Stock Market ETF", 8, "Equity ETF", "US equities"),
        ]
        strategy = "Allocation defensive centree sur la maitrise du drawdown."
    elif "esg" in style or "sustainable" in style or "durable" in style:
        rows = [
            _generated_row("ESGU", "iShares ESG Aware MSCI USA ETF", 34, "Equity ETF", "US ESG"),
            _generated_row("ESGD", "iShares ESG Aware MSCI EAFE ETF", 18, "Equity ETF", "Developed ESG"),
            _generated_row("VTI", "Vanguard Total Stock Market ETF", 16, "Equity ETF", "US equities"),
            _generated_row("BND", "Vanguard Total Bond Market ETF", 20, "Bond ETF", "Core bonds"),
            _generated_row("ICLN", "iShares Global Clean Energy ETF", 6, "Equity ETF", "Clean energy"),
            _generated_row("GLD", "SPDR Gold Shares", 6, "Commodity ETF", "Gold"),
        ]
        strategy = "Allocation ESG diversifiee avec une poche obligataire stabilisatrice."
    else:
        rows = [
            _generated_row("VT", "Vanguard Total World Stock ETF", 42, "Equity ETF", "Global equities"),
            _generated_row("BND", "Vanguard Total Bond Market ETF", 24, "Bond ETF", "Core bonds"),
            _generated_row("VTI", "Vanguard Total Stock Market ETF", 14, "Equity ETF", "US equities"),
            _generated_row("VEA", "Vanguard Developed Markets ETF", 8, "Equity ETF", "Developed equities"),
            _generated_row("GLD", "SPDR Gold Shares", 7, "Commodity ETF", "Gold"),
            _generated_row("SHY", "iShares 1-3 Year Treasury Bond ETF", 5, "Cash/Bond ETF", "Short bonds"),
        ]
        strategy = "Allocation mondiale equilibree coeur-satellite."

    portfolio, warnings = validate_generated_portfolio(pd.DataFrame(rows))

    return {
        "portfolio": portfolio,
        "warnings": warnings,
        "risk_level": preferences.get("risk_level", "Moderate"),
        "horizon": preferences.get("horizon", "Long term"),
        "strategy": strategy,
        "limits": [
            "Les hypotheses du modele sont simplifiees.",
            "Les prix et primes d'options sont indicatifs lorsque la donnee de marche n'est pas disponible.",
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
                "Tu es un assistant de construction de portefeuille pour ARIA. "
                "Reponds uniquement en JSON valide avec les cles portfolio, risk_level, "
                "horizon, strategy, limits. Chaque ligne portfolio doit contenir ticker, "
                "name, weight, asset_class, sector, rationale. Si des options sont demandees, "
                "ajoute de vraies lignes d'options avec instrument_type='option', underlying, "
                "option_type call/put, position long/short, spot, strike, maturity, premium, "
                "implied_volatility, contract_size, quantity si possible, currency, "
                "notional_exposure, delta et option_objective. Regles: poids total 100, "
                "pas de ticker vide, pas de doublon, instruments liquides, aucune promesse "
                "de performance, conseil educatif seulement. Preferences: "
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

    except Exception:
        result = fallback_portfolio(preferences)
        result["warnings"].append(
            "Generation LLM indisponible, portefeuille local coherent utilise."
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
        instrument_type = str(row.get("instrument_type") or "stock").lower()
        currency = str(row.get("currency") or "USD").upper()
        weight = float(row["weight"])
        budget = total_value * weight / 100.0

        if instrument_type == "option":
            underlying = _clean_ticker(row.get("underlying") or ticker)
            spot = float(pd.to_numeric(row.get("spot"), errors="coerce") or PRICE_FALLBACKS.get(underlying, 100.0))
            premium = float(pd.to_numeric(row.get("premium"), errors="coerce") or max(spot * 0.018, 1.0))
            contract_size = float(pd.to_numeric(row.get("contract_size"), errors="coerce") or 100.0)
            quantity = pd.to_numeric(row.get("quantity"), errors="coerce")
            if pd.isna(quantity) or float(quantity) == 0:
                quantity = max(round(abs(budget) / max(premium * contract_size, 1.0), 0), 1)
            if str(row.get("position") or "long").lower() == "short":
                quantity = -abs(float(quantity))
            else:
                quantity = abs(float(quantity))
            value = round(premium * quantity * contract_size, 2)
            notional = round(abs(quantity) * spot * contract_size, 2)
            rows.append(
                {
                    "Asset type": "option",
                    "Asset class": "Option",
                    "Ticker": underlying,
                    "Sous-jacent": underlying,
                    "Nom": row["name"],
                    "Sector": row["sector"],
                    "Currency": currency,
                    "Weight": round(weight, 4),
                    "Value": value,
                    "Quantity": quantity,
                    "Price": spot,
                    "Data source": "IA ARIA - simulation options",
                    "Commentaire": row["rationale"],
                    "Option type": str(row.get("option_type") or "put").lower(),
                    "Strike": round(float(row.get("strike")), 4),
                    "Maturity": round(float(row.get("maturity")), 4),
                    "Volatility": round(float(row.get("implied_volatility")), 4),
                    "Rate": 0.05,
                    "Contract size": contract_size,
                    "Instrument": "Option",
                    "Type option": str(row.get("option_type") or "put").lower(),
                    "Quantite": quantity,
                    "Multiplicateur": contract_size,
                    "Spot": spot,
                    "Volatilite": round(float(row.get("implied_volatility")), 4),
                    "Maturite": round(float(row.get("maturity")), 4),
                    "Position": "Short" if quantity < 0 else "Long",
                    "Prime": premium,
                    "Exposition notionnelle": notional,
                    "Delta": row.get("delta"),
                    "Objectif option": row.get("option_objective"),
                }
            )
            continue

        price = PRICE_FALLBACKS.get(ticker, 100.0)
        quantity = round(budget / price, 4)
        rows.append(
            {
                "Asset type": "stock",
                "Asset class": row["asset_class"],
                "Ticker": ticker,
                "Sous-jacent": ticker,
                "Nom": row["name"],
                "Sector": row["sector"],
                "Currency": currency,
                "Weight": round(weight, 4),
                "Value": round(budget, 2),
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
                "Position": "Long",
                "Prime": None,
                "Exposition notionnelle": round(abs(quantity) * price, 2),
                "Delta": None,
                "Objectif option": "",
            }
        )

    return pd.DataFrame(
        rows,
        columns=PROFESSIONAL_COLUMNS,
    )
