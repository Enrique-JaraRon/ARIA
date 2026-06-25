
"""
ARIA - Moteur de pricing Black-Scholes
"""

from dataclasses import dataclass
from typing import Literal
import warnings

import numpy as np
from scipy.stats import norm


@dataclass
class OptionContract:
    S: float
    K: float
    T: float
    r: float
    sigma: float
    option_type: Literal["call", "put"] = "call"
    q: float = 0.0

    def __post_init__(self) -> None:
        if self.S <= 0:
            raise ValueError("S doit être strictement positif.")

        if self.K <= 0:
            raise ValueError("K doit être strictement positif.")

        if self.T <= 0:
            raise ValueError("T doit être strictement positif.")

        if self.sigma <= 0:
            raise ValueError("sigma doit être strictement positif.")

        if self.option_type not in ("call", "put"):
            raise ValueError("option_type doit être 'call' ou 'put'.")


def compute_d1_d2(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0
) -> tuple[float, float]:
    """Calcule d1 et d2."""

    log_moneyness = np.log(S / K)
    drift = (r - q + 0.5 * sigma**2) * T
    volatility_over_period = sigma * np.sqrt(T)

    d1 = (log_moneyness + drift) / volatility_over_period
    d2 = d1 - volatility_over_period

    return float(d1), float(d2)


def bs_price(contract: OptionContract) -> float:
    """Calcule le prix d'un call ou d'un put européen."""

    S = contract.S
    K = contract.K
    T = contract.T
    r = contract.r
    sigma = contract.sigma
    q = contract.q

    d1, d2 = compute_d1_d2(
        S=S,
        K=K,
        T=T,
        r=r,
        sigma=sigma,
        q=q
    )

    discounted_spot = S * np.exp(-q * T)
    discounted_strike = K * np.exp(-r * T)

    if contract.option_type == "call":
        price = (
            discounted_spot * norm.cdf(d1)
            - discounted_strike * norm.cdf(d2)
        )
    else:
        price = (
            discounted_strike * norm.cdf(-d2)
            - discounted_spot * norm.cdf(-d1)
        )

    return float(price)


def bs_greeks(contract: OptionContract) -> dict[str, float]:
    """Calcule les principaux Greeks."""

    S = contract.S
    K = contract.K
    T = contract.T
    r = contract.r
    sigma = contract.sigma
    q = contract.q

    d1, d2 = compute_d1_d2(
        S=S,
        K=K,
        T=T,
        r=r,
        sigma=sigma,
        q=q
    )

    exp_minus_qT = np.exp(-q * T)
    exp_minus_rT = np.exp(-r * T)
    sqrt_T = np.sqrt(T)
    pdf_d1 = norm.pdf(d1)

    if contract.option_type == "call":
        delta = exp_minus_qT * norm.cdf(d1)
    else:
        delta = exp_minus_qT * (norm.cdf(d1) - 1)

    gamma = (
        pdf_d1 * exp_minus_qT
        / (S * sigma * sqrt_T)
    )

    theta_common = (
        -(S * pdf_d1 * sigma * exp_minus_qT)
        / (2 * sqrt_T)
    )

    if contract.option_type == "call":
        theta_annual = (
            theta_common
            - r * K * exp_minus_rT * norm.cdf(d2)
            + q * S * exp_minus_qT * norm.cdf(d1)
        )
    else:
        theta_annual = (
            theta_common
            + r * K * exp_minus_rT * norm.cdf(-d2)
            - q * S * exp_minus_qT * norm.cdf(-d1)
        )

    theta_daily = theta_annual / 365.0

    vega_absolute = (
        S * exp_minus_qT * pdf_d1 * sqrt_T
    )

    vega_per_vol_point = vega_absolute / 100.0

    if contract.option_type == "call":
        rho_absolute = (
            K * T * exp_minus_rT * norm.cdf(d2)
        )
    else:
        rho_absolute = (
            -K * T * exp_minus_rT * norm.cdf(-d2)
        )

    rho_per_rate_point = rho_absolute / 100.0

    vanna = (
        -exp_minus_qT
        * pdf_d1
        * d2
        / sigma
    )

    volga_absolute = (
        vega_absolute
        * d1
        * d2
        / sigma
    )

    volga_per_vol_point_squared = (
        volga_absolute / 10000.0
    )

    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "theta": float(theta_daily),
        "vega": float(vega_per_vol_point),
        "rho": float(rho_per_rate_point),
        "vanna": float(vanna),
        "volga": float(volga_per_vol_point_squared),
        "d1": float(d1),
        "d2": float(d2),
    }


def option_price_bounds(
    contract: OptionContract
) -> tuple[float, float]:
    """Calcule les bornes théoriques du prix."""

    discounted_spot = (
        contract.S
        * np.exp(-contract.q * contract.T)
    )

    discounted_strike = (
        contract.K
        * np.exp(-contract.r * contract.T)
    )

    if contract.option_type == "call":
        lower_bound = max(
            discounted_spot - discounted_strike,
            0.0
        )

        upper_bound = discounted_spot

    else:
        lower_bound = max(
            discounted_strike - discounted_spot,
            0.0
        )

        upper_bound = discounted_strike

    return float(lower_bound), float(upper_bound)


def implied_volatility(
    market_price: float,
    contract: OptionContract,
    tolerance: float = 1e-8,
    max_iterations: int = 100
) -> float | None:
    """Calcule la volatilité implicite."""

    if market_price <= 0:
        warnings.warn(
            "Le prix de marché doit être strictement positif."
        )
        return None

    lower_bound, upper_bound = option_price_bounds(contract)

    if not lower_bound <= market_price <= upper_bound:
        warnings.warn(
            "Le prix de marché est hors des bornes théoriques."
        )
        return None

    sigma = 0.20

    working_contract = OptionContract(
        S=contract.S,
        K=contract.K,
        T=contract.T,
        r=contract.r,
        sigma=sigma,
        option_type=contract.option_type,
        q=contract.q
    )

    for _ in range(max_iterations):
        working_contract.sigma = sigma

        model_price = bs_price(working_contract)

        d1, _ = compute_d1_d2(
            S=working_contract.S,
            K=working_contract.K,
            T=working_contract.T,
            r=working_contract.r,
            sigma=working_contract.sigma,
            q=working_contract.q
        )

        vega_absolute = (
            working_contract.S
            * np.exp(
                -working_contract.q
                * working_contract.T
            )
            * norm.pdf(d1)
            * np.sqrt(working_contract.T)
        )

        price_error = model_price - market_price

        if abs(price_error) < tolerance:
            return float(sigma)

        if abs(vega_absolute) < 1e-12:
            warnings.warn("Le vega est trop faible.")
            return None

        sigma = sigma - price_error / vega_absolute

        sigma = max(
            0.0001,
            min(sigma, 5.0)
        )

    warnings.warn(
        "La volatilité implicite n'a pas convergé."
    )

    return None


def verify_put_call_parity(
    call: OptionContract,
    put: OptionContract,
    tolerance: float = 1e-8
) -> dict[str, float | bool]:
    """Vérifie la parité call-put."""

    if call.option_type != "call":
        raise ValueError(
            "Le premier contrat doit être un call."
        )

    if put.option_type != "put":
        raise ValueError(
            "Le second contrat doit être un put."
        )

    parameters_to_compare = (
        "S",
        "K",
        "T",
        "r",
        "q"
    )

    for parameter in parameters_to_compare:
        call_value = getattr(call, parameter)
        put_value = getattr(put, parameter)

        if not np.isclose(call_value, put_value):
            raise ValueError(
                f"Le paramètre {parameter} doit être identique."
            )

    call_price = bs_price(call)
    put_price = bs_price(put)

    left_hand_side = call_price - put_price

    right_hand_side = (
        call.S * np.exp(-call.q * call.T)
        - call.K * np.exp(-call.r * call.T)
    )

    error = abs(
        left_hand_side - right_hand_side
    )

    return {
        "call_price": float(call_price),
        "put_price": float(put_price),
        "left_hand_side": float(left_hand_side),
        "right_hand_side": float(right_hand_side),
        "error": float(error),
        "parity_holds": bool(error < tolerance),
    }


if __name__ == "__main__":
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
        K=500,
        T=0.25,
        r=0.05,
        sigma=0.20,
        option_type="put",
        q=0.0
    )

    call_price = bs_price(call)
    put_price = bs_price(put)

    call_greeks = bs_greeks(call)

    parity_result = verify_put_call_parity(
        call=call,
        put=put
    )

    recovered_volatility = implied_volatility(
        market_price=call_price,
        contract=call
    )

    print("ARIA - Moteur de pricing Black-Scholes")

    print("\nParamètres")
    print(f"Sous-jacent : {call.S}")
    print(f"Strike : {call.K}")
    print(f"Maturité : {call.T} an")
    print(f"Taux : {call.r:.2%}")
    print(f"Volatilité : {call.sigma:.2%}")
    print(f"Dividende : {call.q:.2%}")

    print("\nPrix")
    print(f"Call : {call_price:.6f}")
    print(f"Put : {put_price:.6f}")

    print("\nGreeks du call")
    print(f"Delta : {call_greeks['delta']:.6f}")
    print(f"Gamma : {call_greeks['gamma']:.6f}")
    print(f"Theta : {call_greeks['theta']:.6f}")
    print(f"Vega : {call_greeks['vega']:.6f}")
    print(f"Rho : {call_greeks['rho']:.6f}")
    print(f"Vanna : {call_greeks['vanna']:.6f}")
    print(f"Volga : {call_greeks['volga']:.6f}")

    print("\nParité call-put")
    print(
        f"C - P : "
        f"{parity_result['left_hand_side']:.10f}"
    )
    print(
        f"Valeur théorique : "
        f"{parity_result['right_hand_side']:.10f}"
    )
    print(
        f"Erreur : "
        f"{parity_result['error']:.10e}"
    )
    print(
        "Résultat : "
        f"{'OK' if parity_result['parity_holds'] else 'ÉCHEC'}"
    )

    print("\nVolatilité implicite")

    if recovered_volatility is not None:
        print(
            f"Volatilité retrouvée : "
            f"{recovered_volatility:.6%}"
        )
    else:
        print(
            "Impossible de retrouver la volatilité implicite."
        )

