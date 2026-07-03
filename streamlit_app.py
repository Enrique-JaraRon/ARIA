"""
ARIA - Application Streamlit
"""

import re
import unicodedata
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from app.app_config import (
    DEFAULT_MARKET_DATA_PATH,
    PORTFOLIOS_DIR,
    RISK_HISTORY_PATH,
    ensure_runtime_directories,
    relative_to_project,
    resolve_project_path,
)
from app.aria_workflow import generate_llm_analysis
from app.report_generator import generate_professional_pdf_report, generate_risk_report
from app.ui_components import (
    inject_custom_css,
    render_header,
    render_info_card,
    render_metric_row,
    render_risk_badge,
    render_section_title,
)
from portfolio_engine.demo_portfolios import (
    create_demo_portfolio,
    portfolio_to_dataframe,
)
from portfolio_engine.market_data import ManualMarketDataProvider, get_provider
from portfolio_engine.portfolio import Portfolio
from portfolio_engine.portfolio_analytics import (
    PROFESSIONAL_COLUMNS,
    get_model_portfolio,
    get_model_portfolio_names,
    model_portfolio_to_dataframe,
    portfolio_diagnosis,
    validate_portfolio_coherence,
    validate_portfolio_table,
)
from portfolio_engine.pricing_BS import OptionContract
from risk_engine.anomaly_detector import AnomalyDetector, create_snapshot
from risk_engine.greeks_profile import (
    calculate_greeks_profile,
    greeks_profile_to_dataframe,
)
from risk_engine.hedging_analysis import calculate_delta_hedge
from risk_engine.pnl_profile import (
    calculate_pnl_profile,
    find_breakeven_spots,
    pnl_profile_to_dataframe,
)
from risk_engine.probabilistic_risk import (
    contribution_table,
    probabilistic_metrics_table,
    simulate_probabilistic_risk,
)
from risk_engine.risk_history import RiskHistory
from risk_engine.risk_score import calculate_risk_score
from risk_engine.risk_surface import calculate_risk_surface, surface_to_dataframe
from risk_engine.scenario_analysis import (
    run_historical_scenarios,
    run_scenario,
    run_standard_scenarios,
)
from risk_engine.var_analysis import calculate_var_es, parametric_var_estimate

TRANSPARENT_FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='1' height='1'/%3E"
)

st.set_page_config(
    page_title="ARIA Risk Agent",
    page_icon=TRANSPARENT_FAVICON,
    layout="wide",
)

PORTFOLIO_EDITOR_COLUMNS = [
    "Ticker",
    "Nom",
    "Asset class",
    "Sector",
    "Weight",
    "Value",
    "Currency",
    "Quantity",
    "Price",
    "Data source",
    "Commentaire",
    "Asset type",
]

PORTFOLIO_OPTION_COLUMNS = [
    "Option type",
    "Position",
    "Strike",
    "Maturity",
    "Prime",
    "Volatility",
    "Contract size",
    "Exposition notionnelle",
    "Delta",
    "Objectif option",
]

PORTFOLIO_INTERNAL_COLUMNS = PROFESSIONAL_COLUMNS

DEMO_PORTFOLIO_LABELS = {
    "Conservative Balanced Portfolio": "Portefeuille équilibré prudent",
    "Moderate Growth Portfolio": "Portefeuille croissance modérée",
    "Global Diversified Portfolio": "Portefeuille mondial diversifié",
    "Tech Growth Portfolio": "Portefeuille technologie et IA",
    "Defensive Dividend Portfolio": "Portefeuille dividendes défensifs",
    "Hedged Equity Portfolio": "Portefeuille actions couvert",
    "Low Volatility Portfolio": "Portefeuille faible volatilité",
    "Crisis-Resilient Portfolio": "Portefeuille résilient en crise",
    "ESG Sustainable Portfolio": "Portefeuille ESG durable",
    "AI & Semiconductors Portfolio": "Portefeuille IA et semi-conducteurs",
    "European Quality Portfolio": "Portefeuille actions européennes de qualité",
    "US Blue Chips Portfolio": "Portefeuille grandes capitalisations américaines",
    "Global ETF Core Portfolio": "Portefeuille ETF mondial",
    "Inflation Protection Portfolio": "Portefeuille protection inflation",
    "Long-Term Compounders Portfolio": "Portefeuille long terme compounders",
    "Low Risk Options Portfolio": "Portefeuille options faible risque",
}

CURATED_DEMO_PORTFOLIOS = [
    "Conservative Balanced Portfolio",
    "Global Diversified Portfolio",
    "Tech Growth Portfolio",
    "Low Risk Options Portfolio",
]

ensure_runtime_directories()


CANONICAL_COLUMN_ALIASES = {
    "Quantite": ["Quantite", "Quantité", "QuantitÃ©", "QuantitÃƒÆ’Ã‚Â©"],
    "Maturite": ["Maturite", "Maturité", "MaturitÃ©", "MaturitÃƒÆ’Ã‚Â©"],
    "Volatilite": ["Volatilite", "Volatilité", "VolatilitÃ©", "VolatilitÃƒÂ©"],
    "Weight": ["Weight", "Poids", "Ponderation", "Pondération"],
    "Value": ["Value", "Valeur", "Montant"],
    "Asset class": ["Asset class", "Classe actif", "Classe d'actif"],
    "Data source": ["Data source", "Source", "Source donnees", "Source données"],
    "Commentaire": ["Commentaire", "Justification", "Rationale", "Notes"],
    "Spot stressé": ["Spot stresse", "Spot stressé", "Spot stressÃ©"],
    "Scenario": ["Scenario", "Scénario", "ScÃ©nario"],
    "Resultat": ["Resultat", "Résultat", "RÃ©sultat"],
    "Valeur stressee": ["Valeur stressee", "Valeur stressée", "Valeur stressÃ©e"],
    "Delta stresse": ["Delta stresse", "Delta stressé", "Delta stressÃ©"],
    "Gamma stresse": ["Gamma stresse", "Gamma stressé", "Gamma stressÃ©"],
    "Vega stresse": ["Vega stresse", "Vega stressé", "Vega stressÃ©"],
}


def repair_mojibake(value: str) -> str:
    """Repair common UTF-8 / Windows-1252 mojibake in labels."""
    repaired = str(value)

    for _ in range(3):
        if not any(marker in repaired for marker in ("Ã", "Â", "â")):
            break

        try:
            candidate = repaired.encode("cp1252").decode("utf-8")
        except UnicodeError:
            break

        if candidate == repaired:
            break

        repaired = candidate

    return repaired


def normalize_text_key(value: str) -> str:
    """Return an ASCII-safe version of a label or column name."""
    repaired = repair_mojibake(value)

    return (
        unicodedata.normalize("NFKD", repaired)
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def normalize_dataframe_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe columns to stable ASCII names."""
    normalized = data.copy()
    normalized.columns = [normalize_text_key(column) for column in normalized.columns]

    reverse_aliases = {}

    for canonical_name, aliases in CANONICAL_COLUMN_ALIASES.items():
        reverse_aliases[normalize_text_key(canonical_name)] = canonical_name

        for alias in aliases:
            reverse_aliases[normalize_text_key(alias)] = canonical_name

    normalized = normalized.rename(
        columns={
            column: reverse_aliases.get(column, column)
            for column in normalized.columns
        }
    )

    return normalized


def numeric_series(
    data: pd.DataFrame,
    column: str,
) -> pd.Series:
    """Convert a column to numeric values while preserving missing cells."""

    if column not in data.columns:
        return pd.Series(
            pd.NA,
            index=data.index,
            dtype="Float64",
        )

    return pd.to_numeric(
        data[column],
        errors="coerce",
    )


def merge_visible_portfolio_edits(
    current_table: pd.DataFrame,
    edited_table: pd.DataFrame,
) -> pd.DataFrame:
    """Merge visible editor columns without losing hidden option fields."""

    current = current_table.reset_index(drop=True).copy()
    edited = edited_table.reset_index(drop=True).copy()

    if len(edited) <= len(current):
        merged = current.iloc[: len(edited)].copy()
    else:
        extra_rows = pd.DataFrame(
            index=range(len(edited) - len(current)),
            columns=current.columns,
        )
        merged = pd.concat(
            [
                current,
                extra_rows,
            ],
            ignore_index=True,
        )

    for column in edited.columns:
        merged[column] = edited[column]

    return merged


def sanitize_portfolio_name(
    name: str,
) -> str:
    """Return a safe file stem for a user portfolio name."""

    cleaned = re.sub(
        r"[^A-Za-z0-9_\- ]+",
        "",
        str(name).strip(),
    )
    cleaned = re.sub(
        r"\s+",
        "_",
        cleaned,
    ).strip("_")

    return cleaned or "portefeuille_aria"


def saved_portfolio_files() -> list[Path]:
    """List user-saved portfolio CSV files."""

    PORTFOLIOS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sorted(
        PORTFOLIOS_DIR.glob("*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def portfolio_file_label(
    path: Path,
) -> str:
    """Return a clean display label for a saved portfolio file."""

    return path.stem.replace(
        "_",
        " ",
    )


def row_display_label(
    index: int,
    row: pd.Series,
) -> str:
    """Return a readable label for row actions."""

    ticker = str(row.get("Ticker", "") or "").strip() or "Ticker manquant"
    name = str(row.get("Nom", "") or "").strip() or "Sans nom"
    weight = pd.to_numeric(
        row.get("Weight"),
        errors="coerce",
    )
    weight_label = (
        f"{float(weight):.2f}%"
        if not pd.isna(weight)
        else "poids manquant"
    )

    return f"Ligne {index + 1} - {ticker} - {name} - {weight_label}"


def append_portfolio_row(
    row: dict[str, object],
    current_spot: float,
    current_volatility: float,
) -> None:
    """Append a guided row to the current portfolio table."""

    st.session_state.portfolio_data = normalize_portfolio_table(
        pd.concat(
            [
                st.session_state.portfolio_data,
                pd.DataFrame([row]),
            ],
            ignore_index=True,
        ),
        default_spot_value=current_spot,
        default_volatility_value=current_volatility,
    )

    if "portfolio_editor" in st.session_state:
        del st.session_state["portfolio_editor"]


def delete_portfolio_rows(
    selected_labels: list[str],
) -> None:
    """Delete rows selected through their stable display labels."""

    if not selected_labels:
        return

    label_to_index = {
        row_display_label(index, row): index
        for index, row in st.session_state.portfolio_data.iterrows()
    }
    indices_to_drop = [
        label_to_index[label]
        for label in selected_labels
        if label in label_to_index
    ]

    if not indices_to_drop:
        return

    st.session_state.portfolio_data = st.session_state.portfolio_data.drop(
        index=indices_to_drop,
    ).reset_index(
        drop=True,
    )

    if "portfolio_editor" in st.session_state:
        del st.session_state["portfolio_editor"]


def scale_weights_to_100() -> bool:
    """Scale non-missing portfolio weights to exactly 100%."""

    weights = pd.to_numeric(
        st.session_state.portfolio_data.get("Weight", pd.Series(dtype=float)),
        errors="coerce",
    )
    total_weight = float(
        weights.fillna(0).sum()
    )

    if total_weight <= 0:
        return False

    st.session_state.portfolio_data.loc[:, "Weight"] = (
        weights.fillna(0) / total_weight * 100
    ).round(
        4
    )

    if "portfolio_editor" in st.session_state:
        del st.session_state["portfolio_editor"]

    return True


def default_portfolio() -> pd.DataFrame:
    """Cree le portefeuille affiche au premier lancement."""
    return pd.DataFrame(
        [
            {
                "Asset type": "option",
                "Ticker": "SPY",
                "Instrument": "Option",
                "Sous-jacent": "SPY",
                "Nom": "Calls ATM achetes",
                "Sector": "Index options",
                "Currency": "USD",
                "Quantity": 20,
                "Price": 500.0,
                "Option type": "call",
                "Maturity": 0.25,
                "Volatility": 0.20,
                "Rate": 0.05,
                "Contract size": 100,
                "Type option": "call",
                "Quantite": 20,
                "Multiplicateur": 100,
                "Spot": 500.0,
                "Volatilite": 0.20,
                "Strike": 500.0,
                "Maturite": 0.25,
            },
            {
                "Asset type": "option",
                "Ticker": "SPY",
                "Instrument": "Option",
                "Sous-jacent": "SPY",
                "Nom": "Puts vendus",
                "Sector": "Index options",
                "Currency": "USD",
                "Quantity": -10,
                "Price": 500.0,
                "Option type": "put",
                "Maturity": 0.25,
                "Volatility": 0.20,
                "Rate": 0.05,
                "Contract size": 100,
                "Type option": "put",
                "Quantite": -10,
                "Multiplicateur": 100,
                "Spot": 500.0,
                "Volatilite": 0.20,
                "Strike": 470.0,
                "Maturite": 0.25,
            },
            {
                "Asset type": "stock",
                "Ticker": "SPY",
                "Instrument": "Action",
                "Sous-jacent": "SPY",
                "Nom": "Couverture en actions",
                "Sector": "US equities",
                "Currency": "USD",
                "Quantity": -5,
                "Price": 500.0,
                "Option type": "",
                "Strike": None,
                "Maturity": None,
                "Volatility": None,
                "Rate": None,
                "Contract size": 1,
                "Type option": "",
                "Quantite": -5,
                "Multiplicateur": 1,
                "Spot": 500.0,
                "Volatilite": None,
                "Maturite": None,
            },
        ]
    )


def normalize_portfolio_table(
    table: pd.DataFrame,
    default_spot_value: float,
    default_volatility_value: float,
) -> pd.DataFrame:
    """Ensure portfolio tables have the professional multi-underlying schema."""
    normalized = normalize_dataframe_columns(table)
    normalized = normalized.dropna(
        how="all",
    ).copy()

    quantity_columns = [
        column
        for column in normalized.columns
        if column.startswith("Quantit")
    ]

    maturity_columns = [
        column
        for column in normalized.columns
        if column.startswith("Maturit")
    ]

    if "Quantite" not in normalized.columns:
        normalized["Quantite"] = (
            normalized[quantity_columns[0]]
            if quantity_columns
            else 1
        )

    if "Maturite" not in normalized.columns:
        normalized["Maturite"] = (
            normalized[maturity_columns[0]]
            if maturity_columns
            else 0.25
        )

    alias_columns = [
        column
        for column in quantity_columns + maturity_columns
        if column not in {"Quantite", "Maturite"}
    ]

    normalized = normalized.drop(
        columns=alias_columns,
        errors="ignore",
    )

    defaults = {
        "Asset type": "stock",
        "Asset class": pd.NA,
        "Ticker": pd.NA,
        "Sous-jacent": pd.NA,
        "Nom": pd.NA,
        "Sector": "Non classé",
        "Currency": "USD",
        "Weight": pd.NA,
        "Value": pd.NA,
        "Spot": default_spot_value,
        "Price": default_spot_value,
        "Data source": "Manuel",
        "Commentaire": pd.NA,
        "Strike": pd.NA,
        "Option type": pd.NA,
        "Type option": pd.NA,
        "Volatilite": default_volatility_value,
        "Volatility": default_volatility_value,
        "Rate": 0.05,
        "Contract size": 1,
        "Quantite": pd.NA,
        "Quantity": pd.NA,
        "Multiplicateur": 1,
        "Maturite": 0.25,
        "Maturity": 0.25,
        "Instrument": "Action",
    }

    normalized = normalized.replace(
        {
            "": pd.NA,
            " ": pd.NA,
        }
    )

    meaningful_columns = [
        column
        for column in [
            "Ticker",
            "Sous-jacent",
            "Nom",
            "Weight",
            "Value",
            "Quantity",
            "Quantite",
            "Price",
            "Spot",
            "Option type",
            "Strike",
        ]
        if column in normalized.columns
    ]
    if meaningful_columns:
        normalized = normalized.loc[
            ~normalized[meaningful_columns].isna().all(axis=1)
        ].copy()

    for column, value in defaults.items():
        if column not in normalized.columns:
            normalized[column] = value

    normalized["Ticker"] = normalized["Ticker"].fillna(
        normalized["Sous-jacent"]
    )
    normalized["Sous-jacent"] = normalized["Sous-jacent"].fillna(
        normalized["Ticker"]
    )
    normalized["Nom"] = normalized["Nom"].fillna(normalized["Ticker"])
    normalized["Sector"] = normalized["Sector"].fillna("Non classé")
    normalized["Currency"] = normalized["Currency"].fillna("USD")
    normalized["Data source"] = normalized["Data source"].fillna("Manuel")
    normalized["Commentaire"] = normalized["Commentaire"].fillna("")

    normalized["Asset type"] = normalized.apply(
        lambda row: "option"
        if str(row.get("Instrument", "")).strip().lower() == "option"
        or str(row.get("Asset type", "")).strip().lower() == "option"
        else "stock",
        axis=1,
    )
    normalized["Instrument"] = normalized["Asset type"].apply(
        lambda value: "Option"
        if str(value).strip().lower() == "option"
        else "Action"
    )
    normalized["Asset class"] = normalized["Asset class"].fillna(
        normalized["Asset type"].map(
            {
                "stock": "Action / ETF",
                "option": "Option",
            }
        )
    )
    normalized["Quantity"] = normalized["Quantity"].fillna(
        normalized["Quantite"]
    )
    normalized["Quantite"] = normalized["Quantity"]
    normalized["Price"] = normalized["Price"].fillna(
        normalized["Spot"]
    )
    normalized["Spot"] = normalized["Price"]
    normalized["Option type"] = normalized["Option type"].fillna(
        normalized["Type option"]
    )
    normalized["Type option"] = normalized["Option type"]
    normalized["Volatility"] = normalized["Volatility"].fillna(
        normalized["Volatilite"]
    )
    normalized["Volatilite"] = normalized["Volatility"]
    normalized["Maturity"] = normalized["Maturity"].fillna(
        normalized["Maturite"]
    )
    normalized["Maturite"] = normalized["Maturity"]
    normalized["Contract size"] = normalized["Contract size"].fillna(
        normalized["Multiplicateur"]
    )
    normalized["Multiplicateur"] = normalized["Contract size"]

    normalized["Price"] = numeric_series(normalized, "Price").fillna(
        default_spot_value
    )
    normalized["Spot"] = normalized["Price"]
    normalized["Weight"] = numeric_series(normalized, "Weight")
    normalized["Value"] = numeric_series(normalized, "Value")
    normalized["Quantity"] = numeric_series(normalized, "Quantity")
    normalized["Quantite"] = numeric_series(normalized, "Quantite")

    option_mask = normalized["Asset type"].astype(str).str.lower().eq("option")
    stock_mask = ~option_mask

    normalized.loc[stock_mask, ["Option type", "Type option"]] = pd.NA
    normalized.loc[stock_mask, ["Strike", "Maturity", "Maturite"]] = pd.NA
    normalized.loc[stock_mask, ["Volatility", "Volatilite", "Rate"]] = pd.NA
    normalized.loc[stock_mask, ["Contract size", "Multiplicateur"]] = 1

    normalized.loc[option_mask, "Option type"] = normalized.loc[
        option_mask,
        "Option type",
    ].fillna("call")
    normalized.loc[option_mask, "Type option"] = normalized.loc[
        option_mask,
        "Option type",
    ]
    normalized.loc[option_mask, "Strike"] = normalized.loc[
        option_mask,
        "Strike",
    ].fillna(normalized.loc[option_mask, "Price"])
    normalized.loc[option_mask, "Volatility"] = normalized.loc[
        option_mask,
        "Volatility",
    ].fillna(default_volatility_value)
    normalized.loc[option_mask, "Volatilite"] = normalized.loc[
        option_mask,
        "Volatility",
    ]
    normalized.loc[option_mask, "Maturity"] = normalized.loc[
        option_mask,
        "Maturity",
    ].fillna(0.25)
    normalized.loc[option_mask, "Maturite"] = normalized.loc[
        option_mask,
        "Maturity",
    ]
    normalized.loc[option_mask, "Rate"] = normalized.loc[
        option_mask,
        "Rate",
    ].fillna(0.05)
    normalized.loc[option_mask, "Contract size"] = normalized.loc[
        option_mask,
        "Contract size",
    ].fillna(100)
    normalized.loc[option_mask, "Multiplicateur"] = normalized.loc[
        option_mask,
        "Contract size",
    ]

    value_mask = normalized["Value"].notna()
    weight_mask = normalized["Weight"].notna()
    price_positive = normalized["Price"].fillna(0) > 0

    total_value_basis = float(normalized.loc[value_mask, "Value"].abs().sum())
    if total_value_basis <= 0:
        total_value_basis = 100_000.0

    normalized.loc[~value_mask & weight_mask, "Value"] = (
        normalized.loc[~value_mask & weight_mask, "Weight"]
        / 100
        * total_value_basis
    )

    quantity_missing = normalized["Quantity"].isna()
    normalized.loc[quantity_missing & normalized["Value"].notna() & price_positive, "Quantity"] = (
        normalized.loc[quantity_missing & normalized["Value"].notna() & price_positive, "Value"]
        / normalized.loc[quantity_missing & normalized["Value"].notna() & price_positive, "Price"]
    )

    quantity_missing = normalized["Quantity"].isna()
    normalized.loc[quantity_missing & normalized["Quantite"].notna(), "Quantity"] = (
        normalized.loc[quantity_missing & normalized["Quantite"].notna(), "Quantite"]
    )
    normalized["Quantity"] = normalized["Quantity"].fillna(0.0)
    normalized["Quantite"] = normalized["Quantity"]

    value_missing = normalized["Value"].isna()
    normalized.loc[value_missing, "Value"] = (
        normalized.loc[value_missing, "Quantity"]
        * normalized.loc[value_missing, "Price"]
    )

    weight_missing = normalized["Weight"].isna()
    gross_value = float(normalized["Value"].abs().sum())
    if gross_value > 0:
        normalized.loc[weight_missing, "Weight"] = (
            normalized.loc[weight_missing, "Value"].abs()
            / gross_value
            * 100
        )

    desired_columns = PORTFOLIO_INTERNAL_COLUMNS

    existing_columns = [
        column
        for column in desired_columns
        if column in normalized.columns
    ]

    other_columns = [
        column
        for column in normalized.columns
        if column not in existing_columns
    ]

    return normalized[existing_columns + other_columns]


def build_portfolio_from_table(
    portfolio_table: pd.DataFrame,
    spot: float,
    rate: float,
    volatility: float,
    dividend: float,
) -> Portfolio:
    """Transforme le tableau de l'application en portefeuille Python."""

    portfolio_table = normalize_dataframe_columns(portfolio_table)

    def row_value(row, *names, default=None):
        for name in names:
            normalized_name = normalize_text_key(name)
            value = row.get(normalized_name)

            if value is not None and not pd.isna(value):
                return value

        return default

    portfolio = Portfolio(name="Portefeuille ARIA")

    for index, row in portfolio_table.iterrows():
        asset_type = str(
            row_value(row, "Asset type", "Instrument", default="stock")
        ).strip().lower()
        instrument = "Option" if asset_type == "option" else "Action"
        quantity_value = row_value(row, "Quantity", "Quantite")

        if pd.isna(instrument) or pd.isna(quantity_value):
            continue

        quantity = int(quantity_value)

        if quantity == 0:
            continue

        name = row.get("Nom")

        if pd.isna(name) or not str(name).strip():
            name = f"Position {index + 1}"

        underlying = str(
            row_value(
                row,
                "Ticker",
                "Sous-jacent",
                "Underlying",
                default="SPY",
            )
        ).strip() or "SPY"

        row_spot = float(row_value(row, "Price", "Spot", default=spot))
        row_volatility = float(
            row_value(row, "Volatility", "Volatilite", default=volatility)
        )

        if instrument == "Action":
            portfolio.add_stock(
                spot=row_spot,
                quantity=quantity,
                name=str(name),
                underlying=underlying,
            )

        elif instrument == "Option":
            option_type = row_value(row, "Option type", "Type option")
            strike = row.get("Strike")
            maturity = row_value(row, "Maturity", "Maturite")
            multiplier_value = row_value(row, "Contract size", "Multiplicateur")
            option_rate = float(row_value(row, "Rate", default=rate))

            if pd.isna(option_type):
                raise ValueError(
                    f"Le type d'option manque a la ligne {index + 1}."
                )

            if pd.isna(strike) or float(strike) <= 0:
                raise ValueError(
                    f"Le strike est invalide a la ligne {index + 1}."
                )

            if pd.isna(maturity) or float(maturity) <= 0:
                raise ValueError(
                    f"La maturite est invalide a la ligne {index + 1}."
                )

            if pd.isna(multiplier_value):
                multiplier = 1
            else:
                multiplier = int(multiplier_value)

            if multiplier <= 0:
                raise ValueError(
                    f"Le multiplicateur est invalide a la ligne {index + 1}."
                )

            contract = OptionContract(
                S=row_spot,
                K=float(strike),
                T=float(maturity),
                r=option_rate,
                sigma=row_volatility,
                option_type=str(option_type),
                q=dividend,
            )

            portfolio.add_option(
                contract=contract,
                quantity=quantity,
                multiplier=multiplier,
                name=str(name),
                underlying=underlying,
            )

        else:
            raise ValueError(f"Instrument inconnu a la ligne {index + 1}.")

    if not portfolio.positions:
        raise ValueError("Le portefeuille doit contenir au moins une position.")

    return portfolio


def create_stress_chart(
    scenario_results,
    language: str = "fr",
) -> alt.Chart:
    """Cree un graphique des profits et pertes par scenario."""
    is_french = language == "fr"
    loss_label = "Perte" if is_french else "Loss"
    pnl_title = "Profit / Perte" if is_french else "Profit / Loss"
    full_data = pd.DataFrame(
        [
            {
                "Scenario": display_scenario_name(
                    result.name,
                    language,
                ),
                "Profit / Perte": result.profit_and_loss,
                "Resultat": "Gain" if result.profit_and_loss >= 0 else loss_label,
            }
            for result in scenario_results
        ]
    )
    losses = full_data.nsmallest(
        6,
        "Profit / Perte",
    )
    gains = full_data.nlargest(
        3,
        "Profit / Perte",
    )
    chart_data = (
        pd.concat(
            [
                losses,
                gains,
            ],
            ignore_index=True,
        )
        .drop_duplicates("Scenario")
        .sort_values("Profit / Perte")
    )
    max_abs_impact = max(
        float(chart_data["Profit / Perte"].abs().max()),
        1.0,
    )
    chart_data["Scenario court"] = chart_data["Scenario"].str.replace(
        "Crise financière mondiale 2008",
        "Crise 2008",
        regex=False,
    )
    chart_data["Scenario court"] = chart_data["Scenario court"].str.replace(
        "Crise japonaise / yen carry trade",
        "Yen carry",
        regex=False,
    )
    chart_data["Scenario court"] = chart_data["Scenario court"].str.slice(0, 32)
    chart_data["Zero"] = 0.0

    stems = alt.Chart(chart_data).mark_rule(
        strokeWidth=2.5,
        opacity=0.85,
    ).encode(
        y=alt.Y(
            "Scenario court:N",
            sort=alt.SortField(
                field="Profit / Perte",
                order="ascending",
            ),
            title=None,
        ),
        x=alt.X(
            "Profit / Perte:Q",
            title=(
                "Profit / Perte du portefeuille"
                if is_french
                else "Portfolio Profit / Loss"
            ),
            stack=False,
            scale=alt.Scale(
                domain=[
                    -max_abs_impact * 1.12,
                    max_abs_impact * 1.08,
                ],
                nice=False,
            ),
        ),
        x2="Zero:Q",
        color=alt.Color(
            "Resultat:N",
            scale=alt.Scale(
                domain=["Gain", loss_label],
                range=["#19A974", "#E05252"],
            ),
            legend=alt.Legend(
                title=None,
                orient="top",
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "Scenario:N",
                title="Scénario" if is_french else "Scenario",
            ),
            alt.Tooltip(
                "Profit / Perte:Q",
                title=pnl_title,
                format=",.2f",
            ),
        ],
    )

    points = alt.Chart(chart_data).mark_circle(
        size=150,
        stroke="#FFFFFF",
        strokeWidth=1.5,
    ).encode(
        y=alt.Y(
            "Scenario court:N",
            sort=alt.SortField(
                field="Profit / Perte",
                order="ascending",
            ),
            title=None,
        ),
        x=alt.X(
            "Profit / Perte:Q",
            stack=False,
            scale=alt.Scale(
                domain=[
                    -max_abs_impact * 1.12,
                    max_abs_impact * 1.08,
                ],
                nice=False,
            ),
        ),
        color=alt.Color(
            "Resultat:N",
            scale=alt.Scale(
                domain=["Gain", loss_label],
                range=["#19A974", "#E05252"],
            ),
            legend=alt.Legend(
                title=None,
                orient="top",
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "Scenario:N",
                title="Scénario" if is_french else "Scenario",
            ),
            alt.Tooltip(
                "Profit / Perte:Q",
                title=pnl_title,
                format=",.2f",
            ),
        ],
    )

    zero_line = alt.Chart(
        pd.DataFrame({"x": [0]})
    ).mark_rule(
        color="#6B7280",
        strokeWidth=1.5,
    ).encode(
        x="x:Q",
    )

    loss_labels = alt.Chart(
        chart_data[chart_data["Profit / Perte"] < 0]
    ).mark_text(
        baseline="middle",
        fontSize=12,
        fontWeight="bold",
        dx=12,
        align="left",
    ).encode(
        y=alt.Y(
            "Scenario court:N",
            sort=alt.SortField(
                field="Profit / Perte",
                order="ascending",
            ),
        ),
        x=alt.X("Profit / Perte:Q", stack=False),
        text=alt.Text("Profit / Perte:Q", format=",.0f"),
        color=alt.value("#172033"),
    )

    gain_labels = alt.Chart(
        chart_data[chart_data["Profit / Perte"] >= 0]
    ).mark_text(
        baseline="middle",
        fontSize=12,
        fontWeight="bold",
        dx=10,
        align="left",
    ).encode(
        y=alt.Y(
            "Scenario court:N",
            sort=alt.SortField(
                field="Profit / Perte",
                order="ascending",
            ),
        ),
        x=alt.X("Profit / Perte:Q", stack=False),
        text=alt.Text("Profit / Perte:Q", format=",.0f"),
        color=alt.value("#172033"),
    )

    return (
        stems
        + zero_line
        + points
        + loss_labels
        + gain_labels
    ).properties(
        height=max(340, len(chart_data) * 42),
        title=alt.TitleParams(
            text=(
                "P&L par scénario de stress"
                if is_french
                else "Stress Scenario P&L"
            ),
            subtitle=(
                "Pires pertes et meilleurs gains, triés du plus défavorable au plus favorable."
                if is_french
                else "Worst losses and best gains, sorted from most adverse to most favorable."
            ),
            fontSize=20,
            subtitleFontSize=13,
            anchor="start",
            offset=20,
        ),
    ).configure_view(
        strokeWidth=0,
    ).configure_axis(
        labelColor="#475569",
        titleColor="#334155",
        gridColor="rgba(100, 116, 139, 0.18)",
        domainColor="rgba(0, 213, 255, 0.28)",
    ).configure_title(
        color="#172033",
        subtitleColor="#64748B",
    ).configure_legend(
        labelColor="#475569",
        titleColor="#334155",
    ).configure(
        background="transparent",
    )


def create_probabilistic_distribution_chart(
    simulations_data: pd.DataFrame,
    selected_var: float,
    selected_es: float,
    language: str = "fr",
) -> alt.Chart:
    """Create the Monte Carlo return distribution chart."""

    is_french = language == "fr"
    chart_data = simulations_data.copy()
    chart_data["ReturnPct"] = chart_data["Portfolio return"] * 100
    selected_var_percent = selected_var * 100
    selected_es_percent = selected_es * 100
    mean_return_percent = float(chart_data["ReturnPct"].mean())

    histogram = alt.Chart(chart_data).mark_bar(
        opacity=0.82,
    ).encode(
        x=alt.X(
            "ReturnPct:Q",
            bin=alt.Bin(maxbins=55),
            title=(
                "Rendement simulé du portefeuille (%)"
                if is_french
                else "Simulated portfolio return (%)"
            ),
        ),
        y=alt.Y(
            "count():Q",
            title="Nombre de simulations" if is_french else "Number of simulations",
        ),
        color=alt.condition(
            alt.datum.ReturnPct <= selected_var_percent,
            alt.value("#B91C1C"),
            alt.value("#155E75"),
        ),
        tooltip=[
            alt.Tooltip("count():Q", title="Simulations"),
        ],
    )

    thresholds = pd.DataFrame(
        [
            {
                "Threshold": "VaR",
                "Return": selected_var_percent,
            },
            {
                "Threshold": "Expected Shortfall",
                "Return": selected_es_percent,
            },
            {
                "Threshold": "Moyenne" if is_french else "Mean",
                "Return": mean_return_percent,
            },
        ]
    )

    rules = alt.Chart(thresholds).mark_rule(
        strokeWidth=2.5,
    ).encode(
        x="Return:Q",
        color=alt.Color(
            "Threshold:N",
            scale=alt.Scale(
                domain=[
                    "VaR",
                    "Expected Shortfall",
                    "Moyenne" if is_french else "Mean",
                ],
                range=[
                    "#B91C1C",
                    "#7C2D12",
                    "#0F766E",
                ],
            ),
            legend=alt.Legend(
                title=None,
                orient="top",
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "Threshold:N",
                title="Seuil" if is_french else "Threshold",
            ),
            alt.Tooltip(
                "Return:Q",
                title="Rendement" if is_french else "Return",
                format=".2f",
            ),
        ],
    )

    return (
        histogram + rules
    ).properties(
        height=340,
        title=alt.TitleParams(
            text=(
                "Distribution Monte Carlo des rendements"
                if is_french
                else "Monte Carlo Return Distribution"
            ),
            subtitle=(
                "La zone rouge correspond à la queue de perte au-delà de la VaR sélectionnée."
                if is_french
                else "The red area is the loss tail beyond the selected VaR."
            ),
            fontSize=20,
            subtitleFontSize=13,
            anchor="start",
            offset=18,
        ),
    ).configure_view(
        strokeWidth=0,
    ).configure_axis(
        labelColor="#475569",
        titleColor="#334155",
        gridColor="rgba(100, 116, 139, 0.18)",
    ).configure_title(
        color="#172033",
        subtitleColor="#64748B",
    ).configure_legend(
        labelColor="#475569",
        titleColor="#334155",
    ).configure(
        background="transparent",
    )


def create_var_distribution_chart(
    simulations_data: pd.DataFrame,
    var_amount: float,
    expected_shortfall: float,
) -> alt.Chart:
    """Cree un histogramme des pertes simulees."""
    chart_data = simulations_data.copy()

    histogram = alt.Chart(chart_data).mark_bar(
        opacity=0.75,
    ).encode(
        x=alt.X(
            "Perte:Q",
            bin=alt.Bin(maxbins=50),
            title="Perte simulee",
        ),
        y=alt.Y(
            "count():Q",
            title="Nombre de simulations",
        ),
        tooltip=[
            alt.Tooltip("count():Q", title="Nombre de simulations"),
        ],
    )

    var_line = alt.Chart(
        pd.DataFrame(
            {
                "x": [var_amount],
                "Label": ["VaR"],
            }
        )
    ).mark_rule(
        color="#E05252",
        strokeWidth=3,
    ).encode(
        x="x:Q",
    )

    es_line = alt.Chart(
        pd.DataFrame(
            {
                "x": [expected_shortfall],
                "Label": ["Expected Shortfall"],
            }
        )
    ).mark_rule(
        color="#7C3AED",
        strokeWidth=3,
        strokeDash=[6, 4],
    ).encode(
        x="x:Q",
    )

    return (
        histogram
        + var_line
        + es_line
    ).properties(
        height=380,
        title=alt.TitleParams(
            text="Distribution des pertes simulees",
            subtitle="Ligne rouge : VaR - ligne violette : Expected Shortfall",
            fontSize=20,
            subtitleFontSize=13,
            anchor="start",
            offset=20,
        ),
    ).configure_view(
        strokeWidth=0,
    ).configure_axis(
        labelColor="#475569",
        titleColor="#334155",
        gridColor="rgba(100, 116, 139, 0.18)",
        domainColor="rgba(0, 213, 255, 0.28)",
    ).configure_title(
        color="#172033",
        subtitleColor="#64748B",
    ).configure(
        background="transparent",
    )


def create_stress_matrix_chart(
    surface_data: pd.DataFrame,
    language: str = "fr",
) -> alt.Chart:
    """Cree une matrice rouge-vert des P&L spot / volatilite."""

    is_french = language == "fr"
    matrix_data = surface_data.copy()
    matrix_data["Choc spot"] = matrix_data["Variation spot"].map(
        lambda value: f"{value:+.0%}"
    )
    matrix_data["Choc volatilite"] = matrix_data["Variation volatilité"].map(
        lambda value: f"{value:+.0%}"
    )
    matrix_data["P&L"] = matrix_data["Profit / Perte"].map(
        lambda value: f"{value:,.0f}"
    )
    max_abs_pnl = max(
        float(matrix_data["Profit / Perte"].abs().max()),
        1.0,
    )

    base = alt.Chart(matrix_data).encode(
        x=alt.X(
            "Choc spot:N",
            title="Choc spot" if is_french else "Spot shock",
            sort=[
                "-15%",
                "-8%",
                "+0%",
                "+8%",
                "+15%",
            ],
            axis=alt.Axis(labelAngle=0),
        ),
        y=alt.Y(
            "Choc volatilite:N",
            title="Choc volatilité" if is_french else "Volatility shock",
            sort=[
                "+20%",
                "+10%",
                "+0%",
                "-10%",
            ],
        ),
    )

    heatmap = base.mark_rect(
        cornerRadius=4,
    ).encode(
        color=alt.Color(
            "Profit / Perte:Q",
            title="P&L estimé" if is_french else "Estimated P&L",
            scale=alt.Scale(
                domain=[
                    -max_abs_pnl,
                    0,
                    max_abs_pnl,
                ],
                range=[
                    "#B91C1C",
                    "#FFF7CC",
                    "#047857",
                ],
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "Choc spot:N",
                title="Choc spot" if is_french else "Spot shock",
            ),
            alt.Tooltip(
                "Choc volatilite:N",
                title="Choc volatilité" if is_french else "Volatility shock",
            ),
            alt.Tooltip(
                "Profit / Perte:Q",
                title="Profit / Perte" if is_french else "Profit / Loss",
                format=",.2f",
            ),
        ],
    )

    labels = base.mark_text(
        fontSize=12,
        fontWeight="bold",
    ).encode(
        text="P&L:N",
        color=alt.condition(
            f"abs(datum['Profit / Perte']) > {max_abs_pnl * 0.62}",
            alt.value("#FFFFFF"),
            alt.value("#172033"),
        ),
    )

    return (heatmap + labels).properties(
        height=310,
        title=alt.TitleParams(
            text=(
                "Matrice P&L Spot / Volatilité"
                if is_french
                else "Spot / Volatility P&L Matrix"
            ),
            subtitle=(
                "Chaque cellule affiche le P&L estimé pour un choc spot-volatilité."
                if is_french
                else "Each cell shows the estimated P&L for a spot-volatility shock."
            ),
            fontSize=20,
            subtitleFontSize=13,
            anchor="start",
            offset=20,
        ),
    ).configure_view(
        strokeWidth=0,
    ).configure_axis(
        labelColor="#475569",
        titleColor="#334155",
        grid=False,
    ).configure_title(
        color="#172033",
        subtitleColor="#64748B",
    ).configure(
        background="transparent",
    )


def create_pnl_profile_chart(
    pnl_data: pd.DataFrame,
    current_spot: float,
    breakeven_spots: list[float],
) -> alt.Chart:
    """Cree une courbe de P&L selon le spot."""

    chart_data = normalize_dataframe_columns(pnl_data)
    chart_data["Resultat"] = chart_data["Profit / Perte"].apply(
        lambda value: "Gain" if value >= 0 else "Perte"
    )

    line = alt.Chart(chart_data).mark_line(
        strokeWidth=3,
        color="#155E75",
    ).encode(
        x=alt.X("Spot stressé:Q", title="Spot"),
        y=alt.Y("Profit / Perte:Q", title="Profit / Perte"),
        tooltip=[
            alt.Tooltip("Spot stressé:Q", title="Spot", format=",.2f"),
            alt.Tooltip("Variation spot:Q", title="Variation", format="+.1%"),
            alt.Tooltip("Profit / Perte:Q", title="P&L", format=",.2f"),
        ],
    )

    zero_line = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        color="#64748B",
        strokeDash=[6, 4],
    ).encode(y="y:Q")

    spot_line = alt.Chart(pd.DataFrame({"x": [current_spot]})).mark_rule(
        color="#111827",
        strokeWidth=2,
    ).encode(x="x:Q")

    breakeven_lines = alt.Chart(pd.DataFrame({"x": breakeven_spots})).mark_rule(
        color="#B45309",
        strokeDash=[4, 4],
        strokeWidth=2,
    ).encode(x="x:Q")

    return (
        line + zero_line + spot_line + breakeven_lines
    ).properties(
        height=360,
        title=alt.TitleParams(
            text="Evolution du P&L selon le spot",
            subtitle="Ligne noire : spot actuel - lignes orange : points morts",
            fontSize=20,
            subtitleFontSize=13,
            anchor="start",
            offset=18,
        ),
    ).configure_view(strokeWidth=0).configure_axis(
        labelColor="#475569",
        titleColor="#334155",
        gridColor="rgba(100, 116, 139, 0.18)",
    ).configure_title(
        color="#172033",
        subtitleColor="#64748B",
    ).configure(background="transparent")


def create_greeks_profile_chart(
    greeks_data: pd.DataFrame,
    current_spot: float,
    selected_greeks: list[str],
) -> alt.Chart:
    """Cree une courbe des Greeks selon le spot."""

    chart_data = normalize_dataframe_columns(greeks_data)
    long_data = chart_data[
        ["Spot stressé", "Variation spot", *selected_greeks]
    ].melt(
        id_vars=["Spot stressé", "Variation spot"],
        value_vars=selected_greeks,
        var_name="Greek",
        value_name="Valeur",
    )

    lines = alt.Chart(long_data).mark_line(strokeWidth=3).encode(
        x=alt.X("Spot stressé:Q", title="Spot"),
        y=alt.Y("Valeur:Q", title="Valeur"),
        color=alt.Color("Greek:N", legend=alt.Legend(title=None, orient="top")),
        tooltip=[
            alt.Tooltip("Greek:N", title="Greek"),
            alt.Tooltip("Spot stressé:Q", title="Spot", format=",.2f"),
            alt.Tooltip("Variation spot:Q", title="Variation", format="+.1%"),
            alt.Tooltip("Valeur:Q", title="Valeur", format=",.4f"),
        ],
    )

    spot_line = alt.Chart(pd.DataFrame({"x": [current_spot]})).mark_rule(
        color="#111827",
        strokeWidth=2,
    ).encode(x="x:Q")

    return (lines + spot_line).properties(
        height=360,
        title=alt.TitleParams(
            text="Evolution des Greeks selon le spot",
            subtitle="La ligne noire indique le spot actuel",
            fontSize=20,
            subtitleFontSize=13,
            anchor="start",
            offset=18,
        ),
    ).configure_view(strokeWidth=0).configure_axis(
        labelColor="#475569",
        titleColor="#334155",
        gridColor="rgba(100, 116, 139, 0.18)",
    ).configure_title(
        color="#172033",
        subtitleColor="#64748B",
    ).configure_legend(
        labelColor="#475569",
        titleColor="#334155",
    ).configure(background="transparent")


inject_custom_css()

query_language = str(
    st.query_params.get(
        "lang",
        "fr",
    )
).lower()
default_language_index = 1 if query_language.startswith("en") else 0

language_choice = st.sidebar.radio(
    "Langue / Language",
    options=[
        "Français",
        "English",
    ],
    index=default_language_index,
    horizontal=True,
)
ui_language = "en" if language_choice == "English" else "fr"


def tr(
    french: str,
    english: str
) -> str:
    """Return the UI label in the selected language."""

    return english if ui_language == "en" else french


SCENARIO_TRANSLATIONS = {
    "2008 Global Financial Crisis": {
        "fr": "Crise financière mondiale 2008",
        "en": "2008 Global Financial Crisis",
    },
    "Covid Liquidity Shock": {
        "fr": "Choc de liquidité Covid",
        "en": "Covid Liquidity Shock",
    },
    "Japan / Yen Carry Unwind": {
        "fr": "Crise japonaise / yen carry trade",
        "en": "Japan / Yen Carry Unwind",
    },
    "Inflation Shock": {
        "fr": "Choc inflationniste",
        "en": "Inflation Shock",
    },
    "Rates Shock": {
        "fr": "Choc de taux",
        "en": "Rates Shock",
    },
    "Tech Sell-off": {
        "fr": "Vente massive sur la tech",
        "en": "Tech Sell-off",
    },
    "Volatility Spike": {
        "fr": "Pic de volatilité",
        "en": "Volatility Spike",
    },
    "Sovereign / Banking Stress": {
        "fr": "Stress souverain / bancaire",
        "en": "Sovereign / Banking Stress",
    },
    "Hausse modérée": {
        "fr": "Hausse modérée",
        "en": "Moderate Rally",
    },
    "Stress de marché": {
        "fr": "Stress de marché",
        "en": "Market Stress",
    },
    "Scenario personnalise": {
        "fr": "Scénario personnalisé",
        "en": "Custom Scenario",
    },
}

RISK_LABEL_TRANSLATIONS = {
    "Risque faible": "Low risk",
    "Risque modéré": "Moderate risk",
    "Risque eleve": "High risk",
    "Risque élevé": "High risk",
    "Risque très élevé": "Very high risk",
    "Risque critique": "Critical risk",
}


def display_scenario_name(
    name: str,
    language: str | None = None,
) -> str:
    """Return a localized scenario label without touching engine objects."""

    selected_language = language or ui_language
    return SCENARIO_TRANSLATIONS.get(
        str(name),
        {},
    ).get(
        selected_language,
        str(name),
    )


def display_risk_label(
    label: str,
    language: str | None = None,
) -> str:
    """Return a localized risk label for UI and reports."""

    selected_language = language or ui_language
    if selected_language == "en":
        return RISK_LABEL_TRANSLATIONS.get(
            str(label),
            str(label),
        )

    return str(label)


def display_risk_explanation(
    score: int,
    explanation: str,
    language: str | None = None,
) -> str:
    """Return a localized risk explanation."""

    selected_language = language or ui_language
    if selected_language == "fr":
        return explanation

    if score >= 80:
        return "The portfolio combines important concentration, stress losses or sensitivities."
    if score >= 60:
        return "The portfolio carries material risk and should be monitored before increasing exposure."
    if score >= 30:
        return "The portfolio has moderate risk and remains usable with active monitoring."
    return "The portfolio risk appears contained under the selected assumptions."


def display_validation_message(
    message: str,
    language: str | None = None,
) -> str:
    """Translate the most common portfolio validation messages."""

    selected_language = language or ui_language
    if selected_language == "fr":
        return message

    translated = str(message)
    line_match = re.match(
        r"Ligne (\d+) : (.*)",
        translated,
    )
    line_prefix = ""
    if line_match:
        line_prefix = f"Row {line_match.group(1)}: "
        translated = line_match.group(2)

    replacements = {
        "type d'actif manquant.": "missing asset type.",
        "ticker ou sous-jacent manquant.": "missing ticker or underlying.",
        "ticker manquant.": "missing ticker.",
        "quantité manquante.": "missing quantity.",
        "prix ou spot invalide.": "invalid price or spot.",
        "type d'actif invalide.": "invalid asset type.",
        "le type d'option doit être call ou put.": "option type must be call or put.",
        "strike obligatoire pour une option.": "strike is required for an option.",
        "maturité obligatoire pour une option.": "maturity is required for an option.",
        "volatilité obligatoire pour une option.": "volatility is required for an option.",
        "taux requis pour une option.": "rate is required for an option.",
        "nom de l'actif manquant.": "missing asset name.",
        "classe d'actif manquante.": "missing asset class.",
        "secteur manquant, classé par défaut.": "missing sector, classified by default.",
        "devise manquante.": "missing currency.",
        "prix invalide.": "invalid price.",
        "valeur manquante ou nulle.": "missing or zero value.",
        "position vendeuse détectée, valeur de marché négative.": "short position detected, negative market value.",
        "poids manquant ou négatif.": "missing or negative weight.",
        "Le portefeuille est vide.": "The portfolio is empty.",
    }
    for french_text, english_text in replacements.items():
        translated = translated.replace(
            french_text,
            english_text,
        )

    translated = re.sub(
        r"Actifs en double à fusionner :",
        "Duplicate assets to merge:",
        translated,
    )
    translated = re.sub(
        r"La somme des poids doit être égale à 100 %\. Total actuel : ([0-9.,]+) %\.",
        r"Total weight must equal 100%. Current total: \1%.",
        translated,
    )

    return line_prefix + translated


def display_probabilistic_interpretation(
    probabilistic_result,
    language: str | None = None,
) -> str:
    """Return a localized Monte Carlo interpretation for the UI."""

    selected_language = language or ui_language
    if selected_language == "fr":
        return probabilistic_result.interpretation

    return (
        "Monte Carlo read: under the selected assumptions, the portfolio has "
        f"an estimated probability of loss of "
        f"{probabilistic_result.probability_of_loss:.1%}. "
        f"The 95% VaR is {probabilistic_result.var_95:.1%}: 95% of simulated "
        "scenarios perform better than this threshold over the selected "
        f"horizon. The 95% Expected Shortfall is "
        f"{probabilistic_result.expected_shortfall_95:.1%}: in the worst 5% "
        "of simulated scenarios, the average loss is close to that level. "
        f"The main risk driver is {probabilistic_result.main_risk_driver}. "
        "This is a risk-management view, not a certain forecast."
    )


render_header(
    title="ARIA - Adaptive Risk Intelligence Agent",
    subtitle=tr(
        (
            "Application Python / Streamlit de gestion du risque pour "
            "portefeuilles actions, ETF et options : pricing, Greeks, "
            "stress tests, VaR, alertes et reporting professionnel."
        ),
        (
            "Python / Streamlit risk management application for equity, "
            "ETF and option portfolios: pricing, Greeks, stress tests, "
            "VaR, alerts and professional reporting."
        ),
    ),
    badge=tr("Plateforme de risk management", "Risk Management Platform"),
)


st.sidebar.header(tr("Configuration ARIA", "ARIA Configuration"))

with st.sidebar.expander(tr("Données de marché", "Market Data"), expanded=False):
    market_source_display = {
        "Manuel": tr("Manuel", "Manual"),
        "Yahoo Finance": "Yahoo Finance",
        "CSV local": tr("CSV local", "Local CSV"),
        "Bloomberg optionnel": tr("Bloomberg optionnel", "Optional Bloomberg"),
    }
    market_source = st.selectbox(
        tr("Source de données", "Data source"),
        options=[
            "Manuel",
            "Yahoo Finance",
            "CSV local",
            "Bloomberg optionnel",
        ],
        index=0,
        format_func=lambda source: market_source_display.get(source, source),
    )

    market_ticker = st.text_input(
        tr("Ticker de référence", "Reference ticker"),
        value="SPY",
    )

    csv_market_data_path = None

    if market_source == "CSV local":
        csv_market_data_path = st.text_input(
            tr("Chemin du CSV local", "Local CSV path"),
            value=relative_to_project(DEFAULT_MARKET_DATA_PATH),
        )

market_snapshot = None
market_data_status = tr("Mode manuel", "Manual Mode")
default_spot = 500.0
default_volatility_percent = 20.0

if market_source in {"Yahoo Finance", "CSV local", "Bloomberg optionnel"}:
    try:
        provider = get_provider(
            source=market_source,
            csv_path=(
                resolve_project_path(csv_market_data_path)
                if csv_market_data_path
                else None
            ),
        )

        market_snapshot = provider.get_market_snapshot(
            ticker=market_ticker,
        )

        default_spot = market_snapshot.last_price
        default_volatility_percent = market_snapshot.annualized_volatility * 100
        market_data_status = market_snapshot.status

        st.sidebar.success(f"{market_snapshot.source} - {market_snapshot.ticker}")

    except Exception as error:
        market_data_status = (
            tr("Bloomberg indisponible", "Bloomberg unavailable")
            if market_source == "Bloomberg optionnel"
            else tr("Source indisponible", "Source unavailable")
        )
        st.sidebar.info(str(error))


with st.sidebar.expander(tr("Hypothèses de marché", "Market Assumptions"), expanded=False):
    current_spot = st.number_input(
        tr("Prix du sous-jacent", "Underlying price"),
        min_value=0.01,
        value=float(default_spot),
        step=1.0,
    )

    current_volatility_percent = st.number_input(
        tr("Volatilité utilisée en %", "Volatility used (%)"),
        min_value=0.01,
        value=float(default_volatility_percent),
        step=1.0,
    )

    risk_free_rate_percent = st.number_input(
        tr("Taux sans risque en %", "Risk-free rate (%)"),
        value=5.0,
        step=0.25,
    )

    dividend_yield_percent = st.number_input(
        tr("Rendement du dividende en %", "Dividend yield (%)"),
        min_value=0.0,
        value=0.0,
        step=0.25,
    )

current_volatility = current_volatility_percent / 100
risk_free_rate = risk_free_rate_percent / 100
dividend_yield = dividend_yield_percent / 100

if market_source == "Manuel":
    manual_provider = ManualMarketDataProvider(
        spot=current_spot,
        volatility=current_volatility,
    )
    market_snapshot = manual_provider.get_market_snapshot(ticker=market_ticker)
    market_data_status = market_snapshot.status


with st.sidebar.expander(tr("Limites et scénario avancés", "Limits and Advanced Scenario"), expanded=False):
    delta_limit = st.number_input(
        tr("Limite de delta", "Delta limit"),
        min_value=0.0,
        value=10.0,
        step=1.0,
    )

    gamma_limit = st.number_input(
        tr("Limite de gamma", "Gamma limit"),
        min_value=0.0,
        value=1.0,
        step=0.1,
    )

    vega_limit = st.number_input(
        tr("Limite de vega", "Vega limit"),
        min_value=0.0,
        value=20.0,
        step=1.0,
    )

    spot_move_limit_percent = st.number_input(
        tr("Variation maximale du spot en %", "Maximum spot move (%)"),
        min_value=0.1,
        value=3.0,
        step=0.5,
    )

    volatility_move_limit_percent = st.number_input(
        tr("Variation maximale de volatilité en points", "Maximum volatility move (points)"),
        min_value=0.1,
        value=5.0,
        step=0.5,
    )

    z_score_limit = st.number_input(
        tr("Limite du z-score", "Z-score limit"),
        min_value=0.5,
        value=2.5,
        step=0.1,
    )

    custom_spot_change_percent = st.number_input(
        tr("Choc du spot en %", "Spot shock (%)"),
        value=-10.0,
        step=1.0,
    )

    custom_volatility_change_points = st.number_input(
        tr("Choc de volatilité en points", "Volatility shock (points)"),
        value=15.0,
        step=1.0,
    )

with st.sidebar.expander(tr("VaR et analyse probabiliste", "VaR and Probabilistic Analysis"), expanded=False):
    var_confidence_percent = st.selectbox(
        tr("Niveau de confiance", "Confidence level"),
        options=[95, 99],
        index=0,
    )

    var_horizon_days = st.number_input(
        tr("Horizon en jours", "Horizon in days"),
        min_value=1,
        value=1,
        step=1,
    )

    var_simulations = st.number_input(
        tr("Nombre de simulations VaR", "Number of VaR simulations"),
        min_value=100,
        max_value=10000,
        value=1000,
        step=100,
    )

    probabilistic_horizon_options = {
        tr("1 jour", "1 day"): 1,
        tr("1 semaine", "1 week"): 5,
        tr("1 mois", "1 month"): 21,
        tr("3 mois", "3 months"): 63,
        tr("6 mois", "6 months"): 126,
        tr("1 an", "1 year"): 252,
    }
    probabilistic_horizon_label = st.selectbox(
        tr("Horizon probabiliste", "Probabilistic horizon"),
        options=list(probabilistic_horizon_options),
        index=2,
    )

    probabilistic_horizon_days = probabilistic_horizon_options[
        probabilistic_horizon_label
    ]

    probabilistic_simulations_count = st.selectbox(
        tr("Simulations probabilistes", "Probabilistic simulations"),
        options=[
            1000,
            5000,
            10000,
        ],
        index=1,
    )

    probabilistic_confidence_percent = st.selectbox(
        tr("Confiance probabiliste", "Probabilistic confidence"),
        options=[
            95,
            99,
        ],
        index=0,
    )

enable_llm_commentary = st.sidebar.checkbox(
    tr(
        "Inclure un commentaire LLM dans les rapports",
        "Include LLM commentary in reports",
    ),
    value=False,
)


if "portfolio_data" not in st.session_state:
    st.session_state.portfolio_data = default_portfolio()

st.session_state.portfolio_data = normalize_portfolio_table(
    st.session_state.portfolio_data,
    default_spot_value=current_spot,
    default_volatility_value=current_volatility,
)

render_section_title(
    tr("Portefeuille client", "Client Portfolio"),
    tr(
        "Modifiez le portefeuille ou chargez une démonstration prête pour l'analyse.",
        "Edit the portfolio or load a ready-to-analyze demo portfolio.",
    ),
)

investment_horizon = "Long terme"
risk_profile = "Équilibré"
horizon_display = tr("Long terme", "Long term")

manual_tab, demo_tab = st.tabs(
    [
        tr("Modifier le portefeuille", "Edit Portfolio"),
        tr("Charger une démonstration", "Load Demo"),
    ]
)

with manual_tab:
    render_info_card(
        tr("Lecture des positions", "How to Read Positions"),
        tr(
            (
                "Une quantité positive correspond à une position achetée. "
                "Une quantité négative correspond à une position vendue. "
                "Les colonnes techniques nécessaires au moteur ARIA sont "
                "reconstruites automatiquement."
            ),
            (
                "A positive quantity is a long position. A negative quantity is "
                "a short position. Technical columns required by ARIA are "
                "rebuilt automatically."
            ),
        ),
    )

    if "current_portfolio_name" not in st.session_state:
        st.session_state.current_portfolio_name = "Mon portefeuille ARIA"

    saved_files = saved_portfolio_files()
    saved_labels = [
        portfolio_file_label(path)
        for path in saved_files
    ]
    saved_display_options = saved_labels or [
        tr("Aucun portefeuille sauvegardé", "No saved portfolio")
    ]

    portfolio_name = st.text_input(
        tr("Nom du portefeuille", "Portfolio Name"),
        value=st.session_state.current_portfolio_name,
        help=tr(
            "Ce nom sert à sauvegarder plusieurs portefeuilles différents.",
            "This name lets you save several different portfolios.",
        ),
    )
    st.session_state.current_portfolio_name = portfolio_name

    manager_col_1, manager_col_2 = st.columns([1, 1])
    with manager_col_1:
        selected_saved_label = st.selectbox(
            tr("Portefeuille sauvegardé", "Saved Portfolio"),
            options=saved_display_options,
            index=0,
        )
    with manager_col_2:
        st.caption(
            tr(
                "Tu peux sauvegarder autant de portefeuilles que nécessaire. "
                "Chaque sauvegarde reste dans le dossier data/portfolios.",
                "You can save as many portfolios as needed. Each saved "
                "portfolio stays in the data/portfolios folder.",
            )
        )

    selected_saved_path = None
    if selected_saved_label in saved_labels:
        selected_saved_path = saved_files[saved_labels.index(selected_saved_label)]

    save_col, load_col, delete_col, reset_col = st.columns(4)

    if save_col.button(
        tr("Sauvegarder ce portefeuille", "Save This Portfolio"),
        width="stretch",
    ):
        safe_name = sanitize_portfolio_name(portfolio_name)
        portfolio_path = PORTFOLIOS_DIR / f"{safe_name}.csv"
        st.session_state.portfolio_data.to_csv(
            portfolio_path,
            index=False,
        )
        st.success(
            tr("Portefeuille sauvegardé", "Portfolio saved")
            + f" : {relative_to_project(portfolio_path)}"
        )

    if load_col.button(
        tr("Charger la sélection", "Load Selected"),
        width="stretch",
        disabled=selected_saved_path is None,
    ):
        loaded_portfolio = pd.read_csv(selected_saved_path)
        st.session_state.portfolio_data = normalize_portfolio_table(
            loaded_portfolio,
            default_spot_value=current_spot,
            default_volatility_value=current_volatility,
        )
        st.session_state.current_portfolio_name = portfolio_file_label(
            selected_saved_path
        )

        if "portfolio_editor" in st.session_state:
            del st.session_state["portfolio_editor"]

        st.rerun()

    if delete_col.button(
        tr("Supprimer la sélection", "Delete Selected"),
        width="stretch",
        disabled=selected_saved_path is None,
    ):
        selected_saved_path.unlink(
            missing_ok=True,
        )
        st.success(
            tr("Portefeuille supprimé.", "Portfolio deleted.")
        )
        st.rerun()

    if reset_col.button(
        tr("Réinitialiser", "Reset"),
        width="stretch",
    ):
        st.session_state.portfolio_data = default_portfolio()
        st.session_state.current_portfolio_name = "Mon portefeuille ARIA"

        if "portfolio_editor" in st.session_state:
            del st.session_state["portfolio_editor"]

        st.rerun()

    with st.expander(
        tr("Importer un CSV avancé", "Advanced CSV Import"),
        expanded=False,
    ):
        st.info(
            tr(
                (
                    "Cette option sert à importer un portefeuille CSV déjà préparé. "
                    "Le plus simple reste de sauvegarder/charger avec les boutons "
                    "au-dessus. Pour un import externe, le CSV peut contenir par "
                    "exemple : Ticker, Nom, Weight, Price, Quantity, Asset type, "
                    "Sector, Currency, Option type, Strike, Maturity, Volatility."
                ),
                (
                    "This option imports an already prepared CSV portfolio. "
                    "The easiest workflow is still to save/load with the buttons "
                    "above. For an external import, the CSV can contain for "
                    "example: Ticker, Name, Weight, Price, Quantity, Asset type, "
                    "Sector, Currency, Option type, Strike, Maturity, Volatility."
                ),
            )
        )

        uploaded_portfolio_file = st.file_uploader(
            tr("Déposer un CSV de portefeuille", "Upload a Portfolio CSV"),
            type=["csv"],
            accept_multiple_files=False,
        )

        if uploaded_portfolio_file is not None and st.button(
            tr("Importer le CSV déposé", "Import Uploaded CSV"),
            width="stretch",
        ):
            loaded_portfolio = pd.read_csv(uploaded_portfolio_file)
            st.session_state.portfolio_data = normalize_portfolio_table(
                loaded_portfolio,
                default_spot_value=current_spot,
                default_volatility_value=current_volatility,
            )
            st.session_state.current_portfolio_name = Path(
                uploaded_portfolio_file.name
            ).stem

            if "portfolio_editor" in st.session_state:
                del st.session_state["portfolio_editor"]

            st.success(tr("CSV importé.", "CSV imported."))
            st.rerun()

        default_import_path = (
            relative_to_project(saved_files[0])
            if saved_files
            else ""
        )
        portfolio_file_path = st.text_input(
            tr("Chemin du fichier CSV", "CSV file path"),
            value=default_import_path,
            placeholder="data/portfolios/mon_portefeuille.csv",
            help=tr(
                (
                    "Utilise ce champ seulement si le fichier existe déjà dans "
                    "le projet ou si tu colles un chemin absolu."
                ),
                (
                    "Use this field only if the file already exists in the "
                    "project or if you paste an absolute path."
                ),
            ),
        )

        if st.button(
            tr("Importer depuis ce chemin", "Import From This Path"),
            width="stretch",
        ):
            if not portfolio_file_path.strip():
                st.error(
                    tr(
                        "Indique un chemin CSV existant ou dépose un fichier au-dessus.",
                        "Enter an existing CSV path or upload a file above.",
                    )
                )
            else:
                portfolio_path = resolve_project_path(portfolio_file_path)

                if not portfolio_path.exists():
                    st.error(
                        tr("Fichier introuvable", "File not found")
                        + f" : {portfolio_file_path}"
                    )

                else:
                    loaded_portfolio = pd.read_csv(portfolio_path)
                    st.session_state.portfolio_data = normalize_portfolio_table(
                        loaded_portfolio,
                        default_spot_value=current_spot,
                        default_volatility_value=current_volatility,
                    )
                    st.session_state.current_portfolio_name = portfolio_file_label(
                        portfolio_path
                    )

                    if "portfolio_editor" in st.session_state:
                        del st.session_state["portfolio_editor"]

                    st.success(tr("CSV importé.", "CSV imported."))
                    st.rerun()

    with st.expander(
        tr("Ajouter une position guidée", "Add a Guided Position"),
        expanded=True,
    ):
        guided_base_value = st.number_input(
            tr("Valeur de référence du portefeuille", "Reference Portfolio Value"),
            min_value=1_000.0,
            value=100_000.0,
            step=5_000.0,
            help=tr(
                "Sert uniquement à convertir un poids en montant et en quantité.",
                "Only used to convert a weight into amount and quantity.",
            ),
        )
        add_col_1, add_col_2, add_col_3 = st.columns(3)
        asset_kind = add_col_1.selectbox(
            tr("Type d'instrument", "Instrument Type"),
            options=[
                tr("Action / ETF", "Equity / ETF"),
                tr("Option", "Option"),
            ],
        )
        side_label = add_col_2.selectbox(
            tr("Sens", "Side"),
            options=[
                tr("Achat", "Long"),
                tr("Vente / couverture", "Short / hedge"),
            ],
        )
        guided_weight = add_col_3.number_input(
            tr("Poids cible (%)", "Target Weight (%)"),
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=0.5,
        )

        info_col_1, info_col_2, info_col_3 = st.columns(3)
        guided_ticker = info_col_1.text_input(
            tr("Ticker / sous-jacent", "Ticker / Underlying"),
            value="SPY",
        ).upper()
        guided_name = info_col_2.text_input(
            tr("Nom de la position", "Position Name"),
            value=tr("Nouvelle position", "New position"),
        )
        guided_currency = info_col_3.selectbox(
            tr("Devise", "Currency"),
            options=["USD", "EUR", "GBP", "CHF", "JPY"],
        )

        detail_col_1, detail_col_2, detail_col_3 = st.columns(3)
        guided_asset_class = detail_col_1.selectbox(
            tr("Classe d'actif", "Asset Class"),
            options=[
                tr("Action / ETF", "Equity / ETF"),
                tr("Obligation / ETF obligataire", "Bond / Bond ETF"),
                tr("Monétaire / cash", "Cash / Money Market"),
                tr("Option", "Option"),
                tr("Autre", "Other"),
            ],
        )
        guided_sector_choice = detail_col_2.selectbox(
            tr("Secteur", "Sector"),
            options=[
                tr("Indices", "Indices"),
                tr("Technologie", "Technology"),
                tr("Santé", "Healthcare"),
                tr("Finance", "Financials"),
                tr("Obligations", "Bonds"),
                tr("Énergie", "Energy"),
                tr("Consommation", "Consumer"),
                tr("Autre", "Other"),
            ],
        )
        guided_price = detail_col_3.number_input(
            tr("Prix / spot", "Price / Spot"),
            min_value=0.01,
            value=float(current_spot),
            step=1.0,
        )

        guided_sector = guided_sector_choice
        if guided_sector_choice in {tr("Autre", "Other"), "Other"}:
            guided_sector = st.text_input(
                tr("Secteur personnalisé", "Custom Sector"),
                value=tr("Non classé", "Unclassified"),
            )

        is_option = asset_kind == tr("Option", "Option")
        sign = -1 if side_label == tr("Vente / couverture", "Short / hedge") else 1
        guided_value = guided_weight / 100 * guided_base_value * sign
        guided_quantity = 0.0

        option_type = ""
        strike = pd.NA
        maturity = pd.NA
        implied_volatility = pd.NA
        contract_size = 1

        if is_option:
            option_col_1, option_col_2, option_col_3, option_col_4 = st.columns(4)
            option_type = option_col_1.selectbox(
                tr("Type d'option", "Option Type"),
                options=["call", "put"],
            )
            strike = option_col_2.number_input(
                "Strike",
                min_value=0.01,
                value=float(guided_price),
                step=1.0,
            )
            maturity = option_col_3.number_input(
                tr("Maturité en années", "Maturity in Years"),
                min_value=0.01,
                value=0.25,
                step=0.05,
            )
            implied_volatility = option_col_4.number_input(
                tr("Volatilité implicite", "Implied Volatility"),
                min_value=0.01,
                value=float(current_volatility),
                step=0.01,
            )
            contract_size = st.number_input(
                tr("Taille du contrat", "Contract Size"),
                min_value=1,
                value=100,
                step=1,
            )
            guided_quantity = st.number_input(
                tr("Nombre de contrats", "Number of Contracts"),
                min_value=1,
                value=1,
                step=1,
            ) * sign
        else:
            manual_quantity = st.number_input(
                tr("Quantité manuelle (0 = calcul automatique)", "Manual Quantity (0 = automatic)"),
                value=0.0,
                step=1.0,
            )
            guided_quantity = (
                manual_quantity
                if manual_quantity != 0
                else guided_value / guided_price
            )

        if st.button(
            tr("Ajouter la position au portefeuille", "Add Position to Portfolio"),
            type="primary",
            width="stretch",
        ):
            if not guided_ticker.strip():
                st.error(tr("Le ticker est obligatoire.", "Ticker is required."))
                st.stop()

            new_row = {
                "Asset type": "option" if is_option else "stock",
                "Asset class": "Option" if is_option else guided_asset_class,
                "Ticker": guided_ticker.strip(),
                "Sous-jacent": guided_ticker.strip(),
                "Nom": guided_name.strip() or guided_ticker.strip(),
                "Sector": guided_sector,
                "Currency": guided_currency,
                "Weight": guided_weight,
                "Value": guided_value,
                "Quantity": guided_quantity,
                "Quantite": guided_quantity,
                "Price": guided_price,
                "Spot": guided_price,
                "Data source": "Manuel",
                "Commentaire": tr("Ajout guidé", "Guided input"),
                "Instrument": "Option" if is_option else "Action",
                "Option type": option_type,
                "Type option": option_type,
                "Strike": strike,
                "Maturity": maturity,
                "Maturite": maturity,
                "Volatility": implied_volatility,
                "Volatilite": implied_volatility,
                "Rate": risk_free_rate,
                "Contract size": contract_size,
                "Multiplicateur": contract_size,
            }
            append_portfolio_row(
                new_row,
                current_spot=current_spot,
                current_volatility=current_volatility,
            )
            st.success(tr("Position ajoutée.", "Position added."))
            st.rerun()

with demo_tab:
    if st.session_state.get("curated_demo_portfolio") not in {
        None,
        *CURATED_DEMO_PORTFOLIOS,
    }:
        del st.session_state["curated_demo_portfolio"]

    selected_demo_portfolio = st.selectbox(
        tr("Portefeuille de démonstration", "Demo Portfolio"),
        options=CURATED_DEMO_PORTFOLIOS,
        format_func=lambda name: (
            DEMO_PORTFOLIO_LABELS.get(name, name)
            if ui_language == "fr"
            else name
        ),
        key="curated_demo_portfolio",
    )

    if selected_demo_portfolio in get_model_portfolio_names():
        selected_model = get_model_portfolio(selected_demo_portfolio)
        demo_kpi_1, demo_kpi_2, demo_kpi_3, demo_kpi_4 = st.columns(4)
        demo_kpi_1.metric(tr("Risque", "Risk"), selected_model.risk_level)
        demo_kpi_2.metric(tr("Horizon", "Horizon"), horizon_display)
        demo_kpi_3.metric(tr("Vol. estimée", "Estimated Vol."), f"{selected_model.volatility:.1%}")
        demo_kpi_4.metric("Drawdown", f"{selected_model.drawdown:.1%}")
        if ui_language == "fr":
            st.info(
                f"{selected_model.explanation} Profil adapté : "
                f"{selected_model.investor_profile}"
            )
        else:
            st.info(
                "Professional demo portfolio with a coherent long-term risk profile."
            )

    if st.button(
        tr("Charger ce portefeuille", "Load This Portfolio"),
        width="stretch",
    ):
        if selected_demo_portfolio in get_model_portfolio_names():
            loaded_demo_data = model_portfolio_to_dataframe(
                get_model_portfolio(selected_demo_portfolio)
            )
        else:
            if selected_demo_portfolio not in CURATED_DEMO_PORTFOLIOS:
                selected_demo_portfolio = "Low Risk Options Portfolio"

            demo_portfolio = create_demo_portfolio(
                name=selected_demo_portfolio,
                spot=current_spot,
                maturity=0.25,
                rate=risk_free_rate,
                volatility=current_volatility,
            )
            loaded_demo_data = portfolio_to_dataframe(demo_portfolio)

        st.session_state.portfolio_data = normalize_portfolio_table(
            loaded_demo_data,
            default_spot_value=current_spot,
            default_volatility_value=current_volatility,
        )

        if "portfolio_editor" in st.session_state:
            del st.session_state["portfolio_editor"]

        st.rerun()

portfolio_contains_options = (
    st.session_state.portfolio_data.get("Asset type", pd.Series(dtype=str))
    .fillna("")
    .astype(str)
    .str.lower()
    .eq("option")
    .any()
)
editor_columns = PORTFOLIO_EDITOR_COLUMNS.copy()
if portfolio_contains_options:
    editor_columns = [
        *PORTFOLIO_EDITOR_COLUMNS,
        *[column for column in PORTFOLIO_OPTION_COLUMNS if column not in PORTFOLIO_EDITOR_COLUMNS],
    ]

editor_data = st.session_state.portfolio_data.reindex(
    columns=editor_columns
)
for text_column in [
    "Option type",
    "Position",
    "Objectif option",
]:
    if text_column in editor_data.columns:
        editor_data[text_column] = editor_data[text_column].fillna("").astype(str)

portfolio_row_labels = [
    row_display_label(index, row)
    for index, row in st.session_state.portfolio_data.iterrows()
]

row_action_col_1, row_action_col_2 = st.columns([2, 1])
rows_to_delete = row_action_col_1.multiselect(
    tr("Lignes à supprimer", "Rows to Delete"),
    options=portfolio_row_labels,
    placeholder=tr(
        "Choisir une ou plusieurs lignes",
        "Choose one or more rows",
    ),
)

if row_action_col_2.button(
    tr("Supprimer les lignes sélectionnées", "Delete Selected Rows"),
    width="stretch",
    disabled=not rows_to_delete,
):
    delete_portfolio_rows(rows_to_delete)
    st.success(tr("Ligne(s) supprimée(s).", "Row(s) deleted."))
    st.rerun()

edited_portfolio = st.data_editor(
    editor_data,
    key="portfolio_editor",
    num_rows="dynamic",
    hide_index=True,
    width="stretch",
    column_order=editor_columns,
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker"),
        "Nom": st.column_config.TextColumn(tr("Nom", "Name")),
        "Asset class": st.column_config.TextColumn(tr("Classe d'actif", "Asset Class")),
        "Sector": st.column_config.TextColumn(tr("Secteur", "Sector")),
        "Weight": st.column_config.NumberColumn(
            tr("Poids (%)", "Weight (%)"),
            min_value=0.0,
            max_value=100.0,
            step=0.5,
            format="%.2f",
        ),
        "Value": st.column_config.NumberColumn(
            tr("Valeur", "Value"),
            step=100.0,
            format="%.2f",
        ),
        "Currency": st.column_config.SelectboxColumn(
            tr("Devise", "Currency"),
            options=["USD", "EUR", "GBP", "CHF", "JPY"],
        ),
        "Quantity": st.column_config.NumberColumn(
            tr("Quantité", "Quantity"),
            step=1.0,
            format="%.4f",
        ),
        "Price": st.column_config.NumberColumn(
            tr("Prix", "Price"),
            min_value=0.01,
            step=1.0,
        ),
        "Data source": st.column_config.TextColumn(tr("Source", "Source")),
        "Commentaire": st.column_config.TextColumn(tr("Commentaire", "Comment")),
        "Asset type": st.column_config.SelectboxColumn(
            tr("Type d'actif", "Asset Type"),
            options=["stock", "option"],
            required=True,
        ),
        "Option type": st.column_config.SelectboxColumn(
            tr("Type d'option", "Option Type"),
            options=["", "call", "put"],
        ),
        "Position": st.column_config.SelectboxColumn(
            "Position",
            options=["", "Long", "Short"],
        ),
        "Strike": st.column_config.NumberColumn("Strike", min_value=0.01, step=1.0),
        "Maturity": st.column_config.NumberColumn(
            tr("Maturité en années", "Maturity in Years"),
            min_value=0.01,
            step=0.05,
            format="%.4f",
        ),
        "Prime": st.column_config.NumberColumn(tr("Prime", "Premium"), min_value=0.0, step=0.5),
        "Volatility": st.column_config.NumberColumn(
            tr("Volatilité implicite", "Implied Volatility"),
            min_value=0.01,
            step=0.01,
            format="%.4f",
        ),
        "Contract size": st.column_config.NumberColumn(
            tr("Taille contrat", "Contract Size"),
            min_value=1,
            step=1,
        ),
        "Exposition notionnelle": st.column_config.NumberColumn(
            tr("Exposition notionnelle", "Notional Exposure"),
            step=1000.0,
        ),
        "Delta": st.column_config.NumberColumn("Delta", step=0.05, format="%.4f"),
        "Objectif option": st.column_config.TextColumn(tr("Objectif option", "Option Objective")),
    },
)

st.session_state.portfolio_data = normalize_portfolio_table(
    merge_visible_portfolio_edits(
        st.session_state.portfolio_data,
        edited_portfolio,
    ),
    default_spot_value=current_spot,
    default_volatility_value=current_volatility,
)

current_weights = pd.to_numeric(
    st.session_state.portfolio_data.get("Weight", pd.Series(dtype=float)),
    errors="coerce",
)
weight_total = float(
    current_weights.fillna(0).sum()
)
weight_gap = 100.0 - weight_total

weight_col_1, weight_col_2, weight_col_3 = st.columns([1, 1, 1])
weight_col_1.metric(
    tr("Somme des poids", "Total Weight"),
    f"{weight_total:.2f}%",
    f"{weight_gap:+.2f} pt",
)
weight_col_2.metric(
    tr("Nombre de lignes", "Number of Rows"),
    len(st.session_state.portfolio_data),
)
weight_col_3.metric(
    tr("Poids manquants", "Missing Weights"),
    int(current_weights.isna().sum()),
)

if abs(weight_gap) <= 0.05:
    st.success(
        tr(
            "La somme des poids est cohérente. Tu peux lancer l'analyse.",
            "Total weight is coherent. You can run the analysis.",
        )
    )
else:
    st.warning(
        tr(
            "La saisie reste possible, mais l'analyse ARIA sera bloquée tant que la somme des poids n'est pas égale à 100 %.",
            "Input remains possible, but ARIA analysis will be blocked until total weight equals 100%.",
        )
    )
    if st.button(
        tr("Ajuster automatiquement les poids à 100 %", "Scale Weights to 100%"),
        width="stretch",
    ):
        if scale_weights_to_100():
            st.success(tr("Poids ajustés à 100 %.", "Weights scaled to 100%."))
            st.rerun()
        else:
            st.error(
                tr(
                    "Impossible d'ajuster : aucun poids positif détecté.",
                    "Cannot scale: no positive weight detected.",
                )
            )

portfolio_validation_errors = validate_portfolio_table(
    st.session_state.portfolio_data
)
coherence_errors, coherence_warnings = validate_portfolio_coherence(
    st.session_state.portfolio_data,
    risk_profile=risk_profile,
    horizon=investment_horizon,
)

blocking_validation_errors = portfolio_validation_errors + coherence_errors

if blocking_validation_errors:
    with st.expander(
        tr("Corrections obligatoires avant analyse", "Required Corrections Before Analysis"),
        expanded=True,
    ):
        for validation_error in blocking_validation_errors:
            st.error(display_validation_message(validation_error))
elif coherence_warnings:
    pass
else:
    st.success(tr("Portefeuille prêt pour l'analyse.", "Portfolio ready for analysis."))

current_diagnosis = portfolio_diagnosis(
    st.session_state.portfolio_data
)

analyse_button = st.button(
    tr("Lancer l'analyse ARIA", "Run ARIA Analysis"),
    type="primary",
    width="stretch",
)
auto_launch_analysis = bool(
    st.session_state.pop(
        "launch_analysis_requested",
        False,
    )
)


if analyse_button or auto_launch_analysis:
    if blocking_validation_errors:
        st.error(
            tr(
                "Corrige les erreurs de portefeuille avant de lancer l'analyse ARIA.",
                "Fix portfolio errors before running ARIA analysis.",
            )
        )
        st.stop()

    try:
        portfolio = build_portfolio_from_table(
            portfolio_table=st.session_state.portfolio_data,
            spot=current_spot,
            rate=risk_free_rate,
            volatility=current_volatility,
            dividend=dividend_yield,
        )

    except ValueError as error:
        st.error(display_validation_message(str(error)))
        st.stop()

    current_snapshot = create_snapshot(
        portfolio=portfolio,
        spot=current_spot,
        implied_volatility=current_volatility,
    )

    history_manager = RiskHistory(
        file_path=RISK_HISTORY_PATH,
    )

    history = history_manager.load_snapshots()
    previous_snapshot = history[-1] if history else None

    detector = AnomalyDetector(
        delta_limit=delta_limit,
        gamma_limit=gamma_limit,
        vega_limit=vega_limit,
        daily_spot_move_limit=spot_move_limit_percent / 100,
        volatility_move_limit=volatility_move_limit_percent / 100,
        z_score_limit=z_score_limit,
    )

    alerts = detector.detect_all(
        current=current_snapshot,
        history=history,
        previous=previous_snapshot,
    )

    greeks = portfolio.total_greeks()

    hedge_result = calculate_delta_hedge(
        portfolio=portfolio,
        current_spot=current_spot,
    )

    var_result, var_simulations_data = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=current_volatility,
        confidence_level=var_confidence_percent / 100,
        horizon_days=var_horizon_days,
        number_of_simulations=var_simulations,
    )

    parametric_var = parametric_var_estimate(
        portfolio=portfolio,
        annual_volatility=current_volatility,
        confidence_level=var_confidence_percent / 100,
        horizon_days=var_horizon_days,
    )

    probabilistic_result, probabilistic_simulations = simulate_probabilistic_risk(
        portfolio=portfolio,
        horizon_days=probabilistic_horizon_days,
        number_of_simulations=probabilistic_simulations_count,
        confidence_level=probabilistic_confidence_percent / 100,
    )

    scenario_results = run_standard_scenarios(portfolio)

    scenario_results.extend(
        run_historical_scenarios(portfolio)
    )

    custom_result = run_scenario(
        portfolio=portfolio,
        name="Scenario personnalise",
        spot_change_percent=custom_spot_change_percent / 100,
        volatility_change_points=custom_volatility_change_points / 100,
    )

    scenario_results.append(custom_result)

    alerts.extend(detector.detect_concentration(portfolio))
    alerts.extend(detector.detect_correlation_risk(portfolio))
    alerts.extend(
        detector.detect_scenario_loss(
            scenario_results=scenario_results,
            portfolio_value=current_snapshot.portfolio_value,
        )
    )

    risk_score_result = calculate_risk_score(
        portfolio=portfolio,
        alerts=alerts,
        var_result=var_result,
        scenario_results=scenario_results,
        delta_limit=delta_limit,
        gamma_limit=gamma_limit,
        vega_limit=vega_limit,
    )

    history_manager.save_snapshot(current_snapshot)

    (
        overview_tab,
        stress_tab,
        var_tab,
        sensitivities_tab,
        probabilistic_tab,
        alerts_tab,
    ) = st.tabs(
        [
            tr("Vue générale", "Overview"),
            tr("Stress tests", "Stress Tests"),
            "VaR",
            tr("Sensibilités", "Sensitivities"),
            tr("Risque probabiliste", "Probabilistic Risk"),
            tr("Alertes & LLM", "Alerts & LLM"),
        ]
    )

    with overview_tab:
        render_section_title(
            "Risk Score ARIA",
            tr(
                "Synthèse du niveau de risque agrégé par ARIA.",
                "ARIA aggregate risk score summary.",
            ),
        )

        render_risk_badge(
            risk_score_result.label,
            label=display_risk_label(risk_score_result.label),
        )

        score_col_1, score_col_2 = st.columns([1, 3])

        score_col_1.metric(
            tr("Score de risque", "Risk Score"),
            f"{risk_score_result.score}/100",
        )
        score_col_1.caption(display_risk_label(risk_score_result.label))

        with score_col_2:
            st.progress(risk_score_result.score / 100)
            score_explanation = display_risk_explanation(
                risk_score_result.score,
                risk_score_result.explanation,
            )

            if risk_score_result.score >= 80:
                st.error(score_explanation)
            elif risk_score_result.score >= 60:
                st.warning(score_explanation)
            elif risk_score_result.score >= 30:
                st.info(score_explanation)
            else:
                st.success(score_explanation)

        with st.expander(
            tr("Voir les principaux facteurs de risque", "Show Main Risk Drivers"),
            expanded=False,
        ):
            for driver in risk_score_result.main_drivers:
                st.caption(f"- {driver}")

        render_section_title(
            tr("Résumé du portefeuille", "Portfolio Summary"),
            tr(
                "Valeur, paramètres de marché et taille de l'univers analysé.",
                "Value, market assumptions and analyzed universe size.",
            ),
        )

        render_metric_row(
            [
                {
                    "label": tr("Valeur du portefeuille", "Portfolio Value"),
                    "value": f"{portfolio.total_market_value():,.2f}",
                },
                {
                    "label": "Spot",
                    "value": f"{current_spot:,.2f}",
                },
                {
                    "label": tr("Volatilité utilisée", "Volatility Used"),
                    "value": f"{current_volatility:.2%}",
                },
                {
                    "label": tr("Nombre de positions", "Number of Positions"),
                    "value": len(portfolio.positions),
                },
            ]
        )

        render_section_title(
            tr("Greeks du portefeuille", "Portfolio Greeks"),
            tr(
                "Expositions agrégées aux principaux facteurs de risque.",
                "Aggregate exposures to the main risk factors.",
            ),
        )

        render_metric_row(
            [
                {
                    "label": "Delta",
                    "value": f"{greeks['delta']:.4f}",
                },
                {
                    "label": "Gamma",
                    "value": f"{greeks['gamma']:.4f}",
                },
                {
                    "label": "Vega",
                    "value": f"{greeks['vega']:.4f}",
                },
                {
                    "label": tr("Theta journalier", "Daily Theta"),
                    "value": f"{greeks['theta']:.4f}",
                },
                {
                    "label": "Rho",
                    "value": f"{greeks['rho']:.4f}",
                },
                {
                    "label": "Volga",
                    "value": f"{greeks['volga']:.6f}",
                },
            ]
        )

    with stress_tab:
        render_section_title(
            "Stress tests",
            tr(
                "Lecture des pertes et gains sous scénarios de marché.",
                "Read gains and losses under market scenarios.",
            ),
        )

        best_scenario = max(
            scenario_results,
            key=lambda result: result.profit_and_loss,
        )

        worst_scenario = min(
            scenario_results,
            key=lambda result: result.profit_and_loss,
        )

        best_column, worst_column = st.columns(2)

        best_column.metric(
            tr("Meilleur scénario", "Best Scenario"),
            display_scenario_name(best_scenario.name),
            f"{best_scenario.profit_and_loss:+,.2f}",
        )

        worst_column.metric(
            tr("Scénario le plus défavorable", "Worst Scenario"),
            display_scenario_name(worst_scenario.name),
            f"{worst_scenario.profit_and_loss:+,.2f}",
        )

        scenario_column = tr("Scénario", "Scenario")
        spot_move_column = tr("Variation spot", "Spot Move")
        volatility_move_column = tr("Variation volatilité", "Volatility Move")
        rate_shock_column = tr("Choc taux", "Rate Shock")
        correlation_shock_column = tr("Choc corrélation", "Correlation Shock")
        initial_value_column = tr("Valeur initiale", "Initial Value")
        stressed_value_column = tr("Valeur stressée", "Stressed Value")
        pnl_column = tr("Profit / Perte", "Profit / Loss")
        stressed_delta_column = tr("Delta stressé", "Stressed Delta")
        stressed_gamma_column = tr("Gamma stressé", "Stressed Gamma")
        stressed_vega_column = tr("Vega stressé", "Stressed Vega")

        scenario_table = pd.DataFrame(
            [
                {
                    scenario_column: display_scenario_name(result.name),
                    spot_move_column: f"{result.spot_change_percent:+.1%}",
                    volatility_move_column: f"{result.volatility_change_points:+.1%}",
                    rate_shock_column: f"{result.rate_change_points:+.1%}",
                    correlation_shock_column: f"{result.correlation_shock:+.1%}",
                    initial_value_column: result.initial_value,
                    stressed_value_column: result.stressed_value,
                    pnl_column: result.profit_and_loss,
                    stressed_delta_column: result.stressed_delta,
                    stressed_gamma_column: result.stressed_gamma,
                    stressed_vega_column: result.stressed_vega,
                }
                for result in scenario_results
            ]
        )

        stress_summary_tab, stress_matrix_tab, stress_detail_tab = st.tabs(
            [
                tr("Synthèse scénarios", "Scenario Summary"),
                tr("Matrice rouge/vert", "Red/Green Matrix"),
                tr("Tableau complet", "Full Table"),
            ]
        )

        with stress_summary_tab:
            stress_chart = create_stress_chart(
                scenario_results,
                
            )

            st.altair_chart(
                stress_chart,
                width="stretch",
            )

            if worst_scenario.top_contributors:
                render_section_title(
                    tr("Top contributeurs au pire stress", "Top Contributors to Worst Stress"),
                    tr(
                        "Positions qui expliquent le plus la perte du scénario le plus défavorable.",
                        "Positions explaining most of the loss in the worst scenario.",
                    ),
                )

                st.dataframe(
                    pd.DataFrame(worst_scenario.top_contributors).head(8),
                    hide_index=True,
                    width="stretch",
                )

        with stress_matrix_tab:
            surface_points = calculate_risk_surface(
                portfolio=portfolio,
                spot_changes=[
                    -0.15,
                    -0.075,
                    0.00,
                    0.075,
                    0.15,
                ],
                volatility_changes=[
                    -0.10,
                    0.00,
                    0.10,
                    0.20,
                ],
            )
            surface_data = surface_to_dataframe(surface_points)

            st.altair_chart(
                create_stress_matrix_chart(
                    surface_data,
                    
                ),
                width="stretch",
            )

            with st.expander(tr("Voir les valeurs de la matrice", "Show Matrix Values")):
                matrix_table = surface_data.pivot_table(
                    index="Variation volatilité",
                    columns="Variation spot",
                    values="Profit / Perte",
                    aggfunc="sum",
                ).sort_index(ascending=False)
                matrix_table.index = [
                    f"{index:+.0%}" for index in matrix_table.index
                ]
                matrix_table.columns = [
                    f"{column:+.0%}" for column in matrix_table.columns
                ]
                st.dataframe(
                    matrix_table.style.background_gradient(
                        cmap="RdYlGn",
                        axis=None,
                    ).format("{:,.2f}"),
                    width="stretch",
                )

        with stress_detail_tab:
            st.dataframe(
                scenario_table,
                hide_index=True,
                width="stretch",
            )

    with var_tab:
        render_section_title(
            "VaR / Expected Shortfall",
            tr(
                "Estimation de la perte de queue par simulation.",
                "Tail-loss estimate from simulation.",
            ),
        )

        var_col_1, var_col_2, var_col_3, var_col_4 = st.columns(4)
        var_col_1.metric(
            f"VaR {var_confidence_percent}%",
            f"{var_result.var_amount:,.2f}",
        )
        var_col_2.metric(
            "Expected Shortfall",
            f"{var_result.expected_shortfall:,.2f}",
        )
        var_col_3.metric(
            tr("Pire perte simulée", "Worst Simulated Loss"),
            f"{var_result.worst_loss:,.2f}",
        )
        var_col_4.metric(
            tr("VaR paramétrique", "Parametric VaR"),
            f"{parametric_var:,.2f}",
        )

        var_chart = create_var_distribution_chart(
            simulations_data=var_simulations_data,
            var_amount=var_result.var_amount,
            expected_shortfall=var_result.expected_shortfall,
        )
        st.altair_chart(var_chart, width="stretch")

        with st.expander(tr("Simulations VaR", "VaR Simulations")):
            st.dataframe(
                var_simulations_data,
                hide_index=True,
                width="stretch",
            )

    with sensitivities_tab:
        pnl_tab, greeks_tab = st.tabs(
            [
                "P&L / spot",
                "Greeks / spot",
            ]
        )

        with pnl_tab:
            render_section_title(
                tr("Évolution du P&L par rapport au spot", "P&L Evolution vs Spot"),
                tr(
                    "Lecture visuelle de la convexité et des zones de perte.",
                    "Visual read of convexity and loss zones.",
                ),
            )
            pnl_points = calculate_pnl_profile(
                portfolio=portfolio,
                current_spot=current_spot,
                minimum_change=-0.30,
                maximum_change=0.30,
                number_of_points=61,
            )
            pnl_data = normalize_dataframe_columns(
                pnl_profile_to_dataframe(pnl_points)
            )
            breakeven_spots = find_breakeven_spots(pnl_data)
            st.altair_chart(
                create_pnl_profile_chart(
                    pnl_data=pnl_data,
                    current_spot=current_spot,
                    breakeven_spots=breakeven_spots,
                ),
                width="stretch",
            )
            if breakeven_spots:
                st.caption(
                    tr("Points morts estimés : ", "Estimated break-even points: ")
                    + ", ".join(f"{spot:,.2f}" for spot in breakeven_spots)
                )

        with greeks_tab:
            render_section_title(
                tr("Évolution des Greeks par rapport au spot", "Greeks Evolution vs Spot"),
                tr(
                    "Sensibilités principales lorsque le sous-jacent varie.",
                    "Main sensitivities as the underlying changes.",
                ),
            )
            selected_greeks = st.multiselect(
                tr("Greeks affichés", "Displayed Greeks"),
                options=[
                    "Delta",
                    "Gamma",
                    "Theta",
                    "Vega",
                    "Rho",
                    "Vanna",
                    "Volga",
                ],
                default=[
                    "Delta",
                    "Gamma",
                    "Vega",
                ],
            )
            if selected_greeks:
                greeks_points = calculate_greeks_profile(
                    portfolio=portfolio,
                    current_spot=current_spot,
                    minimum_change=-0.30,
                    maximum_change=0.30,
                    number_of_points=61,
                )
                greeks_data = normalize_dataframe_columns(
                    greeks_profile_to_dataframe(greeks_points)
                )
                st.altair_chart(
                    create_greeks_profile_chart(
                        greeks_data=greeks_data,
                        current_spot=current_spot,
                        selected_greeks=selected_greeks,
                    ),
                    width="stretch",
                )

    with probabilistic_tab:
        render_section_title(
            tr("Risque probabiliste", "Probabilistic Risk"),
            tr(
                "Lecture Monte Carlo de la distribution de pertes, des queues de risque et des principaux contributeurs.",
                "Monte Carlo read of loss distribution, tail risk and main downside contributors.",
            ),
        )

        selected_var = (
            probabilistic_result.var_95
            if probabilistic_confidence_percent == 95
            else probabilistic_result.var_99
        )
        selected_es = (
            probabilistic_result.expected_shortfall_95
            if probabilistic_confidence_percent == 95
            else probabilistic_result.expected_shortfall_99
        )

        setup_col_1, setup_col_2, setup_col_3, setup_col_4 = st.columns(4)
        setup_col_1.metric(
            tr("Horizon simulé", "Simulation Horizon"),
            f"{probabilistic_result.horizon_days} "
            + tr("jours", "days"),
        )
        setup_col_2.metric(
            tr("Nombre de scénarios", "Number of Scenarios"),
            f"{probabilistic_result.number_of_simulations:,.0f}",
        )
        setup_col_3.metric(
            tr("Confiance", "Confidence"),
            f"{probabilistic_confidence_percent}%",
        )
        setup_col_4.metric(
            tr("Base d'exposition", "Exposure Base"),
            f"{probabilistic_result.exposure_base:,.2f}",
        )

        prob_col_1, prob_col_2, prob_col_3, prob_col_4 = st.columns(4)

        prob_col_1.metric(
            tr("Probabilité de perte", "Probability of Loss"),
            f"{probabilistic_result.probability_of_loss:.1%}",
        )
        prob_col_2.metric(
            tr("Perte > 10%", "Loss > 10%"),
            f"{probabilistic_result.probability_loss_gt_10:.1%}",
        )
        prob_col_3.metric(
            f"VaR {probabilistic_confidence_percent}%",
            f"{selected_var:.1%}",
        )
        prob_col_4.metric(
            f"ES {probabilistic_confidence_percent}%",
            f"{selected_es:.1%}",
        )

        prob_col_5, prob_col_6, prob_col_7, prob_col_8 = st.columns(4)

        prob_col_5.metric(
            tr("Rendement moyen simulé", "Mean Simulated Return"),
            f"{probabilistic_result.mean_return:.1%}",
        )
        prob_col_6.metric(
            tr("Volatilité simulée", "Simulated Volatility"),
            f"{probabilistic_result.simulated_volatility:.1%}",
        )
        prob_col_7.metric(
            tr("Pire rendement", "Worst Return"),
            f"{probabilistic_result.worst_return:.1%}",
        )
        prob_col_8.metric(
            tr("Moteur principal", "Main Driver"),
            probabilistic_result.main_risk_driver,
        )

        distribution_chart = create_probabilistic_distribution_chart(
            simulations_data=probabilistic_simulations,
            selected_var=selected_var,
            selected_es=selected_es,
            
        )
        st.altair_chart(
            distribution_chart,
            width="stretch",
        )

        interpretation_col, controls_col = st.columns([1.5, 1])
        with interpretation_col:
            render_section_title(
                tr("Lecture institutionnelle", "Institutional Read"),
                tr(
                    "Ce que la simulation dit sur le profil perte/rendement du portefeuille.",
                    "What the simulation says about the portfolio loss/return profile.",
                ),
            )
            st.info(
                display_probabilistic_interpretation(
                    probabilistic_result,
                    ui_language,
                )
            )

        with controls_col:
            render_section_title(
                tr("Seuils de décision", "Decision Thresholds"),
                tr(
                    "Repères simples pour interpréter les probabilités.",
                    "Simple thresholds to interpret probabilities.",
                ),
            )
            if probabilistic_result.probability_loss_gt_10 >= 0.10:
                st.error(
                    tr(
                        "La probabilité de perte supérieure à 10% est élevée : réduire l'exposition ou couvrir avant d'ajouter du risque.",
                        "The probability of a loss greater than 10% is high: reduce exposure or hedge before adding risk.",
                    )
                )
            elif probabilistic_result.probability_of_loss >= 0.55:
                st.warning(
                    tr(
                        "La probabilité de perte est supérieure à 55% : vérifier le couple rendement/risque.",
                        "The probability of loss is above 55%: review the risk-return balance.",
                    )
                )
            else:
                st.success(
                    tr(
                        "La perte de queue reste contenue dans les hypothèses Monte Carlo choisies.",
                        "Tail loss remains contained under the selected Monte Carlo assumptions.",
                    )
                )

        metrics_table = probabilistic_metrics_table(probabilistic_result)
        metrics_display = metrics_table.copy()
        metrics_display["Value"] = metrics_display.apply(
            lambda row: (
                f"{row['Value']:.2%}"
                if row["Format"] == "percent"
                else f"{row['Value']:,.2f}"
            ),
            axis=1,
        )
        metric_labels = {
            "Probability of loss": tr("Probabilité de perte", "Probability of loss"),
            "Probability of loss > 5%": tr("Probabilité perte > 5%", "Probability of loss > 5%"),
            "Probability of loss > 10%": tr("Probabilité perte > 10%", "Probability of loss > 10%"),
            "Probability of loss > 20%": tr("Probabilité perte > 20%", "Probability of loss > 20%"),
            "Mean simulated return": tr("Rendement moyen simulé", "Mean simulated return"),
            "Simulated volatility": tr("Volatilité simulée", "Simulated volatility"),
            "VaR 95%": "VaR 95%",
            "Expected Shortfall 95%": "Expected Shortfall 95%",
            "VaR 99%": "VaR 99%",
            "Expected Shortfall 99%": "Expected Shortfall 99%",
            "Worst simulated return": tr("Pire rendement simulé", "Worst simulated return"),
            "Best simulated return": tr("Meilleur rendement simulé", "Best simulated return"),
        }
        metrics_display["Metric"] = metrics_display["Metric"].map(
            metric_labels
        ).fillna(metrics_display["Metric"])

        st.dataframe(
            metrics_display.rename(
                columns={
                    "Metric": tr("Indicateur", "Metric"),
                    "Value": tr("Valeur", "Value"),
                }
            )[
                [
                    tr("Indicateur", "Metric"),
                    tr("Valeur", "Value"),
                ]
            ],
            hide_index=True,
            width="stretch",
        )

        render_section_title(
            tr("Contributeurs aux pertes extrêmes", "Extreme-Loss Contributors"),
            tr(
                "Contribution moyenne aux pertes dans les pires 5% des simulations.",
                "Average contribution to losses in the worst 5% of simulations.",
            ),
        )

        contributors = contribution_table(probabilistic_result).head(8)
        if contributors.empty:
            st.info(
                tr(
                    "Aucun contributeur de risque significatif détecté.",
                    "No significant risk contributor detected.",
                )
            )
        else:
            contributors_display = contributors.rename(
                columns={
                    "Underlying": tr("Sous-jacent", "Underlying"),
                    "Average tail P&L": tr("P&L moyen en queue", "Average Tail P&L"),
                    "Downside contribution": tr("Contribution à la perte", "Downside Contribution"),
                    "Contribution %": tr("Contribution %", "Contribution %"),
                }
            )
            st.dataframe(
                contributors_display,
                hide_index=True,
                width="stretch",
            )

        render_section_title(
            tr("Actions de risk management", "Risk Management Actions"),
            tr(
                "Pistes prudentes à étudier, basées uniquement sur les résultats simulés.",
                "Prudent actions to review, based only on simulated results.",
            ),
        )

        recommendation_rows = [
            {
                tr("Priorité", "Priority"): "1",
                tr("Action", "Action"): tr(
                    f"Surveiller et réduire si nécessaire l'exposition à {probabilistic_result.main_risk_driver}.",
                    f"Monitor and reduce exposure to {probabilistic_result.main_risk_driver} if needed.",
                ),
                tr("Objectif", "Objective"): tr(
                    "Diminuer la contribution aux pertes extrêmes.",
                    "Reduce contribution to extreme losses.",
                ),
            },
            {
                tr("Priorité", "Priority"): "2",
                tr("Action", "Action"): tr(
                    "Comparer l'Expected Shortfall avec la perte maximale acceptable avant toute hausse de risque.",
                    "Compare Expected Shortfall with the maximum acceptable loss before increasing risk.",
                ),
                tr("Objectif", "Objective"): tr(
                    "Eviter d'augmenter un portefeuille déjà fragile en queue.",
                    "Avoid adding risk to a portfolio already fragile in the tail.",
                ),
            },
            {
                tr("Priorité", "Priority"): "3",
                tr("Action", "Action"): tr(
                    "Tester une couverture ou un allègement si la probabilité de perte dépasse le seuil interne.",
                    "Test hedging or trimming if the probability of loss exceeds the internal threshold.",
                ),
                tr("Objectif", "Objective"): tr(
                    "Optimiser le rendement ajusté du risque plutôt que le rendement brut.",
                    "Optimize risk-adjusted return rather than raw return.",
                ),
            },
        ]
        st.dataframe(
            pd.DataFrame(recommendation_rows),
            hide_index=True,
            width="stretch",
        )

        with st.expander(tr("Voir les simulations probabilistes", "Show Probabilistic Simulations")):
            st.dataframe(
                probabilistic_simulations,
                hide_index=True,
                width="stretch",
            )

    with alerts_tab:
        render_section_title(
            "Alertes quantitatives",
            "Signaux issus des limites, mouvements de marche et z-scores.",
        )

        if not alerts:
            st.success("Aucune anomalie detectee.")

        else:
            st.warning(f"{len(alerts)} anomalie(s) detectee(s).")

            with st.expander("Anomalies détectées", expanded=False):
                for alert in alerts:
                    alert_text = (
                        f"**{alert.name}** - "
                        f"{alert.message}\n\n"
                        f"Valeur actuelle : "
                        f"`{alert.current_value:.6f}`"
                    )

                    if alert.reference_value is not None:
                        alert_text += (
                            "\n\nValeur de reference : "
                            f"`{alert.reference_value:.6f}`"
                        )

                    if alert.z_score is not None:
                        alert_text += (
                            f"\n\nZ-score : "
                            f"`{alert.z_score:.2f}`"
                        )

                    if alert.severity == "CRITIQUE":
                        st.error(alert_text)

                    elif alert.severity in {"ELEVEE", "ÉLEVÉE", "Ã‰LEVÃ‰E"}:
                        st.warning(alert_text)

                    else:
                        st.info(alert_text)

        st.divider()

        render_section_title(
            tr("Note exécutive et LLM optionnel", "Executive Note and Optional LLM"),
            tr(
                "La note ARIA est toujours disponible. Le commentaire LLM n'est généré que si la case est cochée.",
                "The ARIA note is always available. LLM commentary is generated only when the checkbox is enabled.",
            ),
        )

        llm_analysis = None
        llm_analysis_en = None
        worst_scenario_for_commentary = min(
            scenario_results,
            key=lambda result: result.profit_and_loss,
        )
        worst_scenario_name_fr = display_scenario_name(
            worst_scenario_for_commentary.name,
            "fr",
        )
        worst_scenario_name_en = display_scenario_name(
            worst_scenario_for_commentary.name,
            "en",
        )
        aria_note = (
            "### Note exécutive ARIA\n\n"
            f"Le portefeuille obtient un score de risque **{risk_score_result.score}/100 "
            f"({display_risk_label(risk_score_result.label, 'fr')})**. "
            "Le scénario le plus défavorable est "
            f"**{worst_scenario_name_fr}** avec un P&L estimé de "
            f"**{worst_scenario_for_commentary.profit_and_loss:,.2f}**. "
            f"La VaR ressort à **{var_result.var_amount:,.2f}** et l'Expected "
            f"Shortfall à **{var_result.expected_shortfall:,.2f}**.\n\n"
            "**Actions à étudier :** réduire les expositions qui dominent le stress, "
            "contrôler Delta/Gamma/Vega contre les limites, et comparer le coût de "
            "couverture au rendement encore conservé. Ces pistes sont une aide à la "
            "décision de gestion du risque, pas une certitude de performance ni un "
            "conseil financier personnalisé."
        )
        aria_note_en = (
            "### ARIA Executive Note\n\n"
            f"The portfolio receives a risk score of **{risk_score_result.score}/100 "
            f"({display_risk_label(risk_score_result.label, 'en')})**. "
            "The worst scenario is "
            f"**{worst_scenario_name_en}** with estimated P&L of "
            f"**{worst_scenario_for_commentary.profit_and_loss:,.2f}**. "
            f"VaR is **{var_result.var_amount:,.2f}** and Expected Shortfall is "
            f"**{var_result.expected_shortfall:,.2f}**.\n\n"
            "**Actions to review:** reduce exposures dominating stress losses, "
            "check Delta/Gamma/Vega against limits, and compare hedging cost with "
            "remaining return potential. These are risk-management decision aids, "
            "not performance certainty or personalized financial advice."
        )

        if enable_llm_commentary:
            with st.spinner(tr("ARIA génère le commentaire LLM...", "ARIA is generating the LLM commentary...")):
                llm_analysis = generate_llm_analysis(
                    snapshot=current_snapshot,
                    alerts=alerts,
                    risk_score_result=risk_score_result,
                    scenario_results=scenario_results,
                    var_result=var_result,
                    probabilistic_result=probabilistic_result,
                    portfolio_diagnosis_result=current_diagnosis,
                    hedge_result=hedge_result,
                    market_snapshot=market_snapshot,
                    language="fr",
                )

                llm_analysis_en = generate_llm_analysis(
                    snapshot=current_snapshot,
                    alerts=alerts,
                    risk_score_result=risk_score_result,
                    scenario_results=scenario_results,
                    var_result=var_result,
                    probabilistic_result=probabilistic_result,
                    portfolio_diagnosis_result=current_diagnosis,
                    hedge_result=hedge_result,
                    market_snapshot=market_snapshot,
                    language="en",
                )

        else:
            st.info(
                tr(
                    "Commentaire LLM désactivé : aucun appel API n'est lancé. Le rapport reste généré par ARIA avec les métriques quantitatives.",
                    "LLM commentary disabled: no API call is made. The report is still generated by ARIA with quantitative metrics.",
                )
            )

        with st.expander(tr("Voir la note exécutive ARIA", "Show ARIA Executive Note"), expanded=True):
            st.markdown(aria_note if ui_language == "fr" else aria_note_en)

        if llm_analysis:
            with st.expander(tr("Voir le commentaire LLM", "Show LLM Commentary"), expanded=True):
                st.markdown(llm_analysis if ui_language == "fr" else llm_analysis_en)

        st.divider()

        render_section_title(
            tr("Rapport de risque", "Risk Report"),
            tr(
                "Exports Markdown et PDF structurés comme une note de risk management.",
                "Markdown and PDF exports structured as a risk-management memo.",
            ),
        )

        report_text = generate_risk_report(
            portfolio=portfolio,
            spot=current_spot,
            volatility=current_volatility,
            alerts=alerts,
            scenario_results=scenario_results,
            var_result=var_result,
            parametric_var=parametric_var,
            probabilistic_result=probabilistic_result,
            hedge_result=hedge_result,
            risk_score_result=risk_score_result,
            market_snapshot=market_snapshot,
            llm_analysis=llm_analysis_en if ui_language == "en" else llm_analysis,
            
        )

        with st.expander(tr("Aperçu du rapport téléchargeable", "Downloadable Report Preview"), expanded=True):
            st.markdown(report_text)

        report_pdf_fr = generate_professional_pdf_report(
            portfolio=portfolio,
            spot=current_spot,
            volatility=current_volatility,
            alerts=alerts,
            scenario_results=scenario_results,
            var_result=var_result,
            parametric_var=parametric_var,
            probabilistic_result=probabilistic_result,
            hedge_result=hedge_result,
            risk_score_result=risk_score_result,
            market_snapshot=market_snapshot,
            llm_analysis=llm_analysis,
            language="fr",
        )

        report_pdf_en = generate_professional_pdf_report(
            portfolio=portfolio,
            spot=current_spot,
            volatility=current_volatility,
            alerts=alerts,
            scenario_results=scenario_results,
            var_result=var_result,
            parametric_var=parametric_var,
            probabilistic_result=probabilistic_result,
            hedge_result=hedge_result,
            risk_score_result=risk_score_result,
            market_snapshot=market_snapshot,
            llm_analysis=llm_analysis_en,
            language="en",
        )

        report_download_col_1, report_download_col_2, report_download_col_3 = st.columns(3)

        report_download_col_1.download_button(
            label=tr("Télécharger le rapport Markdown", "Download Markdown Report"),
            data=report_text,
            file_name="rapport_risque_aria.md",
            mime="text/markdown",
            type="secondary",
            width="stretch",
        )

        report_download_col_2.download_button(
            label=tr("Télécharger le rapport PDF français", "Download French PDF Report"),
            data=report_pdf_fr,
            file_name="rapport_risque_aria_fr.pdf",
            mime="application/pdf",
            type="primary",
            width="stretch",
        )

        report_download_col_3.download_button(
            label=tr("Télécharger le rapport PDF anglais", "Download English PDF Report"),
            data=report_pdf_en,
            file_name="aria_risk_report_en.pdf",
            mime="application/pdf",
            type="secondary",
            width="stretch",
        )

        st.caption(
            tr(
                "Le rapport est disponible en Markdown, PDF français et PDF anglais. "
                "Il mentionne clairement que le projet a été développé par Enrique Jara Ron.",
                "The report is available as Markdown, French PDF and English PDF. "
                "It clearly states that the project was developed by Enrique Jara Ron.",
            )
        )

    st.success(
        tr(
            "Le snapshot actuel a été ajouté à l'historique.",
            "The current snapshot was added to history.",
        )
    )
