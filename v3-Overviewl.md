#  A counterintuitive AGI architecture solution
 ——Abandoning model-centricity: Constraint-first architecture (NMP) for truly reliable LLM agents

> **Null Model Paradigm
All judgments are based on facts, and the panorama of facts is infinite. Extracting facts that align with the purpose enables LLM to make judgments..**

>**The LLM is not the agent. The shell is.**
This is not a framework. It is an architectural specification for **Purpose–Judgment Partitioning**.

**Version 2.0.2: Refined Architecture and Terminology**

> **Revision Note:** Version 1.0 (Zenodo DOI: 10.5281/zenodo.20463703) established the foundational concept of the Null Model Paradigm. Version 2.0 refines the architecture with (i) explicit knowledge stratification (L0–L3), (ii) the Meta-Fact Vault as a deterministic knowledge layer, (iii) the Case Library as a dynamic feedback layer, and (iv) a clarified mechanism for LLM constraint through input-boundary locking rather than permission deprivation. This revision also introduces the Three-Layer Dual-Perspective (TDA) architecture diagram and the dialectical conflict-resolution layer.

**Authors:** loweswang  
**Date:** June 10, 2026
**Zenodo V2 DOI:** [10.5281/zenodo.20636262](https://doi.org/10.5281/zenodo.20636262)
**Concept DOI (always latest):** [10.5281/zenodo.20643414](https://doi.org/10.5281/zenodo.20643414)
**Previous Version:** [10.5281/zenodo.20463703](https://doi.org/10.5281/zenodo.20463703)

## Abstract

Current LLM-based agents exhibit systematic failures when executing physical-world tasks, as exemplified by the commercial product DuMate's repeated timeouts and crashes during a simple file-organization task on an 8GB-memory consumer device. We argue that these failures are not engineering deficiencies but structural flaws of the Full-Model paradigm, which conflates cognitive generation with physical execution.

We propose the Null Model Paradigm (NMP), a constraint-first architecture that strictly separates a knowledge-free computational judgment layer (Null Model, retaining only a priori computational capacity) from a generative knowledge layer (LLMs and databases, carrying a posteriori probabilistic knowledge), mediated by a human-confirmed static fact layer (Meta-Fact Vault, providing deterministic constraints) and a dynamic feedback layer (Case Library, storing historical cases for threshold adjustment). Drawing on the structural precedent of AlphaGo/AlphaZero—where a general search-and-evaluation engine operates without domain-specific "opening books"—we show that the Null Model generates, evaluates, and selects execution strategies under formal constraints while delegating all semantic interpretation to the LLM. The LLM is the opening book; the Null Model is the player; the Meta-Fact Vault is the rulebook; the Case Library is the game log.

We formalize this separation as a six-step pipeline and demonstrate, via a counterfactual analysis of the DuMate failure, that this architecture would have prevented the crash without additional hardware. We further introduce the Three-Layer Dual-Perspective (TDA) architecture, which adds a dialectical conflict-resolution layer between LLM-generated hypotheses and Null-Model-verified facts. This paper establishes the foundational architecture and formal properties of NMP; a companion technical report on the Null Model Runtime and comparative benchmarks is in preparation.

## 1 Introduction
The proliferation of Large Language Model (LLM) based agents—such as AutoGPT, LangChain agents, and commercial products like DuMate—has promised to automate complex physical-world tasks through natural language interaction. However, these systems routinely fail when confronted with resource-constrained, real-world environments.

Consider the following empirical observation: On May 30, 2026, a user instructed DuMate, a locally-deployed AI office assistant, to organize approximately 100 text files and several dozen Word documents on a consumer-grade machine (Intel Core i5-7400, 8GB RAM, 120GB SSD, Windows 10 Enterprise). The instruction was unambiguous: "Organize all files by content and type; summarize identical content; preserve original files intact; save new files to the kb folder." The agent failed three consecutive times with Internal Server Error: Bad Gateway and execution halts.

Critically, this task is trivial for any rule-based script, yet insurmountable for a state-of-the-art LLM agent. We contend that this failure is not an implementation bug, but a paradigmatic defect. Current agents operate under the Full-Model paradigm, wherein a monolithic LLM is expected to simultaneously understand intent, plan operations, and execute physical actions. The LLM, bloated with internet corpora, cultural knowledge, and statistical patterns, lacks the skeletal structure necessary for physical-world reliability.

## 2 Definitions and Core Concepts
2.1 Knowledge Stratification: The Four-Layer Model
Before defining the Null Model and Full Model, we must clarify what "knowledge" means in NMP. We propose a four-layer stratification that resolves the apparent paradox of a "knowledge-free" system that queries external databases:

Layer	Name	Nature	Owner	Modifiability	Example
L0	A Priori Computational Capacity	Universal algorithmic skeleton: search, evaluation, constraint satisfaction, path selection, checksum verification	Null Model (built-in)	Immutable (architectural constant)	BFS graph distance, boolean logic, arithmetic
L1 (static)	Meta-Fact Vault	Human-confirmed static facts: rules, medical records, archives, gender, ¬Delete(source_file)	Meta-Fact Vault (external)	Human-only	"8GB RAM requires 4GB free for 7B model"
L1 (dynamic)	Case Library	Historical positive/negative cases with human feedback; used for threshold adjustment and rule refinement	Case Library (external)	Feedback-driven	False positive records, success logs
L2	Training Knowledge	Probabilistic language patterns: internet corpora, cultural experience, statistical associations	LLM (internal weights)	Model fine-tuning	"C盘满了要清理" (cultural heuristic)
L3	External Data	Context-dependent dynamic data: enterprise databases, real-time sensors	External systems	System-dependent	Live stock prices, temperature readings
Critical Distinction: The Null Model is L0 only. It queries L1 (Meta-Fact Vault) for constraint conditions and reads L1 (Case Library) for historical feedback, but these are not "learned" or "remembered"—they are boundary conditions applied per-task and discarded afterward. The analogy is a CPU reading from memory: the CPU possesses computational capacity (L0); the memory holds data (L1); the CPU does not "know" the data, it operates on it.

The Meta-Fact Vault is static (human-maintained, rarely changes), while the Case Library is dynamic (continuously updated by execution outcomes and human feedback). Together, they constitute the complete L1 layer. The LLM (L2) has zero visibility into either component of L1.

### 2.2 Full Model
A Full Model is an AI system whose knowledge layer is maximally saturated with domain-specific corpora, cultural experience, value preferences, and autonomous goal-generation mechanisms. Contemporary LLMs (e.g., GPT-4, Qwen, Claude) and their derivative agents are archetypal Full Models.

### 2.3 Null Model
A Null Model is an a posteriori knowledge-free computational judgment substrate. The term Null does not denote emptiness (∅), but evacuation: the systematic stripping of all contingent knowledge—domain corpora (L2), cultural experience (L2), value preferences (L2), autonomous purpose (L2/L3)—while retaining the complete a priori algorithmic skeleton (L0) for judgment, search, evaluation, constraint satisfaction, and optimal path selection.

Operational Inputs:

Human purpose (from L1 Intent Injection)

Physical-world state (filtered through Meta-Fact Vault extraction rules)

Formal constraints (physics, mathematics, logic, causality—applied via L0 capacity)

Operational Outputs:

Permitted action sequences

Execution verdicts

All semantic interpretation required for strategy generation is delegated to the Full Model (LLM), but the LLM has zero authority to modify the Null Model's execution plan.

### 2.4 Meta-Fact Vault and Case Library (L1)
The Meta-Fact Vault is a human-confirmed static fact layer that serves as the deterministic constraint source for the Null Model. The Case Library is a dynamic feedback layer that stores historical execution outcomes with human feedback, used to adjust thresholds, refine rules, and improve future extractions.

Property	Meta-Fact Vault (Static L1)	Case Library (Dynamic L1)	LLM Training Knowledge (L2)
Determinism	100% deterministic	Deterministic (recorded facts)	Probabilistic
Modification	Human-only	Human feedback + automated logging	Gradient descent / fine-tuning
Visibility	Read-only to Null Model; invisible to LLM	Read-only to Null Model; invisible to LLM	Internal to LLM; invisible to Null Model
Function	Constrains extraction actions; provides causal mappings	Provides historical precedent for threshold tuning	Provides language understanding; generates candidate strategies
Source	Human confirmation; rule entry; archive import	Execution logs; user feedback; error reports	Internet corpora; pre-training data
Contents of Meta-Fact Vault:

Meta-Rules: Immutable hard constraints (e.g., ¬Delete(source_file))

Meta-Facts: Deterministic static data (gender, medical records, device specifications)

Domain Ontology Mappings: Entity-to-formal-node mappings for causal skeleton instantiation

Contents of Case Library:

Positive cases: Successful executions with their context (purpose, facts used, strategy)

Negative cases: Failed executions or constraint violations with human feedback

Threshold adjustments: e.g., "false positive rate > 0.2 → increase motion threshold"

Rule refinement suggestions: e.g., "missing fact type 'airport_name' for purpose 'go_to_airport'"

### 2.5 Six-Step Pipeline
The NMP operationalizes agency through a strictly unidirectional pipeline. Steps 2a and 2b both occur within the Null Model layer but represent distinct phases (constraint retrieval vs. strategy computation):

Step	Phase	Layer	Action
1	Problem	L1	Human intent expressed in natural language
2a	Meta-Fact Query	L2	Query Meta-Fact Vault for extraction rules, domain ontology mappings, and constraint formalization
2b	Strategy Computation	L2	Physical resource budgeting, mathematical task decomposition, constraint locking, candidate path generation
3	Cognition	L3	LLM performs semantic understanding on L2-filtered facts; outputs text labels
4	Knowledge Retrieval	L3 ↔ DB	External retrieval of domain-specific information (within L2 constraints)
5	Synthesis	L3	LLM assembles text-only execution blueprint under Null Model constraints
6	Judgment & Execution	L2	Evaluate blueprint against Meta-Fact Vault rules; select path; enforce atomicity; execute with rollback
Output: Physical-world execution result.

3 Architecture: The Three-Layer Dual-Perspective (TDA)
NMP mandates an architectural firewall between cognition and execution, augmented by a dialectical conflict-resolution layer.

<img width="1747" height="865" alt="arch" src="https://github.com/user-attachments/assets/6b90f4e6-b3cd-418e-8371-0e323606fc15" />


Figure 1: TDA Core Architecture. The local side (right) contains the Null Model, Meta-Fact Vault, and Case Library. The cloud side (left) contains the LLM and its Case Library. The Null Model sends desanitized instructions (filtered facts + purpose) to the LLM; the LLM returns strategy proposals. The Null Model performs matching, computation, and adjudication. Data flow: User Input → L2 → Probes → L2 → L3 → L2 → Output (closed loop).

3.1 L1: Intent Injection (Human Sovereignty)
The human provides the goal, the value ranking, and the success criteria. This layer is non-computable and non-delegable.

3.2 L2: Null Model Layer (Computational Judgment Engine)
This is the only layer with physical-world execution privileges. It does not merely "filter" LLM outputs; it computes the execution strategy from scratch. The Null Model comprises four rigid computational modules:

Physical Budgeting Module: Monitors RAM, disk space, file handles, and network state. It computes a safe batch size (e.g., 10 files per batch on an 8GB machine) before any LLM is invoked.

Mathematical Planning Module: Decomposes the task into an optimal sequence of atomic operations under complexity and resource constraints. This is a planning computation, not a knowledge lookup.

Constraint Formalization Module: Translates natural-language intents into immutable logical assertions. For example, "do not delete original files" is formalized as the axiom ¬Delete(S_source), which permanently prunes any candidate operation in the Delete class.

Verification & Rollback Module: Enforces causality (every effect has a traceable cause), identity (a file copied remains the same entity in terms of checksum), and reversibility (every batch is either fully committed or fully rolled back).

3.3 L3: Full Model Layer (Generative Cognition)
The LLM and external databases operate here. Their sole privileges are:

Reading file contents (text-only input)

Outputting text labels (e.g., "Contract," "Meeting Minutes")

Generating human-readable summaries

They possess zero file-system write access, zero process-spawning rights, and zero authority to modify the execution plan.

LLM Constraint Mechanism: Input-Boundary Locking

The LLM is not "caged" through permission deprivation (which would be a brittle operational measure), but through input-boundary locking (an architectural guarantee):

Boundary	Mechanism
Input Boundary	The LLM receives only facts filtered by the Null Model; raw sensor data never reaches L3
Purpose Boundary	The LLM's strategy must align with the human-injected purpose; the Null Model verifies this alignment
Fact Boundary	If the LLM references facts not in the provided set, the Null Model marks the strategy as inconsistent
Meta-Fact Blindness	The LLM has no knowledge of the Meta-Fact Vault's existence or contents
Analogy: The LLM is a student in a closed-book exam. The exam paper (filtered facts + purpose) provides all necessary conditions. The student may reason freely, but answers must conform to the given conditions. The student cannot request additional materials.

3.4 Dialectical Conflict-Resolution Layer
<img width="2307" height="3089" alt="三层双视角（TDA）辩证架构流程图" src="https://github.com/user-attachments/assets/9f29df38-bace-4641-a9d3-677d70ec2c24" />


Figure 2: TDA Dialectical Architecture. The input layer feeds into two parallel processing paths: the LLM (driven by its case library) and the Null Model (driven by the Meta-Fact Vault and its case library). Their outputs enter a structured debate layer (conflict graph construction). The meta-passive layer contains an adjudication AI with dynamic thresholds and justified randomness, informed by historical distributions and periodic audits. A non-cognitive structural circuit breaker (with human audit/external anchor override) provides final pass/reject/interrupt decisions. Feedback loops update the case libraries.

Clarification: The "adjudication AI" in the meta-passive layer is not a separate model. It is the Null Model (L2) itself, acting as the final judge. The Null Model’s existing mechanisms—constraint checking, fact consistency verification, purpose alignment, and dynamic threshold evaluation—constitute the adjudication process. The "justified randomness" refers to probabilistic tie-breaking based on historical distribution recorded in the Case Library (e.g., when two strategies are equally valid, select the one with higher historical success rate). The Null Model remains deterministic in all constraint-satisfaction matters; randomness, if any, is bounded and auditable.

This dialectical structure ensures that:

LLM-generated hypotheses are verified against Null-Model-extracted facts, not merely "filtered by" them

Conflicts between semantic richness (LLM) and formal reliability (Null Model) are resolved structurally, not heuristically

Human oversight retains supreme veto power through the external anchor

4 Case Study: The DuMate Failure
4.1 Failure Analysis (Full-Model Paradigm)
DuMate's architecture allowed the LLM to directly interpret intent and emit execution commands. The following chain of failures occurred:

No Physical Budgeting: The LLM attempted to process 150+ files simultaneously, exhausting 8GB RAM.

No Meta-Fact Constraint: There was no formal lock on "preserve original files"; the LLM "understood" this statistically but had no immutable constraint.

No Atomicity: Operations were not batched; a mid-process crash left the file system in an inconsistent state.

No Rollback: Upon encountering Bad Gateway, the agent generated an apologetic text response rather than reverting partial copies.

The LLM was not "supported" by a missing layer; it was rolling naked on the physical world without a hard shell.

4.2 Counterfactual Success (Null-Model Paradigm)
Under NMP, the same task would execute as follows:

Step 2a (Meta-Fact Query): L2 queries Meta-Fact Vault: Rule SYS001 matched for purpose "optimize"; extraction permissions: file.name, file.size, file.type; forbidden: file.content, file.path; constraint: ¬Delete(S_source), ¬Move(S_source).

Step 2b (Strategy Computation):

L2 Physical Module scans F:\ai: 150 files, total size X, available RAM ≈ 4GB (post-OS). Safe batch size computed as 10.

L2 Constraint Module formalizes intent: Operation ∈ {Copy}, ¬Delete, ¬Move.

Step 3 (Cognition): L3 LLM receives only the text content of 10 files per batch, returns labels (e.g., "Contract").

Step 5 (Synthesis): L2 sanitizes labels (path-traversal characters stripped, reserved names blocked).

Step 6 (Judgment & Execution): L2 executes Copy(src, dst), verifies checksum identity (MD5_src = MD5_dst), logs causally, and proceeds. If LLM times out (Bad Gateway), L2 does not crash. It degrades gracefully: labels default to file extensions, copies continue, and the anomaly is logged for human review.

<img width="692" height="704" alt="2026" src="https://github.com/user-attachments/assets/c2a470db-a2ca-4bd6-b021-b5c3f05970a1" />


Figure 3: Old Paradigm vs. New Paradigm. Left: Pure LLM diagnosis fails after five guesses. Right: NMP three-layer architecture succeeds through fact-driven closed-loop execution.

5 The AlphaGo Precedent
AlphaGo/AlphaZero provides the most rigorous empirical precedent for the structure of the Null Model. AlphaZero had no human Go knowledge injected—no opening books, no professional game records, no cultural intuition. What it retained was precisely a knowledge-free judgment skeleton:

A mathematical state space (19×19 grid, deterministic rules)

A finite, formally defined action set (place stone, pass, resign)

A general search and evaluation framework (MCTS + value network)

A terminal evaluation function

When the Go rules are replaced with file-system rules, the identical skeletal structure can compute an optimal organization strategy. This demonstrates that superhuman judgment requires no domain knowledge in the judge; only the surface rules and the computational skeleton change.

NMP extends this analogy:

Component	AlphaGo	NMP Agent
Problem source	Opponent's move	Human intent + World state
Judgment engine	MCTS + Value Network	Null Model (L0)
Knowledge source	Go corpus / Self-play games	LLM (L2) + Meta-Fact Vault (L1)
Rule source	Game rules (fixed)	Meta-Fact Vault (L1, human-maintained)
Final authority	Engine selects move	Null Model selects action
The LLM supplies the "opening book" (domain knowledge); the Null Model supplies the "MCTS" (judgment and search); the Meta-Fact Vault supplies the "rulebook" (constraints and mappings). Critically, the engine never asks the knowledge base "what should I do?" It asks "what are my options?" and then computes the answer.

## 6 Formal Guarantees
The NMP architecture provides four structural guarantees that the Full-Model paradigm cannot offer:

Resource Safety: By construction, the Null Model budgets resources before invoking the LLM, guaranteeing that physical exhaustion cannot occur due to LLM over-generation.

Constraint Immutability: Once ¬Delete(S) is formalized in L2 (via Meta-Fact Vault rules), no LLM output can override it—by architectural firewall, not by prompt engineering.

Graceful Degradation: If L3 fails (timeout, hallucination), L2 falls back to deterministic defaults, ensuring the system remains in a safe state.

Cross-Domain Reuse: The causal skeleton (L0) is purely formal (Node_A → Node_B). Domain entities (memory, blood_pressure, credit_score) are mapped to formal nodes through the Meta-Fact Vault's ontology tables. The same skeleton serves system monitoring, medical diagnosis, and financial risk assessment with zero code modification.

7 Implications for AGI
Current industry practice pursues AGI by saturation—more parameters, more data, more modalities, more autonomous behavior. NMP argues that this is a category error. AGI is not a bloated Full Model that "knows everything"; it is a minimal Null Model that never falls.

The path to safe AGI is not:

text
More Data → More Knowledge → More Autonomy
But:

text
Harder Constraints → Reliable Judgment → Safe Execution
8 Conclusion and Future Work
The DuMate failure is not an anecdote; it is a paradigm indicator. LLM agents will continue to collapse in physical environments until the industry recognizes that generation without constraint is hallucination, and execution without judgment is destruction.

The Null Model Paradigm does not reject LLMs; it constrains them through architectural fact-boundary locking. The Null Model does not merely constrain the LLM; it out-computes it on the only axis that matters for physical reliability: the ability to plan, evaluate, and execute under hard constraints without hallucinating authority.

The LLM may be infinitely knowledgeable, but it must never touch the file system without passing through the irreversible filter of physics, mathematics, logic, and causality. Intelligence is not the accumulation of knowledge; it is the discipline to know when not to act—and the hard shell that enforces that discipline.

Future Work. This paper establishes the foundational architecture and formal properties of NMP. A companion technical report detailing the Null Model Runtime, constraint representation language, conflict-resolution protocol, and comparative benchmarks against existing agent frameworks is in preparation.

Appendix A: Terminology Clarification
A.1 "Knowledge-Free" Precision
The Null Model is a posteriori knowledge-free, not computationally empty. It retains a priori computational capacity (L0): search, evaluation, constraint satisfaction, path selection, checksum verification. These are not "knowledge"; they are the substrate on which knowledge operates.

A.2 "Meta-Fact Vault" vs. "Privacy Vault"
"Privacy Vault" was an early alias emphasizing the sensitivity of Meta-Fact contents. The preferred term is Meta-Fact Vault (or Knowledge Base 1), which correctly identifies the layer as a deterministic, human-confirmed static fact source rather than a privacy-compliance tool.

A.3 Cross-Domain Mechanism
The causal skeleton is meta-skeletal: it contains only formal nodes (Node_A, Node_B) and edges. Domain entities (memory, ollama, blood_pressure) are mapped to formal nodes through ontology tables stored in the Meta-Fact Vault. The same skeleton serves all domains; only the mapping table changes.

A.4 LLM "Cage" Mechanism
The term "cage" (used in V1) was a metaphor for LLM constraint. V2 replaces this with input-boundary locking: an architectural guarantee that the LLM cannot bypass, rather than an operational restriction that might be circumvented.

A.5 Case Library as Dynamic L1
The Case Library stores historical positive and negative execution outcomes with human feedback. It is used to adjust thresholds (e.g., lowering false positive rates) and refine extraction rules. Unlike the static Meta-Fact Vault, the Case Library is continuously updated through the feedback loop shown in Figure 2.

A.6 Adjudication AI = Null Model
The "adjudication AI" in the dialectical conflict-resolution layer (Figure 2, meta-passive layer) is not a separate model. It is the Null Model (L2) itself, applying its existing constraint checking, fact consistency verification, purpose alignment, and dynamic threshold evaluation. Any "justified randomness" refers to probabilistic tie-breaking based on historical distribution recorded in the Case Library.

## References
[1] Silver, D., et al. (2016). Mastering the game of Go with deep neural networks and tree search. Nature, 529(7587), 484–489.

[2] Silver, D., et al. (2017). Mastering Chess and Shogi by Self-Play with a General Reinforcement Learning Algorithm. arXiv preprint arXiv:1712.01815.

[3] Yao, S., et al. (2023). ReAct: Synergizing reasoning and acting in language models. ICLR 2023.

[4] Richards, T. B. (2023). Auto-GPT: An autonomous GPT-4 experiment. GitHub repository.

[5] Pnueli, A. (1977). The temporal logic of programs. Proceedings of the 18th Annual Symposium on Foundations of Computer Science, 46–57.

[6] Russell, S. (2019). Human Compatible: Artificial Intelligence and the Problem of Control. Viking.

[7] Wang, L. (2026). The Null Model Paradigm: Constraint-First Architecture for Reliable LLM Agents (Version 1.0). 
Zenodo  https://doi.org/10.5281/zenodo.20463703
