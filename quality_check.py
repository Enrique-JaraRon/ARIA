"""
ARIA - Contrôle qualité complet du projet

Ce script lance :
1. Ruff pour vérifier le style du code
2. Pytest pour lancer les tests
3. Le diagnostic projet ARIA
"""

import subprocess
import sys
from dataclasses import dataclass


@dataclass
class CheckResult:
    """Résultat d'un contrôle qualité."""

    name: str
    return_code: int


def run_command(
    name: str,
    command: list[str]
) -> CheckResult:
    """Lance une commande et affiche le résultat."""

    print()
    print("=" * 80)
    print(f"Lancement : {name}")
    print("=" * 80)
    print("Commande :")
    print(" ".join(command))
    print()

    completed_process = subprocess.run(
        command,
        check=False
    )

    if completed_process.returncode == 0:
        print()
        print(f"OK : {name}")

    else:
        print()
        print(f"ERREUR : {name}")

    return CheckResult(
        name=name,
        return_code=completed_process.returncode
    )


def print_final_summary(
    results: list[CheckResult]
) -> None:
    """Affiche le résumé final."""

    print()
    print("=" * 80)
    print("Résumé du contrôle qualité ARIA")
    print("=" * 80)

    for result in results:
        status = (
            "OK"
            if result.return_code == 0
            else "ERREUR"
        )

        print(
            f"{status} - {result.name}"
        )

    has_error = any(
        result.return_code != 0
        for result in results
    )

    print()

    if has_error:
        print(
            "Le contrôle qualité a détecté au moins une erreur."
        )

        print(
            "Corrige les erreurs affichées plus haut avant de commit."
        )

    else:
        print(
            "Tous les contrôles sont passés. Le projet est propre."
        )


def main() -> int:
    """Lance tous les contrôles qualité."""

    python_executable = sys.executable

    results = []

    results.append(
        run_command(
            name="Ruff linting",
            command=[
                python_executable,
                "-m",
                "ruff",
                "check",
                "."
            ]
        )
    )

    results.append(
        run_command(
            name="Pytest",
            command=[
                python_executable,
                "-m",
                "pytest",
                "-v"
            ]
        )
    )

    results.append(
        run_command(
            name="Diagnostic projet",
            command=[
                python_executable,
                "project_diagnostics.py"
            ]
        )
    )

    print_final_summary(
        results
    )

    has_error = any(
        result.return_code != 0
        for result in results
    )

    if has_error:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
