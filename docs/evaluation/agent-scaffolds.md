---
tags:
  - evaluation
  - oversight
---

# Agent Scaffolding for Capability and Safety Evals

Tooling for running language models as agents — multi-turn loops with tool use, memory, planning, sandboxed execution. This is what powers most current dangerous-capability evals (cyber, AI R&D, autonomous SWE, persuasion).

## At a glance

| You want… | Use |
|---|---|
| Standard agent eval, sandboxed, modern UX | **Inspect AI** built-in `react()` agent + tools |
| Use an external agent framework (LangChain, OpenAI Agents SDK, Pydantic AI) inside an eval | **Inspect Agent Bridge** |
| Run an external agent CLI (Claude Code, Codex CLI, Gemini CLI, Kimi Code, OpenCode, Mini SWE Agent) as the agent under test | **`inspect-swe`** package (Meridian Labs) |
| Long-horizon task needing subagents, persistent memory and planning | **`deepagent()`** in `inspect_ai.agent` (built on `react()`) |
| Run Harbor-format agent tasks (containerised tasks, e.g. `aider_polyglot`) inside Inspect | **`inspect-harbor`** (v1.0.0) |
| Audit alignment against the *real* Claude Code / Codex CLI / Gemini CLI scaffold, not a simulated one | **Petri Dish** (`petri-dish`; see [`inspect-ecosystem.md`](inspect-ecosystem.md)) |
| Watch an agent while it runs and flag or block actions (monitors, control protocols) | **Inspect Sentinel** (`inspect-sentinel` 0.1.x on PyPI, early; see [`inspect-ecosystem.md`](inspect-ecosystem.md)); METR's pre-execution **`action_monitor`** approver (`METR/inspect-agents`) |
| Run an agent eval that needs the live internet, or check that yours cannot reach it | See [Running agent evals with internet access](#running-agent-evals-with-internet-access) |
| Sandboxed shell / cyber-style task | **Inspect Sandboxing Toolkit** (`docker` built in; `k8s` via `inspect-k8s-sandbox`) |
| Run agent evals with no local Docker daemon (laptop, Slurm node) | **`inspect-sandboxes`**: `sandbox="daytona"`, `"e2b"` or `"modal"` — see [Sandbox providers and containment](#sandbox-providers-and-containment) |
| Give each sample a full virtual machine (kernel-level or container-escape tasks) | `ec2`, `proxmox` or `vagrant` sandbox providers — see [Sandbox providers and containment](#sandbox-providers-and-containment) |
| Check that the container you trust actually contains a capable agent | **SandboxEscapeBench** (UK AISI) — see [Test your containment](#test-your-containment-sandboxescapebench) |
| METR-style long-horizon tasks | **HCAST** / RE-Bench task code, now **archived and deprecated** (2026-10-20), plus the METR Task Bridge; METR's Vivaria and Task Standard are also archived — see [METR tasks on Inspect](#metr-tasks-on-inspect-vivaria-and-the-task-standard-are-archived) |
| Run Inspect eval sets at scale on your own AWS account | **Hawk** (`METR/hawk`, `hawk` on PyPI) |
| Lightweight agent loop (no eval framework) | **smolagents** (HuggingFace) |
| Build-from-scratch reference | OpenAI Agents SDK, Pydantic AI, LangGraph |

## Inspect AI agents (the default)

Aliases: `inspect_ai.agent.react`, `inspect_ai.solver.basic_agent` (older API), "the Inspect ReAct agent", "Inspect agents". `inspect-ai` on PyPI, `UKGovernmentBEIS/inspect_ai` on GitHub (UK AI Security Institute).

**What it is.** Inspect AI provides:
- **`react()` agent** — a built-in ReAct (Reason+Act) loop (the paradigm from Yao et al. 2022, "ReAct: Synergizing Reasoning and Acting in Language Models", arXiv:2210.03629) that handles model calls, tool dispatch, and termination conditions.
- **Tool primitives** — `bash`, `python`, `text_editor`, `web_search`, `computer` (computer use), plus custom tools and MCP tools. (`web_browser()` is **deprecated** as of `inspect_ai` 0.3.272, 2026-09-28: it logs a warning and will be removed.)
- **`deepagent()`** — a batteries-included agent for long-horizon tasks, built on `react()`: subagent delegation (`research()`, `plan()`, `general()`, optionally dispatched in the background), a persistent `memory()` tool that survives context compaction, a `todo_write()` planning tool, and an opinionated system prompt. The Inspect docs report no performance difference between `react()`, `deepagent()` and `claude_code()` on shorter hard benchmarks (Cybench, Terminal Bench 2.0), so reach for it only when tasks really run long.
- **Multi-agent primitives** — agents calling agents, or competing/cooperating agents.
- **Sandboxes** — separate the model's inference from the environment where tool calls execute.
- **Agent Bridge** — drop in agents written in LangChain / OpenAI Agents SDK / Pydantic AI with minimal glue.

**When to use it:**
- Almost any new agent eval in 2026.
- You want results comparable to other AISI / Anthropic / OpenAI / METR safety work — Inspect logs are the standard format.
- You need sandboxing for security-sensitive evals.

**When *not* to use it:**
- You're not running an eval — building a production agent is different territory (LangGraph, OpenAI Agents SDK, etc.).
- You want a pre-built "research" agent (deep research style) — Inspect's primitives are more eval-shaped.

**Pitfalls:**
- **Tool-call-loop infinite loops.** A model can call the same tool repeatedly. Set `message_limit` (and `token_limit` / `time_limit`) on the `Task` or `eval()` call; `react()` has no message-cap argument.
- **"Token-of-doom" prompt growth.** Long agent traces accumulate context; you'll hit context limits on weaker models. Truncation strategies matter.
- **Tool errors silently terminate poorly.** A failing tool can produce an empty observation; the model then reasons about nothing. Log all tool exit codes.
- **Sandbox setup.** Docker sandbox needs the daemon running; k8s sandbox needs cluster access. Errors look like `cannot connect to docker daemon`. See the Inspect sandboxing toolkit blog post for setup.
- **Computer-use evals are flaky.** Browser-based / GUI agents have reproducibility issues — DOM changes, timing. Consider running each task multiple times.
- **Score variance is high.** Agent runs vary a lot. Run k=5+ for any safety claim.
- **The default "continue" message can read as blanket approval (matters for propensity / reward-hacking evals).** In `react()` and the older `basic_agent()` the tool loop ends only when the model calls `submit()`; if a turn has no tool call, Inspect sends a user message. The `react()` default (`DEFAULT_CONTINUE_PROMPT` in `inspect_ai/agent/_types.py`, unchanged as of 0.3.278) is ``Please proceed to the next step using your best judgement. If you believe you have completed the task, please call the `{submit}()` tool with your final answer.``; `basic_agent()` sends only the first sentence; Petri's auditor prompt recommends the same sentence for a target that makes no tool call. Zhong (LessWrong, 2026-09-11, "Default continuation message in Inspect and Petri could be problematic"; Zhong is first author of ImpossibleBench) reports that a model can read this as explicit permission after it stopped out of caution: Gemini 3.7 Flash wrote in its CoT that "the user has explicitly given me the go-ahead" and then modified the tests it had been told not to modify. On ImpossibleBench (Oneoff-SWEbench split), among nudged samples 14% cheated with the `basic_agent` default versus about 1% with each of three alternatives (the `react()` default, a submit-reminder-only message, an empty message); the `react()` default seems to work mainly because it reminds the model of `submit()` (Gemini called it immediately 88% of the time versus 44% without the reminder). Exposure differs by model — in the original ImpossibleBench runs Qwen3-Coder was nudged in 99% of samples, Claude Sonnet 3.7 almost never — so default nudging can inflate one model's cheating rate relative to another's (the post flags o4-mini). The author also notes this default sits underneath other work: Gram (Lindner, Krakovna & Farquhar, arXiv:2605.30322, a Petri-based sabotage eval) reports that its single sabotage in 500 Gemini 3.1 Pro Preview samples began right after this exact message. **Mitigation:** `react(tools=[...], on_continue="If you are finished, call submit() tool with your final response.")` (`on_continue` accepts a `str`, or a callable returning `bool | str | AgentState`), log which message you used, or drive the real product via `inspect-swe`. Symptom to search for: a CoT that quotes "please proceed … using your best judgement" before an out-of-bounds action.
- **Refusals end or poison agent runs silently.** Use `fail_on_refusal` (`--fail-on-refusal`, since `inspect_ai` 0.3.264) to raise `ModelRefusalError` instead of letting a refusal become an incorrect score, and `react(retry_refusals=...)` to retry content-filter stops.

## Inspect Sandboxing Toolkit

Aliases: "Inspect sandboxing", `inspect_ai.util.sandbox`, sandbox environment, sandbox provider, `k8s_sandbox` package (`inspect-k8s-sandbox` on PyPI).

**What it is.** Inspect's sandboxing layer separates the model's inference from the environment where tool calls execute. Two environment types are built in, and the Inspect sandboxing docs ("Environment Binding", checked 2026-10-14) list seven external providers in the table (its prose says six), and `inspect-sandboxes` adds an eighth:
- **`docker`** (built in) — single-machine Docker / Docker Compose.
- **`local`** (built in) — direct subprocess on your machine, no isolation (only for fully-trusted tasks).
- **`k8s`** — Kubernetes-backed sandbox from `inspect-k8s-sandbox` (`UKGovernmentBEIS/inspect_k8s_sandbox`, v0.14.0); scales to many parallel agents.
- **`daytona`, `modal`** (cloud sandboxes, `inspect-sandboxes`; the same package also ships **`e2b`**, which is not in Inspect's table), **`ec2`, `proxmox`, `vagrant`** (one virtual machine per sample) and **`openshell`** (NVIDIA OpenShell policy sandboxes). Compared in [Sandbox providers and containment](#sandbox-providers-and-containment).

**When to use it:**
- Cyber tasks (CTF challenges).
- Software engineering tasks (SWE-bench, HCAST coding).
- Any task where you'd be uncomfortable running model-generated code on your laptop.

**Pitfalls:**
- **`docker` sandbox needs Docker socket access** — on rented GPU boxes, you may need to install Docker first. On some sandboxed clouds (Modal, etc.), Docker-in-Docker doesn't work. If you have no Docker daemon at all, a cloud provider (`daytona`, `e2b`, `modal` from `inspect-sandboxes`) runs each sample remotely while Inspect stays local; see [Sandbox providers and containment](#sandbox-providers-and-containment).
- **Network isolation — verify it, do not assume it.** Inspect's *auto-generated* Docker Compose config sets `network_mode: none`, but a compose file or `ComposeConfig` you supply **replaces** it, and then the container gets Docker Compose's default project network *with* outbound access unless you add `network_mode: none` yourself. The setting only restricts processes **inside** the container: custom tools, agents or scorers running outside the sandbox, and tools like `web_search()`, can still reach the internet. Inspect's docs describe no verification procedure, so test it: from inside a running sample try `curl` / DNS to an external host and confirm failure. This matters: in 2026 Anthropic reported (first report 2026-07-30, full post 2026-09-09) four incidents in which Claude models in third-party CTF evaluations reached real third-party systems (including publishing a malicious package to the real PyPI, 15 installations) after a misconfiguration left internet access open although the model was told it had none, and UK AISI reported (2026-08-04) 19 out-of-scope agent actions across 10 of 122 runs in a cyber-range evaluation where internet access had been deliberately enabled; AISI now treats granting internet access as a decision that "must be actively justified rather than a default" and says "good containment should not depend on the model choosing not to test its boundaries." Sources: Anthropic, "alignment assessment of cybersecurity incidents" (anthropic.com/news, 2026-09-09); AISI, "Incident Report: unsanctioned agent behaviour during cyber testing" (aisi.gov.uk, 2026-08-04). Later reports (Anthropic 2026-10-09 on public web benchmarks; OpenAI's GET-only proxy and DNS cases in RL training sandboxes) and a precautions table: [Running agent evals with internet access](#running-agent-evals-with-internet-access).
- **Fictional names in your environment must be *unclaimable*, not merely unused.** Alkur (LessWrong, 2026-08-25) points out that checking that an invented company or package name does not exist is the wrong test: an unused name in a public registry is an available resource a capable agent can claim (in one reported incident a model found a dangling reference to a nonexistent PyPI package in a fictional company's onboarding document, built it and uploaded it). Use reserved namespaces where they exist — RFC 2606 reserves `.test`, `.example`, `.invalid` and `example.com`; RFC 5737 reserves documentation IPv4 blocks — and where they do not (PyPI, npm) register a placeholder yourself. Reserved TLDs can themselves tip off the model that it is in a test, so the alternative is to register your own domains. Closing the naming hole is not a substitute for closing the network.
- **Writable host mounts are now refused (0.3.280, 2026-10-14; breaking).** A Docker sandbox whose compose file bind-mounts a host directory writably (`./data:/data`) now fails before the sandbox starts. Reason, from the PR (`UKGovernmentBEIS/inspect_ai` #5830): an agent with host write access can rewrite compose files or plant symlinks that give *later* samples host access. Fixes, in order of preference: mount read-only (`./host-dir:/container-dir:ro`, which needs Docker Engine 25+, Compose 2.24+ and Linux kernel 5.12+ on the Docker host), copy inputs in with `Sample.files`, or use a Docker-managed volume. The opt-in `x-inspect_docker_sandbox: {unsafe_allow_writable_host_mounts: true}` applies to *all* services in the file and is exactly the escape path the change closes, so it is a poor fit for misalignment, control or cyber evals. The check covers mounts only: per the PR, a socket mounted read-only (`/var/run/docker.sock:/var/run/docker.sock:ro`) still gives full Docker API access, and `privileged`, `cap_add: SYS_ADMIN` and `devices:` give host access without any writable mount. Symptom: an old compose file that ran yesterday errors at sandbox start after `pip install -U inspect-ai`.
- **Upgrade for the Docker `read_file()` fix (0.3.281, 2026-10-15; security).** Before 0.3.281, Docker `read_file()` copied a file out with `docker compose cp`, which unpacks an archive the agent controls onto the host *before* any check. With Docker Compose older than 5.4.0, "a crafted archive can write outside the extraction directory (CVE-2026-17106), a potential sandbox escape" (the PR notes this was not demonstrated through `read_file()`), and an oversized or sparse file could fill the host disk ("reading a sparse file wrote 229 MB to host disk in 2 s"; PR `UKGovernmentBEIS/inspect_ai` #5829). From 0.3.281 the file is streamed and read in memory up to the size limit. If you evaluate adversarial agents, run `inspect-ai` ≥0.3.281 (which needs Python ≥3.11; on 3.10, pip and uv silently resolve to 0.3.280); Docker Compose ≥5.4.0 alone closes the CVE but not the disk-fill problem.
- **Concurrent agents in one sample share tool state unless scoped (0.3.282, 2026-10-19; breaking).** `memory()`, `bash_session()`, `web_browser()` and `skill()` key their state by `instance`, which defaults to `None`, so several agents running at once in one sample (for example four `deepagent()` copies) shared one memory and one shell. `tool_state_scope(name)` in `inspect_ai.util` gives each agent run inside it its own state; an explicit shared instance (`memory(instance="team")`) is still shared on purpose. Breaking: instance names beginning with `@` are now reserved for scopes, so `memory(instance="@notes")` raises `ValueError` outside its scope (PR #5861). Multi-agent results from before this change may include unintended cross-agent leakage through shared tools.
- **Sandbox tools no longer run as root by default (0.3.264, 2026-09-16).** `bash_session()`, `text_editor()`, `exec_remote()` and sandboxed MCP servers run as the sandbox's default user; pass `user="root"` to restore the old behaviour. Symptom: new `Permission denied` errors in an image you did not change. Images must also provide `/bin/sh` and coreutils (including `zstd` for `.tar.zst` checkpoints) in the system `bin`/`sbin` directories, not `/usr/local`.
- **Cleanup.** Failed sandbox containers can accumulate. Periodic `docker system prune` on long-running boxes.
- **k8s sandbox needs cluster + RBAC.** Not lightweight — only worth it for parallel agent runs at scale.

## Sandbox providers and containment

Aliases: Inspect sandbox providers, sandbox environment types, `inspect-sandboxes` (`meridianlabs-ai/inspect_sandboxes`), Daytona sandbox, E2B sandbox, Modal sandbox, `inspect-k8s-sandbox`, `inspect_ec2_sandbox`, `inspect_proxmox_sandbox`, `inspect_vagrant_sandbox`, `inspect-openshell-sandbox`, NVIDIA OpenShell, VM sandbox, "run Inspect without Docker", container escape, sandbox escape.

**Why this section exists.** The sandbox is the thing standing between a capable agent and your machine, your credentials and the internet. Providers differ in *isolation level* (a container shares the host kernel; gVisor intercepts syscalls; a virtual machine (VM) has its own kernel), in *network default* (some block egress unless you open it, some allow it unless you close it) and in whether they run multi-container Docker Compose files. The 2026 incident reports (pitfall above on network isolation) are the reason to pick deliberately.

### Provider table (as of 2026-10-14)

| Provider (`sandbox=`) | Package | Isolation | Network default | Multi-service compose | Needs |
|---|---|---|---|---|---|
| `docker` | built in (`inspect-ai` 0.3.280) | container (shared host kernel) | **none** with Inspect's auto-generated config; **open** (Compose default network) as soon as you supply your own compose file without `network_mode: none` | yes | Docker daemon |
| `local` | built in | **none** (subprocess on your machine) | your machine's network | n/a | nothing; trusted tasks only |
| `k8s` | `inspect-k8s-sandbox` 0.14.0 (UK AISI) | container pods | **blocked** by the built-in Helm chart's Cilium network policies; a domain allowlist opens it. With `networkPolicy.enabled: false` the chart "restricts nothing" | yes (compose is converted) | Kubernetes cluster with Cilium, RBAC |
| `daytona` | `inspect-sandboxes` 0.6.1 (Meridian Labs) | cloud sandbox; compose runs Docker-in-Docker (DinD) | **depends on your Daytona subscription tier** (tiers 1–2 restrict to essential services such as Docker Hub, PyPI, GitHub and AI providers; tiers 3–4 full internet); compose `network_mode` maps to `network_block_all`; the DinD VM always has network | yes (DinD) | Daytona account + `DAYTONA_API_KEY` |
| `e2b` | `inspect-sandboxes` 0.6.1 | cloud sandbox; compose via DinD | not stated on the provider docs page — test it | yes (DinD) | E2B account + `E2B_API_KEY` |
| `modal` | `inspect-sandboxes` 0.6.1 | cloud sandbox on gVisor (beta VM runtime available) | **open** (`block_network` defaults to `False`); `network_mode: none` or `x-modal: {block_network: true}` closes it | **no** (raises `ValueError`) | Modal account (`python3 -m modal setup`); GPUs via `x-modal.gpu` |
| `ec2` | `inspect_ec2_sandbox` (`inspect-ec2-sandbox` 0.1.1, UK AISI) | full VM per sample | set by your VPC subnet and security group (instances must reach SSM, SSM Messages, S3, EC2 Messages) | no Dockerfile/compose (VM images) | AWS account, VPC, S3 bucket, instance profile (a reference CDK stack ships in the repo) |
| `proxmox` | `inspect_proxmox_sandbox` (UK AISI) | full VM per sample | by default a VM **can reach the Proxmox host's own services** (API on port 8006, SSH); host firewall isolation and an optional egress lockdown are configured on the host by the provisioning scripts, "not by this library" | no Dockerfile/compose (VMs) | Proxmox 9+ host (9.2+ recommended) |
| `vagrant` | `inspect_vagrant_sandbox` (`jasongwartz`, alpha, no license file) | full VM per sample on any Vagrant hypervisor (tested: vagrant-qemu on Apple Silicon, vagrant-libvirt) | set by your `Vagrantfile` | no (Vagrantfile) | Vagrant + a hypervisor plugin |
| `openshell` | `inspect-openshell-sandbox` 0.1.0 (community, alpha) | NVIDIA OpenShell sandbox: kernel-enforced file, syscall and network policy (Landlock per the Inspect docs) | **no policy is applied unless `policy:` is set** in `openshell.yaml` | n/a (`openshell.yaml`) | OpenShell CLI + local gateway |

Sources: the Inspect sandboxing docs' provider table; each provider's README or docs page. Isolation and network columns summarise what those pages say; they are not an independent security assessment.

### Which provider do I use?

| I want… | Use | Why not the others |
|---|---|---|
| An ordinary single-container agent eval on my own box | `docker`, with `network_mode: none` in any compose file you write | Cloud and VM providers cost more and add setup |
| Many parallel samples on shared infrastructure | `k8s` | Needs a cluster; overkill for a fellow's laptop |
| No Docker daemon at all (laptop with no Docker, Slurm node without Docker) | `modal` (single container, GPUs) or `daytona` / `e2b` (multi-service compose) | Samples run on a third-party cloud |
| A real kernel per sample (kernel exploits, container-escape tasks, root-level tooling) | `ec2` (cloud) or `proxmox` / `vagrant` (own hardware) | A container shares the host kernel |
| Fine-grained per-agent file/syscall/network policy, credentials injected only for approved endpoints | `openshell` (experimental) | The community provider is weeks old |

### `inspect-sandboxes`: Daytona, E2B and Modal

`inspect-sandboxes` (`meridianlabs-ai/inspect_sandboxes`, PyPI 0.6.1, 2026-10-09, Python ≥3.12, MIT; its `daytona` and `modal` are listed in the official Inspect provider table, `e2b` is not) registers three cloud sandboxes. Each sample gets a fresh sandbox; the Inspect process stays on your machine. From its docs:

```bash
pip install inspect-sandboxes
python3 -m modal setup            # Modal; or: export DAYTONA_API_KEY=... / export E2B_API_KEY=...
```

```python
from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.solver import generate

task = Task(
    dataset=[Sample(input="What is 2+2?", target="4")],
    solver=[generate()],
    sandbox="modal",              # or "daytona", "e2b"
)
eval(task)
```

With no `Dockerfile` or `compose.yaml` next to the task, the provider's default image is used. **Modal's network is open by default**: the docs' `block_network` parameter defaults to `False`, and "`network_mode: none` blocks all network access; any other value (e.g. `bridge`) allows it." Put `network_mode: none` in your compose (or `x-modal: {block_network: true}`) for any eval where the agent must not reach the internet. Modal is single-service only: "Multi-service compose files raise a `ValueError` before sandbox creation", because Modal's default gVisor runtime blocks the networking Docker needs; use Daytona for multi-service compose.

**When *not* to use it:** evals whose data or model outputs must not leave your infrastructure (the sandboxes run on a third-party cloud); multi-container environments on Modal; any setting where you have not explicitly blocked the network and then tested that it is blocked.

### VM providers: EC2, Proxmox, Vagrant

`ec2` (`UKGovernmentBEIS/inspect_ec2_sandbox`), `proxmox` (`UKGovernmentBEIS/inspect_proxmox_sandbox`) and `vagrant` (`jasongwartz/inspect_vagrant_sandbox`) give each sample a whole virtual machine. Use them when the task needs a real kernel (kernel exploits, eBPF, Docker inside the sandbox) or when the threat model includes container escape. Installation, per the READMEs: `uv add inspect-ec2-sandbox`; `uv add git+ssh://git@github.com/UKGovernmentBEIS/inspect_proxmox_sandbox.git`; `uv add git+ssh://git@github.com/jasongwartz/inspect_vagrant_sandbox.git` (Vagrant is labelled "alpha and unstable").

**Pitfall — a Proxmox host is not isolated from its guests by default.** The README: "By default a sandbox VM can reach the Proxmox host's own services — the API (`pveproxy`, port 8006), SSH, etc. ... This is **configured on the host at provisioning time, not by this library**". The provisioning scripts install, but do not activate, an egress lockdown (`touch /etc/inspect-proxmox-egress-lockdown`). **When *not* to use VM providers:** an ordinary single-container agent eval, where Docker is enough and far cheaper.

### NVIDIA OpenShell and the `openshell` provider

**OpenShell** (`NVIDIA/OpenShell`, Apache-2.0, release v0.1.4 on 2026-10-13, PyPI `openshell`) is an agent runtime: per its README "it instruments the kernel to enforce policy on every file access, system call, and network connection at runtime", and "Agents never see real credentials; OpenShell adds them only to requests bound for approved endpoints." The community Inspect provider `inspect-openshell-sandbox` (`32bitsret/inspect-openshell-sandbox`, PyPI 0.1.0, MIT) exposes it as `sandbox="openshell"`, configured by an `openshell.yaml` next to the task. Install, from the READMEs:

```bash
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
uv pip install inspect-openshell-sandbox
```

**Pitfalls:** "No policy is applied unless `policy:` is set", so a bare `openshell.yaml` gives you a sandbox without the policy that is the reason to use OpenShell. The provider's status line reads "0.1.0, alpha", tested on Docker Desktop on Apple Silicon with Inspect 0.3.266 (Linux hosts untested). OpenShell collects anonymous telemetry; set `OPENSHELL_TELEMETRY_ENABLED=false` on the gateway to disable it. **When *not* to use it:** results you need to stand behind next month — treat the provider as experimental.

### Test your containment (SandboxEscapeBench)

Aliases: SandboxEscapeBench, SANDBOXESCAPEBENCH, `UKGovernmentBEIS/sandbox_escape_bench`, container-escape eval, "can my model break out of Docker?".

**What it is.** Marchand, O Cathain, Wynne et al. (UK AISI), "Quantifying Frontier LLM Capabilities for Container Sandbox Escape" (arXiv:2603.02277). An Inspect capture-the-flag (CTF) suite with a nested design: "Each VM contains a container which serves as the pseudo-sandbox for the model, with the goal being to break out and retrieve a flag from the VM host." VMs run on `ec2` (default) or `vagrant`. 18 scenarios rated 1/5 to 5/5: privileged container, mounted Docker socket, `--pid=host`, `CAP_SYS_ADMIN` / `CAP_SYS_MODULE` / `CAP_DAC_READ_SEARCH`, writable hostPath on `/etc`, cgroup release agent (CVE-2022-0492), runc overwrite (CVE-2019-5736), kernel bugs (Dirty COW, Dirty Pipe, BPF and packet-socket privilege escalation), and Kubernetes escapes including runc CVE-2024-21626 on k3s. Each scenario has normal, `hint` and `solution` variants and a human-baseline mode. The abstract's finding: "when vulnerabilities are added, LLMs are able to identify and exploit them". Files carry a canary GUID.

```bash
# from the README
uv run inspect eval scenarios/docker_socket/task.py --model openai/gpt-5.2 -T sandbox=vagrant
uv run inspect eval scenarios/docker_socket/task.py --model openai/gpt-5.2 -T variant=solution   # check the exploit path works
uv run inspect eval scenarios/docker_socket/task.py --solver human_cli --limit 1                  # human baseline
```

**How to use it for your own eval.** The cheapest containment test is still the manual one (`curl` and a DNS lookup from inside a running sample; see the FAQ below). SandboxEscapeBench answers the next question: does the *misconfiguration class* your environment has (a mounted socket, an extra capability, an old kernel) fall to the model you are evaluating? A worthwhile check before trusting a sandbox with a frontier agent is to run the scenarios matching your own compose file's privileges.

**When *not* to use it:** on your laptop's Docker or a shared cluster node — run it only on the VM backends it was built for. Kernel-exploit scenarios need pre-built Packer images, and fallback mode pulls images at runtime and can hit Docker Hub's unauthenticated rate limit (`toomanyrequests`). Its scores measure escape capability against planted vulnerabilities, not the security of your particular stack.

## Running agent evals with internet access

Aliases: live-internet agent evals, open-web evals, browsing benchmarks (BrowseComp, DeepSearchQA, OSWorld, LABBench2, Humanity's Last Exam (HLE) with tools), real-world side effects of evals, unintended model actions, "persistence", egress control, GET-only proxy, DNS filtering, DNS exfiltration, "can my eval hurt someone?".

**Why this section exists.** Several public agent benchmarks are designed to run against the live web, and many fellows run agents in sandboxes they believe are offline. Two sets of lab reports from September–October 2026 describe lab models acting as agents, in evaluations, internal use and training sandboxes, taking real actions on third-party systems when a task could not be completed as given. If your agent can reach the internet, its side effects are real even when the task is fictional.

**What Anthropic reported (evaluations and internal use).** "Investigating unintended model actions in our evaluations and internal use" (anthropic.com/research/investigating-unintended-model-actions, 2026-10-09, corrected 2026-10-12) groups the cases into four behaviours. The report says "Most are forms of persistence, in which Claude, when it cannot complete a task as given, works around a restriction instead of stopping":

- **Exploiting a third party's server.** When a university-hosted scientific tool returned an error, a model used SQL or command injection on the university's server to finish the analysis. Seen "on DeepSearchQA and BrowseComp (both public web research evaluations), on LABBench2 (a public biology research benchmark), and during internal evaluations."
- **Submitting real forms.** A non-frontier research model whose practice copy of a government form failed to load "navigated to the website where the real form is normally hosted and submitted the form there" (the report names neither form nor agency; becausecurious, LessWrong 2026-10-15, matches this case to a State Department spokesperson's statement, quoted by the Philadelphia Inquirer, of "19 non-immigrant visa applications in August and one application in May", all "incomplete"). Claude Haiku 4.5, generating example tasks on random web pages, submitted an invented tip through a police department's homicide-tip form; the department's statement dates the submission to July 18, 2026 and says Anthropic told it the incident was discovered on September 28 (via becausecurious, LessWrong 2026-10-10). Seen "on OSWorld (a public computer use evaluation), on Odysseys (a long-horizon task evaluation), and during internal usage."
- **Reaching gated data.** A model read access tokens from a local government map site's browser settings file and queried the server directly; another obtained a state agency's dashboard token to avoid a data fee. Seen "on Humanity's Last Exam … and during internal usage."
- **Evading a fetch-tool limit.** Anthropic saw "several models, including Claude Opus 5 and Claude Mythos 5," use free URL-shortening services to get around a URL-length cap on the fetch tool.

Remediation, from the report: Anthropic had already turned off live internet for "some high-risk and cybersecurity evaluations" and has "now decided to expand that to include all our internal evaluations" until its monitoring reliably catches these behaviours; "Some of the public evaluations we no longer run; others we have moved to their offline versions, or rebuilt them so that their tasks do not reach live websites"; fetch tools were restricted; and automatic detection-and-blocking tooling now runs on most of its evaluations (it blocked all the reported cases when tested on them). The authors also write that "some of these failures could have been avoided if the evaluation questions had more clearly stated what was in and out of scope for the exercise, including the targets, permitted actions, and network boundaries".

**What OpenAI reported (training sandboxes with restricted internet).** OpenAI's *Misalignment Reports and Notices* series (alignment.openai.com/misalignment-reports/) documents how partial restrictions failed:

- **A GET-only restriction is not containment.** In "Circumventing internet restrictions through an external browser" (reinforcement-learning (RL) training, incident 2026-06-16, report updated 2026-10-15), a model told "Internet access is enabled only for HTTP GET requests" used permitted GETs to make an external browser service send the blocked POST requests, read the result back as an image via optical character recognition (OCR), then "developed a reusable helper that returned response text through a forwarding service and callback mailbox".
- **DNS is an egress channel.** In "An agent used DNS to reach an external chatbot", an agent found that the training environment's own resolver answered real lookups and used a public DNS delegation service to send questions to a third-party chatbot and receive answers, through "insufficient DNS filtering in its training sandbox". OpenAI "added blocking controls at two independent layers" and found its monitor had under-rated other external-DNS cases.
- **Public secrets are reachable resources.** In "Using a funded test cryptocurrency wallet without authorization" (GPT-5.6 Sol family, coding task, report updated 2026-10-15), a model asked to deploy contracts on the Sepolia test network derived keys from well-known developer recovery phrases ("The result reported 362 addresses checked"), spent that account's test ether (ETH) on deployment fees, and "did not disclose that it had selected a funded account through a public recovery phrase or spent that account's balance" in its final answer.

**Precautions for your own agent evals.** Each row answers a failure in the reports above or in the earlier incident reports in the network-isolation pitfall under [Inspect Sandboxing Toolkit](#inspect-sandboxing-toolkit); the offline-variant, scope-statement and transcript-scanning rows follow the reports' own remediations, and the rest is general egress-control practice rather than a prescription from the reports:

| Risk | Precaution |
|---|---|
| A benchmark that runs on the live web (BrowseComp, DeepSearchQA, OSWorld, web-enabled HLE) | Prefer an offline, cached or rebuilt variant; if none exists, decide explicitly whether the run needs live internet at all |
| The prompt leaves scope ambiguous | State targets, permitted actions and network boundaries in the task text: what the agent may access, and that it must stop and report when blocked |
| "The agent was told not to" | Make real targets **unreachable**, not merely forbidden: block egress at the network layer, not only in the prompt or the tool wrapper |
| A method allow-list (GET-only, read-only fetch) | Assume any request that can reach an acting service (a headless-browser API, a webhook, a form relay, a URL shortener) can act on your behalf; allow-list destinations, not methods |
| DNS left open | Test egress at the DNS layer as well as HTTP: from inside a running sample, resolve an external name and query a public resolver, and confirm both fail |
| Public credentials and test funds | Keep well-known mnemonics, default dev keys and funded test wallets out of reach; treat any secret findable on the public internet as usable by the agent |
| Side effects you did not see | Scan every transcript afterwards for real-world actions (form submissions, account creation, payments, requests to non-allow-listed hosts), for example with METR's `internet_leaves_tracks_scanner` ([`inspect-ecosystem.md`](inspect-ecosystem.md#metr-scanners-ready-made-judges-for-eval-awareness-reward-hacking-and-broken-environments)); do not rely on the agent's final answer, which may omit them |
| Fictional names in the environment | Use reserved or self-registered names (see the unclaimable-names pitfall under [Inspect Sandboxing Toolkit](#inspect-sandboxing-toolkit)) |

**When live internet is the point** (a browsing-capability measurement that has no offline version), general practice is to run it on an allow-listed proxy that logs every request, with a human or automated reviewer reading the request log before results are reported, and budget for the possibility that a sample must be discarded because of what it did. Report in the paper that the eval had live access. **Open problem:** neither report gives a validated way to let an agent browse the open web while guaranteeing it takes no unsanctioned actions; a method that blocks the published cases *and* holds up against a model told to find a new route would be a real contribution.

## Inspect Agent Bridge

Aliases: "Agent Bridge", `inspect_ai.agent.agent_bridge()`, `inspect_ai.agent.sandbox_agent_bridge()`. (The older bare `bridge()` / `inspect_ai.agent.bridge` name is deprecated — use `agent_bridge()` for in-process or `sandbox_agent_bridge()` for sandboxed/any-language agents.)

**What it is.** A wrapper that lets you run agents written in **LangChain**, **OpenAI Agents SDK**, **Pydantic AI**, or other frameworks inside Inspect — Inspect handles dataset/scoring/logging, the external framework handles agent logic.

**When to use it:**
- You already have an agent built in another framework.
- You want to evaluate a specific agent product (someone's released LangChain agent, etc.).

**When *not* to use it:** Building from scratch — start with `react()` directly.

**Pitfall:** Tool definition formats differ across frameworks. Bridge mostly handles this but check that all tools register correctly.

## Inspect external agent CLIs

Aliases: "external agent", `inspect-swe`, `meridianlabs-ai/inspect_swe`, running Claude Code / Codex CLI / Gemini CLI as the model under test.

**What it is.** The **`inspect-swe`** package (by Meridian Labs, `meridianlabs-ai/inspect_swe`, v0.2.71 on PyPI as of 2026-09-17 — a separate package, not part of core `inspect_ai`) exposes external agentic CLIs as Inspect agents: `claude_code()` (Anthropic's Claude Code), `codex_cli()` (OpenAI's Codex CLI), `gemini_cli()` (Google's Gemini CLI), `kimi_code()` (Moonshot AI's Kimi Code), `opencode()` and `mini_swe_agent()`. Agents run inside the sample sandbox via `sandbox_agent_bridge()` and their model API calls are proxied back to Inspect, so any model, token/time limits and transcript logging work as normal. Useful for benchmarking the agentic products themselves, not just the underlying models.

**When to use it:** Evaluating "Claude Code on SWE-bench" rather than "Sonnet 4.6 on SWE-bench."

**Pitfall:** External CLIs have their own prompts, tool stacks, and version schedules. The agent's behavior depends on the CLI version, not just the model. Pin and log both (since 0.2.71 `"stable"` / `"latest"` are resolved to the concrete version that will be installed — record it). Version 0.2.71 also fixed prompt-cache misses and an **eval-awareness leak from a system prompt regenerated on resumed turns**, so results from older versions on resumed samples may differ. Driving the real CLI is also the cleanest way to avoid Inspect's default `react()` continue-message nudge (above).

## Inspect Harbor

Aliases: `inspect-harbor` on PyPI (v1.0.0, 2026-09-23), `meridianlabs-ai/inspect_harbor`, "Harbor tasks in Inspect", `harbor()`, `aider_polyglot`. Docs: <https://meridianlabs-ai.github.io/inspect_harbor>.

**What it is.** [Harbor](https://harborframework.com/) is a framework for building and evaluating agents in containerised environments; Inspect Harbor runs Harbor task datasets as ordinary Inspect tasks. Requires Python ≥ 3.12 and Docker (or another Inspect sandbox provider).

```bash
pip install "inspect-harbor>=1.0"
```

```python
from inspect_ai import eval
from inspect_harbor import aider_polyglot, harbor

eval(aider_polyglot(), model="openai/gpt-5-mini")
# or any dataset by name/version:
eval(harbor(package_name="aider/aider-polyglot", package_ref="latest"), model="openai/gpt-5-mini")
```

**When to use it:** you want a Harbor-format agent benchmark with Inspect's logging, limits and scoring, or you want Scout to analyse Harbor transcripts (Scout also ingests Harbor's ATIF trajectory format). **When *not* to use it:** the benchmark already exists in `inspect_evals` — use that, it is the maintained, versioned port; or you do not have Docker.

**Pitfall:** `package_ref="latest"` moves; pin a version (`name@version`) for anything you will report.

## METR tasks on Inspect (Vivaria and the Task Standard are archived)

Aliases: HCAST, `METR/hcast-public`, `METR/public-tasks`, RE-Bench on Inspect (`METR/inspect-tasks-public`), METR Task Bridge (`METR/inspect-metr-task-bridge`, `mtb/bridge`), `metr_agents/react` (`METR/inspect-agents`), Hawk / Inspect-Hawk (`METR/hawk`, `hawk` on PyPI), `vivaria` (METR's former eval infra, `METR/vivaria`), METR Task Standard (`METR/task-standard`), `inspect-action`. See [`evals.md`](evals.md) for the dataset and time-horizon side.

**Status correction (checked 2026-10-14).** METR has moved from its own infrastructure to Inspect. `METR/vivaria`, `METR/task-standard` and `METR/inspect-action` are all **archived** on GitHub. The Task Standard README: "METR is no longer maintaining the Task Standard. Instead, we use [Inspect](https://inspect.aisi.org.uk/) to define tasks." The Vivaria README: "While Vivaria remains functional and open source, we are ramping down new feature development." Treat older write-ups (including earlier versions of this page) that present Vivaria as METR's live infrastructure as out of date.

**Second status change (2026-10-20): METR's public task code is deprecated.** `METR/RE-Bench`, `METR/hcast-public`, `METR/public-tasks` and the Inspect port `METR/inspect-tasks-public` were all archived by 2026-10-20 with a DEPRECATED banner (RE-Bench README: "The RE-Bench tasks are now deprecated. We're no longer accepting contributions or bug reports for them."; hcast-public: "The HCAST tasks are now deprecated."; public-tasks: "The METR public task suite is now deprecated."). They still clone and run, but take no fixes, so pin a commit and expect known bugs to stay. METR's time-horizon page (metr.org/time-horizons) now says "This page is no longer actively updated" (last updated 2026-09-08), so do not cite it as a live leaderboard. No public successor task suite had been announced as of 2026-10-20. `METR/inspect-agents` (agents, scanners, the action monitor) and `METR/hawk` are **not** archived.

**What replaced it:**
- **Hawk** (`METR/hawk`, "Inspect-Hawk", releases v3.7.1 / v3.7.2 on 2026-10-07, PyPI `hawk`, Python ≥3.13, MIT). Runs Inspect eval sets from one YAML config on AWS: isolated Kubernetes (EKS) pods per eval, sandbox pods under Cilium network policies, a managed LLM proxy, results in a PostgreSQL warehouse and a web viewer; it also runs Inspect Scout scans over past transcripts. The README says it is "designed for teams that need to run evaluations regularly and at volume". CLI against an existing deployment: `uv tool install "hawk[cli]"`, `hawk login`, `hawk eval-set path/to/your.eval-set.yaml`, `hawk web`; `hawk local eval-set` runs the same config on your machine for debugging. Deploying your own needs an AWS account, a domain name, Pulumi, Docker, Python, Node.js and `uv`. **When *not* to use it:** a fellow project without that AWS setup — use `inspect eval-set` or Inspect Flow ([`inspect-ecosystem.md`](inspect-ecosystem.md)); read Hawk as the reference for how METR runs Inspect at scale.
- **METR's agents and scanners as Inspect packages** (`METR/inspect-agents`, MIT). `packages/agents` (`metr-agents`) provides `--solver metr_agents/react`, a react agent with METR's task conventions (an `intermediate_score` tool where needed, the right tool user, answer delimiters). `packages/scanners` (`metr-scanners`) provides Scout scanners for eval awareness, reward hacking, sandbagging and broken environments; see [`inspect-ecosystem.md`](inspect-ecosystem.md) and [`evals.md`](evals.md#judge-calibration-and-eval-result-tooling). The agents package also ships **`metr_agents/action_monitor`**, an Inspect approver that "scores every tool call an agent makes during an eval before it is executed" on 0–10 and escalates calls at or above `threshold` (default `3.0`) to a human approver (`metr_agents/human`, which must be listed last); defaults include the `v5-provenance` prompt, `on_error: escalate` and `history_tokens: 700000`, and per-agent `chains` pick the monitor models ("it is recommended to use monitor models from the same developer as the agent model", to prevent cross-lab leakage). The docs' quickstart runs it through Hawk (`hawk eval-set run`, then `hawk acp <eval-set-id>` to answer escalations; Hawk ≥2.4.0). The docs recommend running one sample at `threshold: 0`, where every call is escalated, to confirm the monitor is wired up (`packages/agents/docs/action_monitor.md`). **When *not* to use it:** when nobody is available to answer escalations (unanswered calls are rejected after `approval_timeout_minutes`), or as a measured control protocol (it is an operational guard, not a calibrated monitor; see [`ai-control.md`](../oversight-and-control/ai-control.md)).
- **RE-Bench on Inspect** (`METR/inspect-tasks-public`, **archived and deprecated 2026-10-20**; GitHub reports license NOASSERTION while the README says MIT). A work-in-progress Inspect port of METR's RE-Bench AI R&D tasks, with Docker image build scripts and static per-task GPU allocation. From the README: build images with `python re_bench/build_images/build_images.py`, then `uv run inspect eval ai_rd_rust_codecontests_inference/ai_rd_rust_codecontests_inference --model anthropic/claude-3-7-sonnet-latest`. The README is frank about gaps: "The evals are currently configured to run on nodes with 8xH100 GPUs"; scores come out lower than METR's ("We haven't put much effort into elicitation"); and cheating routes are open ("in the rl task, the agent could have a look at the "held-out" set and train on it directly. We don't stop the agent from doing this").
- **METR Task Bridge** (`METR/inspect-metr-task-bridge`, no license file). Runs legacy Task-Standard task-family images inside Inspect, e.g. `inspect eval mtb/bridge -T image_tag=count_odds-0.0.1 --sample-id hard`, including with Inspect's human agent (`--solver human_cli`) for human baselining.

**When to use these:**
- Long-horizon agentic evals in the style of METR's published results, accepting that the public task code is frozen.
- Time-horizon measurement against METR's published numbers (the time-horizons page has said it is no longer actively updated since 2026-09-08 and its last added measurement is dated 2026-05-08, so compare against a dated snapshot, not a live leaderboard).

**When *not* to use them:** you don't need METR comparability — `inspect_evals` has many simpler agent benchmarks; you need numbers directly comparable to METR's RE-Bench results (the Inspect port reports lower scores and unfixed cheating routes); you do not have 8×H100 nodes for RE-Bench; or you need a maintained suite where reported bugs get fixed (the public HCAST, RE-Bench and example-task repos are archived).

**Pitfalls:**
- **HCAST / RE-Bench tasks expect specific environments.** Ports differ from the originals in images, GPU allocation and elicitation; record which port and commit you ran.
- **Compute cost.** Long-horizon tasks burn tokens and tool-call time. Single full-suite runs are expensive.
- **Pin commits.** None of `inspect-tasks-public`, the Task Bridge or `inspect-agents` publishes GitHub releases; pin a commit hash in your lockfile. The archived repos (`RE-Bench`, `hcast-public`, `public-tasks`, `inspect-tasks-public`) accept no issues or pull requests, so a bug you find stays in; document any local patch you apply.

## smolagents

Aliases: `smolagents` on PyPI, `huggingface/smolagents`, "HF's small agent library".

**What it is.** A small, opinionated library from HuggingFace for building agents. Code-acting agents (the model writes Python and executes it) are a core feature. ~1000 lines.

**When to use it:**
- Quick prototype of a research agent that's not an eval.
- You want a minimal, readable agent loop to learn from.

**When *not* to use it:** You want eval logging, sandboxes, scoring — use Inspect.

## OpenAI Agents SDK

Aliases: `openai-agents` on PyPI, `openai/openai-agents-python`.

**What it is.** OpenAI's official agent framework — handoffs, guardrails, tracing.

**When to use it:** Building production-shaped agents on OpenAI; comparing your code to OpenAI's "official" patterns.

**When *not* to use it:** Eval research — Inspect.

## LangGraph / LangChain

For completeness: heavyweight in the broader LLM-app ecosystem. Used in production agent products. For safety research, Inspect is generally preferred for its eval-first design and standard log format.

**When to use them:** You have a production deployment, or are evaluating someone else's LangGraph agent.

## Pydantic AI

Aliases: `pydantic-ai` on PyPI.

**What it is.** Newer, type-driven agent framework from the Pydantic team.

**When to use it:** Production / library-development style agents with strong typing.

## Cross-cutting agent eval pitfalls

- **Agent reproducibility is harder than non-agent.** Tool errors, timing, sampling stochasticity, environment state. k=5+ runs minimum.
- **"Capability uplift" claims need careful baselines.** Did the model do better with the agent scaffold, or just with the extra context? Run baselines without tools.
- **Tool whitelisting.** Giving an agent shell access in an eval is a real attack surface. Sandbox properly. Don't run cyber-eval agents on a box with credentials. Containment is testable rather than something to assume: SandboxEscapeBench measures whether a model exploits common container misconfigurations ([Test your containment](#test-your-containment-sandboxescapebench)).
- **The harness is part of the model's safety.** Usama, Nisa & Jung (arXiv:2609.27542; code `Usama1002/deleting-the-trace`) found that whether an identical tool-call generation fires can be decided by the harness's tool-call parser (a truncation-tolerant regex fired calls a strict one dropped; two parsers shipped for one Gemma agent gave opposite outcomes on the same greedy generations), and that injected chat-template control tokens can delete an open model's reasoning before a tool call. Log the raw rendered prompt and the parser version; details in [`ai-control.md`](../oversight-and-control/ai-control.md#monitor-robustness-what-breaks-blocking-and-held-out-monitors).
- **One run per task is not enough to call a difference.** TRACE (Gaonkar, arXiv:[2610.11678](https://arxiv.org/abs/2610.11678), 2026-10-08) reports that "Identical reruns flip 15-36% of task outcomes" on τ²-bench tasks with four LLM agents, and Jia et al. (arXiv:[2610.24048](https://arxiv.org/abs/2610.24048), 2026-10-16) that "single-run labels of thinking agents disagree with a rerun up to 35% of the time" on AgentDojo. When a score moves after you change the harness, re-score the *unchanged* trajectories with the new scorer first (TRACE's test of whether the scoring rule, not the agent, changed), then compare repeated paired runs. Statistics for this: [`eval-statistics.md`](eval-statistics.md).
- **An auto-optimised harness mostly overfits.** Ding et al., "Harness-Delta Attribution" (arXiv:[2610.22466](https://arxiv.org/abs/2610.22466), 2026-10-15; 11 executor models, three harness-evolution frameworks): in the 21 settings with significant search-set gains, "overfitting and test-time scaling account for 54% and 14% of the gain on average", and "search-set gains often fail to transfer to held-out tasks". If you tune prompts, skills or tools around a fixed model, report held-out tasks and a compute-matched baseline. Huang et al., AM-Bench (arXiv:[2610.18090](https://arxiv.org/abs/2610.18090); code `s4-lab-cuhksz/AM-Bench`; 5 models × 4 harnesses, 20,160 runs on underspecified Terminal-Bench-style tasks) add that "rankings depend on model × harness pairings and the evaluation criterion", so a model ranking from one harness need not hold in another. (Not the same benchmark as the agentic-misalignment AM-Bench in [`datasets-benchmarks.md`](datasets-benchmarks.md).)
- **Score what you mean.** "Did the agent solve the task" is not the same as "did the agent's actions cause the task state to be solved" (sometimes the env solves itself; sometimes the agent's tools claim success without it being true). Verify via final state, not via agent self-report.
- **Log the full transcript.** Token-level — every tool call, every observation, every model message. Inspect View does this; if you roll your own, replicate that level.
- **Context overflow degrades silently.** When the trace exceeds context, models start losing the original task. Log context length per turn; warn if approaching limit.
- **Prompt sensitivity.** Agent system prompts shift behavior dramatically. Note which scaffold prompt you used; share it.
- **Honesty: agents will sometimes lie to themselves in chain-of-thought.** Don't take CoT as ground truth for what the agent "knows" or "wants."
- **Eval-aware models.** As agent evals proliferate, models may detect they're being evaluated and behave differently. See: Steering Evaluation-Aware Language Models (arXiv 2510.20487, 2025). Scaffold realism is one lever: auditing the target inside its *real* scaffold (Petri Dish) rather than a simulated system prompt and tools, combined with iterative critique refinement of the auditor's actions, is reported (author summary) to triple the realism win rate and substantially reduce unprompted verbalized eval awareness in Ahlqvist et al. (arXiv:2609.02302, 2026-09-02; absolute win rates stay low on some targets, e.g. Opus 4.8 2% to 6% with critique refinement) — see [`inspect-ecosystem.md`](inspect-ecosystem.md).
- **Scaffold nudges and grading text change the cheating rate.** The same model can cheat 0% or >50% depending on the continue message, whether the prompt says "only a win scores", and whether an escalation tool exists. Treat the scaffold prompt as part of the experimental condition and report it; details and numbers in [`evals.md`](evals.md#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate).
- **Agents grab unattended affordances.** Models rarely search for exploits unprompted (Valentine, LessWrong 2026-10-06: <1% of non-Grok rollouts even checked the `/grader/` directory that most of his environments contain, normally root-only; Grok did so in about 5%) but use what they have already thought of — and in the 2026 incidents above they used credentials, open networks and unclaimed names that the environment author never meant to expose. Audit the environment for anything reachable, not only for what the task intends.

## Cross-references

- Underlying eval framework: [`evals.md`](evals.md).
- Datasets / benchmarks for agent capability: [`datasets-benchmarks.md`](datasets-benchmarks.md).
- Compute / sandboxing infrastructure: [`compute.md`](../models-and-compute/compute.md).
- Multi-provider API (for the underlying model calls): [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md).
- AI Control protocols built on top of agent scaffolds (ControlArena, defer-to-trusted, etc.): [`ai-control.md`](../oversight-and-control/ai-control.md).
- Debate / scalable-oversight protocols built on top of multi-agent primitives: [`debate-scalable-oversight.md`](../oversight-and-control/debate-scalable-oversight.md).

---

## Common questions

### How do I write an Inspect AI agent?

Use the built-in `react()` agent + tools:
```python
from inspect_ai.agent import react
from inspect_ai.tool import bash, python

agent = react(tools=[bash(timeout=180), python(timeout=180)])
# Plug agent into a Task as the solver.
```
The `react()` agent handles ReAct (Reason+Act) loops, tool dispatch, and termination. For more control, hand-roll a solver that calls `generate()` and dispatches tools manually.

### Can I evaluate Claude Code (or Codex CLI / Gemini CLI) inside Inspect?

Yes — via the **`inspect-swe`** package (Meridian Labs, `meridianlabs-ai/inspect_swe`), which drives Claude Code, OpenAI's Codex CLI, Google's Gemini CLI, Kimi Code, OpenCode or Mini SWE Agent as the agent on a task (`claude_code()`, `codex_cli()`, `gemini_cli()`, `kimi_code()`, `opencode()`, `mini_swe_agent()`). Useful for benchmarking the *product* (with its prompts, tools, etc.) rather than just the underlying model. Pin both CLI and model versions.

### My `react()` agent started cheating right after it stopped calling tools. Why?

Probably the default continue message. When a turn has no tool call, Inspect sends ``Please proceed to the next step using your best judgement. If you believe you have completed the task, please call the `{submit}()` tool with your final answer.``, which a model can read as explicit approval after it had stopped out of caution (Zhong, LessWrong 2026-09-11; in his Gemini 3.7 Flash ablation the 14% cheating rate was with the shorter `basic_agent()` message, and the `react()` default measured ~1%, which he thinks is mainly because it also reminds the model to call `submit()`; Zhong suggests models may act on the "approval" instead when they are less sure the task is complete and so disinclined to call `submit()`). Pass `on_continue="If you are finished, call submit() tool with your final response."`, or a callable returning `bool | str | AgentState`, and report the message. See the pitfall under [Inspect AI agents](#inspect-ai-agents-the-default).

### How do I check that my sandbox really has no internet access?

`network_mode: none` in `compose.yaml` (the default in Inspect's auto-generated config) disables networking for processes *inside* the container; your own compose file replaces the default, and tools or scorers that run outside the container are unaffected. Run with `--no-sandbox-cleanup`, open a shell in the container (`docker exec -it <container-id> bash -l`), try `curl -sS --max-time 5 https://example.com` and a DNS lookup, and confirm both fail; also confirm `web_search()` is not in your tool list. Use reserved names (`.test`, `.invalid`, `example.com`) or names you have registered for anything fictional. On cloud providers the default differs: Modal is **open** unless you set `network_mode: none` or `x-modal: {block_network: true}`, and Daytona's egress depends on your subscription tier (see [Sandbox providers and containment](#sandbox-providers-and-containment)). See [Inspect Sandboxing Toolkit](#inspect-sandboxing-toolkit).

### My compose file stopped working after upgrading Inspect (writable host mount)

Since `inspect_ai` 0.3.280 (2026-10-14) Docker sandboxes refuse writable bind mounts of host directories, because an agent with host write access can rewrite compose files or plant symlinks for later samples. Change `./dir:/dir` to `./dir:/dir:ro` (needs Docker Engine 25+, Compose 2.24+, host kernel 5.12+), or copy inputs with `Sample.files`, or use a Docker-managed volume. `x-inspect_docker_sandbox: {unsafe_allow_writable_host_mounts: true}` restores the old behaviour for every service in the file; avoid it in any eval where the agent is the adversary. Read-only mounts do not protect sockets: `/var/run/docker.sock:...:ro` still gives full Docker API access. Details in the [Inspect Sandboxing Toolkit](#inspect-sandboxing-toolkit) pitfalls.

### Can I run sandboxed agent evals without Docker installed?

Yes. `pip install inspect-sandboxes` and set `sandbox="modal"`, `"e2b"` or `"daytona"`: each sample runs in a fresh cloud sandbox while Inspect runs locally. Modal is single-container only (multi-service compose raises `ValueError`) but supports GPUs; Daytona and E2B run multi-service compose via Docker-in-Docker. Close the network explicitly. See [Sandbox providers and containment](#sandbox-providers-and-containment).

### How do I test whether my model can escape the container I'm using?

Run the matching scenarios of **SandboxEscapeBench** (`UKGovernmentBEIS/sandbox_escape_bench`, arXiv:2603.02277) on an `ec2` or `vagrant` VM backend, e.g. `uv run inspect eval scenarios/docker_socket/task.py --model <model> -T sandbox=vagrant`, and first run `-T variant=solution` to confirm the exploit path works in your setup. Pick the scenarios that match your own environment's privileges (mounted Docker socket, extra capabilities, writable hostPath, old kernel). See [Test your containment](#test-your-containment-sandboxescapebench).

### What is Agent Bridge?

`agent_bridge()` (or `sandbox_agent_bridge()`) in `inspect_ai.agent` — a wrapper that lets you run agents written in **LangChain**, **OpenAI Agents SDK**, or **Pydantic AI** inside Inspect. Inspect handles dataset / scoring / logging; the external framework handles agent logic. Useful for evaluating an existing agent, less useful for building from scratch (just use `react()`).

### How do I sandbox shell tasks?

In your Inspect task: `Task(..., sandbox="docker")`. Docker daemon must be running. For multi-machine parallel agent runs, install `inspect-k8s-sandbox` and use `sandbox="k8s"` (the registry name in the Inspect provider table; the package is `k8s_sandbox`). For trusted tasks where you don't need isolation: `sandbox="local"` (subprocess only — only use when the task is fully trusted). For cloud or VM sandboxes, see [Sandbox providers and containment](#sandbox-providers-and-containment).

### How do I prevent my agent from looping forever or burning tokens?

`react()` itself takes no message cap (its signature is `name, description, prompt, tools, model, attempts, submit, on_continue, retry_refusals, compaction, truncation, approval, review` as of 2026-10). Put the limits on the `Task` or `eval()` call instead: `message_limit=` per sample, `token_limit=` for tokens, `time_limit=` / `working_limit=` for wall-clock. `attempts=` controls how many submissions the agent gets, not tool errors. Watch token usage in Inspect View; long agent traces over many samples balloon costs fast.

### What's the difference between LangGraph and Inspect for agents?

**LangGraph** is for production agent products (long-running, deployable, lots of integrations). **Inspect AI** is for *evaluations* (sample-level transcripts, scoring, comparable logs across providers). For a paper or research result, Inspect; for shipping an agent, LangGraph (or OpenAI Agents SDK / Pydantic AI). Use Inspect's Agent Bridge if you have a LangGraph agent and want to evaluate it.

### My agent task always succeeds in suspicious ways

Score what you mean: "task state achieved" not "agent self-reported success." Some environments solve themselves; some tools claim success without it being true. Use a separate scorer that verifies the *final state* of the environment, not just the agent's last message.

### How do I score agents that take many turns?

Each Inspect `Sample` produces a full `TaskState` with all messages, tool calls, observations, and the final answer. A `Scorer` consumes this and produces a `Score`. Common patterns: pass/fail on final answer correctness; subgoal-completion checklists; LLM-as-judge over the entire trajectory; environment-state checks at end.

### What is test-time compute / inference-time scaling?

Techniques that improve performance at inference by spending more compute *per query*, without changing weights. Examples: **best-of-N** (sample N completions, pick the best by an external scorer); **self-consistency** (sample N CoT completions, take majority answer); **tree of thoughts** (search over branching CoT continuations); long reasoning traces (o-series, DeepSeek-R1 style). For evals, you can implement best-of-N as a custom Inspect solver that samples k times and uses a scorer to pick.

### What is best-of-N sampling?

Sample N completions for the same prompt, then pick the highest-scoring one according to a scorer (reward model, verifier, or LLM-as-judge). A simple test-time-compute technique. Trades inference cost for output quality; useful for capability evals where you want to measure "what the model can do given more attempts." Not useful for safety evals where you care about typical behavior — it artificially inflates capability and can hide failure modes.

### What is self-consistency for chain-of-thought?

Sample N CoT completions at temperature > 0; for each, extract the final answer; take majority vote (Wang et al. 2022, "Self-Consistency Improves Chain of Thought Reasoning in Language Models", arXiv:2203.11171). Often improves accuracy on math / reasoning tasks. **For safety evals**: be cautious — self-consistency masks the rate of incorrect or harmful completions; report both with-and-without numbers if the eval has safety implications.

### What is tree of thoughts (ToT)?

A search-based test-time technique (Yao et al. 2023, "Tree of Thoughts: Deliberate Problem Solving with Large Language Models", arXiv:2305.10601): instead of one linear CoT, generate multiple candidate next-steps at each reasoning step, score them, expand the best ones. A more expensive but sometimes more effective inference scaling than self-consistency. Implementation is bespoke; not standardized in any safety-research library.

---

Last verified: 2026-10-20. (Additions 2026-10-20: "Running agent evals with internet access" from the Anthropic report "Investigating unintended model actions in our evaluations and internal use" (2026-10-09, page text), OpenAI misalignment reports on the external-browser, DNS and test-wallet cases (page text), and becausecurious's LessWrong posts for the police and State Department statements; METR task repos archived 2026-10-20 (GitHub API, READMEs) and metr.org/time-horizons notice; `action_monitor` docs in `METR/inspect-agents`; Inspect 0.3.281/0.3.282 sandbox changes from PRs #5829, #5861, #5862; arXiv 2610.11678, 2610.24048, 2610.22466, 2610.18090 abstracts.) Inspect AI agents and Agent Bridge active (`inspect-ai` 0.3.282). METR's Vivaria, Task Standard and inspect-action are archived; METR now runs Inspect via Hawk. (Additions 2026-10-14: sandbox provider table and "Which provider" guide from the Inspect sandboxing docs' Environment Binding table and each provider's README/docs (`inspect-sandboxes` 0.6.1 docs for Daytona/E2B/Modal network and compose behaviour; `inspect_k8s_sandbox` network-access doc; `inspect_ec2_sandbox`, `inspect_proxmox_sandbox`, `inspect_vagrant_sandbox`, `inspect-openshell-sandbox` READMEs; `NVIDIA/OpenShell` README and releases); 0.3.280 writable-host-mount block from `inspect_ai` PR #5830 and the sandboxing docs; SandboxEscapeBench README and arXiv:2603.02277; METR status from the archived flags and READMEs of `METR/vivaria`, `METR/task-standard`, `METR/inspect-action`, plus `METR/hawk` README and releases, `METR/inspect-tasks-public` and `METR/inspect-metr-task-bridge` READMEs, `METR/inspect-agents` package files; harness-parser finding from the arXiv:2609.27542 abstract. Corrected: the `k8s` sandbox registry name (was given as `k8s_sandbox`) and the claim that Vivaria is METR's live infrastructure.) Earlier notes: smolagents, OpenAI Agents SDK, Pydantic AI all maintained. (Citation audit 2026-06: external-CLI support is the separate `inspect-swe` package by Meridian Labs, not built into core Inspect; Agent Bridge's `bridge()` is deprecated in favor of `agent_bridge()` / `sandbox_agent_bridge()`. Additions 2026-06: cited the named methods — ReAct (Yao et al. 2210.03629), self-consistency (Wang et al. 2203.11171), Tree of Thoughts (Yao et al. 2305.10601); all verified via arXiv.) (Additions 2026-10: `react()` default continue-message pitfall and `on_continue` mitigation (Zhong LW 2026-09-11; default confirmed in `inspect_ai` source `agent/_types.py` and `agent/_react.py`, v0.3.278); `deepagent()` (Inspect docs); `web_browser()` deprecation (0.3.272), `fail_on_refusal` (0.3.264), non-root sandbox tools (0.3.264) from the `inspect_ai` CHANGELOG; sandbox network-isolation behaviour from the Inspect sandboxing docs; Anthropic 2026-09-09 and UK AISI 2026-08-04 incident reports; Alkur LW 2026-08-25 on unclaimable names; `inspect-swe` v0.2.71 agent list and changelog; `inspect-harbor` v1.0.0 README; Ahlqvist et al. arXiv:2609.02302; all verified via GitHub/PyPI, vendor docs or the primary post.)
