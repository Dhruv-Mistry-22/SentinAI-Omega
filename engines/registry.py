"""
SentinAI — Detector Registry
==============================
Auto-discovers all detectors in the detectors/ package that expose
the standard interface:  DETECTOR_INFO, is_available(), detect()
"""

import importlib
import pkgutil
from pathlib import Path


class DetectorRegistry:
    """
    Scans the detectors/ package and builds a list of all
    installed detectors that are ready to use (model present).
    """

    def __init__(self):
        self._all: list[dict] = []      # All discovered
        self._available: list[dict] = []  # Only those with models present
        self._scan()

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    @property
    def all_detectors(self) -> list[dict]:
        """All discovered detectors (including unavailable ones)."""
        return self._all

    @property
    def available_detectors(self) -> list[dict]:
        """Detectors whose model files are present and ready."""
        return self._available

    def get_by_index(self, index: int) -> dict | None:
        """Return an available detector by 1-based display index."""
        if 1 <= index <= len(self._available):
            return self._available[index - 1]
        return None

    def get_by_id(self, detector_id: str) -> dict | None:
        """Return a detector by its string ID (e.g. 'cnn')."""
        for d in self._available:
            if d["id"] == detector_id:
                return d
        return None

    # ──────────────────────────────────────────
    # Internal scan
    # ──────────────────────────────────────────

    def _scan(self):
        import detectors as det_package

        for finder, name, _ in pkgutil.iter_modules(det_package.__path__):
            module_name = f"detectors.{name}"
            try:
                module = importlib.import_module(module_name)
            except Exception:
                continue  # Skip modules that fail to import cleanly at top level

            if not hasattr(module, "DETECTOR_INFO"):
                continue  # Not a detector module

            info = module.DETECTOR_INFO.copy()
            info["id"] = name
            info["module"] = module

            try:
                info["available"] = module.is_available()
            except Exception:
                info["available"] = False

            self._all.append(info)
            if info["available"]:
                self._available.append(info)

        # Sort both lists by priority field (lower = first); default 99 for unlabeled
        self._all.sort(key=lambda d: d.get("priority", 99))
        self._available.sort(key=lambda d: d.get("priority", 99))
