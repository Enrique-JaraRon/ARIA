
"""
ARIA - Visualisation du prix et des Greeks
"""

import matplotlib.pyplot as plt
import numpy as np

from pricing_BS import OptionContract, bs_greeks, bs_price


def calculate_values_for_spots(
    spots: np.ndarray,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
    dividend: float,
    option_type: str
) -> tuple[list[float], list[float], list[float]]:
    """
    Calcule le prix, le delta et le gamma
    pour plusieurs valeurs du sous-jacent.
    """

    prices = []
    deltas = []
    gammas = []

    for spot in spots:
        contract = OptionContract(
            S=float(spot),
            K=strike,
            T=maturity,
            r=rate,
            sigma=volatility,
            option_type=option_type,
            q=dividend
        )

        price = bs_price(contract)
        greeks = bs_greeks(contract)

        prices.append(price)
        deltas.append(greeks["delta"])
        gammas.append(greeks["gamma"])

    return prices, deltas, gammas


def plot_option_price(
    spots: np.ndarray,
    prices: list[float],
    strike: float
) -> None:
    """Affiche le prix de l'option selon le sous-jacent."""

    plt.figure(figsize=(9, 5))

    plt.plot(
        spots,
        prices,
        label="Prix du call"
    )

    plt.axvline(
        strike,
        linestyle="--",
        label=f"Strike = {strike}"
    )

    plt.title("Prix du call selon le prix du sous-jacent")
    plt.xlabel("Prix du sous-jacent")
    plt.ylabel("Prix du call")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_delta(
    spots: np.ndarray,
    deltas: list[float],
    strike: float
) -> None:
    """Affiche le delta selon le sous-jacent."""

    plt.figure(figsize=(9, 5))

    plt.plot(
        spots,
        deltas,
        label="Delta du call"
    )

    plt.axvline(
        strike,
        linestyle="--",
        label=f"Strike = {strike}"
    )

    plt.title("Delta du call selon le prix du sous-jacent")
    plt.xlabel("Prix du sous-jacent")
    plt.ylabel("Delta")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_gamma(
    spots: np.ndarray,
    gammas: list[float],
    strike: float
) -> None:
    """Affiche le gamma selon le sous-jacent."""

    plt.figure(figsize=(9, 5))

    plt.plot(
        spots,
        gammas,
        label="Gamma du call"
    )

    plt.axvline(
        strike,
        linestyle="--",
        label=f"Strike = {strike}"
    )

    plt.title("Gamma du call selon le prix du sous-jacent")
    plt.xlabel("Prix du sous-jacent")
    plt.ylabel("Gamma")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    strike = 500
    maturity = 0.25
    rate = 0.05
    volatility = 0.20
    dividend = 0.0
    option_type = "call"

    # On fait varier le sous-jacent de 300 à 700
    spots = np.linspace(
        300,
        700,
        200
    )

    prices, deltas, gammas = calculate_values_for_spots(
        spots=spots,
        strike=strike,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
        dividend=dividend,
        option_type=option_type
    )

    plot_option_price(
        spots=spots,
        prices=prices,
        strike=strike
    )

    plot_delta(
        spots=spots,
        deltas=deltas,
        strike=strike
    )

    plot_gamma(
        spots=spots,
        gammas=gammas,
        strike=strike
    )

