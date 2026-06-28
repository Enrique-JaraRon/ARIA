"""
ARIA - Diagnostic du projet
"""

from pathlib import Path
import importlib
import os

from dotenv import load_dotenv


REQUIRED_FILES = [
    "streamlit_app.py",
    "pricing_BS.py",
    "portfolio.py",
    "scenario_analysis.py",
    "risk_surface.py",
    "pnl_profile.py",
    "greeks_profile.py",
    "var_analysis.py",
    "risk_score.py",
    "hedging_analysis.py",
    "anomaly_detector.py",
    "risk_history.py",
    "history_analytics.py",
    "market_data.py",
    "report_generator.py",
    "llm_explainer.py",
    "aria_workflow.py",
    "requirements.txt",
    "README.md",
    ".gitignore"
]


REQUIRED_MODULES = [
    "streamlit",
    "pandas",
    "numpy",
    "scipy",
    "altair",
    "openai",
    "dotenv",
    "yfinance",
    "pytest"
]


PROJECT_MODULES = [
    "pricing_BS",
    "portfolio",
    "scenario_analysis",
    "risk_surface",
    "pnl_profile",
    "greeks_profile",
    "var_analysis",
    "risk_score",
    "hedging_analysis",
    "anomaly_detector",
    "risk_history",
    "history_analytics",
    "market_data",
    "report_generator",
    "llm_explainer",
    "aria_workflow"
]


def check_required_files(
    project_path: Path
) -> list[str]:
    """Vérifie que les fichiers importants existent."""

    messages = []

    for file_name in REQUIRED_FILES:

        file_path = project_path / file_name

        if file_path.exists():
            messages.append(
                f"OK fichier trouvé : {file_name}"
            )

        else:
            messages.append(
                f"MANQUANT fichier absent : {file_name}"
            )

    return messages


def check_data_folder(
    project_path: Path
) -> list[str]:
    """Vérifie que le dossier data existe."""

    messages = []

    data_path = project_path / "data"

    if data_path.exists() and data_path.is_dir():
        messages.append(
            "OK dossier data trouvé"
        )

    else:
        messages.append(
            "MANQUANT dossier data absent"
        )

    history_file = data_path / "risk_history.csv"

    if history_file.exists():
        messages.append(
            "OK historique trouvé : data/risk_history.csv"
        )

    else:
        messages.append(
            "INFO aucun historique trouvé pour le moment"
        )

    return messages


def check_python_dependencies() -> list[str]:
    """Vérifie que les librairies externes sont installées."""

    messages = []

    for module_name in REQUIRED_MODULES:

        try:
            importlib.import_module(
                module_name
            )

            messages.append(
                f"OK dépendance installée : {module_name}"
            )

        except ImportError:
            messages.append(
                f"MANQUANT dépendance absente : {module_name}"
            )

    return messages


def check_project_modules() -> list[str]:
    """Vérifie que les modules internes ARIA sont importables."""

    messages = []

    for module_name in PROJECT_MODULES:

        try:
            importlib.import_module(
                module_name
            )

            messages.append(
                f"OK module ARIA importable : {module_name}"
            )

        except Exception as error:
            messages.append(
                f"ERREUR module ARIA : {module_name} -> {error}"
            )

    return messages


def check_environment_variables(
    project_path: Path
) -> list[str]:
    """Vérifie la configuration du fichier .env."""

    messages = []

    env_path = project_path / ".env"

    if env_path.exists():
        messages.append(
            "OK fichier .env trouvé"
        )

    else:
        messages.append(
            "INFO fichier .env absent"
        )

    load_dotenv(
        env_path
    )

    openai_key = os.getenv(
        "OPENAI_API_KEY"
    )

    llm_model = os.getenv(
        "ARIA_LLM_MODEL"
    )

    if openai_key:
        messages.append(
            "OK variable OPENAI_API_KEY configurée"
        )

    else:
        messages.append(
            "INFO variable OPENAI_API_KEY non configurée"
        )

    if llm_model:
        messages.append(
            f"OK variable ARIA_LLM_MODEL configurée : {llm_model}"
        )

    else:
        messages.append(
            "INFO variable ARIA_LLM_MODEL non configurée"
        )

    return messages


def print_section(
    title: str,
    messages: list[str]
) -> None:
    """Affiche une section de diagnostic."""

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    for message in messages:
        print(message)


def run_diagnostics() -> None:
    """Lance tous les diagnostics du projet."""

    project_path = Path.cwd()

    print()
    print("Diagnostic ARIA")
    print(f"Dossier analysé : {project_path}")

    print_section(
        "Fichiers du projet",
        check_required_files(
            project_path
        )
    )

    print_section(
        "Dossier data",
        check_data_folder(
            project_path
        )
    )

    print_section(
        "Dépendances Python",
        check_python_dependencies()
    )

    print_section(
        "Modules ARIA",
        check_project_modules()
    )

    print_section(
        "Variables d'environnement",
        check_environment_variables(
            project_path
        )
    )

    print()
    print("=" * 70)
    print("Diagnostic terminé")
    print("=" * 70)


if __name__ == "__main__":
    run_diagnostics()