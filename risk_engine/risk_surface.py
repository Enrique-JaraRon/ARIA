"""
ARIA - Matrice de stress Spot / Volatilité
"""

from dataclasses import dataclass

import pandas as pd

from portfolio_engine.portfolio import Portfolio
from risk_engine.scenario_analysis import run_scenario


@dataclass
class SurfacePoint:
    """Représente un point de la matrice de stress."""

    spot_change_percent: float
    volatility_change_points: float
    profit_and_loss: float


def calculate_risk_surface(
    portfolio: Portfolio,
    spot_changes: list[float],
    volatility_changes: list[float]
) -> list[SurfacePoint]:
    """Calcule le P&L pour chaque combinaison de chocs."""

    surface_points = []

    for volatility_change in volatility_changes:

        for spot_change in spot_changes:

            result = run_scenario(
                portfolio=portfolio,
                name="Matrice de stress",
                spot_change_percent=spot_change,
                volatility_change_points=volatility_change
            )

            surface_points.append(
                SurfacePoint(
                    spot_change_percent=spot_change,
                    volatility_change_points=volatility_change,
                    profit_and_loss=result.profit_and_loss
                )
            )

    return surface_points


def surface_to_dataframe(
    surface_points: list[SurfacePoint]
) -> pd.DataFrame:
    """Transforme les résultats en tableau utilisable par Streamlit."""

    return pd.DataFrame(
        [
            {
                "Variation spot": point.spot_change_percent,
                "Variation volatilité": (
                    point.volatility_change_points
                ),
                "Profit / Perte": point.profit_and_loss
            }
            for point in surface_points
        ]
    )


if __name__ == "__main__":
    from portfolio_engine.pricing_BS import OptionContract

    portfolio = Portfolio(
        name="Test de matrice"
    )

    call = OptionContract(
        S=500,
        K=500,
        T=0.25,
        r=0.05,
        sigma=0.20,
        option_type="call",
        q=0.0
    )

    portfolio.add_option(
        contract=call,
        quantity=10,
        multiplier=100,
        name="Calls achetés"
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

    points = calculate_risk_surface(
        portfolio=portfolio,
        spot_changes=spot_changes,
        volatility_changes=volatility_changes
    )

    dataframe = surface_to_dataframe(
        points
    )

    print(dataframe)
