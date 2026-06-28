import pytest

from pricing_BS import (
    OptionContract,
    bs_greeks,
    bs_price,
    implied_volatility,
    verify_put_call_parity,
)

# Crée un call simple que l'on réutilise dans plusieurs tests

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


# Crée le put correspondant au call précédent

@pytest.fixture
def put_option():
    return OptionContract(
        S=500,
        K=500,
        T=0.25,
        r=0.05,
        sigma=0.20,
        option_type="put",
        q=0.0
    )


def test_call_price_is_positive(call_option):
    """
    Le prix d'un call valide doit être positif.
    """

    price = bs_price(call_option)

    assert price > 0


def test_put_price_is_positive(put_option):
    """
    Le prix d'un put valide doit être positif.
    """

    price = bs_price(put_option)

    assert price > 0


def test_call_price_matches_expected_value(call_option):
    """
    Vérifie que le prix du call reste proche du résultat attendu.

    Cette valeur vient de notre exemple avec :
    S = 500, K = 500, T = 0.25, r = 5 %, sigma = 20 %.
    """

    price = bs_price(call_option)

    assert price == pytest.approx(23.074986, rel=1e-6)


def test_put_price_matches_expected_value(put_option):
    """
    Vérifie que le prix du put reste proche du résultat attendu.
    """

    price = bs_price(put_option)

    assert price == pytest.approx(16.863886, rel=1e-6)


def test_call_delta_is_between_zero_and_one(call_option):
    """
    Le delta d'un call européen sans cas particulier
    doit normalement être compris entre 0 et 1.
    """

    greeks = bs_greeks(call_option)
    delta = greeks["delta"]

    assert 0 < delta < 1


def test_put_delta_is_between_minus_one_and_zero(put_option):
    """
    Le delta d'un put européen doit normalement
    être compris entre -1 et 0.
    """

    greeks = bs_greeks(put_option)
    delta = greeks["delta"]

    assert -1 < delta < 0


def test_gamma_is_positive(call_option):
    """
    Le gamma d'une option européenne standard est positif.
    """

    greeks = bs_greeks(call_option)
    gamma = greeks["gamma"]

    assert gamma > 0


def test_vega_is_positive(call_option):
    """
    Une hausse de volatilité augmente généralement
    le prix d'un call européen standard.
    Le vega doit donc être positif.
    """

    greeks = bs_greeks(call_option)
    vega = greeks["vega"]

    assert vega > 0


def test_call_theta_is_negative(call_option):
    """
    Pour cet exemple précis, le call perd de la valeur avec le temps.
    Son theta doit donc être négatif.
    """

    greeks = bs_greeks(call_option)
    theta = greeks["theta"]

    assert theta < 0


def test_put_call_parity(call_option, put_option):
    """
    Vérifie que la relation théorique entre call et put est respectée.
    """

    result = verify_put_call_parity(
        call=call_option,
        put=put_option
    )

    assert result["parity_holds"] is True
    assert result["error"] < 1e-8


def test_implied_volatility_recovers_original_sigma(call_option):
    """
    On calcule d'abord le prix avec une volatilité de 20 %.

    Ensuite, on donne ce prix à la fonction de volatilité implicite.
    Elle doit retrouver environ 20 %.
    """

    market_price = bs_price(call_option)

    recovered_volatility = implied_volatility(
        market_price=market_price,
        contract=call_option
    )

    assert recovered_volatility is not None
    assert recovered_volatility == pytest.approx(
        0.20,
        rel=1e-6
    )


def test_invalid_spot_raises_error():
    """
    Un prix du sous-jacent négatif ou nul
    ne doit pas être accepté.
    """

    with pytest.raises(ValueError):
        OptionContract(
            S=-100,
            K=100,
            T=1,
            r=0.05,
            sigma=0.20,
            option_type="call"
        )


def test_invalid_strike_raises_error():
    """
    Un strike négatif ou nul
    ne doit pas être accepté.
    """

    with pytest.raises(ValueError):
        OptionContract(
            S=100,
            K=0,
            T=1,
            r=0.05,
            sigma=0.20,
            option_type="call"
        )


def test_invalid_maturity_raises_error():
    """
    Une maturité négative ou nulle
    ne doit pas être acceptée.
    """

    with pytest.raises(ValueError):
        OptionContract(
            S=100,
            K=100,
            T=0,
            r=0.05,
            sigma=0.20,
            option_type="call"
        )


def test_invalid_volatility_raises_error():
    """
    Une volatilité négative ou nulle
    ne doit pas être acceptée.
    """

    with pytest.raises(ValueError):
        OptionContract(
            S=100,
            K=100,
            T=1,
            r=0.05,
            sigma=0,
            option_type="call"
        )


def test_invalid_option_type_raises_error():
    """
    Le type d'option doit être soit 'call', soit 'put'.
    """

    with pytest.raises(ValueError):
        OptionContract(
            S=100,
            K=100,
            T=1,
            r=0.05,
            sigma=0.20,
            option_type="invalid"
        )
