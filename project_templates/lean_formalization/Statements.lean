/-
Statements.lean: the challenge.

TRUSTED and HUMAN-REVIEWED. Every headline theorem lives here with a `sorry`
body, and every name listed in comparator.json's `theorem_names` must appear
here. A reviewer reads only this file (and what it imports) to know what the
project claims. Next to each statement, record the informal claim it encodes,
so the fidelity check (quantifier order, domains, hidden assumptions) has
something to be checked against.

Do not add proofs here and do not let an agent edit this file while proving.
-/
import Defs

namespace Template

/-- Informal claim: doubling a natural number is the same as multiplying it by two. -/
theorem double_eq_two_mul (n : Nat) : double n = 2 * n := by
  sorry

/-- Informal claim: addition of natural numbers is commutative. -/
theorem add_comm_example (n m : Nat) : n + m = m + n := by
  sorry

end Template
