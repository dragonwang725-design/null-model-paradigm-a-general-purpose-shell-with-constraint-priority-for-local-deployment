# A counterintuitive AGI architecture solution
 ——Abandoning model-centricity: Constraint-first architecture (NMP) for truly reliable LLM agents

> **Null Model Paradigm
All judgments are based on facts, and the panorama of facts is infinite. Extracting facts that align with the purpose enables LLM to make judgments..**

>**The LLM is not the agent. The shell is.**
This is not a framework. It is an architectural specification for **Purpose–Judgment Partitioning**.

---

## I. Definition: The Null Model

The Null Model is **not empty**.  
It is a **judgment substrate** stripped of *a posteriori* domain knowledge, purpose, and value bias, while retaining *a priori* computational capacity.

>**An empty model doesn't make any judgments; it only calculates whether a match is met. Just like a firewall doesn't "understand" hackers, it only matches rules.**
### What "Null" Means: Knowledge-Free, Not Capacity-Free

| Aspect | Null Model "Has" | Null Model "Does Not Have" |
| :--- | :--- | :--- |
| **A Priori Capacity** | Pure computation: logic, search, constraint satisfaction, path selection, checksum verification | — |
| **A Posteriori Knowledge** | — | Domain corpus, cultural experience, value preferences, autonomous goals |
| **Memory** | — | No persistence of state across sessions |
| **Desire** | — | No internal drive to optimize for anything other than the task at hand |
| **Purpose** | — | Waits for human injection; does not generate its own goals |

**Analogy:** The Null Model is a **CPU**. It has instruction sets (computation), but the data in memory (domain knowledge) is not "part of" the CPU. The CPU reads from memory, operates on it, but remains **knowledge-free** as a substrate. The **Meta-Fact Vault** (Knowledge Base 1) is that external memory—static, human-confirmed, deterministic facts (rules, medical records, archives, gender) that the Null Model queries but does not possess.

> **Key Clarification:** The Null Model queries the Meta-Fact Vault *before* extracting any physical-world facts. The vault's rules (e.g., ¬Delete(source_file)) are **constraints on extraction actions**, not "knowledge" that the Null Model "knows." The Null Model is a **container for judgment**; the vault provides the **boundary conditions** for that judgment.

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

## III. Old Paradigm vs. New Paradigm: The "Game Crash" Example

The following diagram contrasts the **Full-Model Paradigm** (pure LLM) with the **Null Model Paradigm** (TDA three-layer architecture) using a real-world diagnostic scenario.

**Left: Old Paradigm (Pure LLM)**
- User says: "Game keeps crashing"
- LLM lists 5 guesses (driver, DX, overheating, VRAM, system files)
- User trial-and-error; root cause never located
- **Red label: Diagnostic failure, zero fact collection**

**Right: New Paradigm (NMP Three-Layer Architecture)**

| Layer | Action | Output |
| :--- | :--- | :--- |
| **L1 Human** | Input problem | "Game keeps crashing" |
| **L2 Null Model** | Intent recognition | Launch Probe-GPU + Probe-EventLog |
| **Probe A** | `nvidia-smi` | VRAM 9785/10240 MiB (95.5% overflow), temp 86°C, power exceeds TDP |
| **Probe B** | Event Viewer | `nvlddmkm` driver TDR timeout, GPU power limit exceeded |
| **L2 Null Model** | Fact packaging | Structured summary plain text |
| **L3 LLM** | Fact-based analysis | Root cause = VRAM overflow + driver TDR bug, recommend upgrade to 552.44 |
| **L2 Null Model** | Verification + Execution | WHQL check → Apply fix → Verify stability |

**Architecture Data Flow:** L1 → L2 → Probe → L2 → L3 → L2 (complete closed loop)

---

## IV. Knowledge Stratification: Where Knowledge Lives in NMP

Before describing the TDA architecture, we must clarify **what "knowledge" means** and **where it resides**:

| Layer | Knowledge Type | Nature | Owner | Example |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | Human Purpose | Non-computable, value-laden | Human | "Preserve original files" |
| **L2 (Null Model)** | **A Priori Computation** | **Universal, domain-free** | Architecture | BFS, constraint satisfaction, checksum verification |
| **L2 ↔ Meta-Fact Vault** | Meta-Facts | **Static, deterministic, human-confirmed** | Human-maintained | ¬Delete(source_file), gender, medical records, rules |
| **L3 (LLM)** | Training Knowledge | Probabilistic, dynamic, model-internal | LLM weights | "C盘满了要清理" (cultural experience) |
| **L3 ↔ External DB** | Domain Data | Contextual, query-dependent | External systems | Wikipedia, enterprise databases |

**Critical Distinction:**
- The **Meta-Fact Vault** (Knowledge Base 1) is **not** the Null Model's "memory." It is an **external read-only register** that the Null Model queries to determine **what facts are allowed to be extracted** from the physical world. The vault's contents (rules, archives, medical records) are **static facts** that constrain the Null Model's **perception actions**, not knowledge that the Null Model "learns" or "possesses."
- The **LLM's training knowledge** is **probabilistic and internal** to the model. It generates candidate strategies but cannot modify the Null Model's execution plan.

---

## V. Architecture: The Three-Layer Dual-Perspective (TDA)

| Layer | Name | Role | Permissions |
| :--- | :--- | :--- | :--- |
| **L1** | **Intent Injection** | Human Sovereignty | Provides goals, values, success criteria. **Non-delegable.** |
| **L2** | **Null Model** | **The Agent** | **Only layer with physical execution rights.** Controls resource budget, math planning, constraints, rollback. Reads from Meta-Fact Vault for extraction rules. |
| **L3** | **Full Model (LLM)** | Cognitive Generator | **Zero FS Write.** **Zero Exec.** **Zero Plan Modification.** Limited to text generation and labeling within fact-boundaries set by L2. |

### The Six-Step Pipeline

1.  **Problem Reception** (L1 → L2): Human intent injected.
2.  **Strategy Calculation** (L2): Query Meta-Fact Vault for extraction rules → Physics budget → Task decomposition → Constraint locking.
3.  **Cognitive Processing** (L3): LLM performs semantic understanding on **L2-filtered facts**; outputs labels only.
4.  **Knowledge Retrieval** (L3 ↔ DB): Fetch domain-specific data (if needed, within L2 constraints).
5.  **Blueprint Synthesis** (L3): LLM assembles a **text-only execution blueprint** under L2 constraints.
6.  **Judgment & Execution** (L2): Evaluate blueprint validity against Meta-Fact Vault rules, select optimal path, enforce atomicity and rollback.

---

## VI. Dual-Phase Theory

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

- `src/null_model/`: L2 Implementation (Budget, Constraints, Execution, Meta-Fact Vault query).
- `docs/architecture/`: Formal specs of TDA.
- `examples/`: Demos of the 6-step pipeline.

## Citation 

 <img width="191" height="20" alt="image" src="https://github.com/user-attachments/assets/6201758a-a40d-4c0b-a345-285fda7fe6cd" />
<img width="191" height="20" alt="image" src="https://github.com/user-attachments/assets/f313de27-8998-4e83-83a7-8d7bbffd34ea" />

---

## Quick Start: See it in action

Run the GPU crash diagnosis demo.  
This demonstrates why **facts beat knowledge**.

```bash
python examples/gpu_crash_demo.py
```

**What you will see:**  
The LLM starts with wild guesses (Knowledge).  
The Null Model injects real system facts (Probes).  

The LLM returns a precise diagnosis (Judgment).

**The difference:**  
One is a consultant. The other is an engineer.

**For a real-world comparison, see the "Game Crash" example in Section III above** (diagram ), which shows the complete L1→L2→Probe→L2→L3→L2 closed loop in action.
