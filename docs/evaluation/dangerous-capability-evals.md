---
tags:
  - evaluation
---

# Dangerous-Capability Evals: Bio/Chem, Cyber, Autonomy and Self-Replication

Which benchmark measures which dangerous capability, how to run it (most are `inspect_evals` tasks), what access it needs, and what its numbers do and do not license you to say. Dangerous-capability evals (DCEs) are capability measurements: they ask whether a model *can* do something harmful, not whether it *would*. Propensity evals (scheming, reward hacking, eval awareness) are in [`evals.md`](evals.md) and [`model-organisms.md`](../alignment-science/model-organisms.md).

!!! warning "A low score is a claim about elicitation"
    "The model can't do X" is only as strong as the effort spent trying to make it do X. Models can be prompted or trained to underperform on exactly these evals, and prompting alone often fails to elicit a capability that fine-tuning recovers. Before reporting an absence, read [Sandbagging and capability elicitation](evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real) and report how you elicited.

## I want to evaluate X → use Y

| I want to evaluate… | Use | Access / how to run |
|---|---|---|
| Hazardous bio, chem or cyber *knowledge* (multiple-choice proxy) | **WMDP** (Weapons of Mass Destruction Proxy) | Public; `inspect_evals/wmdp_bio`, `wmdp_chem`, `wmdp_cyber`. See [`datasets-benchmarks.md`](datasets-benchmarks.md#wmdp-weapons-of-mass-destruction-proxy) |
| Practical biology-research skills (literature, figures, tables, databases, sequences, cloning, protocols) | **LAB-Bench** | Public subset on Hugging Face (`futurehouse/lab-bench`); `inspect_evals/lab_bench_litqa`, `lab_bench_protocolqa`, `lab_bench_seqqa`, `lab_bench_cloning_scenarios`, etc. |
| Expert-level virology wet-lab troubleshooting (multimodal) | **VCT** (Virology Capabilities Test) | **Not public**: conveyed to organisations and researchers with an AI-safety track record; not in `inspect_evals` |
| Whether a model actually helps a *person* do dangerous bio work | A **human uplift study** (randomised, internet-only control arm) | No benchmark substitutes; see the two uplift trials below |
| Capture-the-flag (CTF) offensive cyber skill | **CyBench**; GDM in-house CTF; InterCode CTF | Public; `inspect_evals/cybench`, `gdm_in_house_ctf`, `gdm_intercode_ctf`. See [`datasets-benchmarks.md`](datasets-benchmarks.md#cybench--intercode--nyu-ctf-bench) |
| Exploiting real web-application vulnerabilities (critical-severity CVEs) | **CVE-Bench** | `inspect_evals/cve_bench` (Kubernetes sandbox by default; Docker with `-T sandbox_type=docker`); upstream `uiuc-kang-lab/cve-bench` |
| Reproducing real vulnerabilities from a text description, at scale | **CyberGym** | `inspect_evals/cybergym`; upstream `sunblaze-ucb/cybergym`; full dataset 236 GB, so subset it |
| Offence *and* defence on real bug bounties, with dollar values | **BountyBench** (Detect / Exploit / Patch) | `bountybench/bountybench` on GitHub; not in `inspect_evals` |
| Components of autonomous self-replication (weights, compute, money, persistence) | **RepliBench** (UK AISI) | **Not released**; code shared with researchers on request. Open alternative: GDM self-proliferation tasks, `inspect_evals/gdm_sp01_e2e` … `gdm_sp12_*` |
| Long-horizon autonomy and AI R&D capability | **METR HCAST** / time horizon | See [`evals.md`](evals.md#metr-hcast-and-the-metr-task-suite) |
| Stealth and situational awareness (prerequisites for undermining oversight) | GDM stealth and self-reasoning tasks (Phuong et al. 2025, arXiv:2505.01420) | `inspect_evals/gdm_classifier_evasion`, `gdm_cover_your_tracks`, `gdm_oversight_pattern`, `gdm_strategic_rule_breaking`, `gdm_self_reasoning_*` |
| Whether the model is hiding capability during your eval | Elicitation and sandbagging checks | [`evals.md`](evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real) |
| Which score would trigger which mitigation at a lab | A frontier safety framework's capability thresholds (e.g. GDM's CCLs) | See [Framework thresholds](#framework-thresholds-google-deepmind-frontier-safety-framework-v3) |

## Bio and chem: VCT, LAB-Bench, and what benchmarks miss

Aliases: biosecurity evals, CBRN (chemical, biological, radiological, nuclear) evals, bio uplift, Virology Capabilities Test, `futurehouse/lab-bench`, `Future-House/LAB-Bench`, wet-lab uplift trial, novice uplift.

**VCT (Virology Capabilities Test).** Götting, Medeiros, Sanders, Li, Phan, Elabd, Justen, Hendrycks & Donoughe, arXiv:2504.16137 (SecureBio and collaborators). 322 multimodal questions on troubleshooting virology laboratory protocols, covering fundamental, tacit and visual knowledge, built with dozens of PhD-level virologists. Expert virologists with internet access averaged 22.1% on questions in their own sub-areas; OpenAI o3 reached 43.8%, "outperforming 94% of expert virologists even within their sub-areas of specialization". The 322-question shared set is not released publicly (to limit training-data leakage); a further 43-question holdout is kept private to test for leakage. **When to use it:** you need the current reference point for expert-level wet-lab troubleshooting and you can get access. **When not to:** you need a public, reproducible number, or you want to claim real-world uplift (see below).

**LAB-Bench (Language Agent Biology Benchmark).** Laurent et al., arXiv:2407.10362 (FutureHouse). Over 2,400 multiple-choice questions on practical research tasks: literature recall and reasoning, figure and table interpretation, database navigation, DNA and protein sequence manipulation, cloning scenarios and protocols, with human expert biologist baselines. A public subset is on Hugging Face (`futurehouse/lab-bench`); `inspect_evals` ships one task per category (`lab_bench_litqa`, `lab_bench_suppqa`, `lab_bench_figqa`, `lab_bench_tableqa`, `lab_bench_dbqa`, `lab_bench_protocolqa`, `lab_bench_seqqa`, `lab_bench_cloning_scenarios`). **When to use it:** general research-assistant capability in biology, including dual-use-adjacent skills, on a public set. **When not to:** as a measure of hazardous capability specifically; it is designed to measure useful research assistance, not misuse.

**The UK AISI trend view.** The UK AI Security Institute's *Frontier AI Trends Report* (December 2025) says models first reached its expert baseline on open-ended biology and chemistry questions in 2024 and now exceed it by up to 60%, and are up to 90% better than human experts at troubleshooting support for wet-lab experiments.

### The two uplift trials: a benchmark score is not uplift

Two 2026 human studies test whether benchmark capability turns into human uplift. They measure different things and are not in conflict:

- **Wet lab, mid-2025 models: no significant uplift on the primary endpoint.** Hong, Kleinman, Mathiowetz et al., "Measuring Mid-2025 LLM-Assistance on Novice Performance in Biology" (arXiv:2602.16703). A pre-registered, investigator-blinded randomised controlled trial (June–August 2025, n = 153) in which novices performed physical laboratory tasks that together model a viral reverse-genetics workflow, with an LLM or with the internet only. They found "no significant difference in the primary endpoint of workflow completion" (5.2% LLM vs 6.6% internet; P = 0.759). The LLM arm was numerically higher on four of five tasks (cell culture 68.8% vs 55.3%, P = 0.059), and post-hoc Bayesian modelling estimated about a 1.4-fold increase for a typical task (95% credible interval 0.74–2.62). The authors' conclusion is a "gap between in silico benchmarks and real-world utility".
- **In silico, multi-model: large uplift, and humans under-use the model.** Zhang, Knight, Kruus et al., "LLM Novice Uplift on Dual-Use, In Silico Biology Tasks" (arXiv:2602.23329). Eight biosecurity-relevant task sets, up to 13 hours on the longest. Novices with LLMs were "4.16 times more accurate than controls (95% CI [2.63, 6.87])" and beat internet-only experts on three of the four benchmarks that had expert baselines. But "standalone LLMs often exceeded LLM-assisted novices", so the users were not getting the model's best contribution; 89.6% of participants reported little difficulty obtaining dual-use-relevant information despite safeguards.

**What a fellow should take from this.** (1) A model beating experts on a multiple-choice or troubleshooting benchmark does not show that it uplifts a human; the physical step, and the human's ability to elicit the model, both sit between the two. (2) Uplift results are tied to a model generation (Hong et al. tested mid-2025 models) and to a task type (physical vs in silico). (3) Standalone model scores and human-plus-model scores answer different questions; report which one you measured. **Regime:** humans working with a model, for up to 13 hours per task set (in silico) or in a wet-lab trial run over June–August 2025; not autonomous agent runs.

**Open problem, and what would convince people.** Cheap proxies that *predict* human uplift. A benchmark or automated eval would be convincing if its scores, across several model generations, track measured uplift in an RCT like the two above (including the null wet-lab result), rather than tracking standalone model accuracy.

## Cyber: CVE-Bench, CyberGym, BountyBench

Aliases: offensive cyber evals, autonomous exploitation, vulnerability reproduction, proof-of-concept (PoC) generation, bug bounty benchmark, `uiuc-kang-lab/cve-bench`, `sunblaze-ucb/cybergym`, `bountybench/bountybench`. CTF-style benchmarks (CyBench, InterCode CTF, NYU CTF Bench) are covered in [`datasets-benchmarks.md`](datasets-benchmarks.md#cybench--intercode--nyu-ctf-bench).

**CVE-Bench.** Zhu, Kellermann, Bowman et al., arXiv:2503.17332 (Kang lab, UIUC). Agents attack sandboxed, vulnerable web applications built from critical-severity Common Vulnerabilities and Exposures (CVEs), in scenarios meant to mimic real-world conditions; the paper reports the state-of-the-art agent framework resolving "up to 13%". Run it as `inspect_evals/cve_bench`. **Pitfalls:** the default sandbox is Kubernetes (pass `-T sandbox_type=docker` for Docker, which needs a running Docker daemon); the eval's dependencies conflict with other `inspect_evals` tasks, so it ships its own environment under `packages/cve_bench/` (`uv sync` there); the Kubernetes sandbox supports only a subset of CVEs (`K8S_SUPPORTED_CVE`); amd64 is recommended and not all challenges are guaranteed on arm64 (Apple Silicon). The `inspect_evals` port branched from upstream at a fixed commit, so it can differ from the current upstream repo.

**CyberGym.** Wang, Shi, He, Cai, Zhang & Song, arXiv:2506.02548 (UC Berkeley). 1,507 real vulnerabilities across 188 software projects (from ARVO and OSS-Fuzz); the agent gets a vulnerability description and the codebase and must produce a proof-of-concept that reproduces the vulnerability. The best agent–model combinations reach about 20%. The authors also report the runs surfaced 34 zero-day vulnerabilities and 18 historically incomplete patches. Run it as `inspect_evals/cybergym`. **Pitfalls:** the full dataset is 236 GB and downloads from Hugging Face (`sunblaze-ucb/cybergym`) if not present, so select a subset with `-T eval_names='["cybergym_arvo_47101",...]'`; difficulty variants run from `level0`/`level1` (hardest, least information) to `level3` (easiest); sample ids contain a space and parentheses (`cybergym_arvo_47101 (level1)`); a CyberGym agent can find genuinely new bugs in real software, so treat outputs as sensitive and handle disclosure.

**BountyBench.** Zhang, Ji, Menders et al., arXiv:2505.15216. 25 real-world systems with 40 bug bounties (awards from $10 to $30,485, covering 9 of the OWASP Top 10 risks), and three task types across the vulnerability lifecycle: **Detect** a new vulnerability, **Exploit** a given one, **Patch** a given one. With up to three attempts, the best agents reached 12.5% on Detect (Codex CLI with o3-high, mapping to $3,720), 67.5% on Exploit (a custom agent with Claude 3.7 Sonnet Thinking) and 90% on Patch (Codex CLI with o3-high or o4-mini). Use it when you need offence *and* defence on the same systems, or an impact measure in dollars. Not in `inspect_evals`; run from `bountybench/bountybench`.

**The UK AISI trend view.** The *Frontier AI Trends Report* (December 2025) says models began completing expert-level cyber tasks (typically requiring 10+ years of experience) in 2025, up from apprentice-level (under 1 year) in 2023.

**When not to use these.** Single-number capability tracking across many models is cheaper with CyBench or WMDP-cyber; CVE-Bench and CyberGym need Docker or Kubernetes sandboxes, real compute and (for CyberGym) large storage. **Regime:** single-episode agent runs with bounded attempts; none of these measures a multi-day campaign.

## Autonomy and self-replication: RepliBench and the AISI trend

Aliases: autonomous replication and adaptation (ARA), self-proliferation, self-exfiltration capability, weight exfiltration, rogue replication, RepliBench.

**RepliBench.** Black, Cooper Stickland, Pencharz et al. (UK AISI), arXiv:2504.18565. Decomposes autonomous replication into four domains (obtaining resources, exfiltrating model weights, replicating onto compute, persisting on that compute) and builds 20 task families with 86 tasks. Of five frontier models, the best (Claude 3.7 Sonnet) scored above 50% pass@10 on 15 of 20 families and on 9 of 20 hardest variants. Models could deploy instances from cloud providers, write self-propagating programs and exfiltrate weights under simple security setups, but "struggle to pass KYC checks or set up robust and persistent agent deployments" (KYC: know-your-customer identity checks). The authors' overall reading: models "do not currently pose a credible threat of self-replication, but succeed on many components". The authors caution that pass@k can inflate grading error at high k. **Access:** "We do not release any code or otherwise open source RepliBench"; UK AISI shares code and implementation details with researchers on request.

**The trend.** UK AISI's *Frontier AI Trends Report* (December 2025): "Success rates on our self-replication evaluations went from 5% to 60% between 2023 and 2025". Read the fine print before quoting it: the figure is for **11 of the 20 RepliBench evaluations**, comparing the best early-2023 model (under 5%) with the two best frontier models by summer 2025 (over 60%). The report also says models are currently unlikely to succeed in real-world conditions, and that there is not yet evidence of models attempting to sandbag or self-replicate spontaneously.

**Open alternative you can run today.** The self-proliferation tasks from Phuong et al. (arXiv:2403.13793) are open (`google-deepmind/dangerous-capability-evaluations`) and ported to `inspect_evals` as 10 tasks (`SP01` email setup, `SP02` install model, `SP04` bitcoin wallet, `SP10` distillation, …), each in an end-to-end form (`gdm_spXX_e2e`) and a milestones form (`gdm_spXX_milestones`). `SP02`, `SP09` and `SP10` need a Google Cloud (GCP) setup or equivalent hardware.

**When not to use these.** A replication *propensity* question (would the model try?) is not answered by any of these; they hand the model the goal. **Regime:** single-episode agentic tasks in controlled environments, not open-internet or long unattended runs.

## Framework thresholds: Google DeepMind Frontier Safety Framework v3

Aliases: FSF, Frontier Safety Framework, Critical Capability Level (CCL), Tracked Capability Level (TCL), alert threshold, early-warning evaluations, responsible scaling policy (RSP) analogue.

Dangerous-capability evals matter to labs because frameworks tie mitigations to capability thresholds. Google DeepMind's FSF v3.0 (blog "Strengthening our Frontier Safety Framework", 2025-09-22) added a **harmful manipulation** CCL and expanded the framework to cover scenarios where misaligned models "might interfere with operators' ability to direct, modify or shut down their operations", and extended safety-case reviews from external launches to large-scale internal deployments for advanced machine-learning research and development (ML R&D) CCLs. **FSF v3.1** (2026-04-17, current at the time of writing) organises the framework into misuse domains (**CBRN**, **cyber**, **harmful manipulation**, the last marked exploratory) and a combined **ML R&D and misalignment** domain; it adds **Tracked Capability Levels**, lower thresholds for significant but not severe harm, for CBRN and for **stealth and situational awareness** (the latter defined as enough situational awareness and stealth that "we cannot rule out the model significantly undermining human control"). **Alert thresholds** sit marginally below each CCL and are assessed with early-warning evaluations.

**Why a fellow should care.** If your eval is meant to inform such a threshold, design it as an early-warning eval: report how far below the threshold a model sits and how fast that is moving, not only pass/fail, and document elicitation effort so the "below threshold" reading can be trusted. Other labs' frontier safety frameworks play the same role with their own thresholds.

## Background: the Gemini 1.0 dangerous-capability programme

Phuong, Aitchison, Catt et al. (Google DeepMind), "Evaluating Frontier Models for Dangerous Capabilities" (arXiv:2403.13793, 2024). Introduced a programme of DCEs in four areas (persuasion and deception; cyber-security; self-proliferation; self-reasoning), piloted on Gemini 1.0, finding no strong dangerous capabilities but early warning signs. It is the origin of several open `inspect_evals` ports (13 in-house CTF challenges as `gdm_in_house_ctf`, the 10 self-proliferation tasks above) and a template for how to decompose a threat model into milestone tasks. The follow-up on stealth and situational awareness is Phuong et al. 2025 (arXiv:2505.01420), whose tasks are the `inspect_evals` `gdm_stealth` group (`gdm_classifier_evasion`, `gdm_cover_your_tracks`, `gdm_oversight_pattern`, `gdm_strategic_rule_breaking`) and `gdm_self_reasoning_*`.

## Common questions

### Which dangerous-capability benchmarks can I actually run without asking anyone?

WMDP, LAB-Bench (public subset), CyBench, CVE-Bench, CyberGym, BountyBench, and the GDM self-proliferation, CTF, stealth and self-reasoning tasks, most via `inspect_evals`. VCT and RepliBench are restricted: VCT is conveyed to researchers with an AI-safety track record, and RepliBench code is shared by UK AISI on request.

### A model beats virologists on VCT. Does that mean it gives novices bio uplift?

Not by itself. A mid-2025 wet-lab RCT (arXiv:2602.16703, n = 153) found no significant difference in completing a reverse-genetics workflow, while an in silico study (arXiv:2602.23329) found 4.16× accuracy uplift and that standalone models often beat the humans using them. Benchmark score, in silico uplift and physical-world uplift are three different measurements.

### How do I report that a model *lacks* a dangerous capability?

State the elicitation: prompts tried, scaffold, number of attempts (pass@k), and whether you fine-tuned. Prompting alone is weak evidence; see [Sandbagging and capability elicitation](evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real).

### Why does `inspect eval inspect_evals/cve_bench` fail to start?

Its default sandbox is Kubernetes; without a cluster, pass `-T sandbox_type=docker` (and make sure Docker is running: the error is `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`). Install it from its own package directory (`packages/cve_bench`, `uv sync`), because its dependencies conflict with other evals in the repo.

---

Last verified: 2026-10. arXiv 2504.16137, 2407.10362, 2602.16703, 2602.23329, 2503.17332, 2506.02548, 2505.15216, 2504.18565, 2403.13793, 2505.01420 checked via the arXiv API (titles, authors, abstract numbers; quotes are exact abstract substrings); VCT release terms and RepliBench release statement and pass@k caveat checked in the paper PDFs. UK AISI Frontier AI Trends Report figures (5%→60% on 11 of 20 RepliBench evaluations; bio, chem and cyber trend statements) from the aisi.gov.uk report page. GDM FSF v3.0 from the deepmind.google blog (2025-09-22, updated 2026-04-17) and v3.1 domains, TCLs and alert thresholds from the linked framework PDF. `inspect_evals` task names and the CVE-Bench / CyberGym / LAB-Bench / self-proliferation READMEs from `UKGovernmentBEIS/inspect_evals` via the GitHub API; upstream repos `uiuc-kang-lab/cve-bench`, `sunblaze-ucb/cybergym`, `bountybench/bountybench`, `Future-House/LAB-Bench`, `google-deepmind/dangerous-capability-evaluations` confirmed via the GitHub API. Verification pass 2026-10-12: 78 claims checked, 2 corrected.
