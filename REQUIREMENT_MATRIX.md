# Requirement matrix

| Requirement | Code path | Evidence status |
|---|---|---|
| Consensus-built support graph | `_review` refetches three frozen slots | PASS: forged edge rejected |
| Complete finding coverage | Unique indexes and exact row count | PASS: direct suite |
| Deterministic verdict | Gap union in `review_reasoning` | PASS: reasoned and gapped cases |
| Source attribution | Ordered source digests preserved | PASS: live proof stores three digests |
| Authorization and replay | Owner cancellation only before terminal review | PASS: targeted test |
| Deployed-source match | Verification script | PASS: exact byte match |
