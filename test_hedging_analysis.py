"""
Tests du module hedging_analysis.py
"""

from pricing_BS import OptionContract
from portfolio import Portfolio
from hedging_analysis import calculate_delta_hedge, apply_delta_hedge


def create_test_portfolio() -> Portfolio:
    """Crée un portefeuille simple pour les tests."""

    portfolio = Portfolio(
        name="Test hedge"
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
        name="Calls test"
    )

    return portfolio


def test_delta_hedge_result_is_valid():
    """Vérifie que la couverture delta renvoie des valeurs cohérentes."""

    portfolio = create_test_portfolio()

    result = calculate_delta_hedge(
        portfolio=portfolio,
        current_spot=500
    )

    assert result.current_delta != 0
    assert result.hedge_quantity == -result.current_delta
    assert result.hedged_delta == 0
    assert result.hedge_market_value == result.hedge_quantity * 500
    assert isinstance(
        result.explanation,
        str
    )


def test_apply_delta_hedge_adds_stock_position():
    """Vérifie que la couverture ajoute une position action."""

    portfolio = create_test_portfolio()

    initial_number_of_positions = len(
        portfolio.positions
    )

    apply_delta_hedge(
        portfolio=portfolio,
        current_spot=500
    )

    assert len(portfolio.positions) == initial_number_of_positions + 1