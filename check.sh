#!/bin/sh
# Pre-commit check for this skill. Run from anywhere: ./check.sh
set -u
cd "$(dirname "$0")"
fail=0

# python3 can be a store stub on Windows that resolves but cannot run.
PY=
for c in python3 python; do
  "$c" -c "" >/dev/null 2>&1 && { PY=$c; break; }
done

if [ -n "$PY" ] && "$PY" -c 'import textual' >/dev/null 2>&1; then
  if "$PY" assets/wizard_template.py selftest >/dev/null 2>&1; then
    echo "ok      assets/wizard_template.py selftest"
  else
    echo "FAIL    $PY assets/wizard_template.py selftest"; fail=1
  fi
elif [ -n "${CI:-}" ]; then
  echo "FAIL    no python with textual in CI -- the selftest must run here"; fail=1
else
  echo "skip    selftest (no python with textual here)"
fi

# every assets/ path a doc names must exist
for f in $(grep -ohE 'assets/[A-Za-z0-9_.-]+' SKILL.md | sort -u); do
  [ -e "$f" ] || { echo "FAIL    broken ref: $f"; fail=1; }
done

# SKILL.md loads into every session that triggers it
words=$(wc -w < SKILL.md)
echo "ok      SKILL.md $words words; budget 3000"
[ "$words" -gt 3000 ] && { echo "FAIL    SKILL.md over budget"; fail=1; }

exit $fail
