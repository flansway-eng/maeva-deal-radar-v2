"""Tests de sanité — vérifie que l'environnement fonctionne."""

import maeva_deal_radar_v2


def test_package_importable() -> None:
    """Le package principal doit être importable."""
    assert maeva_deal_radar_v2 is not None


def test_python_version() -> None:
    """On doit tourner sur Python 3.12 ou plus récent."""
    import sys
    assert sys.version_info >= (3, 12), (
        f"Python 3.12+ requis, version actuelle : {sys.version}"
    )


def test_pydantic_importable() -> None:
    """Pydantic v2 doit être disponible."""
    import pydantic
    assert int(pydantic.__version__.split(".")[0]) >= 2, (
        f"Pydantic v2 requis, version actuelle : {pydantic.__version__}"
    )
