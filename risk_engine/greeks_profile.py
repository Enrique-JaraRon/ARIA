
"""
ARIA - Profil des Greeks selon le niveau du spot
"""

from dataclasses import dataclass

import pandas as pd

from portfolio_engine.portfolio import Portfolio
from risk_engine.scenario_analysis import apply_scenario


@dataclass
class GreeksPoint:
    """Représente les Greeks du portefeuille pour un niveau de spot."""

    spot_change_percent: float
    stressed_spot: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    vanna: float
    volga: float


def calculate_greeks_profile(
    portfolio: Portfolio,
    current_spot: float,
    minimum_change: float = -0.30,
    maximum_change: float = 0.30,
    number_of_points: int = 61
) -> list[GreeksPoint]:
    """
    Calcule les Greeks du portefeuille pour plusieurs niveaux du spot.

    La volatilité reste constante.
    """

    if current_spot <= 0:
        raise ValueError(
            "Le spot actuel doit être strictement positif."
        )

    if number_of_points < 2:
        raise ValueError(
            "Il faut au moins deux points."
        )

    step = (
        maximum_change - minimum_change
    ) / (
        number_of_points - 1
    )

    points = []

    for index in range(number_of_points):

        spot_change = (
            minimum_change
            + index * step
        )

        stressed_portfolio = apply_scenario(
            portfolio=portfolio,
            spot_change_percent=spot_change,
            volatility_change_points=0.0
        )

        greeks = stressed_portfolio.total_greeks()

        stressed_spot = (
            current_spot
            * (1 + spot_change)
        )

        points.append(
            GreeksPoint(
                spot_change_percent=spot_change,
                stressed_spot=stressed_spot,
                delta=greeks["delta"],
                gamma=greeks["gamma"],
                theta=greeks["theta"],
                vega=greeks["vega"],
                rho=greeks["rho"],
                vanna=greeks["vanna"],
                volga=greeks["volga"]
            )
        )

    return points


def greeks_profile_to_dataframe(
    points: list[GreeksPoint]
) -> pd.DataFrame:
    """Transforme le profil des Greeks en tableau."""

    return pd.DataFrame(
        [
            {
                "Variation spot": point.spot_change_percent,
                "Spot stressé": point.stressed_spot,
                "Delta": point.delta,
                "Gamma": point.gamma,
                "Theta": point.theta,
                "Vega": point.vega,
                "Rho": point.rho,
                "Vanna": point.vanna,
                "Volga": point.volga
            }
            for point in points
        ]
    )


if __name__ == "__main__":
    from portfolio_engine.pricing_BS import OptionContract

    portfolio = Portfolio(
        name="Test profil des Greeks"
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

    put = OptionContract(
        S=500,
        K=470,
        T=0.25,
        r=0.05,
        sigma=0.20,
        option_type="put",
        q=0.0
    )

    portfolio.add_option(
        contract=call,
        quantity=20,
        multiplier=100,
        name="Calls achetés"
    )

    portfolio.add_option(
        contract=put,
        quantity=-10,
        multiplier=100,
        name="Puts vendus"
    )

    portfolio.add_stock(
        spot=500,
        quantity=-5,
        name="Couverture en actions"
    )

    points = calculate_greeks_profile(
        portfolio=portfolio,
        current_spot=500,
        minimum_change=-0.30,
        maximum_change=0.30,
        number_of_points=61
    )

    dataframe = greeks_profile_to_dataframe(
        points
    )

    print(dataframe)

