# Interrogate a high-risk pull request

Adapted from pstack's `/interrogate`. Only at Level 4, and only for tickets tagged `Risk: high`. It adds adversaries to the normal checklist; it doesn't replace it.

## Run it

1. **Frame.** Write the PR's intent in two sentences from the ticket and the design's scenarios, not from the PR description.
2. **Fan out the adversaries**, in parallel, each in its own fresh worktree of the head commit, and none of them the builder:
   - one subagent on a different Claude model from the builder's;
   - the second model from the harness file's "Second model" line, when it names an external one (the `second-model-review` recipe lists the options).
   Give each only the intent, the diff, the ticket and the scenarios. Ask each to break the change: find inputs, orders, states or failures that violate the intent, and for every finding give a command or test that **reproduces** it.
3. **Prove or drop.** Run every reproduction yourself in a clean worktree. Keep a finding only if your run shows the failure and it breaks the intent. Merge findings with the same root cause. Style, naming and "might break later" go under Dropped.
4. **Report** inside the verdict, under "Interrogate":
   - **Intent:** the two sentences.
   - **Findings:** each with its reproduction and output.
   - **Dropped:** what was raised but not reproduced, one line each.

No findings is a valid result. Any finding that survives makes the verdict FAIL. Never apply a fix: the builder does that in a fix round.
