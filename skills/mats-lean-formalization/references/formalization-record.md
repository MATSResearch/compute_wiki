# Formalization record

Use this compact record alongside a theorem that may matter to a research
argument. Omit fields that genuinely do not apply, but do not silently omit a
failed check or a gap in translation.

- **Informal claim:**
- **Purpose of formalization:** definition / derivation / reusable lemma / counterexample / other
- **Lean target:** theorem or `example`, with file path and line if useful
- **Definitions and assumptions:** include types, quantifiers, and edge-case conventions
- **Scope gap:** what the formal statement leaves out or strengthens
- **Environment:** project revision, Lean/toolchain version, and exact imports
- **Check:** command run, exit status, and relevant output or artifact path
- **Dependency boundary:** `#print axioms` result; note `sorry`, `admit`, `axiom`, `Classical`, or `noncomputable`
- **Unresolved issues:** failed attempts, missing library results, or statements still under debate
- **Interpretation:** what the checked result supports, and what still requires empirical or informal reasoning

For a small example, keep the complete source next to the record so another
researcher can rerun it with the same toolchain.
