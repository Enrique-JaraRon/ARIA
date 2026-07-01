# ARIA - Adaptive Risk Intelligence Agent

ARIA est une application Python / Streamlit d'analyse de portefeuille financier.
Elle permet de construire un portefeuille client, de charger des portefeuilles de
démonstration, de générer un portefeuille avec l'IA, puis de lancer une analyse
de risque complète : expositions, Greeks, stress tests, VaR, score de risque,
alertes, recommandations et rapport PDF.

Projet développé par **Enrique Jara Ron**.

> ARIA est un prototype pédagogique et professionnel. Les résultats ne
> constituent pas un conseil en investissement. Les performances passées,
> simulées ou estimées ne préjugent pas des performances futures.

## Fonctionnalités principales

- Page principale centrée sur un parcours guidé portefeuille client.
- Parcours simple : profil investisseur, horizon, risque, thèmes souhaités,
  création ou chargement du portefeuille, validation, analyse ARIA.
- Import, modification, sauvegarde et chargement CSV.
- Portefeuilles de démonstration professionnels prêts à analyser.
- Générateur de portefeuille assisté par IA avec validation automatique.
- Respect des poids : fusion des doublons, poids total à 100 %, valeurs et
  quantités recalculées proprement.
- Support actions, ETF, obligations représentées par ETF, matières premières et
  options.
- Pricing Black-Scholes pour options européennes.
- Agrégation des Greeks : Delta, Gamma, Theta, Vega, Rho, Vanna, Volga.
- Stress tests standards et scénarios historiques stylisés.
- VaR / Expected Shortfall et simulation probabiliste.
- Score de risque ARIA différencié entre risque faible, modéré, élevé et très
  élevé.
- Alertes quantitatives : concentration, scénarios, Greeks, drawdown,
  corrélation.
- Commentaire LLM optionnel.
- Rapport exécutif Markdown et PDF en français / anglais.
- Compatible local `.env` et Streamlit Cloud `st.secrets`.

## Captures d'écran

### Portefeuille client

![Portefeuille client](screenshots/dashboard.png)

### Portefeuille IA

![Portefeuille IA](screenshots/portfolio_analysis.png)

### Portefeuilles de démonstration

![Portefeuilles de démonstration](screenshots/model_portfolios.png)

### Analyse ARIA

![Analyse ARIA](screenshots/rebalancing.png)

### Stress tests

![Stress tests](screenshots/stress_testing.png)

### Analyse probabiliste

![Analyse probabiliste](screenshots/probabilistic_risk.png)

### Rapport de risque

![Rapport de risque](screenshots/risk_report.png)

## Portefeuilles de démonstration

ARIA inclut des stratégies options et des allocations actions / ETF :

- Long Straddle
- Short Straddle
- Bull Call Spread
- Bear Put Spread
- Protective Put
- Covered Call
- Tech Options Book
- Hedged Equity Portfolio
- Volatility Book
- Crisis-sensitive Portfolio
- Conservative Balanced Portfolio
- Moderate Growth Portfolio
- Global Diversified Portfolio
- Tech Growth Portfolio
- Defensive Dividend Portfolio
- Low Volatility Portfolio
- Crisis-Resilient Portfolio
- ESG Sustainable Portfolio
- AI & Semiconductors Portfolio
- European Quality Portfolio
- US Blue Chips Portfolio
- Global ETF Core Portfolio
- Inflation Protection Portfolio
- Long-Term Compounders Portfolio

Chaque portefeuille modèle contient un niveau de risque, un profil investisseur,
une logique d'allocation, des poids, des prix indicatifs et des secteurs. Les
poids sont conservés et normalisés à 100 %.

## Générateur de portefeuille IA

L'onglet **Créer avec l'IA** permet de définir :

- horizon d'investissement ;
- niveau de risque ;
- instruments préférés ;
- style du portefeuille ;
- zone géographique ;
- secteurs à privilégier ou éviter ;
- entreprises / ETF à inclure ou exclure ;
- montant simulé.

Si `OPENAI_API_KEY` et `ARIA_LLM_MODEL` sont configurés, ARIA demande au LLM un
portefeuille JSON structuré. Sinon, un portefeuille local de secours est généré
pour que la démonstration fonctionne sans API.

Avant chargement dans ARIA, le portefeuille est validé :

- tickers non vides ;
- poids numériques ;
- aucune pondération négative ;
- fusion des tickers en double ;
- somme des poids égale à 100 % ;
- limitation des concentrations absurdes ;
- champs nécessaires à l'analyse remplis automatiquement.

## Installation locale

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Lancer l'application

```powershell
streamlit run streamlit_app.py
```

Puis ouvrir l'URL affichée par Streamlit, en général :

```text
http://localhost:8501
```

Dans ce projet, le port `8502` est souvent utilisé localement :

```powershell
streamlit run streamlit_app.py --server.port 8502
```

## Variables d'environnement

En local, copier `.env.example` vers `.env` :

```powershell
Copy-Item .env.example .env
```

Exemple :

```text
OPENAI_API_KEY=sk-...
ARIA_LLM_MODEL=gpt-5-mini
```

Le commentaire LLM reste optionnel. Sans clé API, l'application continue de
fonctionner avec les calculs ARIA et les commentaires locaux.

## Utilisation rapide

1. Choisir le profil investisseur, l'horizon, le niveau de risque et les thèmes.
2. Cliquer sur **Créer un portefeuille adapté**, charger une démonstration ou
   générer un portefeuille avec l'IA.
3. Ajuster les actifs, poids, valeurs ou commentaires dans le tableau.
4. Vérifier que la validation indique **Prêt** et que les poids totalisent 100 %.
5. Cliquer sur **Lancer l'analyse ARIA**.

Les paramètres avancés de marché, limites, stress tests, VaR et simulation
probabiliste sont repliés dans la barre latérale afin de garder l'interface
principale claire.

## Déploiement Streamlit Cloud

Paramètres recommandés :

- Repository : `Enrique-JaraRon/ARIA`
- Branch : `main`
- Main file path : `streamlit_app.py`

Dans **Secrets**, ajouter si besoin :

```toml
OPENAI_API_KEY = "sk-..."
ARIA_LLM_MODEL = "gpt-5-mini"
```

Ne jamais envoyer `.env` sur GitHub. Le fichier est ignoré par `.gitignore`.

## Contrôle qualité

Lancer tous les contrôles :

```powershell
.\.venv\Scripts\python.exe quality_check.py
```

Ou séparément :

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe project_diagnostics.py
```

## Structure du projet

```text
ARIA/
|-- streamlit_app.py
|-- portfolio.py
|-- portfolio_analytics.py
|-- portfolio_ai_generator.py
|-- pricing_BS.py
|-- scenario_analysis.py
|-- var_analysis.py
|-- probabilistic_risk.py
|-- risk_score.py
|-- report_generator.py
|-- llm_explainer.py
|-- market_data.py
|-- app_config.py
|-- demo_portfolios.py
|-- quality_check.py
|-- screenshots/
|-- data/
`-- test_*.py
```

## Limites

- Les prix de certains portefeuilles modèles sont indicatifs lorsque la donnée
  de marché n'est pas disponible.
- Les stress tests sont des scénarios stylisés, pas des prévisions.
- Le score ARIA est une aide à la lecture du risque, pas une mesure réglementaire.
- Le LLM commente les résultats fournis par ARIA mais ne doit pas inventer de
  chiffres ni promettre de rendement.
- Toute recommandation doit être comprise comme une piste de réduction du risque,
  pas comme une certitude de performance.
