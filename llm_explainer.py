"""
ARIA - Explication des alertes avec un LLM
"""

from openai import OpenAI

from anomaly_detector import Alert, RiskSnapshot
from app_config import get_runtime_setting


class LLMExplainer:
    """Transforme les alertes quantitatives en explication lisible."""

    def __init__(self, model: str) -> None:
        api_key = get_runtime_setting("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "La variable OPENAI_API_KEY n'est pas définie."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def build_prompt(
        self,
        snapshot: RiskSnapshot,
        alerts: list[Alert],
        risk_score_result=None,
        scenario_results=None,
        var_result=None,
        probabilistic_result=None,
        hedge_result=None,
        market_snapshot=None,
        language: str = "fr"
    ) -> str:
        """Prépare les informations envoyées au LLM."""

        alert_lines = []

        for alert in alerts:
            line = (
                f"- {alert.name} | "
                f"gravité : {alert.severity} | "
                f"valeur actuelle : {alert.current_value:.6f}"
            )

            if alert.reference_value is not None:
                line += (
                    f" | référence : "
                    f"{alert.reference_value:.6f}"
                )

            if alert.z_score is not None:
                line += f" | z-score : {alert.z_score:.2f}"

            alert_lines.append(line)

        if alert_lines:
            alerts_text = "\n".join(alert_lines)

        else:
            alerts_text = (
                "Aucune alerte quantitative n'a ete detectee par ARIA."
            )

        context_lines = []

        if risk_score_result is not None:
            context_lines.extend(
                [
                    f"- Risk Score : {risk_score_result.score}/100",
                    f"- Niveau de risque : {risk_score_result.label}",
                    (
                        "- Facteurs de risque principaux : "
                        + ", ".join(risk_score_result.main_drivers)
                    ),
                ]
            )

        if scenario_results:
            worst_scenario = min(
                scenario_results,
                key=lambda result: result.profit_and_loss
            )
            best_scenario = max(
                scenario_results,
                key=lambda result: result.profit_and_loss
            )
            context_lines.extend(
                [
                    (
                        f"- Pire stress test : {worst_scenario.name} | "
                        f"P&L : {worst_scenario.profit_and_loss:.2f}"
                    ),
                    (
                        f"- Meilleur stress test : {best_scenario.name} | "
                        f"P&L : {best_scenario.profit_and_loss:.2f}"
                    ),
                ]
            )

        if var_result is not None:
            context_lines.extend(
                [
                    f"- VaR : {var_result.var_amount:.2f}",
                    f"- Expected Shortfall : {var_result.expected_shortfall:.2f}",
                    f"- Pire perte simulée : {var_result.worst_loss:.2f}",
                ]
            )

        if probabilistic_result is not None:
            context_lines.extend(
                [
                    (
                        "- Analyse probabiliste Monte Carlo : "
                        f"{probabilistic_result.number_of_simulations} simulations, "
                        f"horizon {probabilistic_result.horizon_days} jours"
                    ),
                    (
                        "- Probabilite estimee de perte : "
                        f"{probabilistic_result.probability_of_loss:.2%}"
                    ),
                    (
                        "- Probabilite de perte > 5% : "
                        f"{probabilistic_result.probability_loss_gt_5:.2%}"
                    ),
                    (
                        "- Probabilite de perte > 10% : "
                        f"{probabilistic_result.probability_loss_gt_10:.2%}"
                    ),
                    (
                        "- Probabilite de perte > 20% : "
                        f"{probabilistic_result.probability_loss_gt_20:.2%}"
                    ),
                    (
                        "- Rendement moyen simule : "
                        f"{probabilistic_result.mean_return:.2%}"
                    ),
                    (
                        "- Volatilite simulee : "
                        f"{probabilistic_result.simulated_volatility:.2%}"
                    ),
                    f"- VaR 95% probabiliste : {probabilistic_result.var_95:.2%}",
                    (
                        "- Expected Shortfall 95% probabiliste : "
                        f"{probabilistic_result.expected_shortfall_95:.2%}"
                    ),
                    f"- VaR 99% probabiliste : {probabilistic_result.var_99:.2%}",
                    (
                        "- Expected Shortfall 99% probabiliste : "
                        f"{probabilistic_result.expected_shortfall_99:.2%}"
                    ),
                    (
                        "- Pire rendement simule : "
                        f"{probabilistic_result.worst_return:.2%}"
                    ),
                    (
                        "- Meilleur rendement simule : "
                        f"{probabilistic_result.best_return:.2%}"
                    ),
                    (
                        "- Principal moteur de risque probabiliste : "
                        f"{probabilistic_result.main_risk_driver}"
                    ),
                ]
            )

        if hedge_result is not None:
            context_lines.extend(
                [
                    f"- Delta actuel : {hedge_result.current_delta:.6f}",
                    f"- Quantité indicative de hedge : {hedge_result.hedge_quantity:.2f}",
                    f"- Delta après hedge : {hedge_result.hedged_delta:.6f}",
                ]
            )

        if market_snapshot is not None:
            context_lines.extend(
                [
                    f"- Source market data : {market_snapshot.source}",
                    f"- Dernier prix : {market_snapshot.last_price:.2f}",
                    f"- Rendement journalier : {market_snapshot.daily_return:.2%}",
                    (
                        "- Volatilité historique annualisée : "
                        f"{market_snapshot.annualized_volatility:.2%}"
                    ),
                ]
            )

        if context_lines:
            extended_context = "\n".join(
                context_lines
            )

        else:
            extended_context = (
                "Aucun contexte VaR, stress test, hedge ou market data "
                "supplementaire n'a ete fourni."
            )

        if language.lower() == "en":
            language_instruction = (
                "Output language: English only. Use clear professional English "
                "section titles. If an original field name is French, translate "
                "the explanation around it."
            )

        else:
            language_instruction = (
                "Langue de sortie : francais uniquement."
            )

        return f"""
Tu es l'assistant d'analyse des risques d'ARIA.

Tu reçois uniquement des résultats déjà calculés par un moteur quantitatif.
Tu ne dois pas inventer de données ni prétendre prédire le marché.
Tu ne dois pas donner de conseil financier personnalisé.
Tu dois rester prudent et rappeler que l'analyse dépend des hypothèses du modèle.
Tu dois expliquer clairement quelles actions peuvent être étudiées pour diminuer
le risque tout en préservant ou en améliorant le couple rendement / risque.
Ces actions doivent être formulées comme des pistes de risk management à valider,
pas comme des ordres d'achat ou de vente.

État actuel :
- Spot : {snapshot.spot}
- Volatilité implicite : {snapshot.implied_volatility:.2%}
- Valeur du portefeuille : {snapshot.portfolio_value:.2f}
- Delta : {snapshot.delta:.6f}
- Gamma : {snapshot.gamma:.6f}
- Theta : {snapshot.theta:.6f}
- Vega : {snapshot.vega:.6f}
- Rho : {snapshot.rho:.6f}

Alertes détectées :
{alerts_text}

Contexte de risque complémentaire :
{extended_context}

Réponds en français avec cette structure :

1. Résumé exécutif
2. Niveau de risque global
3. Principaux facteurs de risque
4. Lecture des Greeks
5. Lecture des stress tests si les données sont disponibles
6. Lecture VaR / Expected Shortfall si les données sont disponibles
7. Plan d'action pour réduire le risque et optimiser le rendement ajusté du risque
8. Couverture et arbitrages possibles à étudier
9. Points à surveiller
10. Limites du modèle

Si une information numérique n'est pas fournie, indique qu'elle n'est pas disponible.
Dans le plan d'action, sois concret :
- si une quantite de hedge est fournie, cite clairement une action indicative du type acheter/vendre environ cette quantite de sous-jacent pour reduire le delta ;
- si une exposition semble trop concentree, propose une action a etudier : reduire la taille, transformer une position optionnelle nue en spread, decaler un strike, modifier une maturite ou compenser une exposition grecque ;
- si le delta domine, explique comment une couverture delta ou une réduction directionnelle peut réduire le risque ;
- si le gamma domine, explique comment réduire la convexité instable ou ajuster les strikes / maturités ;
- si la vega domine, explique comment réduire ou rééquilibrer l'exposition volatilité ;
- si la VaR ou les stress tests dominent, explique comment réduire les pertes extrêmes ;
- explique toujours le compromis attendu entre réduction du risque, coût de couverture et potentiel de rendement.
Précise que les couvertures proposées doivent être vérifiées avant toute décision.
Ne recommande pas un achat ou une vente directionnelle speculative non justifiee par les chiffres fournis.
Termine par un avertissement clair : ces pistes sont une aide a la decision de gestion du risque, pas une certitude de performance ni un conseil financier personnalise, et elles doivent etre verifiees avant toute decision.

{language_instruction}
""".strip()

    def explain(
        self,
        snapshot: RiskSnapshot,
        alerts: list[Alert],
        risk_score_result=None,
        scenario_results=None,
        var_result=None,
        probabilistic_result=None,
        hedge_result=None,
        market_snapshot=None,
        language: str = "fr"
    ) -> str:
        """Envoie les alertes au LLM et récupère son explication."""

        prompt = self.build_prompt(
            snapshot=snapshot,
            alerts=alerts,
            risk_score_result=risk_score_result,
            scenario_results=scenario_results,
            var_result=var_result,
            probabilistic_result=probabilistic_result,
            hedge_result=hedge_result,
            market_snapshot=market_snapshot,
            language=language
        )

        response = self.client.responses.create(
            model=self.model,
            input=prompt
        )

        return response.output_text


if __name__ == "__main__":
    from datetime import datetime

    snapshot = RiskSnapshot(
        timestamp=datetime.now(),
        spot=465,
        implied_volatility=0.32,
        portfolio_value=850,
        delta=18.0,
        gamma=1.4,
        theta=-4.0,
        vega=30.0,
        rho=2.0
    )

    alerts = [
        Alert(
            name="Exposition delta élevée",
            severity="ÉLEVÉE",
            message=(
                "Le portefeuille est très sensible "
                "aux mouvements du sous-jacent."
            ),
            current_value=18.0,
            reference_value=10.0
        ),
        Alert(
            name="Variation importante de volatilité",
            severity="CRITIQUE",
            message=(
                "La volatilité implicite a fortement augmenté."
            ),
            current_value=0.12,
            reference_value=0.05,
            z_score=3.8
        )
    ]

    model = get_runtime_setting("ARIA_LLM_MODEL")

    if not model:
        raise ValueError(
            "La variable ARIA_LLM_MODEL n'est pas définie."
        )

    explainer = LLMExplainer(model=model)

    explanation = explainer.explain(
        snapshot=snapshot,
        alerts=alerts
    )

    print("Analyse ARIA\n")
    print(explanation)


