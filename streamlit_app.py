"""
ARIA - Application Streamlit
"""

import unicodedata

import altair as alt
import pandas as pd
import streamlit as st

from anomaly_detector import AnomalyDetector, create_snapshot
from app_config import (
    DEFAULT_MARKET_DATA_PATH,
    DEFAULT_PORTFOLIO_PATH,
    RISK_HISTORY_PATH,
    ensure_runtime_directories,
    relative_to_project,
    resolve_project_path,
)
from aria_workflow import generate_llm_analysis
from demo_portfolios import (
    create_demo_portfolio,
    get_demo_portfolio_names,
    portfolio_to_dataframe,
)
from greeks_profile import calculate_greeks_profile, greeks_profile_to_dataframe
from hedging_analysis import calculate_delta_hedge
from history_analytics import (
    clean_history_dataframe,
    get_history_summary,
    load_history_dataframe,
)
from market_data import ManualMarketDataProvider, get_provider
from pnl_profile import (
    calculate_pnl_profile,
    find_breakeven_spots,
    pnl_profile_to_dataframe,
)
from portfolio import Portfolio
from portfolio_ai_generator import (
    DISCLAIMER as AI_PORTFOLIO_DISCLAIMER,
)
from portfolio_ai_generator import (
    generate_ai_portfolio,
    generated_portfolio_to_aria_table,
)
from portfolio_analytics import (
    PROFESSIONAL_COLUMNS,
    get_model_portfolio,
    get_model_portfolio_names,
    model_portfolio_to_dataframe,
    portfolio_diagnosis,
    portfolio_exposure_table,
    rebalancing_recommendations,
    validate_portfolio_table,
)
from pricing_BS import OptionContract
from probabilistic_risk import (
    contribution_table,
    probabilistic_metrics_table,
    simulate_probabilistic_risk,
)
from report_generator import generate_professional_pdf_report, generate_risk_report
from risk_history import RiskHistory
from risk_score import calculate_risk_score
from risk_surface import calculate_risk_surface, surface_to_dataframe
from scenario_analysis import (
    run_historical_scenarios,
    run_scenario,
    run_standard_scenarios,
)
from ui_components import (
    inject_custom_css,
    render_header,
    render_info_card,
    render_metric_row,
    render_risk_badge,
    render_section_title,
    render_status_pill,
)
from var_analysis import calculate_var_es, parametric_var_estimate

st.set_page_config(
    page_title="ARIA Risk Agent",
    page_icon="📊",
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
    "Ticker",
    "Nom",
    "Asset type",
    "Option type",
    "Strike",
    "Maturity",
    "Volatility",
    "Rate",
    "Contract size",
]

PORTFOLIO_INTERNAL_COLUMNS = PROFESSIONAL_COLUMNS

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
        "Ticker": "SPY",
        "Sous-jacent": "SPY",
        "Nom": "Position",
        "Sector": "Unclassified",
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

    for column, value in defaults.items():
        if column not in normalized.columns:
            normalized[column] = value

    normalized = normalized.replace(
        {
            "": pd.NA,
            " ": pd.NA,
        }
    )

    normalized["Ticker"] = normalized["Ticker"].fillna(
        normalized["Sous-jacent"]
    )
    normalized["Ticker"] = normalized["Ticker"].fillna("SPY")
    normalized["Sous-jacent"] = normalized["Sous-jacent"].fillna(
        normalized["Ticker"]
    )
    normalized["Nom"] = normalized["Nom"].fillna(normalized["Ticker"])
    normalized["Sector"] = normalized["Sector"].fillna("Unclassified")
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

    stock_rows = normalized.loc[stock_mask].copy()
    option_rows = normalized.loc[option_mask].copy()

    if not stock_rows.empty:
        grouped_stock_rows = []
        for _, group in stock_rows.groupby("Ticker", dropna=False, sort=False):
            first = group.iloc[0].copy()
            first["Quantity"] = group["Quantity"].sum()
            first["Quantite"] = first["Quantity"]
            first["Value"] = group["Value"].sum()
            first["Weight"] = group["Weight"].sum()
            comments = [
                str(comment)
                for comment in group["Commentaire"].dropna().unique()
                if str(comment).strip()
            ]
            first["Commentaire"] = " | ".join(comments[:3])
            grouped_stock_rows.append(first)
        stock_rows = pd.DataFrame(grouped_stock_rows)

    normalized = pd.concat(
        [
            option_rows,
            stock_rows,
        ],
        ignore_index=True,
    )

    weight_total = float(normalized["Weight"].fillna(0).sum())
    if not normalized.empty and abs(weight_total - 100.0) <= 0.05:
        rounding_gap = 100.0 - weight_total
        max_weight_index = normalized["Weight"].fillna(0).idxmax()
        normalized.loc[max_weight_index, "Weight"] = round(
            float(normalized.loc[max_weight_index, "Weight"]) + rounding_gap,
            4,
        )

    normalized = normalized.drop_duplicates(
        ignore_index=True,
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


def create_stress_chart(scenario_results) -> alt.Chart:
    """Cree un graphique des profits et pertes par scenario."""
    chart_data = pd.DataFrame(
        [
            {
                "Scenario": result.name,
                "Profit / Perte": result.profit_and_loss,
                "Resultat": "Gain" if result.profit_and_loss >= 0 else "Perte",
            }
            for result in scenario_results
        ]
    )

    bars = alt.Chart(chart_data).mark_bar(
        cornerRadiusEnd=6,
        size=32,
    ).encode(
        y=alt.Y(
            "Scenario:N",
            sort=None,
            title=None,
        ),
        x=alt.X(
            "Profit / Perte:Q",
            title="Profit / Perte du portefeuille",
        ),
        color=alt.Color(
            "Resultat:N",
            scale=alt.Scale(
                domain=["Gain", "Perte"],
                range=["#19A974", "#E05252"],
            ),
            legend=alt.Legend(
                title=None,
                orient="top",
            ),
        ),
        tooltip=[
            alt.Tooltip("Scenario:N", title="Scenario"),
            alt.Tooltip(
                "Profit / Perte:Q",
                title="Profit / Perte",
                format=",.2f",
            ),
        ],
    )

    labels = alt.Chart(chart_data).mark_text(
        align="left",
        baseline="middle",
        dx=6,
        fontSize=13,
        fontWeight="bold",
    ).encode(
        y=alt.Y("Scenario:N", sort=None),
        x=alt.X("Profit / Perte:Q"),
        text=alt.Text("Profit / Perte:Q", format=",.2f"),
        color=alt.condition(
            alt.datum["Profit / Perte"] >= 0,
            alt.value("#117A55"),
            alt.value("#B83A3A"),
        ),
    )

    zero_line = alt.Chart(
        pd.DataFrame({"x": [0]})
    ).mark_rule(
        color="#6B7280",
        strokeWidth=1.5,
    ).encode(
        x="x:Q",
    )

    return (
        bars
        + labels
        + zero_line
    ).properties(
        height=360,
        title=alt.TitleParams(
            text="Impact des scenarios sur le portefeuille",
            subtitle="A droite : gain potentiel - A gauche : perte potentielle",
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


def create_pnl_profile_chart(
    pnl_data: pd.DataFrame,
    current_spot: float,
    breakeven_spots: list[float],
) -> alt.Chart:
    """Cree une courbe de P&L selon le niveau du spot."""
    chart_data = normalize_dataframe_columns(pnl_data)

    chart_data["Resultat"] = chart_data["Profit / Perte"].apply(
        lambda value: "Gain" if value >= 0 else "Perte"
    )

    line = alt.Chart(chart_data).mark_line(
        strokeWidth=3,
        color="#2563EB",
    ).encode(
        x=alt.X(
            "Spot stressé:Q",
            title="Niveau du spot",
        ),
        y=alt.Y(
            "Profit / Perte:Q",
            title="Profit / Perte",
        ),
        tooltip=[
            alt.Tooltip(
                "Spot stressé:Q",
                title="Spot",
                format=",.2f",
            ),
            alt.Tooltip(
                "Variation spot:Q",
                title="Variation du spot",
                format="+.1%",
            ),
            alt.Tooltip(
                "Profit / Perte:Q",
                title="Profit / Perte",
                format=",.2f",
            ),
        ],
    )

    points = alt.Chart(chart_data).mark_circle(
        size=45,
    ).encode(
        x="Spot stressé:Q",
        y="Profit / Perte:Q",
        color=alt.Color(
            "Resultat:N",
            scale=alt.Scale(
                domain=["Gain", "Perte"],
                range=["#19A974", "#E05252"],
            ),
            legend=alt.Legend(
                title=None,
                orient="top",
            ),
        ),
    )

    zero_line = alt.Chart(
        pd.DataFrame({"y": [0]})
    ).mark_rule(
        color="#6B7280",
        strokeDash=[6, 4],
        strokeWidth=1.5,
    ).encode(
        y="y:Q",
    )

    current_spot_line = alt.Chart(
        pd.DataFrame({"x": [current_spot]})
    ).mark_rule(
        color="#111827",
        strokeWidth=2,
    ).encode(
        x="x:Q",
    )

    breakeven_lines = alt.Chart(
        pd.DataFrame({"x": breakeven_spots})
    ).mark_rule(
        color="#F59E0B",
        strokeDash=[4, 4],
        strokeWidth=2,
    ).encode(
        x="x:Q",
    )

    return (
        line
        + points
        + zero_line
        + current_spot_line
        + breakeven_lines
    ).properties(
        height=420,
        title=alt.TitleParams(
            text="Profil de P&L selon le niveau du spot",
            subtitle="Ligne noire : spot actuel - ligne orange : point mort approximatif",
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
) -> alt.Chart:
    """Create the Monte Carlo return distribution chart."""

    chart_data = simulations_data.copy()
    chart_data["Portfolio return percent"] = chart_data["Portfolio return"] * 100
    selected_var_percent = selected_var * 100
    selected_es_percent = selected_es * 100

    histogram = alt.Chart(chart_data).mark_bar(
        color="#155E75",
        opacity=0.82,
    ).encode(
        x=alt.X(
            "Portfolio return percent:Q",
            bin=alt.Bin(maxbins=55),
            title="Rendement simulé du portefeuille (%)",
        ),
        y=alt.Y(
            "count():Q",
            title="Nombre de simulations",
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
                ],
                range=[
                    "#B91C1C",
                    "#7C2D12",
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
                title="Seuil",
            ),
            alt.Tooltip(
                "Return:Q",
                title="Rendement",
                format=".2f",
            ),
        ],
    )

    return (
        histogram + rules
    ).properties(
        height=340,
        title=alt.TitleParams(
            text="Distribution Monte Carlo des rendements",
            subtitle="Chaque barre regroupe des scénarios simulés sur l'horizon sélectionné",
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


def create_greeks_profile_chart(
    greeks_data: pd.DataFrame,
    current_spot: float,
    selected_greeks: list[str],
) -> alt.Chart:
    """Cree une courbe des Greeks selon le niveau du spot."""
    greeks_data = normalize_dataframe_columns(greeks_data)

    chart_data = greeks_data[
        ["Spot stressé", "Variation spot"] + selected_greeks
    ].copy()

    long_data = chart_data.melt(
        id_vars=["Spot stressé", "Variation spot"],
        value_vars=selected_greeks,
        var_name="Greek",
        value_name="Valeur",
    )

    lines = alt.Chart(long_data).mark_line(
        strokeWidth=3,
    ).encode(
        x=alt.X(
            "Spot stressé:Q",
            title="Niveau du spot",
        ),
        y=alt.Y(
            "Valeur:Q",
            title="Valeur du Greek",
        ),
        color=alt.Color(
            "Greek:N",
            legend=alt.Legend(
                title=None,
                orient="top",
            ),
        ),
        tooltip=[
            alt.Tooltip("Greek:N", title="Greek"),
            alt.Tooltip(
                "Spot stressé:Q",
                title="Spot",
                format=",.2f",
            ),
            alt.Tooltip(
                "Variation spot:Q",
                title="Variation du spot",
                format="+.1%",
            ),
            alt.Tooltip(
                "Valeur:Q",
                title="Valeur",
                format=",.4f",
            ),
        ],
    )

    current_spot_line = alt.Chart(
        pd.DataFrame({"x": [current_spot]})
    ).mark_rule(
        color="#111827",
        strokeWidth=2,
    ).encode(
        x="x:Q",
    )

    return (
        lines
        + current_spot_line
    ).properties(
        height=420,
        title=alt.TitleParams(
            text="Profil des Greeks selon le niveau du spot",
            subtitle="La volatilite reste constante. La ligne noire indique le spot actuel.",
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


def create_history_chart(
    history_data: pd.DataFrame,
    metric: str,
) -> alt.Chart:
    """Cree une courbe historique pour une metrique donnee."""
    chart_data = history_data.copy()

    line = alt.Chart(chart_data).mark_line(
        strokeWidth=3,
        color="#2563EB",
    ).encode(
        x=alt.X(
            "timestamp:T",
            title="Date",
        ),
        y=alt.Y(
            f"{metric}:Q",
            title=metric,
        ),
        tooltip=[
            alt.Tooltip("timestamp:T", title="Date"),
            alt.Tooltip(
                f"{metric}:Q",
                title=metric,
                format=",.4f",
            ),
        ],
    )

    points = alt.Chart(chart_data).mark_circle(
        size=50,
        color="#2563EB",
    ).encode(
        x="timestamp:T",
        y=f"{metric}:Q",
        tooltip=[
            alt.Tooltip("timestamp:T", title="Date"),
            alt.Tooltip(
                f"{metric}:Q",
                title=metric,
                format=",.4f",
            ),
        ],
    )

    return (
        line
        + points
    ).properties(
        height=380,
        title=alt.TitleParams(
            text=f"Historique de {metric}",
            subtitle="Evolution des snapshots sauvegardes par ARIA",
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


inject_custom_css()

render_header(
    title="ARIA - Adaptive Risk Intelligence Agent",
    subtitle=(
        "Dashboard Python / Streamlit pour le suivi du risque de "
        "portefeuilles actions-options : pricing, Greeks, stress tests, "
        "VaR, alertes quantitatives et reporting LLM."
    ),
)


st.sidebar.header("Donnees de marche")

market_source = st.sidebar.selectbox(
    "Source de donnees de marche",
    options=[
        "Manuel",
        "Yahoo Finance",
        "CSV local",
        "Bloomberg optionnel",
    ],
    index=0,
)

market_ticker = st.sidebar.text_input(
    "Ticker",
    value="SPY",
)

csv_market_data_path = None

if market_source == "CSV local":
    csv_market_data_path = st.sidebar.text_input(
        "Chemin du CSV local",
        value=relative_to_project(DEFAULT_MARKET_DATA_PATH),
    )

market_snapshot = None
market_data_status = "Manual Mode"
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
            "Bloomberg Unavailable"
            if market_source == "Bloomberg optionnel"
            else "Source unavailable"
        )
        st.sidebar.info(str(error))


st.sidebar.header("Marche")

current_spot = st.sidebar.number_input(
    "Prix du sous-jacent",
    min_value=0.01,
    value=float(default_spot),
    step=1.0,
)

current_volatility_percent = st.sidebar.number_input(
    "Volatilite utilisee en %",
    min_value=0.01,
    value=float(default_volatility_percent),
    step=1.0,
)

risk_free_rate_percent = st.sidebar.number_input(
    "Taux sans risque en %",
    value=5.0,
    step=0.25,
)

dividend_yield_percent = st.sidebar.number_input(
    "Rendement du dividende en %",
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


st.sidebar.header("Limites de risque")

delta_limit = st.sidebar.number_input(
    "Limite de delta",
    min_value=0.0,
    value=10.0,
    step=1.0,
)

gamma_limit = st.sidebar.number_input(
    "Limite de gamma",
    min_value=0.0,
    value=1.0,
    step=0.1,
)

vega_limit = st.sidebar.number_input(
    "Limite de vega",
    min_value=0.0,
    value=20.0,
    step=1.0,
)

spot_move_limit_percent = st.sidebar.number_input(
    "Variation maximale du spot en %",
    min_value=0.1,
    value=3.0,
    step=0.5,
)

volatility_move_limit_percent = st.sidebar.number_input(
    "Variation maximale de volatilite en points",
    min_value=0.1,
    value=5.0,
    step=0.5,
)

z_score_limit = st.sidebar.number_input(
    "Limite du z-score",
    min_value=0.5,
    value=2.5,
    step=0.1,
)


st.sidebar.header("Scenario personnalise")

custom_spot_change_percent = st.sidebar.number_input(
    "Choc du spot en %",
    value=-10.0,
    step=1.0,
)

custom_volatility_change_points = st.sidebar.number_input(
    "Choc de volatilite en points",
    value=15.0,
    step=1.0,
)


st.sidebar.header("VaR / Expected Shortfall")

var_confidence_percent = st.sidebar.selectbox(
    "Niveau de confiance",
    options=[95, 99],
    index=0,
)

var_horizon_days = st.sidebar.number_input(
    "Horizon en jours",
    min_value=1,
    value=1,
    step=1,
)

var_simulations = st.sidebar.number_input(
    "Nombre de simulations",
    min_value=100,
    max_value=10000,
    value=1000,
    step=100,
)

st.sidebar.header("Probabilistic Risk")

probabilistic_horizon_label = st.sidebar.selectbox(
    "Horizon probabiliste",
    options=[
        "1 jour",
        "1 semaine",
        "1 mois",
        "3 mois",
        "6 mois",
        "1 an",
    ],
    index=2,
)

probabilistic_horizon_days = {
    "1 jour": 1,
    "1 semaine": 5,
    "1 mois": 21,
    "3 mois": 63,
    "6 mois": 126,
    "1 an": 252,
}[probabilistic_horizon_label]

probabilistic_simulations_count = st.sidebar.selectbox(
    "Simulations probabilistes",
    options=[
        1000,
        5000,
        10000,
    ],
    index=1,
)

probabilistic_confidence_percent = st.sidebar.selectbox(
    "Confiance probabiliste",
    options=[
        95,
        99,
    ],
    index=0,
)

st.sidebar.header("LLM")

enable_llm_commentary = st.sidebar.checkbox(
    "Activer le commentaire LLM",
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
    "Portefeuille client",
    "Importez, chargez une allocation modèle ou générez un portefeuille assisté par IA.",
)

manual_tab, demo_tab, ai_tab = st.tabs(
    [
        "A. Modifier / importer",
        "B. Portefeuilles de démonstration",
        "C. Créer avec l'IA",
    ]
)

with manual_tab:
    portfolio_file_path = st.text_input(
        "Fichier portefeuille CSV",
        value=relative_to_project(DEFAULT_PORTFOLIO_PATH),
    )

    portfolio_action_col_1, portfolio_action_col_2, portfolio_action_col_3 = st.columns(3)

    if portfolio_action_col_1.button(
        "Sauvegarder le portefeuille",
        width="stretch",
    ):
        portfolio_path = resolve_project_path(portfolio_file_path)
        portfolio_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        st.session_state.portfolio_data.reindex(
            columns=PORTFOLIO_EDITOR_COLUMNS
        ).to_csv(
            portfolio_path,
            index=False,
        )

        st.success(f"Portefeuille sauvegarde : {portfolio_file_path}")

    if portfolio_action_col_2.button(
        "Charger le portefeuille",
        width="stretch",
    ):
        portfolio_path = resolve_project_path(portfolio_file_path)

        if not portfolio_path.exists():
            st.error(f"Fichier introuvable : {portfolio_file_path}")
            st.stop()

        loaded_portfolio = pd.read_csv(portfolio_path)

        st.session_state.portfolio_data = normalize_portfolio_table(
            loaded_portfolio,
            default_spot_value=current_spot,
            default_volatility_value=current_volatility,
        )

        if "portfolio_editor" in st.session_state:
            del st.session_state["portfolio_editor"]

        st.rerun()

    if portfolio_action_col_3.button(
        "Reinitialiser",
        width="stretch",
    ):
        st.session_state.portfolio_data = default_portfolio()

        if "portfolio_editor" in st.session_state:
            del st.session_state["portfolio_editor"]

        st.rerun()

    render_info_card(
        "Lecture des positions",
        (
            "Une quantité positive correspond à une position achetée. "
            "Une quantité négative correspond à une position vendue. "
            "Les colonnes techniques nécessaires au moteur ARIA sont "
            "reconstruites automatiquement."
        ),
    )

with demo_tab:
    selected_demo_portfolio = st.selectbox(
        "Portefeuille de démonstration",
        options=get_demo_portfolio_names(),
    )

    if selected_demo_portfolio in get_model_portfolio_names():
        selected_model = get_model_portfolio(selected_demo_portfolio)
        demo_kpi_1, demo_kpi_2, demo_kpi_3, demo_kpi_4 = st.columns(4)
        demo_kpi_1.metric("Risque", selected_model.risk_level)
        demo_kpi_2.metric("Horizon", "Long terme")
        demo_kpi_3.metric("Vol. estimée", f"{selected_model.volatility:.1%}")
        demo_kpi_4.metric("Drawdown", f"{selected_model.drawdown:.1%}")
        st.info(
            f"{selected_model.explanation} Profil adapté : "
            f"{selected_model.investor_profile}"
        )

    if st.button(
        "Charger ce portefeuille",
        width="stretch",
    ):
        if selected_demo_portfolio in get_model_portfolio_names():
            loaded_demo_data = model_portfolio_to_dataframe(
                get_model_portfolio(selected_demo_portfolio)
            )
        else:
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

with ai_tab:
    st.caption(AI_PORTFOLIO_DISCLAIMER)

    with st.form("ai_portfolio_form"):
        ai_col_1, ai_col_2 = st.columns(2)
        horizon = ai_col_1.selectbox(
            "Horizon",
            ["Long term", "Medium term", "Short term"],
        )
        risk_level = ai_col_2.selectbox(
            "Niveau de risque",
            ["Moderate", "Low", "High"],
        )
        instruments = ai_col_1.multiselect(
            "Instruments preferes",
            ["ETF", "Stocks", "Bonds", "Commodities", "Options"],
            default=["ETF", "Stocks", "Bonds"],
        )
        style = ai_col_2.selectbox(
            "Style",
            [
                "Balanced",
                "Growth",
                "Defensive",
                "Dividend",
                "ESG",
                "AI / Semiconductors",
                "Inflation protection",
            ],
        )
        geography = ai_col_1.selectbox(
            "Zone geographique",
            ["Global", "US", "Europe", "Emerging markets"],
        )
        simulated_amount = ai_col_2.number_input(
            "Montant simule",
            min_value=1_000,
            value=100_000,
            step=5_000,
        )
        preferred_sectors = st.text_input(
            "Secteurs a privilegier",
            value="technology, healthcare, quality equities",
        )
        avoided_sectors = st.text_input(
            "Secteurs a eviter",
            value="",
        )
        included_names = st.text_input(
            "Entreprises ou ETF a inclure si coherent",
            value="",
        )
        excluded_names = st.text_input(
            "Entreprises ou ETF a exclure",
            value="",
        )
        submitted_ai_portfolio = st.form_submit_button(
            "Generer le portefeuille",
            width="stretch",
        )

    if submitted_ai_portfolio:
        st.session_state.ai_portfolio_result = generate_ai_portfolio(
            {
            "horizon": horizon,
            "risk_level": risk_level,
                "instruments": instruments,
                "style": style,
                "geography": geography,
                "simulated_amount": simulated_amount,
                "preferred_sectors": preferred_sectors,
                "avoided_sectors": avoided_sectors,
                "included_names": included_names,
                "excluded_names": excluded_names,
            }
        )
        st.session_state.ai_portfolio_result["simulated_amount"] = float(
            simulated_amount
        )

    if "ai_portfolio_result" in st.session_state:
        ai_result = st.session_state.ai_portfolio_result
        st.success(
            "Portefeuille genere avec le LLM."
            if ai_result["used_llm"]
            else "Portefeuille genere en mode structure local."
        )
        st.write(ai_result["strategy"])
        if ai_result["warnings"]:
            for warning in ai_result["warnings"]:
                st.warning(warning)
        ai_display = ai_result["portfolio"].rename(
            columns={
                "ticker": "Ticker",
                "name": "Nom",
                "weight": "Poids (%)",
                "asset_class": "Classe d'actif",
                "sector": "Secteur",
                "rationale": "Justification",
            }
        )
        st.dataframe(
            ai_display,
            hide_index=True,
            width="stretch",
        )
        if ai_result["limits"]:
            st.caption("Limites : " + " | ".join(ai_result["limits"]))

        use_ai_col_1, use_ai_col_2 = st.columns(2)
        if use_ai_col_1.button(
            "Utiliser ce portefeuille dans ARIA",
            width="stretch",
        ):
            st.session_state.portfolio_data = normalize_portfolio_table(
                generated_portfolio_to_aria_table(
                    ai_result["portfolio"],
                    total_value=float(
                        ai_result.get("simulated_amount", simulated_amount)
                    ),
                ),
                default_spot_value=current_spot,
                default_volatility_value=current_volatility,
            )

            if "portfolio_editor" in st.session_state:
                del st.session_state["portfolio_editor"]

            st.rerun()
        if use_ai_col_2.button(
            "Lancer l'analyse ARIA",
            width="stretch",
        ):
            st.session_state.portfolio_data = normalize_portfolio_table(
                generated_portfolio_to_aria_table(
                    ai_result["portfolio"],
                    total_value=float(
                        ai_result.get("simulated_amount", simulated_amount)
                    ),
                ),
                default_spot_value=current_spot,
                default_volatility_value=current_volatility,
            )
            st.session_state.launch_analysis_requested = True

            if "portfolio_editor" in st.session_state:
                del st.session_state["portfolio_editor"]

            st.rerun()

editor_data = st.session_state.portfolio_data.reindex(
    columns=PORTFOLIO_EDITOR_COLUMNS
)

edited_portfolio = st.data_editor(
    editor_data,
    key="portfolio_editor",
    num_rows="dynamic",
    hide_index=True,
    width="stretch",
    column_order=PORTFOLIO_EDITOR_COLUMNS,
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker"),
        "Nom": st.column_config.TextColumn("Nom"),
        "Asset class": st.column_config.TextColumn("Classe d'actif"),
        "Sector": st.column_config.TextColumn("Secteur"),
        "Weight": st.column_config.NumberColumn(
            "Poids (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.5,
            format="%.2f",
        ),
        "Value": st.column_config.NumberColumn(
            "Valeur",
            min_value=0.0,
            step=100.0,
            format="%.2f",
        ),
        "Currency": st.column_config.SelectboxColumn(
            "Devise",
            options=["USD", "EUR", "GBP", "CHF", "JPY"],
        ),
        "Quantity": st.column_config.NumberColumn(
            "Quantité",
            step=1.0,
            format="%.4f",
        ),
        "Price": st.column_config.NumberColumn(
            "Prix",
            min_value=0.01,
            step=1.0,
        ),
        "Data source": st.column_config.TextColumn("Source"),
        "Commentaire": st.column_config.TextColumn("Commentaire"),
        "Asset type": st.column_config.SelectboxColumn(
            "Type d'actif",
            options=["stock", "option"],
            required=True,
        ),
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

portfolio_validation_errors = validate_portfolio_table(
    st.session_state.portfolio_data
)

if portfolio_validation_errors:
    render_section_title(
        "Validation du portefeuille",
        "ARIA bloque les incohérences avant de lancer les calculs de risque.",
    )
    for validation_error in portfolio_validation_errors:
        st.error(validation_error)

render_section_title(
    "Diagnostic rapide du portefeuille",
    "Lecture synthétique avant analyse ARIA.",
)

current_exposure_table = portfolio_exposure_table(
    st.session_state.portfolio_data
)
current_diagnosis = portfolio_diagnosis(
    st.session_state.portfolio_data
)

portfolio_kpi_1, portfolio_kpi_2, portfolio_kpi_3, portfolio_kpi_4 = st.columns(4)
portfolio_kpi_1.metric(
    "Exposition brute",
    f"{current_diagnosis['gross_exposure']:,.0f}",
)
portfolio_kpi_2.metric(
    "1re position",
    current_diagnosis["top_position"],
    f"{current_diagnosis['top_weight']:.1%}",
)
portfolio_kpi_3.metric(
    "Actifs",
    current_diagnosis["number_of_assets"],
)
portfolio_kpi_4.metric(
    "Concentration",
    current_diagnosis["concentration_level"],
)

st.caption(current_diagnosis["diversification_comment"])

with st.expander("Détails avancés : expositions, poids et réallocation", expanded=False):
    if not current_exposure_table.empty:
        exposure_display = current_exposure_table.copy()
        exposure_display["Gross weight"] = exposure_display["Gross weight"].map(
            "{:.2%}".format
        )
        exposure_display["Net weight"] = exposure_display["Net weight"].map(
            "{:.2%}".format
        )
        exposure_display = exposure_display.rename(
            columns={
                "Ticker": "Ticker",
                "Name": "Nom",
                "Asset type": "Type d'actif",
                "Asset class": "Classe d'actif",
                "Sector": "Secteur",
                "Currency": "Devise",
                "Quantity": "Quantité",
                "Price": "Prix",
                "Market value": "Valeur",
                "Gross exposure": "Exposition brute",
                "Gross weight": "Poids brut",
                "Net weight": "Poids net",
                "Data source": "Source",
            }
        )
        st.dataframe(
            exposure_display,
            hide_index=True,
            width="stretch",
        )

    target_model_name = st.selectbox(
        "Portefeuille cible pour comparer la réallocation",
        options=get_model_portfolio_names(),
        index=1,
    )
    target_model = get_model_portfolio(target_model_name)

    model_col_1, model_col_2, model_col_3, model_col_4 = st.columns(4)
    model_col_1.metric("Profil cible", target_model.risk_level)
    model_col_2.metric("Rendement estimé", f"{target_model.expected_return:.1%}")
    model_col_3.metric("Volatilité estimée", f"{target_model.volatility:.1%}")
    model_col_4.metric("Drawdown indicatif", f"{target_model.drawdown:.1%}")

    st.info(
        f"{target_model.explanation} Profil adapté : {target_model.investor_profile} "
        "Ces chiffres sont des estimations basées sur les hypothèses ARIA, pas des rendements garantis."
    )

    rebalance_table, rebalance_summary = rebalancing_recommendations(
        current_table=st.session_state.portfolio_data,
        target_model=target_model,
    )

    rebalance_display = rebalance_table.copy()
    for percent_column in [
        "Current weight",
        "Target weight",
    ]:
        rebalance_display[percent_column] = rebalance_display[percent_column].map(
            "{:.2%}".format
        )
    for amount_column in [
        "Current amount",
        "Target amount",
        "Change amount",
    ]:
        rebalance_display[amount_column] = rebalance_display[amount_column].map(
            "{:,.0f}".format
        )

    st.dataframe(
        rebalance_display,
        hide_index=True,
        width="stretch",
    )
    st.write(rebalance_summary["expected_impact"])


analyse_button = st.button(
    "Lancer l'analyse ARIA",
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
    if portfolio_validation_errors:
        st.error(
            "Corrige les erreurs de portefeuille avant de lancer l'analyse ARIA."
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
        st.error(str(error))
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

    updated_history = load_history_dataframe(RISK_HISTORY_PATH)
    updated_history = clean_history_dataframe(updated_history)
    history_summary = get_history_summary(updated_history)

    (
        overview_tab,
        stress_tab,
        probabilistic_tab,
        profiles_tab,
        history_tab,
        alerts_tab,
    ) = st.tabs(
        [
            "Vue generale",
            "Stress tests",
            "Probabilistic risk",
            "Profils de risque",
            "Historique",
            "Alertes & LLM",
        ]
    )

    with overview_tab:
        render_section_title(
            "Risk Score ARIA",
            "Synthese du niveau de risque agrege par ARIA.",
        )

        render_risk_badge(risk_score_result.label)

        score_col_1, score_col_2 = st.columns([1, 3])

        score_col_1.metric(
            "Score de risque",
            f"{risk_score_result.score}/100",
            risk_score_result.label,
        )

        with score_col_2:
            st.progress(risk_score_result.score / 100)

            if risk_score_result.score >= 80:
                st.error(risk_score_result.explanation)
            elif risk_score_result.score >= 60:
                st.warning(risk_score_result.explanation)
            elif risk_score_result.score >= 30:
                st.info(risk_score_result.explanation)
            else:
                st.success(risk_score_result.explanation)

        st.write("**Principaux facteurs de risque :**")

        for driver in risk_score_result.main_drivers:
            st.write(f"- {driver}")

        if market_snapshot is not None:
            render_section_title(
                "Donnees de marche utilisees",
                "Contexte de prix, volatilite et source active.",
            )

            render_status_pill(market_data_status)

            render_metric_row(
                [
                    {
                        "label": "Source",
                        "value": market_snapshot.source,
                        "helper": market_snapshot.status,
                    },
                    {
                        "label": "Ticker",
                        "value": market_snapshot.ticker,
                    },
                    {
                        "label": "Dernier prix",
                        "value": f"{market_snapshot.last_price:,.2f}",
                    },
                    {
                        "label": "Prix precedent",
                        "value": f"{market_snapshot.previous_price:,.2f}",
                    },
                    {
                        "label": "Rendement journalier",
                        "value": f"{market_snapshot.daily_return:+.2%}",
                    },
                    {
                        "label": "Volatilite historique",
                        "value": f"{market_snapshot.annualized_volatility:.2%}",
                    },
                    {
                        "label": "Observations",
                        "value": market_snapshot.number_of_observations,
                    },
                    {
                        "label": "Timestamp",
                        "value": market_snapshot.timestamp or "N/A",
                    },
                ]
            )

        render_section_title(
            "Resume du portefeuille",
            "Valeur, parametres de marche et taille de l'univers analyse.",
        )

        render_metric_row(
            [
                {
                    "label": "Valeur du portefeuille",
                    "value": f"{portfolio.total_market_value():,.2f}",
                },
                {
                    "label": "Spot",
                    "value": f"{current_spot:,.2f}",
                },
                {
                    "label": "Volatilite utilisee",
                    "value": f"{current_volatility:.2%}",
                },
                {
                    "label": "Nombre de positions",
                    "value": len(portfolio.positions),
                },
            ]
        )

        render_section_title(
            "Greeks du portefeuille",
            "Expositions agregees aux principaux facteurs de risque.",
        )

        greek_1, greek_2, greek_3 = st.columns(3)

        greek_1.metric("Delta", f"{greeks['delta']:.4f}")
        greek_2.metric("Gamma", f"{greeks['gamma']:.4f}")
        greek_3.metric("Vega", f"{greeks['vega']:.4f}")

        greek_4, greek_5, greek_6 = st.columns(3)

        greek_4.metric("Theta journalier", f"{greeks['theta']:.4f}")
        greek_5.metric("Rho", f"{greeks['rho']:.4f}")
        greek_6.metric("Volga", f"{greeks['volga']:.6f}")

        render_section_title(
            "Couverture delta indicative",
            "Action instantanee theorique pour neutraliser le delta courant.",
        )

        if hedge_result.hedge_quantity > 0:
            hedge_action = "Acheter"
        elif hedge_result.hedge_quantity < 0:
            hedge_action = "Vendre"
        else:
            hedge_action = "Ne rien faire"

        hedge_col_1, hedge_col_2, hedge_col_3, hedge_col_4 = st.columns(4)

        hedge_col_1.metric(
            "Delta actuel",
            f"{hedge_result.current_delta:,.4f}",
        )

        hedge_col_2.metric(
            "Action de couverture",
            hedge_action,
        )

        hedge_col_3.metric(
            "Quantite sous-jacent",
            f"{abs(hedge_result.hedge_quantity):,.0f}",
        )

        hedge_col_4.metric(
            "Valeur de couverture",
            f"{hedge_result.hedge_market_value:,.2f}",
        )

        st.info(hedge_result.explanation)

        render_section_title(
            "Positions analysees",
            "Inventaire des lignes retenues dans le moteur de risque.",
        )

        positions_summary = []

        for position in portfolio.positions:
            if hasattr(position, "contract"):
                positions_summary.append(
                    {
                        "Nom": position.name,
                        "Instrument": position.contract.option_type.upper(),
                        "Quantite": position.quantity,
                        "Multiplicateur": position.multiplier,
                        "Exposition": position.quantity * position.multiplier,
                        "Strike": position.contract.K,
                        "Maturite": position.contract.T,
                        "Valeur": position.market_value(),
                    }
                )

            else:
                positions_summary.append(
                    {
                        "Nom": position.name,
                        "Instrument": "ACTION",
                        "Quantite": position.quantity,
                        "Multiplicateur": 1,
                        "Exposition": position.quantity,
                        "Strike": None,
                        "Maturite": None,
                        "Valeur": position.market_value(),
                    }
                )

        st.dataframe(
            pd.DataFrame(positions_summary),
            hide_index=True,
            width="stretch",
        )

    with stress_tab:
        render_section_title(
            "Stress tests",
            "Lecture des pertes et gains sous scenarios de marche.",
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
            "Meilleur scenario",
            best_scenario.name,
            f"{best_scenario.profit_and_loss:+,.2f}",
        )

        worst_column.metric(
            "Scenario le plus defavorable",
            worst_scenario.name,
            f"{worst_scenario.profit_and_loss:+,.2f}",
        )

        stress_chart = create_stress_chart(scenario_results)

        st.altair_chart(
            stress_chart,
            width="stretch",
        )

        scenario_table = pd.DataFrame(
            [
                {
                    "Scenario": result.name,
                    "Variation spot": f"{result.spot_change_percent:+.1%}",
                    "Variation volatilite": f"{result.volatility_change_points:+.1%}",
                    "Choc taux": f"{result.rate_change_points:+.1%}",
                    "Choc correlation": f"{result.correlation_shock:+.1%}",
                    "Valeur initiale": result.initial_value,
                    "Valeur stressee": result.stressed_value,
                    "Profit / Perte": result.profit_and_loss,
                    "Delta stresse": result.stressed_delta,
                    "Gamma stresse": result.stressed_gamma,
                    "Vega stresse": result.stressed_vega,
                }
                for result in scenario_results
            ]
        )

        with st.expander("Voir le detail complet des stress tests"):
            st.dataframe(
                scenario_table,
                hide_index=True,
                width="stretch",
            )

        if worst_scenario.top_contributors:
            render_section_title(
                "Top contributeurs au pire stress",
                "Positions qui expliquent le plus la perte du scenario le plus defavorable.",
            )

            st.dataframe(
                pd.DataFrame(worst_scenario.top_contributors).head(8),
                hide_index=True,
                width="stretch",
            )

        st.divider()

        render_section_title(
            "Matrice de risque",
            "Carte spot / volatilite pour reperer les zones de fragilite.",
        )

        spot_changes = [-0.10, -0.05, 0.00, 0.05, 0.10]
        volatility_changes = [-0.10, -0.05, 0.00, 0.05, 0.10]

        surface_points = calculate_risk_surface(
            portfolio=portfolio,
            spot_changes=spot_changes,
            volatility_changes=volatility_changes,
        )

        surface_data = normalize_dataframe_columns(
            surface_to_dataframe(surface_points)
        )

        volatility_surface_column = next(
            column
            for column in surface_data.columns
            if column.startswith("Variation vol")
        )

        risk_matrix = surface_data.pivot(
            index=volatility_surface_column,
            columns="Variation spot",
            values="Profit / Perte",
        )

        risk_matrix = risk_matrix.sort_index(ascending=False)

        risk_matrix.columns = [
            f"Spot {value:+.0%}"
            for value in risk_matrix.columns
        ]

        risk_matrix.index = [
            f"Vol {value:+.0%}"
            for value in risk_matrix.index
        ]

        styled_matrix = (
            risk_matrix.style
            .background_gradient(
                cmap="RdYlGn",
                axis=None,
            )
            .format("{:+,.0f}")
            .set_properties(
                **{
                    "font-weight": "bold",
                    "text-align": "center",
                }
            )
        )

        st.dataframe(
            styled_matrix,
            width="stretch",
            height=260,
        )

        st.divider()

        render_section_title(
            "VaR / Expected Shortfall",
            "Estimation simplifiee de la perte de queue par simulation.",
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
            "Pire perte simulee",
            f"{var_result.worst_loss:,.2f}",
        )

        var_col_4.metric(
            "VaR parametrique",
            f"{parametric_var:,.2f}",
        )

        var_chart = create_var_distribution_chart(
            simulations_data=var_simulations_data,
            var_amount=var_result.var_amount,
            expected_shortfall=var_result.expected_shortfall,
        )

        st.altair_chart(
            var_chart,
            width="stretch",
        )

        with st.expander("Voir les simulations VaR"):
            st.dataframe(
                var_simulations_data,
                hide_index=True,
                width="stretch",
            )

    with probabilistic_tab:
        render_section_title(
            "Probabilistic Risk Analysis",
            "Probabilité de perte, VaR, Expected Shortfall et moteurs de risque par simulation Monte Carlo.",
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

        prob_col_1, prob_col_2, prob_col_3, prob_col_4 = st.columns(4)

        prob_col_1.metric(
            "Probabilité de perte",
            f"{probabilistic_result.probability_of_loss:.1%}",
        )
        prob_col_2.metric(
            "Perte > 10%",
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
            "Rendement moyen simulé",
            f"{probabilistic_result.mean_return:.1%}",
        )
        prob_col_6.metric(
            "Volatilité simulée",
            f"{probabilistic_result.simulated_volatility:.1%}",
        )
        prob_col_7.metric(
            "Pire rendement",
            f"{probabilistic_result.worst_return:.1%}",
        )
        prob_col_8.metric(
            "Moteur principal",
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

        st.info(probabilistic_result.interpretation)

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

        st.dataframe(
            metrics_display[
                [
                    "Metric",
                    "Value",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

        render_section_title(
            "Positions les plus risquées",
            "Contribution moyenne aux pertes dans les pires 5% des simulations.",
        )

        contributors = contribution_table(probabilistic_result).head(8)
        if contributors.empty:
            st.info("Aucun contributeur de risque significatif détecté.")
        else:
            st.dataframe(
                contributors,
                hide_index=True,
                width="stretch",
            )

        render_section_title(
            "Recommandations de risk management",
            "Pistes prudentes à étudier, basées uniquement sur les résultats simulés.",
        )

        recommendation_lines = [
            (
                f"Surveiller en priorité {probabilistic_result.main_risk_driver}, "
                "car cette ligne ressort comme le principal moteur de perte dans la queue de distribution."
            ),
            (
                "Comparer la probabilité de perte et l'Expected Shortfall avec l'objectif du portefeuille "
                "avant d'augmenter l'exposition."
            ),
            (
                "Si la perte simulée semble trop élevée, étudier une réduction de concentration, "
                "une couverture par options ou une baisse de l'exposition Delta/Vega."
            ),
            (
                "Ces probabilités dépendent du modèle Monte Carlo, des volatilités et des corrélations; "
                "elles ne sont pas des prédictions certaines."
            ),
        ]

        for recommendation in recommendation_lines:
            st.write(f"- {recommendation}")

        with st.expander("Voir les simulations probabilistes"):
            st.dataframe(
                probabilistic_simulations,
                hide_index=True,
                width="stretch",
            )

    with profiles_tab:
        render_section_title(
            "Profil de P&L",
            "Projection du resultat sur une grille de niveaux du sous-jacent.",
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

        pnl_data = pnl_data.rename(
            columns={
                "Spot stressé": "Spot stressé",
                "Spot stressÃ©": "Spot stressé",
                "Spot stresse": "Spot stressé",
                "Valeur stressée": "Valeur stressee",
                "Valeur stressÃ©e": "Valeur stressee",
                "Valeur stressee": "Valeur stressee",
            }
        )

        breakeven_spots = find_breakeven_spots(pnl_data)

        pnl_chart = create_pnl_profile_chart(
            pnl_data=pnl_data,
            current_spot=current_spot,
            breakeven_spots=breakeven_spots,
        )

        st.altair_chart(
            pnl_chart,
            width="stretch",
        )

        best_pnl_point = pnl_data.loc[
            pnl_data["Profit / Perte"].idxmax()
        ]

        worst_pnl_point = pnl_data.loc[
            pnl_data["Profit / Perte"].idxmin()
        ]

        pnl_column_1, pnl_column_2, pnl_column_3 = st.columns(3)

        pnl_column_1.metric(
            "Meilleur spot testé",
            f"{best_pnl_point['Spot stressé']:,.2f}",
            f"{best_pnl_point['Profit / Perte']:+,.2f}",
        )

        pnl_column_2.metric(
            "Pire spot testé",
            f"{worst_pnl_point['Spot stressé']:,.2f}",
            f"{worst_pnl_point['Profit / Perte']:+,.2f}",
        )

        if breakeven_spots:
            breakeven_text = ", ".join(
                f"{spot:,.2f}"
                for spot in breakeven_spots
            )
        else:
            breakeven_text = "Aucun dans l'intervalle"

        pnl_column_3.metric(
            "Point mort estime",
            breakeven_text,
        )

        st.divider()

        render_section_title(
            "Profil des Greeks",
            "Evolution des sensibilites lorsque le spot est stresse.",
        )

        selected_greeks = st.multiselect(
            "Greeks a afficher",
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

            greeks_chart = create_greeks_profile_chart(
                greeks_data=greeks_data,
                current_spot=current_spot,
                selected_greeks=selected_greeks,
            )

            st.altair_chart(
                greeks_chart,
                width="stretch",
            )

    with history_tab:
        render_section_title(
            "Historique des snapshots",
            "Memoire locale des observations de risque sauvegardees.",
        )

        if updated_history.empty:
            st.info("Aucun historique disponible pour le moment.")

        else:
            hist_col_1, hist_col_2, hist_col_3, hist_col_4 = st.columns(4)

            hist_col_1.metric(
                "Nombre de snapshots",
                history_summary["number_of_snapshots"],
            )

            hist_col_2.metric(
                "Derniere valeur",
                (
                    f"{history_summary['latest_portfolio_value']:,.2f}"
                    if history_summary["latest_portfolio_value"] is not None
                    else "N/A"
                ),
            )

            hist_col_3.metric(
                "Valeur min",
                (
                    f"{history_summary['minimum_portfolio_value']:,.2f}"
                    if history_summary["minimum_portfolio_value"] is not None
                    else "N/A"
                ),
            )

            hist_col_4.metric(
                "Valeur max",
                (
                    f"{history_summary['maximum_portfolio_value']:,.2f}"
                    if history_summary["maximum_portfolio_value"] is not None
                    else "N/A"
                ),
            )

            available_metrics = [
                column
                for column in [
                    "portfolio_value",
                    "spot",
                    "implied_volatility",
                    "delta",
                    "gamma",
                    "theta",
                    "vega",
                    "rho",
                    "vanna",
                    "volga",
                ]
                if column in updated_history.columns
            ]

            selected_metric = st.selectbox(
                "Metrique a afficher",
                available_metrics,
            )

            if (
                "timestamp" in updated_history.columns
                and selected_metric in updated_history.columns
            ):
                history_chart = create_history_chart(
                    history_data=updated_history,
                    metric=selected_metric,
                )

                st.altair_chart(
                    history_chart,
                    width="stretch",
                )

            with st.expander("Voir l'historique complet"):
                st.dataframe(
                    updated_history,
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
            "Analyse du LLM",
            "Commentaire prudent base uniquement sur les resultats ARIA.",
        )

        llm_analysis = None
        llm_analysis_en = None

        if enable_llm_commentary:
            with st.spinner("ARIA genere l'explication..."):
                llm_analysis = generate_llm_analysis(
                    snapshot=current_snapshot,
                    alerts=alerts,
                    risk_score_result=risk_score_result,
                    scenario_results=scenario_results,
                    var_result=var_result,
                    probabilistic_result=probabilistic_result,
                    portfolio_diagnosis_result=current_diagnosis,
                    rebalancing_summary=rebalance_summary,
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
                    rebalancing_summary=rebalance_summary,
                    hedge_result=hedge_result,
                    market_snapshot=market_snapshot,
                    language="en",
                )

        else:
            llm_analysis = (
                "### Synthese ARIA\n\n"
                "Le commentaire LLM est desactive pour cette analyse. "
                "Les metriques quantitatives, alertes, stress tests, VaR "
                "et recommandations de couverture restent disponibles. "
                "Active le commentaire LLM dans la sidebar pour generer "
                "une analyse narrative a partir des chiffres produits par ARIA, "
                "avec des pistes pour reduire le risque et ameliorer le rendement "
                "ajuste du risque."
            )

            llm_analysis_en = (
                "### ARIA Summary\n\n"
                "LLM commentary is disabled for this analysis. "
                "The quantitative metrics, alerts, stress tests, VaR and hedge "
                "recommendations remain available. Enable LLM commentary in the "
                "sidebar to generate a narrative analysis from ARIA outputs, with "
                "ideas to reduce risk and improve risk-adjusted return."
            )

        st.markdown(llm_analysis)

        st.divider()

        render_section_title(
            "Rapport de risque",
            "Exports Markdown et PDF structures comme une note de risk management.",
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
            llm_analysis=llm_analysis,
        )

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
            label="Telecharger le rapport Markdown",
            data=report_text,
            file_name="rapport_risque_aria.md",
            mime="text/markdown",
            type="secondary",
            width="stretch",
        )

        report_download_col_2.download_button(
            label="Telecharger le rapport PDF",
            data=report_pdf_fr,
            file_name="rapport_risque_aria_fr.pdf",
            mime="application/pdf",
            type="primary",
            width="stretch",
        )

        report_download_col_3.download_button(
            label="Download EN PDF",
            data=report_pdf_en,
            file_name="aria_risk_report_en.pdf",
            mime="application/pdf",
            type="secondary",
            width="stretch",
        )

        st.caption(
            "Le rapport est disponible en Markdown, PDF francais et PDF anglais. "
            "Il mentionne clairement que le projet a ete developpe par Enrique Jara Ron."
        )

    st.success("Le snapshot actuel a ete ajoute a l'historique.")
