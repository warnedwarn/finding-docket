# Finding Docket

The question is not whether a decision sounds official. The question is whether every required finding has a visible support path.

The filer freezes a governing standard, a decision, an evidence packet, and two to seven required findings. Validators build one bounded support row per finding. Contract code marks a gap when the standard does not authorize the finding, the decision fails to address it, the packet does not support it, or material counterevidence goes unanswered.

No model emits the final verdict. The contract stores the complete support graph and deterministically closes the docket as `REASONED` or `GAPPED`.

The sample documents are operator-authored fixtures and make no claim of independent legal authority.

```bash
genvm-lint contracts/contract.py
python -m pytest -q
```
