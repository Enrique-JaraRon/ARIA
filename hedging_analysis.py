"""
ARIA - Analyse de couverture delta
"""

from dataclasses import dataclass

from portfolio import Portfolio


@dataclass
class DeltaHedgeResult:
    """Résultat d'une couverture delta indicative."""

    current_delta: float
    hedge_quantity: float
    hedge_market_value: float
    hedged_delta: float
    explanation: str


def calculate_delta_hedge(
    portfolio: Portfolio,
    current_spot: float
) -> DeltaHedgeResult:
    """
    Calcule la quantité de sous-jacent nécessaire
    pour neutraliser approximativement le delta du portefeuille.
    """

    if current_spot <= 0:
        raise ValueError(
            "Le spot actuel doit être strictement positif."
        )

    greeks = portfolio.total_greeks()

    current_delta = greeks["delta"]

    hedge_quantity = -current_delta

    hedge_market_value = (
        hedge_quantity
        * current_spot
    )

    hedged_delta = (
        current_delta
        + hedge_quantity
    )

    if current_delta > 0:
        explanation = (
            "Le portefeuille a un delta positif. "
            "Il est globalement exposé à une hausse du sous-jacent. "
            "Une couverture delta consiste à vendre du sous-jacent."
        )

    elif current_delta < 0:
        explanation = (
            "Le portefeuille a un delta négatif. "
            "Il est globalement exposé à une baisse du sous-jacent. "
            "Une couverture delta consiste à acheter du sous-jacent."
        )

    else:
        explanation = (
            "Le portefeuille est déjà approximativement delta-neutre."
        )

    return DeltaHedgeResult(
        current_delta=current_delta,
        hedge_quantity=hedge_quantity,
        hedge_market_value=hedge_market_value,
        hedged_delta=hedged_delta,
        explanation=explanation
    )


def apply_delta_hedge(
    portfolio: Portfolio,
    current_spot: float,
    hedge_name: str = "Couverture delta"
) -> Portfolio:
    """
    Ajoute une position de couverture delta au portefeuille.

    Cette fonction modifie le portefeuille donné.
    """

    hedge_result = calculate_delta_hedge(
        portfolio=portfolio,
        current_spot=current_spot
    )

    hedge_quantity = round(
        hedge_result.hedge_quantity
    )

    if hedge_quantity == 0:
        return portfolio

    portfolio.add_stock(
        spot=current_spot,
        quantity=hedge_quantity,
        name=hedge_name
    )

    return portfolio


if __name__ == "__main__":
    from pricing_BS import OptionContract

    portfolio = Portfolio(
        name="Test couverture delta"
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

    result = calculate_delta_hedge(
        portfolio=portfolio,
        current_spot=500
    )

    print("Couverture delta")
    print(f"Delta actuel : {result.current_delta:.4f}")
    print(f"Quantité de couverture : {result.hedge_quantity:.4f}")
    print(f"Valeur de couverture : {result.hedge_market_value:.2f}")
    print(f"Delta après couverture : {result.hedged_delta:.4f}")
    print(result.explanation)
