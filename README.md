# ARIA - Adaptive Risk Intelligence Agent

ARIA est une application Python / Streamlit d'analyse de portefeuille financier.
Elle aide a composer un portefeuille client, charger une demonstration, generer
une allocation avec l'IA, valider les donnees, puis lancer une analyse de risque
complete.

Projet developpe par **Enrique Jara Ron**.

> ARIA est un prototype pedagogique et professionnel. Les resultats ne
> constituent pas un conseil en investissement. Les performances passees,
> simulees ou estimees ne prejugent pas des performances futures.

## Experience utilisateur

La page principale est centree sur le portefeuille client. Le parcours visible
reste volontairement simple, avec deux ou trois choix par categorie :

1. Profil investisseur : preservation, equilibre ou croissance.
2. Horizon : court, moyen ou long terme.
3. Objectif : croissance, preservation du capital ou couverture.
4. Risque accepte : prudent, equilibre ou dynamique.
5. Types d'actifs : ETF, actions ou options.
6. Generation, composition ou chargement du portefeuille.
7. Validation automatique.
8. Analyse ARIA.

Les reglages avances de marche, limites, scenarios, VaR et probabilites sont
replies dans la barre laterale pour garder l'interface claire.

## Fonctionnalites principales

- Portefeuille client editable au centre de l'application.
- Chargement de portefeuilles de demonstration professionnels.
- Generateur IA en deux modes : guide et libre.
- Validation automatique : poids a 100 %, tickers non vides, doublons,
  classes d'actifs, secteurs, devises, prix, valeurs et coherence risque/horizon.
- Tableau adaptatif : classique pour actions/ETF, enrichi automatiquement pour
  les portefeuilles avec options.
- Gestion des options : sous-jacent, call/put, position long/short, spot,
  strike, maturite, prime, volatilite implicite, taille de contrat, quantite,
  notionnel, delta et objectif.
- Pricing Black-Scholes et Greeks agreges.
- Stress tests standards et scenarios historiques stylises.
- VaR, Expected Shortfall et simulation probabiliste.
- Score de risque dynamique : Greeks, VaR, stress tests, concentration,
  diversification, options, exposition vendeuse, levier et notionnel.
- Alertes quantitatives et recommandations.
- Rapport executif PDF en francais et en anglais.
- Compatible local `.env` et Streamlit Cloud `st.secrets`.

## Captures d'ecran

### Portefeuille client

![Portefeuille client](screenshots/dashboard.png)

### Portefeuille IA

![Portefeuille IA](screenshots/portfolio_analysis.png)

### Portefeuilles de demonstration

![Portefeuilles de demonstration](screenshots/model_portfolios.png)

### Analyse ARIA

![Analyse ARIA](screenshots/rebalancing.png)

### Stress tests

![Stress tests](screenshots/stress_testing.png)

### Analyse probabiliste

![Analyse probabiliste](screenshots/probabilistic_risk.png)

### Rapport de risque

![Rapport de risque](screenshots/risk_report.png)

## Generation IA

Le mode guide utilise des criteres proches d'une interface bancaire :

- objectif ;
- horizon ;
- profil de risque ;
- montant simule ;
- devise ;
- zone geographique ;
- secteurs souhaites ou exclus ;
- ETF, actions ou options ;
- besoin de liquidite ;
- drawdown tolere ;
- concentration maximale par ligne et par secteur ;
- contrainte ESG ;
- entreprises ou ETF a inclure ou exclure.

Le mode libre permet d'ecrire une demande precise, par exemple :

```text
Construire un portefeuille mondial avec ETF, actions de qualite et une
protection par puts SPY a trois mois.
```

Si une cle `OPENAI_API_KEY` et un modele `ARIA_LLM_MODEL` sont configures, ARIA
demande un portefeuille JSON structure au LLM. Sinon, un generateur local de
secours produit une allocation coherente pour que la demonstration fonctionne
sans API.

## Gestion des options

Quand l'utilisateur demande des options, ARIA genere de vraies lignes
optionnelles au lieu de les convertir en actions. Si les donnees exactes ne sont
pas disponibles, l'application affiche une simulation avec hypotheses visibles :
spot, strike, maturite, prime, volatilite implicite, contract size, quantite,
notionnel et objectif de l'option.

Une position vendeuse ou une option vendue est autorisee. Elle apparait comme un
avertissement de risque, pas comme une erreur bloquante.

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

Ou sur le port utilise en local pendant le developpement :

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

Sans cle API, ARIA continue de fonctionner avec le moteur local et les analyses
quantitatives.

## Deploiement Streamlit Cloud

Parametres recommandes :

- Repository : `Enrique-JaraRon/ARIA`
- Branch : `main`
- Main file path : `streamlit_app.py`

Dans **Secrets**, ajouter si besoin :

```toml
OPENAI_API_KEY = "sk-..."
ARIA_LLM_MODEL = "gpt-5-mini"
```

Ne jamais envoyer `.env` sur GitHub. Le fichier est ignore par `.gitignore`.

## Controle qualite

```powershell
.\.venv\Scripts\python.exe quality_check.py
```

Commandes separees :

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe project_diagnostics.py
```

## Structure

- `streamlit_app.py` : application Streamlit.
- `portfolio_ai_generator.py` : generation IA guidee/libre et portefeuille de secours.
- `portfolio_analytics.py` : modeles, validation et diagnostic portefeuille.
- `risk_score.py` : score de risque ARIA.
- `scenario_analysis.py` : stress tests.
- `report_generator.py` : rapports PDF.
- `screenshots/` : captures utiles pour GitHub.
