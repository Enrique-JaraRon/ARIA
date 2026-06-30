"""
ARIA - Portefeuilles de démonstration

Ce module crée plusieurs stratégies options classiques
pour tester rapidement l'application ARIA.
"""

from portfolio import Portfolio
from pricing_BS import OptionContract


def create_call_option(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
    dividend: float = 0.0,
) -> OptionContract:
    """Crée une option call européenne."""

    return OptionContract(
        S=spot,
        K=strike,
        T=maturity,
        r=rate,
        sigma=volatility,
        option_type="call",
        q=dividend,
    )


def create_put_option(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
    dividend: float = 0.0,
) -> OptionContract:
    """Crée une option put européenne."""

    return OptionContract(
        S=spot,
        K=strike,
        T=maturity,
        r=rate,
        sigma=volatility,
        option_type="put",
        q=dividend,
    )


def create_long_straddle(
    spot: float = 500.0,
    maturity: float = 0.25,
    rate: float = 0.05,
    volatility: float = 0.20,
    multiplier: int = 100,
) -> Portfolio:
    """
    Crée un long straddle.

    Stratégie :
    - achat d'un call ATM
    - achat d'un put ATM

    Objectif :
    profiter d'un fort mouvement du sous-jacent,
    peu importe la direction.
    """

    portfolio = Portfolio(
        name="Long Straddle"
    )

    call = create_call_option(
        spot=spot,
        strike=spot,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )

    put = create_put_option(
        spot=spot,
        strike=spot,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )

    portfolio.add_option(
        contract=call,
        quantity=1,
        multiplier=multiplier,
        name="Call ATM acheté",
    )

    portfolio.add_option(
        contract=put,
        quantity=1,
        multiplier=multiplier,
        name="Put ATM acheté",
    )

    return portfolio


def create_short_straddle(
    spot: float = 500.0,
    maturity: float = 0.25,
    rate: float = 0.05,
    volatility: float = 0.20,
    multiplier: int = 100,
) -> Portfolio:
    """
    Crée un short straddle.

    Stratégie :
    - vente d'un call ATM
    - vente d'un put ATM

    Objectif :
    gagner la prime si le sous-jacent reste stable.
    Risque important si le marché bouge fortement.
    """

    portfolio = Portfolio(
        name="Short Straddle"
    )

    call = create_call_option(
        spot=spot,
        strike=spot,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )

    put = create_put_option(
        spot=spot,
        strike=spot,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )

    portfolio.add_option(
        contract=call,
        quantity=-1,
        multiplier=multiplier,
        name="Call ATM vendu",
    )

    portfolio.add_option(
        contract=put,
        quantity=-1,
        multiplier=multiplier,
        name="Put ATM vendu",
    )

    return portfolio


def create_bull_call_spread(
    spot: float = 500.0,
    lower_strike: float = 500.0,
    upper_strike: float = 540.0,
    maturity: float = 0.25,
    rate: float = 0.05,
    volatility: float = 0.20,
    multiplier: int = 100,
) -> Portfolio:
    """
    Crée un bull call spread.

    Stratégie :
    - achat d'un call strike bas
    - vente d'un call strike haut

    Objectif :
    profiter d'une hausse modérée du sous-jacent
    avec un risque limité.
    """

    portfolio = Portfolio(
        name="Bull Call Spread"
    )

    long_call = create_call_option(
        spot=spot,
        strike=lower_strike,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )

    short_call = create_call_option(
        spot=spot,
        strike=upper_strike,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )

    portfolio.add_option(
        contract=long_call,
        quantity=1,
        multiplier=multiplier,
        name="Call strike bas acheté",
    )

    portfolio.add_option(
        contract=short_call,
        quantity=-1,
        multiplier=multiplier,
        name="Call strike haut vendu",
    )

    return portfolio


def create_bear_put_spread(
    spot: float = 500.0,
    lower_strike: float = 460.0,
    upper_strike: float = 500.0,
    maturity: float = 0.25,
    rate: float = 0.05,
    volatility: float = 0.20,
    multiplier: int = 100,
) -> Portfolio:
    """
    Crée un bear put spread.

    Stratégie :
    - achat d'un put strike haut
    - vente d'un put strike bas

    Objectif :
    profiter d'une baisse modérée du sous-jacent
    avec un risque limité.
    """

    portfolio = Portfolio(
        name="Bear Put Spread"
    )

    long_put = create_put_option(
        spot=spot,
        strike=upper_strike,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )

    short_put = create_put_option(
        spot=spot,
        strike=lower_strike,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )

    portfolio.add_option(
        contract=long_put,
        quantity=1,
        multiplier=multiplier,
        name="Put strike haut acheté",
    )

    portfolio.add_option(
        contract=short_put,
        quantity=-1,
        multiplier=multiplier,
        name="Put strike bas vendu",
    )

    return portfolio


def create_protective_put(
    spot: float = 500.0,
    put_strike: float = 470.0,
    maturity: float = 0.25,
    rate: float = 0.05,
    volatility: float = 0.20,
    stock_quantity: int = 100,
    multiplier: int = 100,
) -> Portfolio:
    """
    Crée une stratégie protective put.

    Stratégie :
    - achat du sous-jacent
    - achat d'un put de protection

    Objectif :
    conserver le potentiel de hausse
    tout en limitant la perte en cas de baisse.
    """

    portfolio = Portfolio(
        name="Protective Put"
    )

    put = create_put_option(
        spot=spot,
        strike=put_strike,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )

    portfolio.add_stock(
        spot=spot,
        quantity=stock_quantity,
        name="Actions détenues",
    )

    portfolio.add_option(
        contract=put,
        quantity=1,
        multiplier=multiplier,
        name="Put de protection acheté",
    )

    return portfolio


def create_covered_call(
    spot: float = 500.0,
    call_strike: float = 540.0,
    maturity: float = 0.25,
    rate: float = 0.05,
    volatility: float = 0.20,
    stock_quantity: int = 100,
    multiplier: int = 100,
) -> Portfolio:
    """
    Crée une stratégie covered call.

    Stratégie :
    - achat du sous-jacent
    - vente d'un call

    Objectif :
    générer une prime supplémentaire,
    en échange d'un potentiel de hausse plafonné.
    """

    portfolio = Portfolio(
        name="Covered Call"
    )

    call = create_call_option(
        spot=spot,
        strike=call_strike,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )

    portfolio.add_stock(
        spot=spot,
        quantity=stock_quantity,
        name="Actions détenues",
    )

    portfolio.add_option(
        contract=call,
        quantity=-1,
        multiplier=multiplier,
        name="Call vendu",
    )

    return portfolio


def create_tech_options_book(
    rate: float = 0.045,
    volatility: float = 0.28,
) -> Portfolio:
    """Create a multi-name technology options book."""

    portfolio = Portfolio(
        name="Tech Options Book"
    )
    names = [
        (
            "AAPL",
            195.0
        ),
        (
            "MSFT",
            430.0
        ),
        (
            "NVDA",
            125.0
        ),
    ]

    for ticker, spot in names:
        portfolio.add_stock(
            spot=spot,
            quantity=80,
            name=f"{ticker} cash equity",
            underlying=ticker,
        )
        portfolio.add_option(
            contract=create_put_option(
                spot=spot,
                strike=spot * 0.92,
                maturity=0.35,
                rate=rate,
                volatility=volatility + 0.04,
            ),
            quantity=2,
            multiplier=100,
            name=f"{ticker} protective puts",
            underlying=ticker,
        )
        portfolio.add_option(
            contract=create_call_option(
                spot=spot,
                strike=spot * 1.10,
                maturity=0.35,
                rate=rate,
                volatility=volatility,
            ),
            quantity=-1,
            multiplier=100,
            name=f"{ticker} overwrite calls",
            underlying=ticker,
        )

    return portfolio


def create_hedged_equity_portfolio(
    rate: float = 0.045,
    volatility: float = 0.22,
) -> Portfolio:
    """Create an institutional hedged equity portfolio."""

    portfolio = Portfolio(
        name="Hedged Equity Portfolio"
    )

    equity_lines = [
        (
            "SPY",
            520.0,
            160
        ),
        (
            "IWM",
            210.0,
            120
        ),
        (
            "EFA",
            82.0,
            180
        ),
    ]

    for ticker, spot, quantity in equity_lines:
        portfolio.add_stock(
            spot=spot,
            quantity=quantity,
            name=f"{ticker} equity allocation",
            underlying=ticker,
        )

    portfolio.add_option(
        contract=create_put_option(
            spot=520.0,
            strike=485.0,
            maturity=0.50,
            rate=rate,
            volatility=volatility + 0.03,
        ),
        quantity=3,
        multiplier=100,
        name="SPY index hedge puts",
        underlying="SPY",
    )

    return portfolio


def create_volatility_book(
    rate: float = 0.045,
) -> Portfolio:
    """Create a volatility-sensitive options book."""

    portfolio = Portfolio(
        name="Volatility Book"
    )

    for ticker, spot, vol in [
        (
            "SPY",
            520.0,
            0.24
        ),
        (
            "QQQ",
            455.0,
            0.30
        ),
    ]:
        portfolio.add_option(
            contract=create_call_option(
                spot=spot,
                strike=spot,
                maturity=0.25,
                rate=rate,
                volatility=vol,
            ),
            quantity=4,
            multiplier=100,
            name=f"{ticker} ATM calls long vega",
            underlying=ticker,
        )
        portfolio.add_option(
            contract=create_put_option(
                spot=spot,
                strike=spot,
                maturity=0.25,
                rate=rate,
                volatility=vol,
            ),
            quantity=4,
            multiplier=100,
            name=f"{ticker} ATM puts long vega",
            underlying=ticker,
        )

    return portfolio


def create_crisis_sensitive_portfolio(
    rate: float = 0.045,
    volatility: float = 0.24,
) -> Portfolio:
    """Create a portfolio intentionally vulnerable to crisis shocks."""

    portfolio = Portfolio(
        name="Crisis-sensitive Portfolio"
    )

    for ticker, spot in [
        (
            "SPY",
            520.0
        ),
        (
            "QQQ",
            455.0
        ),
        (
            "KRE",
            52.0
        ),
    ]:
        portfolio.add_stock(
            spot=spot,
            quantity=200,
            name=f"{ticker} long risk",
            underlying=ticker,
        )
        portfolio.add_option(
            contract=create_put_option(
                spot=spot,
                strike=spot * 0.90,
                maturity=0.20,
                rate=rate,
                volatility=volatility,
            ),
            quantity=-2,
            multiplier=100,
            name=f"{ticker} short downside puts",
            underlying=ticker,
        )

    return portfolio


def get_demo_portfolio_names() -> list[str]:
    """Renvoie la liste des portefeuilles de démonstration disponibles."""

    return [
        "Long Straddle",
        "Short Straddle",
        "Bull Call Spread",
        "Bear Put Spread",
        "Protective Put",
        "Covered Call",
        "Tech Options Book",
        "Hedged Equity Portfolio",
        "Volatility Book",
        "Crisis-sensitive Portfolio",
    ]


def create_demo_portfolio(
    name: str,
    spot: float = 500.0,
    maturity: float = 0.25,
    rate: float = 0.05,
    volatility: float = 0.20,
) -> Portfolio:
    """Crée un portefeuille de démonstration à partir de son nom."""

    if name == "Long Straddle":
        return create_long_straddle(
            spot=spot,
            maturity=maturity,
            rate=rate,
            volatility=volatility,
        )

    if name == "Short Straddle":
        return create_short_straddle(
            spot=spot,
            maturity=maturity,
            rate=rate,
            volatility=volatility,
        )

    if name == "Bull Call Spread":
        return create_bull_call_spread(
            spot=spot,
            lower_strike=spot,
            upper_strike=spot * 1.08,
            maturity=maturity,
            rate=rate,
            volatility=volatility,
        )

    if name == "Bear Put Spread":
        return create_bear_put_spread(
            spot=spot,
            lower_strike=spot * 0.92,
            upper_strike=spot,
            maturity=maturity,
            rate=rate,
            volatility=volatility,
        )

    if name == "Protective Put":
        return create_protective_put(
            spot=spot,
            put_strike=spot * 0.94,
            maturity=maturity,
            rate=rate,
            volatility=volatility,
        )

    if name == "Covered Call":
        return create_covered_call(
            spot=spot,
            call_strike=spot * 1.08,
            maturity=maturity,
            rate=rate,
            volatility=volatility,
        )

    if name == "Tech Options Book":
        return create_tech_options_book(
            rate=rate,
            volatility=volatility,
        )

    if name == "Hedged Equity Portfolio":
        return create_hedged_equity_portfolio(
            rate=rate,
            volatility=volatility,
        )

    if name == "Volatility Book":
        return create_volatility_book(
            rate=rate,
        )

    if name == "Crisis-sensitive Portfolio":
        return create_crisis_sensitive_portfolio(
            rate=rate,
            volatility=volatility,
        )

    raise ValueError(
        f"Portefeuille de démonstration inconnu : {name}"
    )


def portfolio_to_dataframe(
    portfolio: Portfolio
):
    """Convertit un portefeuille ARIA en DataFrame compatible Streamlit."""

    import pandas as pd

    rows = []

    for position in portfolio.positions:
        if hasattr(
            position,
            "contract",
        ):
            rows.append(
                {
                    "Instrument": "Option",
                    "Sous-jacent": position.underlying,
                    "Nom": position.name,
                    "Type option": position.contract.option_type,
                    "QuantitÃ©": position.quantity,
                    "Multiplicateur": position.multiplier,
                    "Spot": position.contract.S,
                    "Volatilite": position.contract.sigma,
                    "Strike": position.contract.K,
                    "MaturitÃ©": position.contract.T,
                }
            )

        else:
            rows.append(
                {
                    "Instrument": "Action",
                    "Sous-jacent": position.underlying,
                    "Nom": position.name,
                    "Type option": "call",
                    "QuantitÃ©": position.quantity,
                    "Multiplicateur": 1,
                    "Spot": position.spot,
                    "Volatilite": 0.20,
                    "Strike": position.spot,
                    "MaturitÃ©": 0.25,
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "Instrument",
            "Sous-jacent",
            "Nom",
            "Type option",
            "QuantitÃ©",
            "Multiplicateur",
            "Spot",
            "Volatilite",
            "Strike",
            "MaturitÃ©",
        ],
    )


if __name__ == "__main__":
    for demo_name in get_demo_portfolio_names():
        demo_portfolio = create_demo_portfolio(
            name=demo_name
        )

        print()
        print("=" * 70)
        print(demo_name)
        print("=" * 70)
        print(f"Valeur : {demo_portfolio.total_market_value():,.2f}")
        print(demo_portfolio.total_greeks())
