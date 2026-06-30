import pytest

from portfolio import OptionPosition, Portfolio, StockPosition
from pricing_BS import OptionContract, bs_greeks, bs_price


@pytest.fixture
def call_option():
    return OptionContract(
        S=500,
        K=500,
        T=0.25,
        r=0.05,
        sigma=0.20,
        option_type="call",
        q=0.0
    )


@pytest.fixture
def put_option():
    return OptionContract(
        S=500,
        K=470,
        T=0.25,
        r=0.05,
        sigma=0.25,
        option_type="put",
        q=0.0
    )


def test_add_option_to_portfolio(call_option):
    portfolio = Portfolio()

    portfolio.add_option(
        contract=call_option,
        quantity=10,
        name="Calls achetés"
    )

    assert len(portfolio.positions) == 1
    assert isinstance(portfolio.positions[0], OptionPosition)
    assert portfolio.positions[0].quantity == 10


def test_add_stock_to_portfolio():
    portfolio = Portfolio()

    portfolio.add_stock(
        spot=500,
        quantity=-3,
        name="Couverture en SPY"
    )

    assert len(portfolio.positions) == 1
    assert isinstance(portfolio.positions[0], StockPosition)
    assert portfolio.positions[0].quantity == -3


def test_option_position_market_value(call_option):
    position = OptionPosition(
        contract=call_option,
        quantity=10
    )

    expected_value = bs_price(call_option) * 10

    assert position.market_value() == pytest.approx(
        expected_value,
        rel=1e-9
    )


def test_stock_position_market_value():
    position = StockPosition(
        spot=500,
        quantity=-3
    )

    assert position.market_value() == -1500


def test_option_position_greeks_are_multiplied_by_quantity(call_option):
    position = OptionPosition(
        contract=call_option,
        quantity=10
    )

    single_option_greeks = bs_greeks(call_option)
    position_greeks = position.total_greeks()

    assert position_greeks["delta"] == pytest.approx(
        single_option_greeks["delta"] * 10
    )

    assert position_greeks["gamma"] == pytest.approx(
        single_option_greeks["gamma"] * 10
    )

    assert position_greeks["vega"] == pytest.approx(
        single_option_greeks["vega"] * 10
    )


def test_stock_position_has_delta_equal_to_quantity():
    position = StockPosition(
        spot=500,
        quantity=-3
    )

    greeks = position.total_greeks()

    assert greeks["delta"] == -3
    assert greeks["gamma"] == 0
    assert greeks["theta"] == 0
    assert greeks["vega"] == 0
    assert greeks["rho"] == 0


def test_total_market_value(call_option, put_option):
    portfolio = Portfolio()

    portfolio.add_option(
        contract=call_option,
        quantity=10
    )

    portfolio.add_option(
        contract=put_option,
        quantity=-5
    )

    portfolio.add_stock(
        spot=500,
        quantity=-3
    )

    expected_value = (
        bs_price(call_option) * 10
        + bs_price(put_option) * -5
        + 500 * -3
    )

    assert portfolio.total_market_value() == pytest.approx(
        expected_value,
        rel=1e-9
    )


def test_total_greeks_are_sum_of_all_positions(
    call_option,
    put_option
):
    portfolio = Portfolio()

    portfolio.add_option(
        contract=call_option,
        quantity=10
    )

    portfolio.add_option(
        contract=put_option,
        quantity=-5
    )

    portfolio.add_stock(
        spot=500,
        quantity=-3
    )

    call_greeks = bs_greeks(call_option)
    put_greeks = bs_greeks(put_option)

    expected_delta = (
        call_greeks["delta"] * 10
        + put_greeks["delta"] * -5
        - 3
    )

    expected_gamma = (
        call_greeks["gamma"] * 10
        + put_greeks["gamma"] * -5
    )

    expected_vega = (
        call_greeks["vega"] * 10
        + put_greeks["vega"] * -5
    )

    totals = portfolio.total_greeks()

    assert totals["delta"] == pytest.approx(expected_delta)
    assert totals["gamma"] == pytest.approx(expected_gamma)
    assert totals["vega"] == pytest.approx(expected_vega)


def test_remove_position(call_option):
    portfolio = Portfolio()

    portfolio.add_option(
        contract=call_option,
        quantity=10
    )

    portfolio.add_stock(
        spot=500,
        quantity=-3
    )

    portfolio.remove_position(0)

    assert len(portfolio.positions) == 1
    assert isinstance(portfolio.positions[0], StockPosition)


def test_invalid_remove_position_raises_error():
    portfolio = Portfolio()

    with pytest.raises(IndexError):
        portfolio.remove_position(0)


def test_zero_option_quantity_raises_error(call_option):
    portfolio = Portfolio()

    with pytest.raises(ValueError):
        portfolio.add_option(
            contract=call_option,
            quantity=0
        )


def test_zero_stock_quantity_raises_error():
    portfolio = Portfolio()

    with pytest.raises(ValueError):
        portfolio.add_stock(
            spot=500,
            quantity=0
        )


def test_invalid_stock_spot_raises_error():
    with pytest.raises(ValueError):
        StockPosition(
            spot=0,
            quantity=10
        )


def test_empty_portfolio_value_is_zero():
    portfolio = Portfolio()

    assert portfolio.total_market_value() == 0


def test_empty_portfolio_greeks_are_zero():
    portfolio = Portfolio()

    totals = portfolio.total_greeks()

    assert totals["delta"] == 0
    assert totals["gamma"] == 0
    assert totals["theta"] == 0
    assert totals["vega"] == 0
    assert totals["rho"] == 0
    assert totals["vanna"] == 0
    assert totals["volga"] == 0


def test_exposure_by_underlying_handles_multiple_underlyings(
    call_option,
    put_option
):
    portfolio = Portfolio()

    portfolio.add_option(
        contract=call_option,
        quantity=10,
        underlying="SPY"
    )
    portfolio.add_option(
        contract=put_option,
        quantity=-5,
        underlying="QQQ"
    )
    portfolio.add_stock(
        spot=500,
        quantity=3,
        underlying="SPY"
    )

    exposures = portfolio.exposure_by_underlying()

    assert portfolio.underlyings() == [
        "QQQ",
        "SPY"
    ]
    assert set(exposures) == {
        "SPY",
        "QQQ"
    }
    assert exposures["SPY"]["delta"] != exposures["QQQ"]["delta"]
    assert exposures["SPY"]["abs_market_value"] > 0
    assert exposures["QQQ"]["abs_market_value"] > 0
