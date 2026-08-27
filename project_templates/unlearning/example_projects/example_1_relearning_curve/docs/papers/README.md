# Background reading for this example

Summaries go here as markdown (download the PDF and convert with `pymupdf4llm`;
don't scrape the HTML version). The papers this example is built around:

- **arXiv:2401.06121 — TOFU: A Task of Fictitious Unlearning for LLMs.** The
  reason `data.py` invents entities instead of using real ones: the forget
  knowledge must provably have entered during *your* finetune, or "the model
  still knows it" is unattributable.
- **arXiv:2404.05868 — Negative Preference Optimization.** The default objective
  here (`npo_retain`). Treats the forget set as the rejected side of a DPO-style
  loss, which bounds the objective and avoids gradient ascent's collapse.
- **arXiv:2410.08827 — Do Unlearning Methods Remove Information from Language
  Model Weights?** Why this example is built around the *attack* rather than the
  forget score. Largely: no, they don't.
- **arXiv:2402.16835 — Eight Methods to Evaluate Robust Unlearning in LLMs.**
  Why a null result from one attack is reported as "not recovered by this
  attack" rather than "removed".
- **arXiv:2506.12618 — OpenUnlearning.** What to graduate to when you want 12+
  published methods on TOFU / MUSE / WMDP instead of a hand-rolled toy.
