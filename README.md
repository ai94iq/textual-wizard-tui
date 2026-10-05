# tui-guidelines

[![check](https://github.com/ai94iq/textual-wizard-tui/actions/workflows/check.yml/badge.svg)](https://github.com/ai94iq/textual-wizard-tui/actions/workflows/check.yml)

A Claude Code skill: rules for terminal user interfaces that work for someone
who has never seen them -- wizard flows, validation, back navigation, keys,
state without colour, sizing, slow work, the exit receipt, headless tests.

`SKILL.md` is the skill. `assets/wizard_template.py` is a runnable Textual
wizard with every rule wired in.

## Install

```sh
git clone https://github.com/ai94iq/textual-wizard-tui ~/.claude/skills/tui-guidelines
```

## Check

```sh
./check.sh     # runs the template's headless selftest (needs textual), refs, size
```
