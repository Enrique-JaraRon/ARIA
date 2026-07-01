"""
ARIA - Profil de P&L selon le niveau du spot
"""

from dataclasses import dataclass

import os
import pandas as pd

from portfolio import Portfolio
from scenario_analysis import run_scenario


print("PNL_PROFILE UTILISE =", os.path.abspath(__file__))
print("VERSION TEST = PNL_PROFILE_CORRIGE_2026")


@dataclass
class PnLPoint:
    """Represente un point de la courbe de P&L."""

    spot_change_percent: float
    stressed_spot: float
    profit_and_loss: float
    stressed_value: float


def normalize_pnl_columns(
    pnl_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Normalise les noms de colonnes du profil de P&L.
    """

    data = pnl_data.copy()

    data = data.rename(
        columns={
            "Spot stressé": "Spot stressé",
            "Spot stressÃ©": "Spot stressé",
            "Spot stresse": "Spot stressé",
            "Valeur stressée": "Valeur stressee",
            "Valeur stressÃ©e": "Valeur stressee",
            "Valeur stressee": "Valeur stressee",
        }
    )

    return data


def calculate_pnl_profile(
    portfolio: Portfolio,
    current_spot: float,
    minimum_change: float = -0.30,
    maximum_change: float = 0.30,
    number_of_points: int = 61
) -> list[PnLPoint]:
    """
    Calcule le P&L pour plusieurs niveaux du spot.
    """

    if current_spot <= 0:
        raise ValueError(
            "Le spot actuel doit etre strictement positif."
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

        result = run_scenario(
            portfolio=portfolio,
            name="Profil de P&L",
            spot_change_percent=spot_change,
            volatility_change_points=0.0
        )

        stressed_spot = (
            current_spot
            * (1 + spot_change)
        )

        points.append(
            PnLPoint(
                spot_change_percent=spot_change,
                stressed_spot=stressed_spot,
                profit_and_loss=result.profit_and_loss,
                stressed_value=result.stressed_value
            )
        )

    return points


def pnl_profile_to_dataframe(
    points: list[PnLPoint]
) -> pd.DataFrame:
    """
    Transforme le profil de P&L en tableau.
    """

    return pd.DataFrame(
        [
            {
                "Variation spot": point.spot_change_percent,
                "Spot stressé": point.stressed_spot,
                "Profit / Perte": point.profit_and_loss,
                "Valeur stresséé": point.stressed_value
            }
            for point in points
        ]
    )


def find_breakeven_spots(
    pnl_data: pd.DataFrame
) -> list[float]:
    """
    Trouve les spots ou le P&L traverse zero.
    """

    pnl_data = normalize_pnl_columns(
        pnl_data
    )

    if "Spot stressé" not in pnl_data.columns:
        raise KeyError(
            "Colonne 'Spot stressé' introuvable. "
            f"Colonnes disponibles : {list(pnl_data.columns)}"
        )

    if "Profit / Perte" not in pnl_data.columns:
        raise KeyError(
            "Colonne 'Profit / Perte' introuvable. "
            f"Colonnes disponibles : {list(pnl_data.columns)}"
        )

    breakeven_spots = []

    sorted_data = pnl_data.sort_values(
        "Spot stressé"
    ).reset_index(
        drop=True
    )

    for index in range(
        len(sorted_data) - 1
    ):

        spot_1 = sorted_data.loc[
            index,
            "Spot stressé"
        ]

        spot_2 = sorted_data.loc[
            index + 1,
            "Spot stressé"
        ]

        pnl_1 = sorted_data.loc[
            index,
            "Profit / Perte"
        ]

        pnl_2 = sorted_data.loc[
            index + 1,
            "Profit / Perte"
        ]

        if pnl_1 == 0:
            breakeven_spots.append(
                spot_1
            )

        elif pnl_1 * pnl_2 < 0:

            breakeven_spot = spot_1 + (
                (0 - pnl_1)
                * (spot_2 - spot_1)
                / (pnl_2 - pnl_1)
            )

            breakeven_spots.append(
                breakeven_spot
            )

    return breakeven_spots


if __name__ == "__main__":
    from pricing_BS import OptionContract

    portfolio = Portfolio(
        name="Test profil de P&L"
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
        name="Calls achetes"
    )

    points = calculate_pnl_profile(
        portfolio=portfolio,
        current_spot=500,
        minimum_change=-0.30,
        maximum_change=0.30,
        number_of_points=61
    )

    dataframe = pnl_profile_to_dataframe(
        points
    )

    breakevens = find_breakeven_spots(
        dataframe
    )

    print(dataframe)

    print("\nPoints morts")

    if breakevens:
        for spot in breakevens:
            print(
                f"Spot environ {spot:.2f}"
            )
    else:
        print(
            "Aucun point mort trouve dans l'intervalle teste."
        )