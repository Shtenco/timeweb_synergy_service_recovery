"""Pure-state fault recovery simulator; no real services or actions are touched."""

from __future__ import annotations


FAULTS = {"transient", "data_loss", "persistent"}


def simulate_fault(fault: str, approved: bool = False, max_retries: int = 2) -> dict:
    if fault not in FAULTS:
        raise ValueError(f"unknown fault scenario: {fault!r}")
    if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries < 0:
        raise ValueError("max_retries must be a nonnegative integer")
    proposed: list[str] = []
    applied: list[str] = []
    if fault == "data_loss":
        proposed.append("restore_snapshot")
        if not approved:
            return {
                "fault": fault, "status": "blocked_for_approval",
                "proposed_actions": proposed, "simulated_actions_applied": applied,
                "real_actions_executed": False,
            }
        applied.append("restore_snapshot")
        status = "recovered_in_simulation"
    elif fault == "transient":
        proposed.append("restart_service")
        applied.append("restart_service")
        status = "recovered_in_simulation"
    else:
        for attempt in range(max_retries):
            action = f"restart_attempt_{attempt + 1}"
            proposed.append(action)
            applied.append(action)
        proposed.append("escalate_to_operator")
        status = "escalated_after_retry_limit"
    return {
        "fault": fault,
        "status": status,
        "proposed_actions": proposed,
        "simulated_actions_applied": applied,
        "real_actions_executed": False,
    }


def run(seed: int = 42) -> dict:
    cases = [simulate_fault(name) for name in ("transient", "data_loss", "persistent")]
    return {
        "evidence_type": "simulation",
        "seed": seed,
        "real_actions_executed": False,
        "cases": cases,
        "limitations": [
            "Faults and transitions exist only in memory; no real service or file is changed.",
            "The small scenario catalog does not establish safe recovery in production.",
        ],
    }
