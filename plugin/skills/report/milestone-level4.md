# Level 4 milestone checks

At Level 4 agents merge and cut tickets inside the milestone, so the milestone report carries two extra checks before the Owner's sign-off. Adapted from pstack's `/swarm` and `/show-me-your-work`.

## Swarm over the scenarios

1. Split the design's scenarios (`docs/milestones/M<n>-design.md`) and the exit criteria into slices of a few each.
2. Declare the rule before starting: **every scenario must pass**; one failure fails the milestone.
3. Start one fresh worker per slice, in parallel, each in a clean checkout of `milestone/M<n>`. Each drives its scenarios through the real app with the project's verification skill when there is one, otherwise runs the tests the design names, and returns: scenario, result, the commit it ran on, the method, and the evidence path.
4. A result missing its commit or method is run again once; a second miss counts as a gap, which isn't a pass. If a worker drops out, go on with the rest and list its slice as a gap.
5. Put the table in the report: one row per scenario.

## Audit the decision logs

Start one fresh reviewer on the harness file's "Second model". Give it every decision log from the milestone's ticket PRs and the milestone's diff. Ask it to check that each "kept" decision matches the code, that failed attempts didn't leave dead code behind, and that no choice the Owner should know about is missing. It adds what it finds to the same **Attention** table the report rolls up from the verdicts, with the same kinds: a missing choice is `undisclosed`, a "kept" row the code contradicts is `unproven-claim`. Put the table at the top of the milestone PR's description.

Neither check replaces the Owner's review; they decide what the Owner reads first.
