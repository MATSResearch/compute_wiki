/-
Solutions.lean: the solution.

UNTRUSTED until `lake comparator` accepts it. Restate each theorem from
Statements.lean with exactly the same name and type, then prove it. Do not
import Statements (the names would clash); import Defs and any proof library.
Helper lemmas may live here or in a separate library that this file imports.
-/
import Defs

namespace Template

theorem double_eq_two_mul (n : Nat) : double n = 2 * n := by
  unfold double
  omega

theorem add_comm_example (n m : Nat) : n + m = m + n :=
  Nat.add_comm n m

end Template
