"""Harness d'évaluation du qualifier sur le dataset synthétique.

Charge les cas depuis data/eval_cases.json, appelle le qualifier,
et produit un EvalReport avec précision, rappel et F1 par classe.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from maeva_deal_radar_v2.qualification.qualifier import qualify_lead
from maeva_deal_radar_v2.qualification.schemas import (
    EvalCase,
    EvalReport,
    QualificationDecision,
)

logger = logging.getLogger(__name__)

EVAL_CASES_PATH = Path("data/eval_cases.json")


def load_eval_cases() -> list[EvalCase]:
    """Charge les cas d'évaluation depuis le fichier JSON."""
    data = json.loads(EVAL_CASES_PATH.read_text(encoding="utf-8"))
    return [EvalCase(**case) for case in data["cases"]]


def _compute_f1(precision: float, recall: float) -> float:
    """Calcule le F1 score depuis précision et rappel."""
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def run_eval(
    cases: list[EvalCase] | None = None,
    delay_seconds: float = 0.5,
    verbose: bool = True,
) -> EvalReport:
    """Lance l'évaluation complète du qualifier.

    Args:
        cases: Liste de cas à évaluer. Si None, charge depuis le fichier.
        delay_seconds: Pause entre chaque appel API (évite le rate limiting).
        verbose: Affiche la progression en temps réel.

    Returns:
        EvalReport avec métriques agrégées et liste des erreurs.
    """
    if cases is None:
        cases = load_eval_cases()

    results: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    tp_keep = tn_keep = fp_keep = fn_keep = 0
    tp_stop = tn_stop = fp_stop = fn_stop = 0
    correct = 0

    if verbose:
        print(f"\nDémarrage de l'évaluation sur {len(cases)} cas...\n")

    for i, case in enumerate(cases, 1):
        if verbose:
            print(f"[{i:2d}/{len(cases)}] {case.company_name:<30} ", end="", flush=True)

        try:
            result = qualify_lead(
                company_name=case.company_name,
                source_url=case.source_url,
                content=case.content,
                signal_type=case.signal_type,
                geography=case.geography,
            )

            predicted = result.decision
            expected = case.human_decision
            is_correct = predicted == expected

            if is_correct:
                correct += 1
                marker = "✓"
            else:
                marker = "✗"
                errors.append({
                    "id": case.id,
                    "company": case.company_name,
                    "expected": expected.value,
                    "predicted": predicted.value,
                    "justification": result.justification,
                })

            if verbose:
                print(
                    f"{marker} {predicted.value:<6} "
                    f"(attendu: {expected.value:<6}) "
                    f"conf: {result.confidence:.0%}"
                )

            pos = QualificationDecision.KEEP
            if expected == pos and predicted == pos:
                tp_keep += 1
            elif expected != pos and predicted != pos:
                tn_keep += 1
            elif expected != pos and predicted == pos:
                fp_keep += 1
            else:
                fn_keep += 1

            pos = QualificationDecision.STOP
            if expected == pos and predicted == pos:
                tp_stop += 1
            elif expected != pos and predicted != pos:
                tn_stop += 1
            elif expected != pos and predicted == pos:
                fp_stop += 1
            else:
                fn_stop += 1

            results.append({
                "id": case.id,
                "expected": expected.value,
                "predicted": predicted.value,
            })

        except Exception as e:
            logger.error("Erreur sur le cas '%s': %s", case.company_name, e)
            if verbose:
                print(f"ERREUR: {e}")

        if i < len(cases):
            time.sleep(delay_seconds)

    total = len(cases)
    accuracy = correct / total if total > 0 else 0.0

    prec_keep = tp_keep / (tp_keep + fp_keep) if (tp_keep + fp_keep) > 0 else 0.0
    rec_keep = tp_keep / (tp_keep + fn_keep) if (tp_keep + fn_keep) > 0 else 0.0
    f1_keep = _compute_f1(prec_keep, rec_keep)

    prec_stop = tp_stop / (tp_stop + fp_stop) if (tp_stop + fp_stop) > 0 else 0.0
    rec_stop = tp_stop / (tp_stop + fn_stop) if (tp_stop + fn_stop) > 0 else 0.0
    f1_stop = _compute_f1(prec_stop, rec_stop)

    report = EvalReport(
        total_cases=total,
        correct=correct,
        precision_keep=prec_keep,
        recall_keep=rec_keep,
        f1_keep=f1_keep,
        precision_stop=prec_stop,
        recall_stop=rec_stop,
        f1_stop=f1_stop,
        accuracy=accuracy,
        errors=errors,
    )

    if verbose:
        print(f"\n{'='*60}")
        print(f"RÉSULTAT : {report.summary}")
        print(f"{'='*60}")
        if errors:
            print(f"\nErreurs ({len(errors)}) :")
            for err in errors:
                print(f"  [{err['id']}] {err['company']}")
                print(f"    Attendu: {err['expected']} | Prédit: {err['predicted']}")
                print(f"    Justification: {err['justification']}")

    return report
