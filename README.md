# ARIA - Adaptive Risk Intelligence Agent

ARIA est une application Streamlit d'analyse de portefeuille financier. Elle est
concue pour une demonstration claire en entretien : construire ou charger un
portefeuille, verifier sa coherence, lancer une analyse de risque, puis exporter
un rapport.

Projet developpe par **Enrique Jara Ron**.

> ARIA est un prototype educatif et professionnel. Les resultats ne constituent
> pas un conseil en investissement. Les performances passees, simulees ou
> estimees ne prejugent pas des performances futures.

## Ce que fait l'application

- Edition d'un portefeuille client dans un tableau simple.
- Chargement de quelques portefeuilles de demonstration pertinents.
- Generation IA simplifiee avec horizon, risque, objectif, style et instruments.
- Validation automatique des poids, tickers, valeurs, doublons et champs options.
- Analyse ARIA : score de risque, stress tests, risque probabiliste, alertes et
  rapport PDF.
- Gestion des options quand elles sont utiles : call/put, long/short, strike,
  maturite, prime, volatilite implicite et taille de contrat.
- Fonctionnement local avec `.env` et Streamlit Cloud avec `st.secrets`.

## Portefeuilles de demonstration conserves

La liste est volontairement courte pour garder une interface professionnelle :

- `Conservative Balanced Portfolio` : portefeuille defensif.
- `Global Diversified Portfolio` : allocation mondiale diversifiee.
- `Tech Growth Portfolio` : portefeuille croissance / technologie.
- `Covered Call` : exemple simple avec options.

## Captures d'ecran

### Portefeuille client

![Portefeuille client](screenshots/dashboard.png)

### Generation IA

![Generation IA](screenshots/portfolio_analysis.png)

### Stress tests

![Stress tests](screenshots/stress_testing.png)

### Rapport de risque

![Rapport de risque](screenshots/risk_report.png)

## Generation IA

La generation IA a ete simplifiee pour rester stable :

- horizon : court, moyen ou long terme ;
- risque : prudent, equilibre ou dynamique ;
- objectif : croissance, preservation du capital ou couverture ;
- instruments : ETF, actions ou options ;
- style : equilibre, croissance ou defensif ;
- zone geographique : monde, Etats-Unis ou Europe.

Si le LLM n'est pas disponible ou ne renvoie pas un JSON exploitable, ARIA charge
un portefeuille local coherent. L'utilisateur ne voit pas de message technique
brut.

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

Ou sur le port utilise en local :

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

Sans cle API, l'application reste utilisable avec le generateur local et les
analyses quantitatives.

## Streamlit Cloud

Parametres recommandes :

- Repository : `Enrique-JaraRon/ARIA`
- Branch : `main`
- Main file path : `streamlit_app.py`

Secrets optionnels :

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
