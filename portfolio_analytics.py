"""
Professional portfolio analytics and model allocation utilities for ARIA.
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd

from pricing_BS import OptionContract, bs_price


@dataclass(frozen=True)
class ModelPortfolio:
    """Description of a professional model allocation."""

    name: str
    risk_level: str
    expected_return: float
    volatility: float
    drawdown: float
    diversification_score: int
    investor_profile: str
    explanation: str
    target_weights: dict[str, float]
    sectors: dict[str, str]
    prices: dict[str, float]
    currency: str = "USD"


MODEL_PORTFOLIOS: dict[str, ModelPortfolio] = {
    "Conservative Balanced Portfolio": ModelPortfolio(
        name="Conservative Balanced Portfolio",
        risk_level="Low to moderate",
        expected_return=0.045,
        volatility=0.085,
        drawdown=-0.12,
        diversification_score=88,
        investor_profile="Capital preservation, income and limited drawdown tolerance.",
        explanation=(
            "A diversified mix of bonds, quality equities and gold designed "
            "for a cautious investor seeking stability before growth."
        ),
        target_weights={
            "BND": 0.40,
            "VTI": 0.25,
            "VEA": 0.12,
            "VIG": 0.10,
            "GLD": 0.08,
            "SHV": 0.05,
        },
        sectors={
            "BND": "Core bonds",
            "VTI": "US equities",
            "VEA": "Developed equities",
            "VIG": "Dividend equities",
            "GLD": "Gold",
            "SHV": "Cash equivalents",
        },
        prices={
            "BND": 72.0,
            "VTI": 285.0,
            "VEA": 52.0,
            "VIG": 190.0,
            "GLD": 220.0,
            "SHV": 110.0,
        },
    ),
    "Moderate Growth Portfolio": ModelPortfolio(
        name="Moderate Growth Portfolio",
        risk_level="Moderate",
        expected_return=0.065,
        volatility=0.125,
        drawdown=-0.20,
        diversification_score=82,
        investor_profile="Balanced investor accepting equity risk for long-term growth.",
        explanation=(
            "A growth-oriented allocation with meaningful bonds and global "
            "equities to reduce concentration."
        ),
        target_weights={
            "VTI": 0.42,
            "VEA": 0.18,
            "VWO": 0.10,
            "BND": 0.20,
            "VNQ": 0.05,
            "GLD": 0.05,
        },
        sectors={
            "VTI": "US equities",
            "VEA": "Developed equities",
            "VWO": "Emerging equities",
            "BND": "Core bonds",
            "VNQ": "Real estate",
            "GLD": "Gold",
        },
        prices={
            "VTI": 285.0,
            "VEA": 52.0,
            "VWO": 44.0,
            "BND": 72.0,
            "VNQ": 88.0,
            "GLD": 220.0,
        },
    ),
    "Global Diversified Portfolio": ModelPortfolio(
        name="Global Diversified Portfolio",
        risk_level="Moderate",
        expected_return=0.06,
        volatility=0.115,
        drawdown=-0.18,
        diversification_score=92,
        investor_profile="Investor seeking broad geographic and asset-class balance.",
        explanation=(
            "A globally diversified allocation designed to reduce dependence "
            "on one country, sector or macro factor."
        ),
        target_weights={
            "VT": 0.45,
            "BNDX": 0.18,
            "BND": 0.17,
            "VNQ": 0.07,
            "GLD": 0.08,
            "SHV": 0.05,
        },
        sectors={
            "VT": "Global equities",
            "BNDX": "Global bonds",
            "BND": "US bonds",
            "VNQ": "Real estate",
            "GLD": "Gold",
            "SHV": "Cash equivalents",
        },
        prices={
            "VT": 118.0,
            "BNDX": 49.0,
            "BND": 72.0,
            "VNQ": 88.0,
            "GLD": 220.0,
            "SHV": 110.0,
        },
    ),
    "Tech Growth Portfolio": ModelPortfolio(
        name="Tech Growth Portfolio",
        risk_level="High",
        expected_return=0.09,
        volatility=0.22,
        drawdown=-0.35,
        diversification_score=58,
        investor_profile="Long-horizon investor comfortable with large equity swings.",
        explanation=(
            "A concentrated growth allocation that keeps a technology tilt but "
            "limits single-name dominance with broad market exposure."
        ),
        target_weights={
            "QQQ": 0.40,
            "VTI": 0.25,
            "NVDA": 0.10,
            "MSFT": 0.10,
            "AAPL": 0.08,
            "BND": 0.07,
        },
        sectors={
            "QQQ": "Growth equities",
            "VTI": "US equities",
            "NVDA": "Semiconductors",
            "MSFT": "Software",
            "AAPL": "Hardware",
            "BND": "Core bonds",
        },
        prices={
            "QQQ": 455.0,
            "VTI": 285.0,
            "NVDA": 125.0,
            "MSFT": 430.0,
            "AAPL": 195.0,
            "BND": 72.0,
        },
    ),
    "Defensive Dividend Portfolio": ModelPortfolio(
        name="Defensive Dividend Portfolio",
        risk_level="Moderate defensive",
        expected_return=0.055,
        volatility=0.105,
        drawdown=-0.16,
        diversification_score=80,
        investor_profile="Income-focused investor seeking resilient equity exposure.",
        explanation=(
            "A defensive equity allocation focused on dividends, quality and "
            "lower cyclical exposure."
        ),
        target_weights={
            "VIG": 0.30,
            "SCHD": 0.25,
            "XLV": 0.12,
            "XLP": 0.10,
            "BND": 0.18,
            "SHV": 0.05,
        },
        sectors={
            "VIG": "Dividend equities",
            "SCHD": "Dividend equities",
            "XLV": "Healthcare",
            "XLP": "Consumer staples",
            "BND": "Core bonds",
            "SHV": "Cash equivalents",
        },
        prices={
            "VIG": 190.0,
            "SCHD": 80.0,
            "XLV": 145.0,
            "XLP": 77.0,
            "BND": 72.0,
            "SHV": 110.0,
        },
    ),
    "Hedged Equity Portfolio": ModelPortfolio(
        name="Hedged Equity Portfolio",
        risk_level="Moderate hedged",
        expected_return=0.058,
        volatility=0.095,
        drawdown=-0.14,
        diversification_score=84,
        investor_profile="Equity investor seeking downside control and smoother returns.",
        explanation=(
            "A diversified equity allocation combined with bonds and gold to "
            "keep market participation while reducing downside sensitivity."
        ),
        target_weights={
            "VTI": 0.32,
            "USMV": 0.18,
            "VEA": 0.12,
            "BND": 0.22,
            "GLD": 0.10,
            "SHV": 0.06,
        },
        sectors={
            "VTI": "US equities",
            "USMV": "Minimum volatility equities",
            "VEA": "Developed equities",
            "BND": "Core bonds",
            "GLD": "Gold",
            "SHV": "Cash equivalents",
        },
        prices={
            "VTI": 285.0,
            "USMV": 85.0,
            "VEA": 52.0,
            "BND": 72.0,
            "GLD": 220.0,
            "SHV": 110.0,
        },
    ),
    "Low Volatility Portfolio": ModelPortfolio(
        name="Low Volatility Portfolio",
        risk_level="Low",
        expected_return=0.04,
        volatility=0.07,
        drawdown=-0.10,
        diversification_score=86,
        investor_profile="Very cautious investor prioritizing stability.",
        explanation=(
            "A lower-volatility allocation with short bonds, quality stocks "
            "and defensive assets."
        ),
        target_weights={
            "SHV": 0.25,
            "BND": 0.30,
            "USMV": 0.20,
            "VIG": 0.10,
            "GLD": 0.10,
            "XLU": 0.05,
        },
        sectors={
            "SHV": "Cash equivalents",
            "BND": "Core bonds",
            "USMV": "Minimum volatility equities",
            "VIG": "Dividend equities",
            "GLD": "Gold",
            "XLU": "Utilities",
        },
        prices={
            "SHV": 110.0,
            "BND": 72.0,
            "USMV": 85.0,
            "VIG": 190.0,
            "GLD": 220.0,
            "XLU": 70.0,
        },
    ),
    "Crisis-Resilient Portfolio": ModelPortfolio(
        name="Crisis-Resilient Portfolio",
        risk_level="Defensive",
        expected_return=0.042,
        volatility=0.075,
        drawdown=-0.09,
        diversification_score=90,
        investor_profile="Investor focused on resilience in stressed markets.",
        explanation=(
            "A defensive allocation designed to combine liquidity, bonds, "
            "gold and quality equity exposure."
        ),
        target_weights={
            "SHV": 0.20,
            "IEF": 0.25,
            "BND": 0.20,
            "GLD": 0.15,
            "USMV": 0.12,
            "VIG": 0.08,
        },
        sectors={
            "SHV": "Cash equivalents",
            "IEF": "Treasuries",
            "BND": "Core bonds",
            "GLD": "Gold",
            "USMV": "Minimum volatility equities",
            "VIG": "Dividend equities",
        },
        prices={
            "SHV": 110.0,
            "IEF": 95.0,
            "BND": 72.0,
            "GLD": 220.0,
            "USMV": 85.0,
            "VIG": 190.0,
        },
    ),
    "ESG Sustainable Portfolio": ModelPortfolio(
        name="ESG Sustainable Portfolio",
        risk_level="Moderate",
        expected_return=0.061,
        volatility=0.13,
        drawdown=-0.21,
        diversification_score=81,
        investor_profile="Investor seeking diversified equity exposure with an ESG tilt.",
        explanation=(
            "A global ESG-oriented allocation combining broad sustainable equity "
            "funds, clean energy exposure and a bond sleeve to control volatility."
        ),
        target_weights={
            "ESGU": 0.35,
            "ESGD": 0.18,
            "ICLN": 0.08,
            "VTI": 0.17,
            "BND": 0.17,
            "GLD": 0.05,
        },
        sectors={
            "ESGU": "US ESG equities",
            "ESGD": "Developed ESG equities",
            "ICLN": "Clean energy",
            "VTI": "US equities",
            "BND": "Core bonds",
            "GLD": "Gold",
        },
        prices={
            "ESGU": 123.0,
            "ESGD": 86.0,
            "ICLN": 14.0,
            "VTI": 285.0,
            "BND": 72.0,
            "GLD": 220.0,
        },
    ),
    "AI & Semiconductors Portfolio": ModelPortfolio(
        name="AI & Semiconductors Portfolio",
        risk_level="High",
        expected_return=0.105,
        volatility=0.255,
        drawdown=-0.42,
        diversification_score=55,
        investor_profile="Long-term growth investor comfortable with sector concentration.",
        explanation=(
            "A high-conviction technology allocation focused on AI infrastructure, "
            "semiconductors and software, balanced by broad-market and bond exposure."
        ),
        target_weights={
            "SMH": 0.28,
            "QQQ": 0.24,
            "NVDA": 0.12,
            "MSFT": 0.10,
            "AVGO": 0.08,
            "VTI": 0.10,
            "BND": 0.08,
        },
        sectors={
            "SMH": "Semiconductors ETF",
            "QQQ": "Growth equities",
            "NVDA": "AI chips",
            "MSFT": "Cloud software",
            "AVGO": "Semiconductors",
            "VTI": "US equities",
            "BND": "Core bonds",
        },
        prices={
            "SMH": 260.0,
            "QQQ": 455.0,
            "NVDA": 125.0,
            "MSFT": 430.0,
            "AVGO": 170.0,
            "VTI": 285.0,
            "BND": 72.0,
        },
    ),
    "European Quality Portfolio": ModelPortfolio(
        name="European Quality Portfolio",
        risk_level="Moderate",
        expected_return=0.057,
        volatility=0.135,
        drawdown=-0.22,
        diversification_score=78,
        investor_profile="Investor seeking European quality, healthcare and industrial exposure.",
        explanation=(
            "A Europe-focused allocation built around broad European equities, "
            "quality global franchises and a stabilizing bond sleeve."
        ),
        target_weights={
            "VGK": 0.35,
            "IEUR": 0.20,
            "EWQ": 0.10,
            "EWL": 0.08,
            "BNDX": 0.20,
            "GLD": 0.07,
        },
        sectors={
            "VGK": "Europe equities",
            "IEUR": "Europe equities",
            "EWQ": "France equities",
            "EWL": "Switzerland equities",
            "BNDX": "Global bonds",
            "GLD": "Gold",
        },
        prices={
            "VGK": 71.0,
            "IEUR": 59.0,
            "EWQ": 42.0,
            "EWL": 52.0,
            "BNDX": 49.0,
            "GLD": 220.0,
        },
    ),
    "US Blue Chips Portfolio": ModelPortfolio(
        name="US Blue Chips Portfolio",
        risk_level="Moderate to high",
        expected_return=0.073,
        volatility=0.165,
        drawdown=-0.28,
        diversification_score=70,
        investor_profile="Investor seeking liquid US large-cap leaders with some diversification.",
        explanation=(
            "A liquid US blue-chip allocation diversified across technology, "
            "healthcare, consumer and broad-market exposure."
        ),
        target_weights={
            "SPY": 0.35,
            "MSFT": 0.12,
            "AAPL": 0.10,
            "JNJ": 0.08,
            "JPM": 0.08,
            "PG": 0.07,
            "BND": 0.15,
            "SHV": 0.05,
        },
        sectors={
            "SPY": "US large caps",
            "MSFT": "Software",
            "AAPL": "Hardware",
            "JNJ": "Healthcare",
            "JPM": "Financials",
            "PG": "Consumer staples",
            "BND": "Core bonds",
            "SHV": "Cash equivalents",
        },
        prices={
            "SPY": 500.0,
            "MSFT": 430.0,
            "AAPL": 195.0,
            "JNJ": 155.0,
            "JPM": 205.0,
            "PG": 165.0,
            "BND": 72.0,
            "SHV": 110.0,
        },
    ),
    "Global ETF Core Portfolio": ModelPortfolio(
        name="Global ETF Core Portfolio",
        risk_level="Moderate",
        expected_return=0.058,
        volatility=0.11,
        drawdown=-0.17,
        diversification_score=94,
        investor_profile="Long-term investor seeking a simple global core allocation.",
        explanation=(
            "A simple global ETF core with world equities, bonds, real estate, "
            "gold and short-duration bonds."
        ),
        target_weights={
            "VT": 0.45,
            "BND": 0.25,
            "GLD": 0.10,
            "VNQ": 0.10,
            "SHY": 0.10,
        },
        sectors={
            "VT": "Global equities",
            "BND": "Core bonds",
            "GLD": "Gold",
            "VNQ": "Real estate",
            "SHY": "Short-duration treasuries",
        },
        prices={
            "VT": 118.0,
            "BND": 72.0,
            "GLD": 220.0,
            "VNQ": 88.0,
            "SHY": 82.0,
        },
    ),
    "Inflation Protection Portfolio": ModelPortfolio(
        name="Inflation Protection Portfolio",
        risk_level="Moderate defensive",
        expected_return=0.052,
        volatility=0.105,
        drawdown=-0.15,
        diversification_score=87,
        investor_profile="Investor concerned about inflation, rates and purchasing-power risk.",
        explanation=(
            "A real-asset and inflation-aware allocation using TIPS, commodities, "
            "gold, energy and short-duration bonds."
        ),
        target_weights={
            "TIP": 0.28,
            "DBC": 0.12,
            "GLD": 0.15,
            "XLE": 0.10,
            "VTI": 0.20,
            "SHY": 0.15,
        },
        sectors={
            "TIP": "Inflation-linked bonds",
            "DBC": "Commodities",
            "GLD": "Gold",
            "XLE": "Energy",
            "VTI": "US equities",
            "SHY": "Short-duration treasuries",
        },
        prices={
            "TIP": 108.0,
            "DBC": 23.0,
            "GLD": 220.0,
            "XLE": 93.0,
            "VTI": 285.0,
            "SHY": 82.0,
        },
    ),
    "Long-Term Compounders Portfolio": ModelPortfolio(
        name="Long-Term Compounders Portfolio",
        risk_level="High quality growth",
        expected_return=0.082,
        volatility=0.18,
        drawdown=-0.30,
        diversification_score=72,
        investor_profile="Long-horizon investor seeking quality growth franchises.",
        explanation=(
            "A concentrated but diversified set of high-quality compounders, "
            "balanced with broad equity and bond exposure."
        ),
        target_weights={
            "VTI": 0.25,
            "MSFT": 0.12,
            "AAPL": 0.10,
            "GOOGL": 0.09,
            "COST": 0.08,
            "LLY": 0.08,
            "BRK-B": 0.10,
            "BND": 0.18,
        },
        sectors={
            "VTI": "US equities",
            "MSFT": "Software",
            "AAPL": "Hardware",
            "GOOGL": "Digital advertising",
            "COST": "Consumer staples",
            "LLY": "Healthcare",
            "BRK-B": "Diversified financials",
            "BND": "Core bonds",
        },
        prices={
            "VTI": 285.0,
            "MSFT": 430.0,
            "AAPL": 195.0,
            "GOOGL": 180.0,
            "COST": 850.0,
            "LLY": 880.0,
            "BRK-B": 410.0,
            "BND": 72.0,
        },
    ),
}


PROFESSIONAL_COLUMNS = [
    "Asset type",
    "Asset class",
    "Ticker",
    "Sous-jacent",
    "Nom",
    "Sector",
    "Currency",
    "Weight",
    "Value",
    "Quantity",
    "Price",
    "Data source",
    "Commentaire",
    "Option type",
    "Strike",
    "Maturity",
    "Volatility",
    "Rate",
    "Contract size",
    "Instrument",
    "Type option",
    "Quantite",
    "Multiplicateur",
    "Spot",
    "Volatilite",
    "Maturite",
]


def get_model_portfolio_names() -> list[str]:
    """Return professional model portfolio names."""

    return list(MODEL_PORTFOLIOS)


def get_model_portfolio(name: str) -> ModelPortfolio:
    """Return a model portfolio by name."""

    try:
        return MODEL_PORTFOLIOS[name]
    except KeyError as error:
        raise ValueError(f"Unknown model portfolio: {name}") from error


def model_portfolio_to_dataframe(
    model: ModelPortfolio,
    total_value: float = 100_000.0,
) -> pd.DataFrame:
    """Convert a model allocation to the Streamlit portfolio schema."""

    rows = []

    for ticker, weight in model.target_weights.items():
        price = model.prices[ticker]
        quantity = round(total_value * weight / price, 4)
        rows.append(
            {
                "Asset type": "stock",
                "Asset class": "ETF / action",
                "Ticker": ticker,
                "Sous-jacent": ticker,
                "Nom": f"{ticker} - {model.sectors[ticker]}",
                "Sector": model.sectors[ticker],
                "Currency": model.currency,
                "Weight": round(weight * 100, 4),
                "Value": round(total_value * weight, 2),
                "Quantity": quantity,
                "Price": price,
                "Data source": "Portefeuille de demonstration ARIA",
                "Commentaire": model.explanation,
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
                "Volatilite": 0.20,
                "Maturite": None,
            }
        )

    return pd.DataFrame(rows, columns=PROFESSIONAL_COLUMNS)


def _clean_asset_type(value: Any) -> str:
    text = str(value).strip().lower()

    if text in {
        "action",
        "stock",
        "equity",
    }:
        return "stock"

    if text in {
        "option",
        "options",
    }:
        return "option"

    return text


def _row_value(row: pd.Series, *names: str, default: Any = None) -> Any:
    for name in names:
        if name in row and not pd.isna(row[name]):
            return row[name]

    return default


def _market_value(row: pd.Series) -> float:
    asset_type = _clean_asset_type(
        _row_value(row, "Asset type", "Instrument", default="stock")
    )
    quantity = float(_row_value(row, "Quantity", "Quantite", default=0.0))
    price = float(_row_value(row, "Price", "Spot", default=0.0))

    if asset_type == "option":
        option_type = str(_row_value(row, "Option type", "Type option", default="call"))
        strike = float(_row_value(row, "Strike", default=price))
        maturity = float(_row_value(row, "Maturity", "Maturite", default=0.25))
        volatility = float(_row_value(row, "Volatility", "Volatilite", default=0.20))
        rate = float(_row_value(row, "Rate", default=0.05))
        contract_size = float(_row_value(row, "Contract size", "Multiplicateur", default=100))
        contract = OptionContract(
            S=price,
            K=strike,
            T=maturity,
            r=rate,
            sigma=volatility,
            option_type=option_type,
            q=0.0,
        )
        return bs_price(contract) * quantity * contract_size

    return quantity * price


def validate_portfolio_table(table: pd.DataFrame) -> list[str]:
    """Validate stock and option rows with clear user-facing messages."""

    errors = []

    for index, row in table.iterrows():
        if row.dropna().empty:
            continue

        asset_type = _clean_asset_type(
            _row_value(row, "Asset type", "Instrument", default="")
        )

        if not asset_type:
            errors.append(f"Line {index + 1}: asset type is missing.")
            continue

        ticker = str(_row_value(row, "Ticker", "Sous-jacent", default="")).strip()
        quantity = _row_value(row, "Quantity", "Quantite")
        price = _row_value(row, "Price", "Spot")

        if not ticker:
            errors.append(f"Line {index + 1}: ticker / underlying is missing.")

        if quantity is None:
            errors.append(f"Line {index + 1}: quantity is missing.")

        if price is None or float(price) <= 0:
            errors.append(f"Line {index + 1}: price must be positive.")

        if asset_type == "stock":
            continue

        if asset_type != "option":
            errors.append(f"Line {index + 1}: asset type must be stock or option.")
            continue

        option_type = str(_row_value(row, "Option type", "Type option", default="")).strip()
        strike = _row_value(row, "Strike")
        maturity = _row_value(row, "Maturity", "Maturite")
        volatility = _row_value(row, "Volatility", "Volatilite")
        rate = _row_value(row, "Rate")

        if option_type not in {
            "call",
            "put",
        }:
            errors.append(f"Line {index + 1}: option type must be call or put.")

        if strike is None or float(strike) <= 0:
            errors.append(f"Line {index + 1}: strike must be positive for an option.")

        if maturity is None or float(maturity) <= 0:
            errors.append(f"Line {index + 1}: maturity must be positive for an option.")

        if volatility is None or float(volatility) <= 0:
            errors.append(f"Line {index + 1}: volatility must be positive for an option.")

        if rate is None:
            errors.append(f"Line {index + 1}: rate is required for an option.")

    return errors


def validate_portfolio_coherence(
    table: pd.DataFrame,
    risk_profile: str = "Équilibré",
    horizon: str = "Long terme",
) -> tuple[list[str], list[str]]:
    """Validate business coherence before the ARIA analysis is launched."""

    errors = []
    warnings = []

    if table.empty:
        return ["Le portefeuille est vide."], warnings

    working_table = table.copy()
    weight_values = pd.to_numeric(
        working_table.get("Weight", pd.Series(dtype=float)),
        errors="coerce",
    )

    for index, row in working_table.iterrows():
        line_number = index + 1
        ticker = str(_row_value(row, "Ticker", "Sous-jacent", default="")).strip()
        name = str(_row_value(row, "Nom", default="")).strip()
        asset_class = str(_row_value(row, "Asset class", default="")).strip()
        sector = str(_row_value(row, "Sector", default="")).strip()
        currency = str(_row_value(row, "Currency", default="")).strip()
        price = _row_value(row, "Price", "Spot")
        value = _row_value(row, "Value")
        weight = _row_value(row, "Weight")

        if not ticker:
            errors.append(f"Ligne {line_number} : ticker manquant.")

        if not name:
            errors.append(f"Ligne {line_number} : nom de l'actif manquant.")

        if not asset_class:
            errors.append(f"Ligne {line_number} : classe d'actif manquante.")

        if not sector:
            warnings.append(f"Ligne {line_number} : secteur manquant, classé par défaut.")

        if not currency:
            errors.append(f"Ligne {line_number} : devise manquante.")

        if price is None or float(price) <= 0:
            errors.append(f"Ligne {line_number} : prix invalide.")

        value_numeric = pd.to_numeric(value, errors="coerce")
        if pd.isna(value_numeric) or float(value_numeric) == 0:
            errors.append(f"Ligne {line_number} : valeur manquante ou nulle.")
        elif float(value_numeric) < 0:
            warnings.append(
                f"Ligne {line_number} : position vendeuse détectée, valeur de marché négative."
            )

        if weight is None or float(weight) < 0:
            errors.append(f"Ligne {line_number} : poids manquant ou négatif.")

        if weight is not None and float(weight) > 60:
            warnings.append(
                f"Ligne {line_number} : poids très concentré ({float(weight):.1f} %)."
            )

    duplicate_mask = working_table.duplicated(
        subset=["Asset type", "Ticker"],
        keep=False,
    )
    duplicated_rows = working_table[duplicate_mask]
    duplicated_stock_tickers = sorted(
        {
            str(row["Ticker"])
            for _, row in duplicated_rows.iterrows()
            if _clean_asset_type(row.get("Asset type", "stock")) == "stock"
        }
    )
    if duplicated_stock_tickers:
        errors.append(
            "Actifs en double à fusionner : "
            + ", ".join(duplicated_stock_tickers)
        )

    weight_total = float(weight_values.fillna(0).sum())
    if abs(weight_total - 100.0) > 0.05:
        errors.append(
            f"La somme des poids doit être égale à 100 %. Total actuel : {weight_total:.2f} %."
        )

    exposure = portfolio_exposure_table(working_table)
    if not exposure.empty:
        stock_or_equity_text = (
            working_table.get("Asset class", pd.Series(dtype=str))
            .fillna("")
            .astype(str)
            .str.lower()
        )
        risky_assets = stock_or_equity_text.str.contains(
            "action|equity|growth|semi|tech|option",
            regex=True,
        )
        risky_weight = float(weight_values[risky_assets].fillna(0).sum())
        bond_or_cash = stock_or_equity_text.str.contains(
            "bond|obligation|cash|monétaire|tresor|treasury",
            regex=True,
        )
        defensive_weight = float(weight_values[bond_or_cash].fillna(0).sum())

        if risk_profile.lower().startswith("prudent") and risky_weight > 65:
            warnings.append(
                "Profil prudent : la part d'actifs risqués semble élevée."
            )

        if risk_profile.lower().startswith("dynamique") and defensive_weight > 70:
            warnings.append(
                "Profil dynamique : la poche défensive domine le portefeuille."
            )

        if horizon.lower().startswith("court") and risky_weight > 70:
            warnings.append(
                "Horizon court terme : réduire la part d'actifs volatils peut être pertinent."
            )

    return errors, warnings


def portfolio_exposure_table(table: pd.DataFrame) -> pd.DataFrame:
    """Return position-level exposure, weights and concentration metrics."""

    if table.empty:
        return pd.DataFrame()

    rows = []

    for _, row in table.iterrows():
        asset_type = _clean_asset_type(
            _row_value(row, "Asset type", "Instrument", default="stock")
        )
        ticker = str(_row_value(row, "Ticker", "Sous-jacent", default="")).strip()
        name = str(_row_value(row, "Nom", default=ticker)).strip()
        quantity = _row_value(row, "Quantity", "Quantite")
        price = _row_value(row, "Price", "Spot")
        target_weight = _row_value(row, "Weight")
        value = _row_value(row, "Value")

        if not ticker or price is None:
            continue

        if quantity is None and value is None:
            continue

        sector = str(_row_value(row, "Sector", default="Unclassified")).strip()
        currency = str(_row_value(row, "Currency", default="USD")).strip()
        market_value = float(value) if value is not None else _market_value(row)
        rows.append(
            {
                "Ticker": ticker,
                "Name": name or ticker,
                "Asset type": asset_type,
                "Asset class": str(_row_value(row, "Asset class", default=asset_type)),
                "Sector": sector or "Unclassified",
                "Currency": currency or "USD",
                "Quantity": float(quantity) if quantity is not None else 0.0,
                "Price": float(price),
                "Portfolio weight": (
                    float(target_weight) / 100
                    if target_weight is not None
                    else None
                ),
                "Market value": market_value,
                "Gross exposure": abs(market_value),
                "Data source": str(_row_value(row, "Data source", default="Manuel / demo")),
            }
        )

    if not rows:
        return pd.DataFrame()

    exposure = pd.DataFrame(rows)
    gross_total = max(float(exposure["Gross exposure"].sum()), 1.0)
    net_total = float(exposure["Market value"].sum())
    exposure["Gross weight"] = exposure["Gross exposure"] / gross_total
    if exposure["Portfolio weight"].notna().any():
        explicit_weight = exposure["Portfolio weight"].fillna(
            exposure["Gross weight"]
        )
        explicit_total = float(explicit_weight.sum())
        if explicit_total > 0:
            exposure["Gross weight"] = explicit_weight / explicit_total
    exposure["Net weight"] = (
        exposure["Market value"] / net_total
        if abs(net_total) > 1e-9
        else 0.0
    )

    return exposure.sort_values("Gross exposure", ascending=False)


def portfolio_diagnosis(table: pd.DataFrame) -> dict[str, Any]:
    """Build a concise current portfolio diagnosis."""

    exposure = portfolio_exposure_table(table)

    if exposure.empty:
        return {
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "top_position": "N/A",
            "top_weight": 0.0,
            "number_of_assets": 0,
            "number_of_sectors": 0,
            "concentration_level": "N/A",
            "diversification_comment": "Aucune donnée de portefeuille disponible.",
        }

    top_row = exposure.iloc[0]
    top_weight = float(top_row["Gross weight"])
    concentration_level = (
        "Élevée"
        if top_weight >= 0.35
        else "Modérée"
        if top_weight >= 0.20
        else "Maîtrisée"
    )
    number_of_assets = int(exposure["Ticker"].nunique())
    number_of_sectors = int(exposure["Sector"].nunique())

    return {
        "gross_exposure": float(exposure["Gross exposure"].sum()),
        "net_exposure": float(exposure["Market value"].sum()),
        "top_position": str(top_row["Ticker"]),
        "top_weight": top_weight,
        "number_of_assets": number_of_assets,
        "number_of_sectors": number_of_sectors,
        "concentration_level": concentration_level,
            "diversification_comment": (
            "La diversification est large entre actifs et secteurs."
            if number_of_assets >= 6 and number_of_sectors >= 4
            else "La diversification peut être améliorée en élargissant les actifs ou secteurs."
        ),
    }


def rebalancing_recommendations(
    current_table: pd.DataFrame,
    target_model: ModelPortfolio,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compare current weights with a target model portfolio."""

    exposure = portfolio_exposure_table(current_table)
    base_value = max(float(exposure["Gross exposure"].sum()), 1.0)
    current_weights = (
        exposure.groupby("Ticker")["Gross exposure"].sum() / base_value
        if not exposure.empty
        else pd.Series(dtype=float)
    )

    rows = []
    all_tickers = sorted(set(current_weights.index) | set(target_model.target_weights))

    for ticker in all_tickers:
        current_weight = float(current_weights.get(ticker, 0.0))
        target_weight = float(target_model.target_weights.get(ticker, 0.0))
        current_amount = current_weight * base_value
        target_amount = target_weight * base_value
        delta_amount = target_amount - current_amount

        if abs(delta_amount) < base_value * 0.005:
            action = "Maintain"
            wording = "maintain the current allocation"
        elif delta_amount > 0:
            action = "Increase"
            wording = "consider increasing the allocation"
        else:
            action = "Reduce"
            wording = "consider reducing the allocation"

        rows.append(
            {
                "Ticker": ticker,
                "Current weight": current_weight,
                "Target weight": target_weight,
                "Current amount": current_amount,
                "Target amount": target_amount,
                "Change amount": delta_amount,
                "Action": action,
                "Risk-management wording": (
                    f"The client could {wording} in {ticker} "
                    f"from {current_weight:.1%} to {target_weight:.1%}."
                ),
            }
        )

    summary = portfolio_diagnosis(current_table)
    summary.update(
        {
            "target_model": target_model.name,
            "target_volatility": target_model.volatility,
            "target_drawdown": target_model.drawdown,
            "target_diversification_score": target_model.diversification_score,
            "expected_impact": (
                "The proposed allocation is designed to reduce concentration "
                "and improve diversification. The figures are model-based "
                "estimates, not guaranteed outcomes."
            ),
        }
    )

    return pd.DataFrame(rows), summary
