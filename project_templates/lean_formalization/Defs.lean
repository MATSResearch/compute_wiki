/-
Defs.lean: definitions the headline statements mention.

TRUSTED. Statements.lean imports this file, so it is part of the challenge:
comparator checks that every declaration a statement uses is identical in the
challenge and the solution, and it is this file that makes them identical.
Review it together with Statements.lean. Keep proofs out of it.
-/

namespace Template

/-- Twice a natural number, written as a sum so the example has something to unfold. -/
def double (n : Nat) : Nat := n + n

end Template
