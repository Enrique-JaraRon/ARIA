
"""
ARIA - Gestion d'un portefeuille d'options
"""

from dataclasses import dataclass, field

from portfolio_engine.pricing_BS import OptionContract, bs_greeks, bs_price


@dataclass
class OptionPosition:
    """Représente une position sur une option."""

    contract: OptionContract
    quantity: int
    multiplier: int = 1
    name: str = ""
    underlying: str = "SPY"

    def __post_init__(self) -> None:
        """Vérifie que la position est valide."""

        if self.quantity == 0:
            raise ValueError(
                "La quantité ne peut pas être égale à zéro."
            )

        if self.multiplier <= 0:
            raise ValueError(
                "Le multiplicateur doit être strictement positif."
            )

    def market_value(self) -> float:
        """
        Calcule la valeur totale de la position.

        Valeur =
        prix d'une option × quantité × multiplicateur.
        """

        option_price = bs_price(
            self.contract
        )

        return (
            option_price
            * self.quantity
            * self.multiplier
        )

    def total_greeks(self) -> dict[str, float]:
        """
        Calcule les Greeks de toute la position.

        Chaque Greek est multiplié par la quantité
        et par le multiplicateur du contrat.
        """

        greeks = bs_greeks(
            self.contract
        )

        position_size = (
            self.quantity
            * self.multiplier
        )

        return {
            "delta": greeks["delta"] * position_size,
            "gamma": greeks["gamma"] * position_size,
            "theta": greeks["theta"] * position_size,
            "vega": greeks["vega"] * position_size,
            "rho": greeks["rho"] * position_size,
            "vanna": greeks["vanna"] * position_size,
            "volga": greeks["volga"] * position_size,
        }


@dataclass
class StockPosition:
    """Représente une position sur le sous-jacent."""

    spot: float
    quantity: int
    name: str = "Sous-jacent"
    underlying: str = "SPY"

    def __post_init__(self) -> None:
        """Vérifie que la position est valide."""

        if self.spot <= 0:
            raise ValueError(
                "Le prix du sous-jacent doit être strictement positif."
            )

        if self.quantity == 0:
            raise ValueError(
                "La quantité ne peut pas être égale à zéro."
            )

    def market_value(self) -> float:
        """Calcule la valeur totale de la position en actions."""

        return (
            self.spot
            * self.quantity
        )

    def total_greeks(self) -> dict[str, float]:
        """
        Une action a un delta égal à 1.

        Les autres Greeks sont considérés comme nuls
        dans ce modèle simplifié.
        """

        return {
            "delta": float(self.quantity),
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0,
            "vanna": 0.0,
            "volga": 0.0,
        }


Position = OptionPosition | StockPosition


@dataclass
class Portfolio:
    """Regroupe plusieurs positions financières."""

    name: str = "Portefeuille ARIA"
    positions: list[Position] = field(
        default_factory=list
    )

    def add_option(
        self,
        contract: OptionContract,
        quantity: int,
        name: str = "",
        multiplier: int = 1,
        underlying: str = "SPY"
    ) -> None:
        """
        Ajoute une position sur option.

        Le multiplicateur vaut 1 par défaut
        pour conserver la compatibilité avec l'ancien code.
        """

        position = OptionPosition(
            contract=contract,
            quantity=quantity,
            multiplier=multiplier,
            name=name,
            underlying=underlying
        )

        self.positions.append(
            position
        )

    def add_stock(
        self,
        spot: float,
        quantity: int,
        name: str = "Sous-jacent",
        underlying: str = "SPY"
    ) -> None:
        """Ajoute une position sur le sous-jacent."""

        position = StockPosition(
            spot=spot,
            quantity=quantity,
            name=name,
            underlying=underlying
        )

        self.positions.append(
            position
        )

    def remove_position(
        self,
        index: int
    ) -> None:
        """Supprime une position grâce à son numéro."""

        if index < 0 or index >= len(self.positions):
            raise IndexError(
                "Le numéro de position n'existe pas."
            )

        self.positions.pop(
            index
        )

    def total_market_value(self) -> float:
        """Calcule la valeur totale du portefeuille."""

        return sum(
            position.market_value()
            for position in self.positions
        )

    def total_greeks(self) -> dict[str, float]:
        """Additionne les Greeks de toutes les positions."""

        totals = {
            "delta": 0.0,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0,
            "vanna": 0.0,
            "volga": 0.0,
        }

        for position in self.positions:
            position_greeks = (
                position.total_greeks()
            )

            for greek in totals:
                totals[greek] += (
                    position_greeks[greek]
                )

        return totals

    def underlyings(self) -> list[str]:
        """Return all underlyings represented in the portfolio."""

        return sorted(
            {
                position.underlying
                for position in self.positions
            }
        )

    def exposure_by_underlying(self) -> dict[str, dict[str, float]]:
        """Aggregate market value and Greeks by underlying."""

        exposures: dict[str, dict[str, float]] = {}

        for position in self.positions:
            underlying = position.underlying

            if underlying not in exposures:
                exposures[underlying] = {
                    "market_value": 0.0,
                    "abs_market_value": 0.0,
                    "delta": 0.0,
                    "gamma": 0.0,
                    "theta": 0.0,
                    "vega": 0.0,
                    "rho": 0.0,
                    "vanna": 0.0,
                    "volga": 0.0,
                }

            market_value = position.market_value()
            exposures[underlying]["market_value"] += market_value
            exposures[underlying]["abs_market_value"] += abs(
                market_value
            )

            for greek, value in position.total_greeks().items():
                exposures[underlying][greek] += value

        return exposures

    def summary(self) -> None:
        """Affiche un résumé lisible du portefeuille."""

        print(
            f"\n{self.name}"
        )

        print(
            f"Nombre de positions : "
            f"{len(self.positions)}"
        )

        if not self.positions:
            print(
                "Le portefeuille est vide."
            )
            return

        print(
            "\nPositions"
        )

        for index, position in enumerate(
            self.positions,
            start=1
        ):
            position_name = (
                position.name
                if position.name
                else f"Position {index}"
            )

            if isinstance(
                position,
                OptionPosition
            ):
                contract = position.contract

                print(
                    f"{index}. {position_name} | "
                    f"{position.quantity:+d} contrat(s) "
                    f"{contract.option_type.upper()} | "
                    f"Multiplicateur {position.multiplier} | "
                    f"Strike {contract.K} | "
                    f"Maturité {contract.T} an | "
                    f"Valeur "
                    f"{position.market_value():.2f}"
                )

            else:
                print(
                    f"{index}. {position_name} | "
                    f"{position.quantity:+d} actions | "
                    f"Spot {position.spot} | "
                    f"Valeur "
                    f"{position.market_value():.2f}"
                )

        totals = self.total_greeks()

        print(
            "\nValeur totale"
        )

        print(
            f"{self.total_market_value():.2f}"
        )

        print(
            "\nGreeks du portefeuille"
        )

        print(
            f"Delta : {totals['delta']:.6f}"
        )

        print(
            f"Gamma : {totals['gamma']:.6f}"
        )

        print(
            f"Theta : {totals['theta']:.6f}"
        )

        print(
            f"Vega : {totals['vega']:.6f}"
        )

        print(
            f"Rho : {totals['rho']:.6f}"
        )

        print(
            f"Vanna : {totals['vanna']:.6f}"
        )

        print(
            f"Volga : {totals['volga']:.6f}"
        )


if __name__ == "__main__":
    portfolio = Portfolio(
        name="Portefeuille de démonstration"
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
        sigma=0.25,
        option_type="put",
        q=0.0
    )

    portfolio.add_option(
        contract=call,
        quantity=10,
        multiplier=100,
        name="Calls ATM achetés"
    )

    portfolio.add_option(
        contract=put,
        quantity=-5,
        multiplier=100,
        name="Puts vendus"
    )

    portfolio.add_stock(
        spot=500,
        quantity=-300,
        name="Couverture en SPY"
    )

    portfolio.summary()

