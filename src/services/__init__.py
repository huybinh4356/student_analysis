"""
Services package for Student Analysis Platform v3.
"""

from src.services.prediction_service import PredictionService, StudentPrediction
from src.services.whatif_service import (
    WhatIfService,
    SimulationResult,
    SensitivityItem,
    TargetSolution,
)

__all__ = [
    "PredictionService",
    "StudentPrediction",
    "WhatIfService",
    "SimulationResult",
    "SensitivityItem",
    "TargetSolution",
]
