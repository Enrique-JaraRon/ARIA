"""
ARIA - Script de lancement de l'application Streamlit
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Lance l'application Streamlit ARIA."""

    project_path = Path(__file__).resolve().parent
    app_path = project_path / "streamlit_app.py"

    if not app_path.exists():
        print("ERREUR : streamlit_app.py est introuvable.")
        print(f"Dossier analysé : {project_path}")
        return 1

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
    ]

    print()
    print("=" * 80)
    print("Lancement de ARIA")
    print("=" * 80)
    print("Commande :")
    print(" ".join(command))
    print()

    completed_process = subprocess.run(
        command,
        check=False,
    )

    return completed_process.returncode


if __name__ == "__main__":
    raise SystemExit(
        main()
    )