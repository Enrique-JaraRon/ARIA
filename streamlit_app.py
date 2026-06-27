
"""
ARIA - Application Streamlit
"""

import altair as alt
import pandas as pd
import streamlit as st

from pricing_BS import OptionContract
from portfolio import Portfolio
from anomaly_detector import AnomalyDetector, create_snapshot
from risk_history import RiskHistory
from aria_workflow import generate_llm_analysis
from scenario_analysis import run_scenario, run_standard_scenarios
from risk_surface import calculate_risk_surface, surface_to_dataframe
from pnl_profile import (
    calculate_pnl_profile,
    pnl_profile_to_dataframe,
    find_breakeven_spots
)
from greeks_profile import (
    calculate_greeks_profile,
    greeks_profile_to_dataframe
)
from history_analytics import (
    load_history_dataframe,
    clean_history_dataframe,
    get_history_summary
)


st.set_page_config(
    page_title="ARIA Risk Agent",
    page_icon="📊",
    layout="wide"
)


def default_portfolio() -> pd.DataFrame:
    """Crée le portefeuille affiché au premier lancement."""

    return pd.DataFrame(
        [
            {
                "Instrument": "Option",
                "Nom": "Calls ATM achetés",
                "Type option": "call",
                "Quantité": 20,
                "Multiplicateur": 100,
                "Strike": 500.0,
                "Maturité": 0.25
            },
            {
                "Instrument": "Option",
                "Nom": "Puts vendus",
                "Type option": "put",
                "Quantité": -10,
                "Multiplicateur": 100,
                "Strike": 470.0,
                "Maturité": 0.25
            },
            {
                "Instrument": "Action",
                "Nom": "Couverture en actions",
                "Type option": "call",
                "Quantité": -5,
                "Multiplicateur": 1,
                "Strike": 500.0,
                "Maturité": 0.25
            }
        ]
    )


def build_portfolio_from_table(
    portfolio_table: pd.DataFrame,
    spot: float,
    rate: float,
    volatility: float,
    dividend: float
) -> Portfolio:
    """Transforme le tableau de l'application en portefeuille Python."""

    portfolio = Portfolio(
        name="Portefeuille ARIA"
    )

    for index, row in portfolio_table.iterrows():

        instrument = row.get("Instrument")
        quantity_value = row.get("Quantité")

        if pd.isna(instrument) or pd.isna(quantity_value):
            continue

        quantity = int(quantity_value)

        if quantity == 0:
            continue

        name = row.get("Nom")

        if pd.isna(name) or not str(name).strip():
            name = f"Position {index + 1}"

        if instrument == "Action":
            portfolio.add_stock(
                spot=spot,
                quantity=quantity,
                name=str(name)
            )

        elif instrument == "Option":
            option_type = row.get("Type option")
            strike = row.get("Strike")
            maturity = row.get("Maturité")
            multiplier_value = row.get("Multiplicateur")

            if pd.isna(option_type):
                raise ValueError(
                    f"Le type d'option manque à la ligne {index + 1}."
                )

            if pd.isna(strike) or float(strike) <= 0:
                raise ValueError(
                    f"Le strike est invalide à la ligne {index + 1}."
                )

            if pd.isna(maturity) or float(maturity) <= 0:
                raise ValueError(
                    f"La maturité est invalide à la ligne {index + 1}."
                )

            if pd.isna(multiplier_value):
                multiplier = 1
            else:
                multiplier = int(multiplier_value)

            if multiplier <= 0:
                raise ValueError(
                    f"Le multiplicateur est invalide à la ligne {index + 1}."
                )

            contract = OptionContract(
                S=spot,
                K=float(strike),
                T=float(maturity),
                r=rate,
                sigma=volatility,
                option_type=str(option_type),
                q=dividend
            )

            portfolio.add_option(
                contract=contract,
                quantity=quantity,
                multiplier=multiplier,
                name=str(name)
            )

        else:
            raise ValueError(
                f"Instrument inconnu à la ligne {index + 1}."
            )

    if not portfolio.positions:
        raise ValueError(
            "Le portefeuille doit contenir au moins une position."
        )

    return portfolio


def create_stress_chart(
    scenario_results
) -> alt.Chart:
    """Crée un graphique des profits et pertes par scénario."""

    chart_data = pd.DataFrame(
        [
            {
                "Scénario": result.name,
                "Profit / Perte": result.profit_and_loss,
                "Résultat": (
                    "Gain"
                    if result.profit_and_loss >= 0
                    else "Perte"
                )
            }
            for result in scenario_results
        ]
    )

    bars = alt.Chart(
        chart_data
    ).mark_bar(
        cornerRadiusEnd=6,
        size=32
    ).encode(
        y=alt.Y(
            "Scénario:N",
            sort=None,
            title=None
        ),
        x=alt.X(
            "Profit / Perte:Q",
            title="Profit / Perte du portefeuille"
        ),
        color=alt.Color(
            "Résultat:N",
            scale=alt.Scale(
                domain=["Gain", "Perte"],
                range=["#19A974", "#E05252"]
            ),
            legend=alt.Legend(
                title=None,
                orient="top"
            )
        ),
        tooltip=[
            alt.Tooltip(
                "Scénario:N",
                title="Scénario"
            ),
            alt.Tooltip(
                "Profit / Perte:Q",
                title="Profit / Perte",
                format=",.2f"
            )
        ]
    )

    labels = alt.Chart(
        chart_data
    ).mark_text(
        align="left",
        baseline="middle",
        dx=6,
        fontSize=13,
        fontWeight="bold"
    ).encode(
        y=alt.Y(
            "Scénario:N",
            sort=None
        ),
        x=alt.X(
            "Profit / Perte:Q"
        ),
        text=alt.Text(
            "Profit / Perte:Q",
            format=",.2f"
        ),
        color=alt.condition(
            alt.datum["Profit / Perte"] >= 0,
            alt.value("#117A55"),
            alt.value("#B83A3A")
        )
    )

    zero_line = alt.Chart(
        pd.DataFrame(
            {
                "x": [0]
            }
        )
    ).mark_rule(
        color="#6B7280",
        strokeWidth=1.5
    ).encode(
        x="x:Q"
    )

    return (
        bars
        + labels
        + zero_line
    ).properties(
        height=360,
        title=alt.TitleParams(
            text="Impact des scénarios sur le portefeuille",
            subtitle="À droite : gain potentiel — À gauche : perte potentielle",
            fontSize=20,
            subtitleFontSize=13,
            anchor="start",
            offset=20
        )
    ).configure_view(
        strokeWidth=0
    )


def create_pnl_profile_chart(
    pnl_data: pd.DataFrame,
    current_spot: float,
    breakeven_spots: list[float]
) -> alt.Chart:
    """Crée une courbe de P&L selon le niveau du spot."""

    chart_data = pnl_data.copy()

    chart_data["Résultat"] = chart_data[
        "Profit / Perte"
    ].apply(
        lambda value: (
            "Gain"
            if value >= 0
            else "Perte"
        )
    )

    line = alt.Chart(
        chart_data
    ).mark_line(
        strokeWidth=3,
        color="#2563EB"
    ).encode(
        x=alt.X(
            "Spot stressé:Q",
            title="Niveau du spot"
        ),
        y=alt.Y(
            "Profit / Perte:Q",
            title="Profit / Perte"
        ),
        tooltip=[
            alt.Tooltip(
                "Spot stressé:Q",
                title="Spot",
                format=",.2f"
            ),
            alt.Tooltip(
                "Variation spot:Q",
                title="Variation du spot",
                format="+.1%"
            ),
            alt.Tooltip(
                "Profit / Perte:Q",
                title="Profit / Perte",
                format=",.2f"
            )
        ]
    )

    points = alt.Chart(
        chart_data
    ).mark_circle(
        size=45
    ).encode(
        x="Spot stressé:Q",
        y="Profit / Perte:Q",
        color=alt.Color(
            "Résultat:N",
            scale=alt.Scale(
                domain=["Gain", "Perte"],
                range=["#19A974", "#E05252"]
            ),
            legend=alt.Legend(
                title=None,
                orient="top"
            )
        )
    )

    zero_line = alt.Chart(
        pd.DataFrame(
            {
                "y": [0]
            }
        )
    ).mark_rule(
        color="#6B7280",
        strokeDash=[6, 4],
        strokeWidth=1.5
    ).encode(
        y="y:Q"
    )

    current_spot_line = alt.Chart(
        pd.DataFrame(
            {
                "x": [current_spot]
            }
        )
    ).mark_rule(
        color="#111827",
        strokeWidth=2
    ).encode(
        x="x:Q"
    )

    breakeven_lines = alt.Chart(
        pd.DataFrame(
            {
                "x": breakeven_spots
            }
        )
    ).mark_rule(
        color="#F59E0B",
        strokeDash=[4, 4],
        strokeWidth=2
    ).encode(
        x="x:Q"
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
            subtitle="Ligne noire : spot actuel — ligne orange : point mort approximatif",
            fontSize=20,
            subtitleFontSize=13,
            anchor="start",
            offset=20
        )
    ).configure_view(
        strokeWidth=0
    )


def create_greeks_profile_chart(
    greeks_data: pd.DataFrame,
    current_spot: float,
    selected_greeks: list[str]
) -> alt.Chart:
    """Crée une courbe des Greeks selon le niveau du spot."""

    chart_data = greeks_data[
        [
            "Spot stressé",
            "Variation spot"
        ]
        + selected_greeks
    ].copy()

    long_data = chart_data.melt(
        id_vars=[
            "Spot stressé",
            "Variation spot"
        ],
        value_vars=selected_greeks,
        var_name="Greek",
        value_name="Valeur"
    )

    lines = alt.Chart(
        long_data
    ).mark_line(
        strokeWidth=3
    ).encode(
        x=alt.X(
            "Spot stressé:Q",
            title="Niveau du spot"
        ),
        y=alt.Y(
            "Valeur:Q",
            title="Valeur du Greek"
        ),
        color=alt.Color(
            "Greek:N",
            legend=alt.Legend(
                title=None,
                orient="top"
            )
        ),
        tooltip=[
            alt.Tooltip(
                "Greek:N",
                title="Greek"
            ),
            alt.Tooltip(
                "Spot stressé:Q",
                title="Spot",
                format=",.2f"
            ),
            alt.Tooltip(
                "Variation spot:Q",
                title="Variation du spot",
                format="+.1%"
            ),
            alt.Tooltip(
                "Valeur:Q",
                title="Valeur",
                format=",.4f"
            )
        ]
    )

    current_spot_line = alt.Chart(
        pd.DataFrame(
            {
                "x": [current_spot]
            }
        )
    ).mark_rule(
        color="#111827",
        strokeWidth=2
    ).encode(
        x="x:Q"
    )

    return (
        lines
        + current_spot_line
    ).properties(
        height=420,
        title=alt.TitleParams(
            text="Profil des Greeks selon le niveau du spot",
            subtitle="La volatilité reste constante. La ligne noire indique le spot actuel.",
            fontSize=20,
            subtitleFontSize=13,
            anchor="start",
            offset=20
        )
    ).configure_view(
        strokeWidth=0
    )


def create_history_chart(
    history_data: pd.DataFrame,
    metric: str
) -> alt.Chart:
    """Crée une courbe historique pour une métrique donnée."""

    chart_data = history_data.copy()

    line = alt.Chart(
        chart_data
    ).mark_line(
        strokeWidth=3,
        color="#2563EB"
    ).encode(
        x=alt.X(
            "timestamp:T",
            title="Date"
        ),
        y=alt.Y(
            f"{metric}:Q",
            title=metric
        ),
        tooltip=[
            alt.Tooltip(
                "timestamp:T",
                title="Date"
            ),
            alt.Tooltip(
                f"{metric}:Q",
                title=metric,
                format=",.4f"
            )
        ]
    )

    points = alt.Chart(
        chart_data
    ).mark_circle(
        size=50,
        color="#2563EB"
    ).encode(
        x="timestamp:T",
        y=f"{metric}:Q",
        tooltip=[
            alt.Tooltip(
                "timestamp:T",
                title="Date"
            ),
            alt.Tooltip(
                f"{metric}:Q",
                title=metric,
                format=",.4f"
            )
        ]
    )

    return (
        line
        + points
    ).properties(
        height=380,
        title=alt.TitleParams(
            text=f"Historique de {metric}",
            subtitle="Évolution des snapshots sauvegardés par ARIA",
            fontSize=20,
            subtitleFontSize=13,
            anchor="start",
            offset=20
        )
    ).configure_view(
        strokeWidth=0
    )


st.title(
    "ARIA - Adaptive Risk Intelligence Agent"
)

st.write(
    "Construis ton portefeuille, modifie les conditions de marché "
    "et lance une analyse complète des risques."
)


st.sidebar.header(
    "Marché"
)

current_spot = st.sidebar.number_input(
    "Prix du sous-jacent",
    min_value=0.01,
    value=500.0,
    step=1.0
)

current_volatility_percent = st.sidebar.number_input(
    "Volatilité implicite en %",
    min_value=0.01,
    value=20.0,
    step=1.0
)

risk_free_rate_percent = st.sidebar.number_input(
    "Taux sans risque en %",
    value=5.0,
    step=0.25
)

dividend_yield_percent = st.sidebar.number_input(
    "Rendement du dividende en %",
    min_value=0.0,
    value=0.0,
    step=0.25
)

current_volatility = (
    current_volatility_percent / 100
)

risk_free_rate = (
    risk_free_rate_percent / 100
)

dividend_yield = (
    dividend_yield_percent / 100
)


st.sidebar.header(
    "Limites de risque"
)

delta_limit = st.sidebar.number_input(
    "Limite de delta",
    min_value=0.0,
    value=10.0,
    step=1.0
)

gamma_limit = st.sidebar.number_input(
    "Limite de gamma",
    min_value=0.0,
    value=1.0,
    step=0.1
)

vega_limit = st.sidebar.number_input(
    "Limite de vega",
    min_value=0.0,
    value=20.0,
    step=1.0
)

spot_move_limit_percent = st.sidebar.number_input(
    "Variation maximale du spot en %",
    min_value=0.1,
    value=3.0,
    step=0.5
)

volatility_move_limit_percent = st.sidebar.number_input(
    "Variation maximale de volatilité en points",
    min_value=0.1,
    value=5.0,
    step=0.5
)

z_score_limit = st.sidebar.number_input(
    "Limite du z-score",
    min_value=0.5,
    value=2.5,
    step=0.1
)


st.sidebar.header(
    "Scénario personnalisé"
)

custom_spot_change_percent = st.sidebar.number_input(
    "Choc du spot en %",
    value=-10.0,
    step=1.0,
    help="-10 signifie une baisse du spot de 10 %."
)

custom_volatility_change_points = st.sidebar.number_input(
    "Choc de volatilité en points",
    value=15.0,
    step=1.0,
    help="15 signifie une hausse de volatilité de 15 points."
)


if "portfolio_data" not in st.session_state:
    st.session_state.portfolio_data = (
        default_portfolio()
    )


st.subheader(
    "Composition du portefeuille"
)

st.write(
    "Une quantité positive correspond à une position achetée. "
    "Une quantité négative correspond à une position vendue."
)

st.caption(
    "Pour une option, l'exposition réelle est égale à "
    "quantité × multiplicateur."
)

if st.button(
    "Réinitialiser le portefeuille"
):
    st.session_state.portfolio_data = (
        default_portfolio()
    )

    if "portfolio_editor" in st.session_state:
        del st.session_state[
            "portfolio_editor"
        ]

    st.rerun()


edited_portfolio = st.data_editor(
    st.session_state.portfolio_data,
    key="portfolio_editor",
    num_rows="dynamic",
    hide_index=True,
    width="stretch",
    column_config={
        "Instrument": st.column_config.SelectboxColumn(
            "Instrument",
            options=[
                "Option",
                "Action"
            ],
            required=True
        ),
        "Nom": st.column_config.TextColumn(
            "Nom de la position"
        ),
        "Type option": st.column_config.SelectboxColumn(
            "Type d'option",
            options=[
                "call",
                "put"
            ]
        ),
        "Quantité": st.column_config.NumberColumn(
            "Quantité",
            step=1,
            format="%d"
        ),
        "Multiplicateur": st.column_config.NumberColumn(
            "Multiplicateur",
            min_value=1,
            step=1,
            format="%d",
            help=(
                "Nombre d'unités du sous-jacent "
                "représentées par un contrat."
            )
        ),
        "Strike": st.column_config.NumberColumn(
            "Strike",
            min_value=0.01,
            step=1.0
        ),
        "Maturité": st.column_config.NumberColumn(
            "Maturité en années",
            min_value=0.001,
            step=0.05,
            format="%.3f"
        )
    }
)

st.session_state.portfolio_data = (
    edited_portfolio
)


analyse_button = st.button(
    "Lancer l'analyse ARIA",
    type="primary",
    width="stretch"
)


if analyse_button:

    try:
        portfolio = build_portfolio_from_table(
            portfolio_table=edited_portfolio,
            spot=current_spot,
            rate=risk_free_rate,
            volatility=current_volatility,
            dividend=dividend_yield
        )

    except ValueError as error:
        st.error(
            str(error)
        )
        st.stop()


    current_snapshot = create_snapshot(
        portfolio=portfolio,
        spot=current_spot,
        implied_volatility=current_volatility
    )

    history_manager = RiskHistory(
        file_path="data/risk_history.csv"
    )

    history = (
        history_manager.load_snapshots()
    )

    previous_snapshot = (
        history[-1]
        if history
        else None
    )

    detector = AnomalyDetector(
        delta_limit=delta_limit,
        gamma_limit=gamma_limit,
        vega_limit=vega_limit,
        daily_spot_move_limit=(
            spot_move_limit_percent / 100
        ),
        volatility_move_limit=(
            volatility_move_limit_percent / 100
        ),
        z_score_limit=z_score_limit
    )

    alerts = detector.detect_all(
        current=current_snapshot,
        history=history,
        previous=previous_snapshot
    )

    greeks = (
        portfolio.total_greeks()
    )

    history_manager.save_snapshot(
        current_snapshot
    )

    updated_history = load_history_dataframe(
        "data/risk_history.csv"
    )

    updated_history = clean_history_dataframe(
        updated_history
    )

    history_summary = get_history_summary(
        updated_history
    )


    overview_tab, stress_tab, profiles_tab, history_tab, alerts_tab = st.tabs(
        [
            "Vue générale",
            "Stress tests",
            "Profils de risque",
            "Historique",
            "Alertes & LLM"
        ]
    )


    with overview_tab:

        st.subheader(
            "Résumé du portefeuille"
        )

        column_1, column_2, column_3, column_4 = (
            st.columns(4)
        )

        column_1.metric(
            "Valeur du portefeuille",
            f"{portfolio.total_market_value():,.2f}"
        )

        column_2.metric(
            "Spot",
            f"{current_spot:,.2f}"
        )

        column_3.metric(
            "Volatilité implicite",
            f"{current_volatility:.2%}"
        )

        column_4.metric(
            "Nombre de positions",
            len(portfolio.positions)
        )


        st.subheader(
            "Greeks du portefeuille"
        )

        greek_1, greek_2, greek_3 = (
            st.columns(3)
        )

        greek_1.metric(
            "Delta",
            f"{greeks['delta']:.4f}"
        )

        greek_2.metric(
            "Gamma",
            f"{greeks['gamma']:.4f}"
        )

        greek_3.metric(
            "Vega",
            f"{greeks['vega']:.4f}"
        )

        greek_4, greek_5, greek_6 = (
            st.columns(3)
        )

        greek_4.metric(
            "Theta journalier",
            f"{greeks['theta']:.4f}"
        )

        greek_5.metric(
            "Rho",
            f"{greeks['rho']:.4f}"
        )

        greek_6.metric(
            "Volga",
            f"{greeks['volga']:.6f}"
        )


        st.subheader(
            "Positions analysées"
        )

        positions_summary = []

        for position in portfolio.positions:

            if hasattr(
                position,
                "contract"
            ):
                positions_summary.append(
                    {
                        "Nom": position.name,
                        "Instrument": (
                            position.contract.option_type.upper()
                        ),
                        "Quantité": position.quantity,
                        "Multiplicateur": position.multiplier,
                        "Exposition": (
                            position.quantity
                            * position.multiplier
                        ),
                        "Strike": position.contract.K,
                        "Maturité": position.contract.T,
                        "Valeur": position.market_value()
                    }
                )

            else:
                positions_summary.append(
                    {
                        "Nom": position.name,
                        "Instrument": "ACTION",
                        "Quantité": position.quantity,
                        "Multiplicateur": 1,
                        "Exposition": position.quantity,
                        "Strike": None,
                        "Maturité": None,
                        "Valeur": position.market_value()
                    }
                )

        st.dataframe(
            pd.DataFrame(
                positions_summary
            ),
            hide_index=True,
            width="stretch"
        )


    with stress_tab:

        st.subheader(
            "Stress tests"
        )

        scenario_results = (
            run_standard_scenarios(
                portfolio
            )
        )

        custom_result = run_scenario(
            portfolio=portfolio,
            name="Scénario personnalisé",
            spot_change_percent=(
                custom_spot_change_percent / 100
            ),
            volatility_change_points=(
                custom_volatility_change_points / 100
            )
        )

        scenario_results.append(
            custom_result
        )

        best_scenario = max(
            scenario_results,
            key=lambda result: result.profit_and_loss
        )

        worst_scenario = min(
            scenario_results,
            key=lambda result: result.profit_and_loss
        )

        best_column, worst_column = (
            st.columns(2)
        )

        best_column.metric(
            "Meilleur scénario",
            best_scenario.name,
            f"{best_scenario.profit_and_loss:+,.2f}"
        )

        worst_column.metric(
            "Scénario le plus défavorable",
            worst_scenario.name,
            f"{worst_scenario.profit_and_loss:+,.2f}"
        )

        stress_chart = create_stress_chart(
            scenario_results
        )

        st.altair_chart(
            stress_chart,
            width="stretch"
        )

        scenario_table = pd.DataFrame(
            [
                {
                    "Scénario": result.name,
                    "Variation spot": (
                        f"{result.spot_change_percent:+.1%}"
                    ),
                    "Variation volatilité": (
                        f"{result.volatility_change_points:+.1%}"
                    ),
                    "Valeur initiale": result.initial_value,
                    "Valeur stressée": result.stressed_value,
                    "Profit / Perte": result.profit_and_loss,
                    "Delta stressé": result.stressed_delta,
                    "Gamma stressé": result.stressed_gamma,
                    "Vega stressé": result.stressed_vega
                }
                for result in scenario_results
            ]
        )

        with st.expander(
            "Voir le détail complet des stress tests"
        ):
            st.dataframe(
                scenario_table,
                hide_index=True,
                width="stretch"
            )


        st.divider()

        st.subheader(
            "Matrice de risque"
        )

        spot_changes = [
            -0.10,
            -0.05,
            0.00,
            0.05,
            0.10
        ]

        volatility_changes = [
            -0.10,
            -0.05,
            0.00,
            0.05,
            0.10
        ]

        surface_points = calculate_risk_surface(
            portfolio=portfolio,
            spot_changes=spot_changes,
            volatility_changes=volatility_changes
        )

        surface_data = surface_to_dataframe(
            surface_points
        )

        risk_matrix = surface_data.pivot(
            index="Variation volatilité",
            columns="Variation spot",
            values="Profit / Perte"
        )

        risk_matrix = risk_matrix.sort_index(
            ascending=False
        )

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
                axis=None
            )
            .format(
                "{:+,.0f}"
            )
            .set_properties(
                **{
                    "font-weight": "bold",
                    "text-align": "center"
                }
            )
        )

        st.dataframe(
            styled_matrix,
            width="stretch",
            height=260
        )


    with profiles_tab:

        st.subheader(
            "Profil de P&L"
        )

        pnl_points = calculate_pnl_profile(
            portfolio=portfolio,
            current_spot=current_spot,
            minimum_change=-0.30,
            maximum_change=0.30,
            number_of_points=61
        )

        pnl_data = pnl_profile_to_dataframe(
            pnl_points
        )

        breakeven_spots = find_breakeven_spots(
            pnl_data
        )

        pnl_chart = create_pnl_profile_chart(
            pnl_data=pnl_data,
            current_spot=current_spot,
            breakeven_spots=breakeven_spots
        )

        st.altair_chart(
            pnl_chart,
            width="stretch"
        )

        best_pnl_point = pnl_data.loc[
            pnl_data["Profit / Perte"].idxmax()
        ]

        worst_pnl_point = pnl_data.loc[
            pnl_data["Profit / Perte"].idxmin()
        ]

        pnl_column_1, pnl_column_2, pnl_column_3 = (
            st.columns(3)
        )

        pnl_column_1.metric(
            "Meilleur spot testé",
            f"{best_pnl_point['Spot stressé']:,.2f}",
            f"{best_pnl_point['Profit / Perte']:+,.2f}"
        )

        pnl_column_2.metric(
            "Pire spot testé",
            f"{worst_pnl_point['Spot stressé']:,.2f}",
            f"{worst_pnl_point['Profit / Perte']:+,.2f}"
        )

        if breakeven_spots:
            breakeven_text = ", ".join(
                f"{spot:,.2f}"
                for spot in breakeven_spots
            )
        else:
            breakeven_text = "Aucun dans l'intervalle"

        pnl_column_3.metric(
            "Point mort estimé",
            breakeven_text
        )


        st.divider()

        st.subheader(
            "Profil des Greeks"
        )

        selected_greeks = st.multiselect(
            "Greeks à afficher",
            options=[
                "Delta",
                "Gamma",
                "Theta",
                "Vega",
                "Rho",
                "Vanna",
                "Volga"
            ],
            default=[
                "Delta",
                "Gamma",
                "Vega"
            ]
        )

        if selected_greeks:

            greeks_points = calculate_greeks_profile(
                portfolio=portfolio,
                current_spot=current_spot,
                minimum_change=-0.30,
                maximum_change=0.30,
                number_of_points=61
            )

            greeks_data = greeks_profile_to_dataframe(
                greeks_points
            )

            greeks_chart = create_greeks_profile_chart(
                greeks_data=greeks_data,
                current_spot=current_spot,
                selected_greeks=selected_greeks
            )

            st.altair_chart(
                greeks_chart,
                width="stretch"
            )


    with history_tab:

        st.subheader(
            "Historique des snapshots"
        )

        if updated_history.empty:
            st.info(
                "Aucun historique disponible pour le moment."
            )

        else:
            hist_col_1, hist_col_2, hist_col_3, hist_col_4 = (
                st.columns(4)
            )

            hist_col_1.metric(
                "Nombre de snapshots",
                history_summary["number_of_snapshots"]
            )

            hist_col_2.metric(
                "Dernière valeur",
                (
                    f"{history_summary['latest_portfolio_value']:,.2f}"
                    if history_summary["latest_portfolio_value"] is not None
                    else "N/A"
                )
            )

            hist_col_3.metric(
                "Valeur min",
                (
                    f"{history_summary['minimum_portfolio_value']:,.2f}"
                    if history_summary["minimum_portfolio_value"] is not None
                    else "N/A"
                )
            )

            hist_col_4.metric(
                "Valeur max",
                (
                    f"{history_summary['maximum_portfolio_value']:,.2f}"
                    if history_summary["maximum_portfolio_value"] is not None
                    else "N/A"
                )
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
                    "volga"
                ]
                if column in updated_history.columns
            ]

            selected_metric = st.selectbox(
                "Métrique à afficher",
                available_metrics
            )

            if (
                "timestamp" in updated_history.columns
                and selected_metric in updated_history.columns
            ):
                history_chart = create_history_chart(
                    history_data=updated_history,
                    metric=selected_metric
                )

                st.altair_chart(
                    history_chart,
                    width="stretch"
                )

            with st.expander(
                "Voir l'historique complet"
            ):
                st.dataframe(
                    updated_history,
                    hide_index=True,
                    width="stretch"
                )


    with alerts_tab:

        st.subheader(
            "Alertes quantitatives"
        )

        if not alerts:
            st.success(
                "Aucune anomalie détectée."
            )

        else:
            st.warning(
                f"{len(alerts)} anomalie(s) détectée(s)."
            )

            for alert in alerts:

                alert_text = (
                    f"**{alert.name}** — "
                    f"{alert.message}\n\n"
                    f"Valeur actuelle : "
                    f"`{alert.current_value:.6f}`"
                )

                if alert.reference_value is not None:
                    alert_text += (
                        "\n\nValeur de référence : "
                        f"`{alert.reference_value:.6f}`"
                    )

                if alert.z_score is not None:
                    alert_text += (
                        f"\n\nZ-score : "
                        f"`{alert.z_score:.2f}`"
                    )

                if alert.severity == "CRITIQUE":
                    st.error(
                        alert_text
                    )

                elif alert.severity == "ÉLEVÉE":
                    st.warning(
                        alert_text
                    )

                else:
                    st.info(
                        alert_text
                    )


        st.divider()

        st.subheader(
            "Analyse du LLM"
        )

        if alerts:

            with st.spinner(
                "ARIA génère l'explication..."
            ):
                llm_analysis = generate_llm_analysis(
                    snapshot=current_snapshot,
                    alerts=alerts
                )

            st.markdown(
                llm_analysis
            )

        else:
            st.write(
                "Aucune analyse LLM supplémentaire "
                "n'est nécessaire."
            )


    st.success(
        "Le snapshot actuel a été ajouté à l'historique."
    )

