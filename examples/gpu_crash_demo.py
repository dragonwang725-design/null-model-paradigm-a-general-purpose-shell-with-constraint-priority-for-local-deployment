"""
Null Model Paradigm: GPU Crash Diagnosis Demo
-------------------------------------------------
Assertion: Fact-Driven, Not Knowledge-Driven.
"""

import json
import random

# ----------------------
# L3: Simulated LLM (Knowledge only)
# ----------------------
class MockLLM:
    """This LLM knows everything, but touches nothing."""
    def guess(self, symptom: str):
        print(f"[LLM] Based on '{symptom}', guessing possible causes...")
        return [
            "Outdated graphics drivers.",
            "Overheating due to dust.",
            "Corrupted game files.",
            "Insufficient power supply."
        ]

# ----------------------
# L2: Null Model (The Probe)
# ----------------------
class NullModelProbe:
    """
    This has NO knowledge of 'why'.
    It ONLY collects FACTS from the physical world.
    """
    def collect_facts(self):
        print("[NULL MODEL] Injecting probes into system...")

        # Fact 1: GPU Status (Simulated hardware query)
        gpu_fact = {
            "driver_version": "512.34",
            "memory_used": "8192MB / 8192MB",  # FULL
            "temperature": "67C"
        }

        # Fact 2: System Log (Simulated log query)
        log_fact = {
            "last_error": "DXGI_ERROR_DEVICE_REMOVED",
            "timestamp": "2026-06-09 22:05:01"
        }

        print(f"[NULL MODEL] Facts collected: {gpu_fact['memory_used']} used.")
        return {"gpu": gpu_fact, "log": log_fact}

# ----------------------
# Execution Pipeline
# ----------------------
def run_diagnosis():
    print("=== Scenario: Game Crashing ===\n")

    # L1: Human input
    symptom = "My game keeps crashing."

    # L3: LLM guesses (Old way)
    llm = MockLLM()
    guesses = llm.guess(symptom)
    print(f"[LLM GUESS] {guesses}\n")

    # L2: Null Model collects FACTS (New way)
    probe = NullModelProbe()
    facts = probe.collect_facts()

    # L3: LLM diagnoses based on FACTS
    print("[LLM] Analyzing provided facts...")
    if facts["gpu"]["memory_used"] == "8192MB / 8192MB":
        diagnosis = "Diagnosis: VRAM Overload. Suggest closing background apps or lowering texture settings."
        print(f"\n✅ [FINAL JUDGMENT]: {diagnosis}")
    else:
        diagnosis = "Unknown issue."

if __name__ == "__main__":
    run_diagnosis()
