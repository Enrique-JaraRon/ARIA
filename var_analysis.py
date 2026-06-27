
"""
ARIA - Analyse VaR et Expected Shortfall
"""

from dataclasses import dataclass
from statistics import NormalDist
import random

import pandas as pd

from portfolio import Portfolio
from scenario_analysis import run_scenario


@dataclass
class VarResult:
    """Résultat d'une analyse VaR / Expected Shortfall."""

    confidence_level: float
    horizon_days: int
    number_of_simulations: int
    portfolio_value: float
    var_amount: float
    expected_shortfall: float
    worst_loss: float
    best_pnl: float
    mean_pnl: float


def calculate_var_es(
    portfolio: Portfolio,
    annual_volatility: float,
    confidence_level: float = 0.95,
    horizon_days: int = 1,
    number_of_simulations: int = 1000,
    seed: int = 42
) -> tuple[VarResult, pd.DataFrame]:
    """
    Calcule une VaR et un Expected Shortfall simplifiés.

    Hypothèses :
    - le rendement du sous-jacent suit une loi normale ;
    - la volatilité utilisée est annualisée ;
    - la volatilité implicite reste constante ;
    - le portefeuille est repricé avec Black-Scholes à chaque scénario.
    """

    if annual_volatility <= 0:
        raise ValueError(
            "La volatilité annuelle doit être strictement positive."
        )

    if confidence_level <= 0 or confidence_level >= 1:
        raise ValueError(
            "Le niveau de confiance doit être compris entre 0 et 1."
        )

    if horizon_days <= 0:
        raise ValueError(
            "L'horizon doit être strictement positif."
        )

    if number_of_simulations < 100:
        raise ValueError(
            "Il faut au moins 100 simulations."
        )

    random.seed(
        seed
    )

    portfolio_value = portfolio.total_market_value()

    horizon_volatility = annual_volatility * (
        horizon_days / 252
    ) ** 0.5

    simulations = []

    for simulation_id in range(
        1,
        number_of_simulations + 1
    ):

        spot_return = random.gauss(
            0,
            horizon_volatility
        )

        scenario_result = run_scenario(
            portfolio=portfolio,
            name=f"Simulation {simulation_id}",
            spot_change_percent=spot_return,
            volatility_change_points=0.0
        )

        pnl = scenario_result.profit_and_loss

        loss = -pnl

        simulations.append(
            {
                "Simulation": simulation_id,
                "Rendement spot": spot_return,
                "Profit / Perte": pnl,
                "Perte": loss
            }
        )

    simulations_data = pd.DataFrame(
        simulations
    )

    var_amount = simulations_data[
        "Perte"
    ].quantile(
        confidence_level
    )

    tail_losses = simulations_data[
        simulations_data["Perte"] >= var_amount
    ]

    expected_shortfall = tail_losses[
        "Perte"
    ].mean()

    worst_loss = simulations_data[
        "Perte"
    ].max()

    best_pnl = simulations_data[
        "Profit / Perte"
    ].max()

    mean_pnl = simulations_data[
        "Profit / Perte"
    ].mean()

    result = VarResult(
        confidence_level=confidence_level,
        horizon_days=horizon_days,
        number_of_simulations=number_of_simulations,
        portfolio_value=portfolio_value,
        var_amount=var_amount,
        expected_shortfall=expected_shortfall,
        worst_loss=worst_loss,
        best_pnl=best_pnl,
        mean_pnl=mean_pnl
    )

    return result, simulations_data


def parametric_var_estimate(
    portfolio: Portfolio,
    annual_volatility: float,
    confidence_level: float = 0.95,
    horizon_days: int = 1
) -> float:
    """
    Calcule une VaR paramétrique très simplifiée.

    Cette approximation utilise seulement le delta du portefeuille.
    Elle ne prend pas en compte la convexité, le gamma, la vega, etc.
    """

    if annual_volatility <= 0:
        raise ValueError(
            "La volatilité annuelle doit être strictement positive."
        )

    greeks = portfolio.total_greeks()

    delta = greeks["delta"]

    horizon_volatility = annual_volatility * (
        horizon_days / 252
    ) ** 0.5

    z_score = NormalDist().inv_cdf(
        confidence_level
    )

    var_estimate = abs(
        delta
    ) * horizon_volatility * z_score

    return var_estimate


if __name__ == "__main__":
    from pricing_BS import OptionContract

    portfolio = Portfolio(
        name="Test VaR"
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

    result, simulations = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=1000
    )

    print("Analyse VaR / Expected Shortfall")
    print(f"Valeur du portefeuille : {result.portfolio_value:.2f}")
    print(f"VaR : {result.var_amount:.2f}")
    print(f"Expected Shortfall : {result.expected_shortfall:.2f}")
    print(f"Pire perte simulée : {result.worst_loss:.2f}")
    print(f"Meilleur P&L simulé : {result.best_pnl:.2f}")
    print(f"P&L moyen : {result.mean_pnl:.2f}")

    print("\nPremières simulations")
    print(simulations.head())

