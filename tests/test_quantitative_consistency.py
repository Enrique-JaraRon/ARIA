from portfolio_engine.demo_portfolios import create_demo_portfolio
from portfolio_engine.pricing_BS import OptionContract, bs_greeks, bs_price
from risk_engine.probabilistic_risk import simulate_probabilistic_risk
from risk_engine.risk_score import calculate_risk_score
from risk_engine.scenario_analysis import (
    run_historical_scenarios,
    run_standard_scenarios,
)
from risk_engine.var_analysis import calculate_var_es


def test_black_scholes_call_put_and_greeks_are_coherent():
    """Check core pricing and Greeks on a standard ATM option."""

    call = OptionContract(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.20,
        option_type="call",
    )
    put = OptionContract(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.20,
        option_type="put",
    )

    call_price = bs_price(call)
    put_price = bs_price(put)
    call_greeks = bs_greeks(call)
    put_greeks = bs_greeks(put)

    assert round(call_price, 4) == 10.4506
    assert round(put_price, 4) == 5.5735
    assert call_price > put_price
    assert 0 < call_greeks["delta"] < 1
    assert -1 < put_greeks["delta"] < 0
    assert call_greeks["gamma"] > 0
    assert put_greeks["gamma"] > 0
    assert call_greeks["vega"] > 0
    assert put_greeks["vega"] > 0


def test_low_risk_options_demo_has_low_score_and_valid_tail_metrics():
    """Prevent regressions on the interview-ready defensive options demo."""

    portfolio = create_demo_portfolio("Low Risk Options Portfolio")
    scenarios = run_standard_scenarios(portfolio) + run_historical_scenarios(portfolio)
    var_result, _ = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=0.18,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=1000,
        seed=42,
    )
    probabilistic_result, simulations = simulate_probabilistic_risk(
        portfolio=portfolio,
        horizon_days=20,
        number_of_simulations=1000,
        confidence_level=0.95,
        seed=42,
    )
    risk_score = calculate_risk_score(
        portfolio=portfolio,
        alerts=[],
        var_result=var_result,
        scenario_results=scenarios,
        delta_limit=10,
        gamma_limit=1,
        vega_limit=20,
    )

    assert risk_score.score < 30
    assert risk_score.label == "Risque faible"
    assert var_result.var_amount > 0
    assert var_result.expected_shortfall >= var_result.var_amount
    assert 0 <= probabilistic_result.probability_of_loss <= 1
    assert 0 <= probabilistic_result.probability_loss_gt_10 <= 1
    assert len(simulations) == 1000
