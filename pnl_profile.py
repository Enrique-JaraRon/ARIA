"""
ARIA - Profil de P&L selon le niveau du spot
"""

from dataclasses import dataclass

import pandas as pd

from portfolio import Portfolio
from scenario_analysis import run_scenario


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

    Objectif :
    - eviter les bugs d'encodage avec les accents ;
    - accepter les anciens noms comme "Spot stressé" ;
    - utiliser en interne uniquement des noms ASCII.
    """

    column_aliases = {
        "Spot stressé": "Spot stresse",
        "Spot stressÃ©": "Spot stresse",
        "Spot stresse": "Spot stresse",

        "Valeur stressée": "Valeur stressee",
        "Valeur stressÃ©e": "Valeur stressee",
        "Valeur stressee": "Valeur stressee",

        "Résultat": "Resultat",
        "RÃ©sultat": "Resultat",
        "Resultat": "Resultat",
    }

    return pnl_data.rename(
        columns=column_aliases
    )


def calculate_pnl_profile(
    portfolio: Portfolio,
    current_spot: float,
    minimum_change: float = -0.30,
    maximum_change: float = 0.30,
    number_of_points: int = 61
) -> list[PnLPoint]:
    """
    Calcule le P&L pour plusieurs niveaux du spot.

    La volatilite reste constante.
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

    Important :
    les noms de colonnes internes sont volontairement sans accents.
    Cela evite les erreurs de type KeyError avec pandas.
    """

    return pd.DataFrame(
        [
            {
                "Variation spot": point.spot_change_percent,
                "Spot stresse": point.stressed_spot,
                "Profit / Perte": point.profit_and_loss,
                "Valeur stressee": point.stressed_value
            }
            for point in points
        ]
    )


def find_breakeven_spots(
    pnl_data: pd.DataFrame
) -> list[float]:
    """
    Trouve les spots ou le P&L traverse zero.

    La methode utilise une interpolation lineaire entre deux points.
    """

    pnl_data = normalize_pnl_columns(
        pnl_data
    )

    required_columns = [
        "Spot stresse",
        "Profit / Perte"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in pnl_data.columns
    ]

    if missing_columns:
        raise KeyError(
            "Colonnes manquantes dans le profil de P&L : "
            f"{missing_columns}. "
            f"Colonnes disponibles : {list(pnl_data.columns)}"
        )

    breakeven_spots = []

    sorted_data = pnl_data.sort_values(
        "Spot stresse"
    ).reset_index(
        drop=True
    )

    for index in range(
        len(sorted_data) - 1
    ):

        spot_1 = sorted_data.loc[
            index,
            "Spot stresse"
        ]

        spot_2 = sorted_data.loc[
            index + 1,
            "Spot stresse"
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