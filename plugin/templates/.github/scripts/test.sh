#!/bin/sh
# pitaya template 0.1.9 · .github/scripts/test.sh
# The project's test command, in the one place it is written. Run it as
#   sh .github/scripts/test.sh
# The tests workflow, the JUnit checks (no-weakened-tests, done-when), AGENTS.md, the harness file
# and the allow rule in .claude/settings.json all run this script, so they can't end up running
# different commands. Change the command here and nowhere else.
# It is a rule file like the rest of .github/: an agent asks before editing it, and a ticket PR
# can't change it unless the ticket names it (read-only-paths), so the tests can't be narrowed
# to get green.
# From Level 2 the command must also write JUnit XML to "$JUNIT" when that is set, for example
#   python -m pytest -q ${JUNIT:+--junitxml="$JUNIT"}
# When to remove: never while tests are the definition of done.
set -e
<TEST_COMMAND>
