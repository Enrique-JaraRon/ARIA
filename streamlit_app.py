
"""
ARIA - Application Streamlit
"""

import pandas as pd
import streamlit as st
from scenario_analysis import run_standard_scenarios

from pricing_BS import OptionContract
from portfolio import Portfolio
from anomaly_detector import AnomalyDetector, create_snapshot
from risk_history import RiskHistory
from aria_workflow import generate_llm_analysis


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
                "Strike": 500.0,
                "Maturité": 0.25
            },
            {
                "Instrument": "Option",
                "Nom": "Puts vendus",
                "Type option": "put",
                "Quantité": -10,
                "Strike": 470.0,
                "Maturité": 0.25
            },
            {
                "Instrument": "Action",
                "Nom": "Couverture en actions",
                "Type option": "call",
                "Quantité": -5,
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

        if pd.isna(instrument):
            continue

        quantity_value = row.get("Quantité")

        if pd.isna(quantity_value):
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


st.title("ARIA - Adaptive Risk Intelligence Agent")

st.write(
    "Construis ton portefeuille, modifie les conditions de marché "
    "et lance une analyse complète des risques."
)


st.sidebar.header("Marché")

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

current_volatility = current_volatility_percent / 100
risk_free_rate = risk_free_rate_percent / 100
dividend_yield = dividend_yield_percent / 100


st.sidebar.header("Limites de risque")

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


if "portfolio_data" not in st.session_state:
    st.session_state.portfolio_data = default_portfolio()


st.subheader("Composition du portefeuille")

st.write(
    "Une quantité positive correspond à une position achetée. "
    "Une quantité négative correspond à une position vendue."
)

if st.button("Réinitialiser le portefeuille"):
    st.session_state.portfolio_data = default_portfolio()

    if "portfolio_editor" in st.session_state:
        del st.session_state["portfolio_editor"]

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
            options=["Option", "Action"],
            required=True
        ),
        "Nom": st.column_config.TextColumn(
            "Nom de la position"
        ),
        "Type option": st.column_config.SelectboxColumn(
            "Type d'option",
            options=["call", "put"]
        ),
        "Quantité": st.column_config.NumberColumn(
            "Quantité",
            step=1,
            format="%d"
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

st.session_state.portfolio_data = edited_portfolio


analyse_button = st.button(
    "Lancer l'analyse ARIA",
    type="primary"
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
        st.error(str(error))
        st.stop()

    current_snapshot = create_snapshot(
        portfolio=portfolio,
        spot=current_spot,
        implied_volatility=current_volatility
    )

    history_manager = RiskHistory(
        file_path="data/risk_history.csv"
    )

    history = history_manager.load_snapshots()

    previous_snapshot = (
        history[-1]
        if history
        else None
    )

    detector = AnomalyDetector(
        delta_limit=delta_limit,
        gamma_limit=gamma_limit,
        vega_limit=vega_limit,
        daily_spot_move_limit=spot_move_limit_percent / 100,
        volatility_move_limit=volatility_move_limit_percent / 100,
        z_score_limit=z_score_limit
    )

    alerts = detector.detect_all(
        current=current_snapshot,
        history=history,
        previous=previous_snapshot
    )

    greeks = portfolio.total_greeks()


    st.subheader("Résumé du portefeuille")

    column_1, column_2, column_3, column_4 = st.columns(4)

    column_1.metric(
        "Valeur du portefeuille",
        f"{portfolio.total_market_value():.2f}"
    )

    column_2.metric(
        "Spot",
        f"{current_spot:.2f}"
    )

    column_3.metric(
        "Volatilité implicite",
        f"{current_volatility:.2%}"
    )

    column_4.metric(
        "Nombre de positions",
        len(portfolio.positions)
    )


    st.subheader("Greeks du portefeuille")

    greek_1, greek_2, greek_3 = st.columns(3)

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

    greek_4, greek_5, greek_6 = st.columns(3)

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


    st.subheader("Positions analysées")

    positions_summary = []

    for position in portfolio.positions:

        if hasattr(position, "contract"):
            positions_summary.append(
                {
                    "Nom": position.name,
                    "Instrument": position.contract.option_type.upper(),
                    "Quantité": position.quantity,
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
                    "Strike": None,
                    "Maturité": None,
                    "Valeur": position.market_value()
                }
            )

    st.dataframe(
        pd.DataFrame(positions_summary),
        hide_index=True,
        width="stretch"
    )

    st.subheader("Stress tests")

    scenario_results = run_standard_scenarios(
        portfolio
    )

    scenario_table = pd.DataFrame(
        [
            {
                "Scénario": result.name,
                "Variation spot": (
                    f"{result.spot_change_percent:.1%}"
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

    st.dataframe(
        scenario_table,
        hide_index=True,
        width="stretch",
        column_config={
            "Valeur initiale": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "Valeur stressée": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "Profit / Perte": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "Delta stressé": st.column_config.NumberColumn(
                format="%.4f"
            ),
            "Gamma stressé": st.column_config.NumberColumn(
                format="%.4f"
            ),
            "Vega stressé": st.column_config.NumberColumn(
                format="%.4f"
            )
        }
    )

    st.write("Profit ou perte par scénario")

    chart_data = pd.DataFrame(
        {
            "Scénario": [
                result.name
                for result in scenario_results
            ],
            "Profit / Perte": [
                result.profit_and_loss
                for result in scenario_results
            ]
        }
    ).set_index("Scénario")

    st.bar_chart(
        chart_data,
        width="stretch"
    )

    st.subheader("Alertes quantitatives")

    if not alerts:
        st.success("Aucune anomalie détectée.")

    else:
        st.warning(
            f"{len(alerts)} anomalie(s) détectée(s)."
        )

        for alert in alerts:

            alert_text = (
                f"**{alert.name}** — {alert.message}\n\n"
                f"Valeur actuelle : `{alert.current_value:.6f}`"
            )

            if alert.reference_value is not None:
                alert_text += (
                    "\n\nValeur de référence : "
                    f"`{alert.reference_value:.6f}`"
                )

            if alert.z_score is not None:
                alert_text += (
                    f"\n\nZ-score : `{alert.z_score:.2f}`"
                )

            if alert.severity == "CRITIQUE":
                st.error(alert_text)

            elif alert.severity == "ÉLEVÉE":
                st.warning(alert_text)

            else:
                st.info(alert_text)


    st.subheader("Analyse du LLM")

    if alerts:

        with st.spinner(
            "ARIA génère l'explication..."
        ):
            llm_analysis = generate_llm_analysis(
                snapshot=current_snapshot,
                alerts=alerts
            )

        st.markdown(llm_analysis)

    else:
        st.write(
            "Aucune analyse LLM supplémentaire n'est nécessaire."
        )


    history_manager.save_snapshot(
        current_snapshot
    )

    st.success(
        "Le snapshot actuel a été ajouté à l'historique."
    )

