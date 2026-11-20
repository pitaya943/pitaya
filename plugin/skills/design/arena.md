# Arena for a contested design

Adapted from pstack's `/arena`. Only at Level 4, and only when the design is contested: the two shapes come out close, or the Owner asks for alternatives. It costs about four design sessions.

1. **Frame.** Write the artifact (this milestone's design), a rubric of three to six criteria (state ownership, one way per task, caller knowledge, the scenarios covered, cost to build), and one prompt every candidate gets: the prompt is the contract.
2. **Fan out** three candidates in parallel, on different models where you can (the harness file's "Second model" for one), each writing its own design file in its own worktree.
3. **Judge.** One read-only judge, on a different model from most candidates, scores each against the rubric.
4. **Pick a base** by the rubric, then **graft** one or two strong parts from the others into it, by hand.
5. **Verify** the result: every scenario still has a test, and the state-owners table has one owner per row.

If the candidates converge, take the consensus with no graft. If they diverge widely, the problem is framed wrong: re-frame and run again rather than averaging. Record in the design's "Shapes considered" which candidate won and what was grafted.
