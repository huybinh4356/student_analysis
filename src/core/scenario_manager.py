"""
Scenario manager module for managing, storing, and comparing What-If simulation scenarios.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class Scenario:
    id: str
    name: str
    student_id: str
    student_name: str
    original_score: float
    simulated_score: float
    delta: float
    changes: Dict[str, Any]
    advice: str
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class ScenarioManager:
    """
    Manages saved What-If simulation scenarios in memory for side-by-side comparison.
    """

    def __init__(self):
        self._scenarios: Dict[str, Scenario] = {}

    def save_scenario(
        self,
        name: str,
        student_id: str,
        student_name: str,
        original_score: float,
        simulated_score: float,
        changes: Dict[str, Any],
        advice: str,
    ) -> Scenario:
        """
        Saves a simulation scenario.

        Args:
            name: Custom scenario name (e.g., "Kịch bản Tăng Chuyên Cần + Nộp bài").
            student_id: Student ID code.
            student_name: Full name of student.
            original_score: Score before simulation.
            simulated_score: Score after simulation.
            changes: Dictionary of feature modifications.
            advice: Action advice generated.

        Returns:
            Scenario: Saved scenario instance.
        """
        scenario_id = f"SCN_{len(self._scenarios) + 1:03d}_{datetime.now().strftime('%H%M%S')}"
        delta = round(simulated_score - original_score, 2)

        scenario = Scenario(
            id=scenario_id,
            name=name if name.strip() else f"Kịch bản #{len(self._scenarios) + 1}",
            student_id=student_id,
            student_name=student_name,
            original_score=original_score,
            simulated_score=simulated_score,
            delta=delta,
            changes=changes,
            advice=advice,
        )

        self._scenarios[scenario_id] = scenario
        return scenario

    def get_all_scenarios(self) -> List[Scenario]:
        """Returns all saved scenarios sorted by creation time."""
        return list(self._scenarios.values())

    def get_scenarios_for_student(self, student_id: str) -> List[Scenario]:
        """Returns all scenarios saved for a specific student."""
        return [s for s in self._scenarios.values() if s.student_id == student_id]

    def delete_scenario(self, scenario_id: str) -> bool:
        """Deletes a scenario by ID."""
        if scenario_id in self._scenarios:
            del self._scenarios[scenario_id]
            return True
        return False

    def clear_all(self):
        """Clears all stored scenarios."""
        self._scenarios.clear()
