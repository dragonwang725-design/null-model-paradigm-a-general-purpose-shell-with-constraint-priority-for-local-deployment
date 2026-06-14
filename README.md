# Null Model Paradigm (NMP)

> **The LLM is not the agent. The shell is.**

This is not a framework. It is an architectural specification for **Purpose–Judgment Partitioning**.

---

## I. Definition: The Null Model

The Null Model is **not empty**.  
It is a **judgment substrate** stripped of domain knowledge, purpose, and value bias.

- **No Memory.** No persistence of state across sessions.
- **No Desire.** No internal drive to optimize for anything other than the task at hand.
- **No Purpose.** It waits for human injection.

It is a **pure capacity for computation**, acting solely as a container for judgment.

---

## II. The Core Axiom: AGI Requires No Consciousness

**Autonomous Consciousness = Purpose + Judgment**

| Component | Owner | Constraint |
| :--- | :--- | :--- |
| **Purpose** | **Human** | Immutable. Non-computable. |
| **Judgment** | **Machine** | Computable. Irreversible. |

**Judgment is Fact-Driven, not Knowledge-Driven.**  
Knowledge is a map. Facts are the terrain.  
The Null Model executes based on terrain, selecting maps as needed.

---

## III. Architecture: The Three-Layer Dual-Perspective (TDA)

| Layer | Name | Role | Permissions |
| :--- | :--- | :--- | :--- |
| **L1** | **Intent Injection** | Human Sovereignty | Provides goals, values, success criteria. **Non-delegable.** |
| **L2** | **Null Model** | **The Agent** | **Only layer with physical execution rights.** Controls resource budget, math planning, constraints, rollback. |
| **L3** | **Full Model (LLM)** | Cognitive Generator | **Zero FS Write.** **Zero Exec.** **Zero Plan Modification.** Limited to text generation and labeling. |

### The Six-Step Pipeline

1.  **Problem Reception** (L1 → L2): Human intent injected.
2.  **Strategy Calculation** (L2): Physics budget, task decomposition, constraint locking.
3.  **Cognitive Processing** (L3): LLM performs semantic understanding; outputs labels only.
4.  **Knowledge Retrieval** (L3 ↔ DB): Fetch domain-specific data.
5.  **Blueprint Synthesis** (L3): LLM assembles a **text-only execution blueprint** under L2 constraints.
6.  **Judgment & Execution** (L2): Evaluate blueprint validity, select optimal path, enforce atomicity and rollback.

---

## IV. Dual-Phase Theory

### Phase 1: Training — Freedom = Creativity
- **AI**: Unbound curiosity. No external goals, no rewards, no borders.
- **Human**: Defines value. Discovers meaning from AI-generated patterns.
- **Essence**: The soil of creation is freedom. AI provides the material; humans provide the value.

### Phase 2: Usage — Constraint = Capability
- **Human**: Injects purpose (task, direction, value).
- **AI**: Extreme judgment within boundaries. Precision execution.
- **Essence**: Constraints focus power. Purpose provides direction. Zero drift, zero hallucination, full audit.

---

## Current Status

This repository contains the **Phase 1 Proof-of-Concept**.  
It implements the L2 Null Model skeleton and the TDA permission boundaries.  
LLM integration is simulated to demonstrate the separation logic.

## Structure

- `src/null_model/`: L2 Implementation (Budget, Constraints, Execution).
- `docs/architecture/`: Formal specs of TDA.
- `examples/`: Demos of the 6-step pipeline.

## Citation

**DOI:** [10.5281/zenodo.20463703](https://doi.org/10.5281/zenodo.20463703)

---

## Quick Start: See it in action

Run the GPU crash diagnosis demo.  
This demonstrates why **facts beat knowledge**.
**What you will see:**  
The LLM starts with wild guesses (Knowledge).  
The Null Model injects real system facts (Probes).  
The LLM returns a precise diagnosis (Judgment).

**The difference:**  
One is a consultant. The other is an engineer.
