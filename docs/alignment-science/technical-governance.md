---
tags:
  - alignment-science
---

# Technical AI Governance: Verification and Compute

**Technical AI governance** (TAIG) means technical analysis and tools that support governing AI: verifying what a lab trained or deployed, securing model weights, and making agreements checkable. This page covers the problem map and two verification lines with code or concrete designs. Evaluations used as governance evidence are on [`dangerous-capability-evals.md`](../evaluation/dangerous-capability-evals.md); unlearning and tamper resistance are on [`unlearning.md`](unlearning.md).

## At a glance

| I want to… | Start with |
|---|---|
| A map of open technical governance problems to pick a project from | **Open Problems in Technical AI Governance** (Reuel, Bucknall, Casper et al., arXiv:2407.14981) |
| Detect model weights being smuggled out through an inference server's responses | **Inference verification** (Rinberg, Karvonen et al., arXiv:2511.02620; `RoyRin/inference_verification_for_model_weight_exfiltration`) |
| A reference design for verifying compute use between parties who do not trust each other | **Low-trust compute verification** (Naci Cankaya, LessWrong, 2026-06-23, working draft) |
| A working demo of an LLM inside a trusted execution environment acting as a third-party auditor over private data | **Auditor-in-a-Box** (Roy Rinberg and Ben Penchas, LessWrong, 2026-07-28; `RoyRin/auditor-in-a-TEE`) |
| Know how a governance reader will weigh your scheming or loss-of-control eval | **Uuk et al.**, "Assessing the Empirical Evidence for Loss of Control from Agentic General-Purpose AI" (arXiv:2610.25241) |
| Formal guarantees and machine-checked proofs | [`agent-foundations-and-formal.md`](agent-foundations-and-formal.md) |

## Open Problems in Technical AI Governance (Reuel et al., arXiv:2407.14981)

A catalogue of open problems in technical AI governance (TAIG), written for technical researchers and funders. It is organised on two axes:

- **Capacities:** Assessment, Access, Verification, Security, Operationalization, Ecosystem Monitoring.
- **Targets:** Data, Compute, Models and Algorithms, Deployment.

Each cell lists open problems with example research questions. Cells that fit an ML fellow include verification of training data (5.1.1), verification of compute workloads (5.2.2), proof-of-learning (5.3.3), prevention of model theft (6.3.1), modification-resistant models (6.4.2), and (multi-)agent evaluations (3.3.3). The authors call the catalogue incomplete, and the v2 revision is dated April 2025, so check newer work before claiming a problem is untouched.

**When not to use it:** as evidence that a problem is still open in 2026. Use it as a map, then search for later work.

## Inference verification against weight exfiltration

Rinberg, Karvonen, Hoover, Reuter & Warr, "Verifying LLM Inference to Detect Model Weight Exfiltration" (arXiv:2511.02620). Code: `RoyRin/inference_verification_for_model_weight_exfiltration` (GitHub; no license file detected via the GitHub API, last push 2026-02-19).

- **Threat:** an attacker who controls an inference server hides weight bits inside ordinary model responses (steganography).
- **Method:** formalises weight exfiltration as a security game and proposes a verification framework for inference that provably mitigates steganographic exfiltration. To make verification possible, the paper characterises the legitimate sources of non-determinism in large language model (LLM) inference and introduces two practical estimators for them.
- **Result:** on MOE-Qwen-30B the detector reduces exfiltratable information to under 0.5% at a false-positive rate under 0.01%, which the authors equate to a more than 200x slowdown for an adversary. Models tested ranged from 3B to 30B parameters.
- **Scope:** the threat model is weights hidden in model responses from an inference server, under the trust assumptions the paper states. Other routes to weight theft are not what it addresses.

**Follow-up: combining evidence over time.** Ortega-Fernandez, Kowalczyk & Warr, "Anytime-valid detection of LLM weight exfiltration" (arXiv:2610.11843, 2026-10-08) note that replaying prompts on a trusted server exposes token mismatches but "benign numerical nondeterminism also causes token mismatches", so a patient attacker hides in normal variation unless evidence is combined across responses. Their prompt-level **e-process**, calibrated on benign traffic, accumulates evidence sequentially while (under a calibration-transfer assumption) "controlling the probability of any false alarm over an unbounded monitoring horizon"; it is evaluated on four models against a seed-blind attacker and a stronger seed-aware attacker that hides payload bits only in near-ties. Use it when a detector has to run indefinitely and you need a stated false-alarm guarantee rather than a per-token threshold.

**Open problem / evidence bar:** the same guarantee at frontier-model scale and production batching, against an adaptive attacker who knows the detector, with the overhead measured on real serving infrastructure.

## Low-trust compute verification (Cankaya, 2026)

Naci Cankaya, "A system overview for near-term, low-trust AI compute verification" (LessWrong, 2026-06-23, version 0.2 working draft). A reference architecture for verifying AI compute use under an arms-control-style agreement between rival states:

- **Evidence capture:** network taps (optionally memory pinging) record what workloads ran. The verifier receives only cryptographic commitments (signed hashes); the prover keeps the plaintext.
- **Evidence evaluation:** the verifier challenges a random subset of committed records, which are evaluated in an air-gapped environment (plan A) or with zero-knowledge proofs once those mature (plan B), and released only in a pre-agreed disclosure format.
- **Design goals:** retrofittable to existing hardware from off-the-shelf components; no mutually trusted chips; physical security is a prerequisite.

**When not to use it:** as a settled design. The author published it to draw out what it gets wrong, and invites critique from policy, security and engineering readers. Building and red-teaming one component, such as the tap-to-commitment path or the sampling scheme, is a concrete project.

## Auditor-in-a-Box: an LLM in a trusted execution environment as a third-party auditor (Rinberg, 2026)

Aliases: auditor in a box, auditor-in-a-TEE, trusted capable model environment, TEE auditing, privacy-preserving monitoring, ZDR-lite.

Roy Rinberg and Ben Penchas, "Auditor-in-a-Box: Tools for Third-Party Auditing" (LessWrong, 2026-07-28; written in Rinberg's voice). The scheme runs an open-weight large language model (LLM) inside a **trusted execution environment (TEE)**, a hardware-isolated processor region whose memory the host cannot read and whose loaded binary is measured and remotely attested. Two mutually distrustful parties sign a **Plan** (inputs, computation steps such as Python code and LLM calls, and the outputs to release), send their private data encrypted to the TEE's key, and each receives only the agreed outputs. The post proposes two near-term applications: **verifiably-scoped monitoring** ("ZDR-lite", a relaxation of zero data retention that lets a lab run safety monitoring while bounding what it may monitor *for*) and **recurring third-party auditing** of a lab's internal practice. Its threat model trusts the TEE hardware and attestation and trusts the LLM "to be a faithful classifier *within distribution*"; it does not assume either party refrains from trying to exploit the model.

Code: `RoyRin/auditor-in-a-TEE` (main), `RoyRin/auditor-in-a-TEE-webapp` and `RoyRin/auditor-in-a-TEE-deployer`, all with no licence file detected by the GitHub API and 1–3 stars as of 2026-10-14; a live demo is linked from the post, which describes it as ready to be "lightly poked and interrogated" but not for regular use. A short paper by Penchas, Rinberg and a collaborator was submitted to the TAIGR workshop.

**When not to use it:** as production infrastructure, or where code reuse needs a licence. **Open problem / evidence bar:** the post's mitigations for prompt injection against the in-box model (authorising several interchangeable models and choosing one at runtime with trusted randomness; each party placing its own uninspectable injection filter in front of the model) are design proposals; a measured attack-success rate against a fixed egress limit (for example a one-bit yes/no answer), with an adaptive adversary who can probe the same open-weight model offline, would show how much the scheme leaks.

## How strong is the evidence for loss of control? (Uuk et al. 2026)

Uuk, Koivula, Pacchiardi, Gipiškis, Caroli & Horton, "Assessing the Empirical Evidence for Loss of Control from Agentic General-Purpose AI" (arXiv:2610.25241, 2026-10-18). Motivated by the EU General-Purpose AI Code of Practice, which lists loss of control as a systemic risk to assess, the authors grade 19 empirical studies across eight threat-model properties (for example strategic deception, situational awareness, autonomous replication) on **construct, content and external validity**. Central finding: the evidence "supports a judgment of loss of control as 'weakly plausible'" (plausibility here means strength and direction of evidence, not a probability). "No study clears the validity thresholds for a stronger judgment that a property is present; a single study clears them only for a negative-direction judgment (against situational awareness)." Validity gaps are widespread, "particularly in external validity", and for the most dangerous properties the authors argue high external validity "may be structurally unachievable under responsible research practices".

**Use it as:** a checklist of what a policy reader will discount in a scheming, deception or self-replication eval; pair it with Apollo's four claims for a scheming safety case (no training incentive, no propensity in evals, no attempts during internal deployment, reasoning would be detected), summarized in [`model-organisms.md`](model-organisms.md#scheming-propensity-in-realistic-settings-anti-scheming-training-and-inability-safety-cases-20242026). **When not to cite it as current:** it grades a fixed set of 19 studies (the arXiv comment says it was first posted on SSRN on 28 May 2026), and the authors note that "empirical assessments may systematically lag behind the capability frontier"; check its reference list before treating a newer result as already weighed.

## What does a first deliverable look like?

A working verifier for one narrow claim (for example, "these outputs came from this model under this sampling configuration"), measured against an adversary who knows how it works, with its false-positive rate and overhead reported. The [`project-shapes.md`](../start-here/project-shapes.md) catalog has a "Governance / verification paper" shape.

---

Last verified: 2026-10-20. 2026-10-20: arXiv:2610.25241 and 2610.11843 abstracts from arxiv.org abs pages; quotes exact. Verification pass 2026-10-20: 2610.11843 PDF read (authors' affiliations, attack regimes, Rinberg et al. as the baseline it builds on); Apollo's four claims re-read from LessWrong LZGuqoYHphet9sfZs. 2026-10-14: Auditor-in-a-Box post (LessWrong uWYk7MM9hAf9GEbGe) via GraphQL; the three `RoyRin/auditor-in-a-TEE*` repositories via the GitHub API (licence, stars, last push); the TAIGR paper and the live demo were not opened. Earlier, 2026-10. arXiv 2407.14981 (title, authors, abstract, and the table of contents of the v2 HTML for the capacity/target taxonomy and section numbers) and 2511.02620 (abstract, including the <0.5% / <0.01% / >200x figures and the code URL) checked via the arXiv API and HTML. Repository `RoyRin/inference_verification_for_model_weight_exfiltration` checked with `gh api`. LessWrong post fgvmKqRGvBteKeDoc (Cankaya) fetched via GraphQL; the summary follows its introduction and system overview.
