"""
ARIA - Application Streamlit
"""

import os

import streamlit as st

from aria_workflow import (
    build_demo_portfolio,
    update_portfolio_market,
    generate_llm_analysis
)
from anomaly_detector import AnomalyDetector, create_snapshot
from risk_history import RiskHistory


st.set_page_config(
    page_title="ARIA Risk Agent",
    page_icon="📊",
    layout="wide"
)

st.title("ARIA - Adaptive Risk Intelligence Agent")

st.write(
    "ARIA analyse un portefeuille d'options, "
    "détecte les expositions inhabituelles "
    "et génère une explication en langage naturel."
)


# Paramètres du marché

st.sidebar.header("Paramètres du marché")

current_spot = st.sidebar.number_input(
    "Prix du sous-jacent",
    min_value=1.0,
    value=500.0,
    step=1.0
)

current_volatility_percent = st.sidebar.number_input(
    "Volatilité implicite en %",
    min_value=0.1,
    value=20.0,
    step=1.0
)

current_volatility = current_volatility_percent / 100


# Paramètres de détection

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


analyse_button = st.sidebar.button(
    "Lancer l'analyse"
)


if analyse_button:

    portfolio = build_demo_portfolio()

    update_portfolio_market(
        portfolio=portfolio,
        spot=current_spot,
        implied_volatility=current_volatility
    )

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


    # Résumé du portefeuille

    st.subheader("Résumé du portefeuille")

    column_1, column_2, column_3 = st.columns(3)

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


    # Greeks

    st.subheader("Greeks du portefeuille")

    greek_column_1, greek_column_2, greek_column_3 = st.columns(3)

    greek_column_1.metric(
        "Delta",
        f"{greeks['delta']:.4f}"
    )

    greek_column_2.metric(
        "Gamma",
        f"{greeks['gamma']:.4f}"
    )

    greek_column_3.metric(
        "Vega",
        f"{greeks['vega']:.4f}"
    )

    greek_column_4, greek_column_5, greek_column_6 = st.columns(3)

    greek_column_4.metric(
        "Theta journalier",
        f"{greeks['theta']:.4f}"
    )

    greek_column_5.metric(
        "Rho",
        f"{greeks['rho']:.4f}"
    )

    greek_column_6.metric(
        "Nombre de positions",
        len(portfolio.positions)
    )


    # Alertes

    st.subheader("Alertes quantitatives")

    if not alerts:
        st.success("Aucune anomalie détectée.")

    else:
        st.warning(
            f"{len(alerts)} anomalie(s) détectée(s)."
        )

        for alert in alerts:

            if alert.severity == "CRITIQUE":
                st.error(
                    f"{alert.name} — {alert.message}"
                )

            elif alert.severity == "ÉLEVÉE":
                st.warning(
                    f"{alert.name} — {alert.message}"
                )

            else:
                st.info(
                    f"{alert.name} — {alert.message}"
                )

            st.write(
                f"Valeur actuelle : "
                f"{alert.current_value:.6f}"
            )

            if alert.reference_value is not None:
                st.write(
                    f"Valeur de référence : "
                    f"{alert.reference_value:.6f}"
                )

            if alert.z_score is not None:
                st.write(
                    f"Z-score : {alert.z_score:.2f}"
                )


    # Analyse du LLM

    st.subheader("Analyse du LLM")

    if alerts:

        with st.spinner(
            "ARIA prépare l'analyse..."
        ):
            llm_analysis = generate_llm_analysis(
                snapshot=current_snapshot,
                alerts=alerts
            )

        st.write(llm_analysis)

    else:
        st.write(
            "Aucune analyse LLM supplémentaire "
            "n'est nécessaire."
        )


    # Sauvegarde dans l'historique

    history_manager.save_snapshot(
        current_snapshot
    )

    st.success(
        "Le snapshot a été ajouté à l'historique."
    )

else:
    st.info(
        "Choisis les paramètres dans la barre latérale, "
        "puis clique sur « Lancer l'analyse »."
    )