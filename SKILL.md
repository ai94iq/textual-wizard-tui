---
name: tui-guidelines
description: >-
  Design and build terminal user interfaces (TUIs) that people can use the first
  time: form/wizard flows, pickers, busy states, back navigation that keeps
  answers, validation on submit, small-terminal and narrow-terminal behaviour,
  state shown in text not only colour, keyboard and footer conventions, the exit
  receipt, and headless testing. Framework-agnostic rules; a runnable Textual
  (Python) wizard in assets/ as the worked example.
  Use when: building or reviewing a TUI, "add a wizard", "interactive CLI",
  "terminal UI", Textual, Rich, Bubble Tea, Ratatui, curses, prompt_toolkit,
  "the TUI hangs", "ctrl+c doesn't quit", "test my TUI".
  Not for: plain argparse/click CLIs with no interactive screen, or web UIs.
license: MIT
---

# TUI guidelines

Rules for terminal interfaces that work for someone who has never seen them.
Every rule below exists because its absence was a real bug. The worked example
is `assets/wizard_template.py` (Textual): every pattern here is wired into it,
and `python assets/wizard_template.py selftest` proves it headlessly.

## 1. Decide the shape first

- **Bounded flow or app you live in?** A wizard (N questions, then done) and a
  dashboard (open all day) want different things. Most tool TUIs are wizards:
  build them as a list of steps, not as a free-form app.
- **Never require the TUI.** Every answer the TUI collects must also be
  passable as flags or a config file, so CI and repeat runs skip it. Offer to
  save the answers as that config at the end.
- **No arguments opens the TUI**, not a usage message. Someone who ran the
  launcher wants to be asked, not lectured. Pre-fill what you can discover
  (nearby files, defaults from the input).
- **Inline vs alternate screen.** Inline keeps output in scrollback, but is
  unsupported or flaky on some platforms (Textual's inline mode on Windows).
  If you use the alternate screen, honour the exit contract (§8).

## 2. Shared chrome, one place

One base screen owns the parts every step shares: the step line
(`Step 2 of 5 - <question>`), a one-line hint, the button row (Next / Back),
the key bindings, the footer, and the validation loop. Each step supplies only
its fields and a `submit()`. Consequences:

- every step behaves identically, so the user learns it once;
- the footer is never empty — it is where a first-time user looks for keys;
- the step line counts real steps; sub-steps read `3a of 5`, `3b of 5`.

## 3. Validation and navigation

- **Validate on submit, never per keystroke.** A half-typed value is not an
  error. `submit()` returns the value or raises `Invalid(message)`; the base
  shows the message and stays put.
- **Validate early.** Check what can be checked at the step that asks (target
  folder exists and is a file, folder is not empty, names are unique, URL has a
  scheme), not five screens later.
- **Error messages say what to do**, not what failed: "Give at least one name,
  such as 'test'", not "invalid input".
- **Back keeps every answer.** Back must never close the wizard or clear
  fields. Store answers by step name; each screen is built from its previous
  answer. On the first step, Back is labelled **Cancel** and exits.
- **Rebuild the step list after every answer.** Later steps often depend on
  earlier ones (one details step per item named earlier; a picker that only
  shows what an earlier filter left in). A static list goes stale on Back.
- **One sentinel for Back** (`None`), never a value a step could return.

## 4. Keys

- **Enter in a field moves on** — what every form does. Exceptions: a filter
  or search box (Enter applies it, it must not skip the step) and list widgets
  where Enter toggles a row. Test each.
- **Escape is Back. Ctrl+C quits** — from every screen, including the last.
  Frameworks that rebind Ctrl+C to copy must be overridden if the footer says
  "^c Quit". A footer that lies is worse than none.
- **Focus lands on the first input** when a step opens. If a scroll container
  takes focus, the first keystrokes go nowhere — the first thing a new user
  tries is typing.
- **Bulk keys for lists**: `a` ticks/unticks all, shown in the footer.
- **Trim framework extras** you do not support (help panels listing
  platform-specific keys, screenshot commands). Every key shown must work on
  every OS you ship to.

## 5. Show state in text, not only colour

- A chosen checkbox reads `[X]`, an unchosen one `[ ]`; a chosen radio `(*)`,
  the rest `( )`. Many widget sets draw the same glyph everywhere and let
  colour carry the state — invisible under low-contrast themes and to anyone
  who cannot separate the two colours.
- Unchosen markers must be as readable as their labels (no dim-on-dim).
- No pictograms a terminal may not have (magnifying glass, emoji): they draw
  as boxes. Plain ASCII markers work everywhere.
- Themes are fine; correctness must not depend on one.

## 6. Size and layout

- **Relative sizes only** (`1fr`, `%`, `max-width`). Absolute widths break in
  a 60-column split and look lost on an ultrawide.
- **Fold below a width** (e.g. 80 columns): two side-by-side panes stack.
- **A floor, stated honestly.** Below the minimum (measure it: label + field
  + a usable list + buttons), show "This window is too small. It needs W x H.
  Make it bigger and it carries on" — and resume where it was when resized.
  A silently truncated list is a wrong answer the user cannot see.
- **No border around everything.** The terminal edge already frames the
  screen; nested boxes cost rows and separate nothing a column of space would
  not. Keep one blank row between panes and buttons so borders do not merge.

## 7. Slow work

- **Never block the UI thread.** Downloads, parses, builds go to a thread or
  worker (`asyncio.to_thread`, a worker, a goroutine). A frozen screen is
  indistinguishable from a hang.
- **Busy screen**: say what is running and, after ~2 s, the elapsed seconds.
  No stopwatch flash for fast work.
- **Optional expensive work is a button**, not automatic. Do not make someone
  who answered five questions wait for a check they did not ask for.
- **Live previews** for filters: "Keeping 41 of 120 items" updates as they
  tick or type, and submit refuses a filter that leaves nothing.

## 8. The end: done screen and exit contract

- **Do not vanish.** Finish on a done screen: what was produced, where, and
  the one command to run next.
- **Print a receipt to stdout after the alternate screen closes** — the
  summary of what happened survives in scrollback; everything drawn inside the
  TUI does not. Cancel prints "Cancelled - nothing was written."
- **Exit codes**: 0 done, non-zero cancelled or failed. Errors from the work
  are shown, never swallowed.

## 9. Wording

- Write for the person running it, not the spec author: "web address" not
  "base URL", "group" not "tag", "log in as an application" not "client
  credentials grant". Keep the precise term in brackets or in the docs for
  anyone who needs to search for it.
- Questions are questions: "which environments will you test against?"
- Placeholders match the user's OS (a `C:\` path on Windows, `~/` elsewhere).
- Hints say what happens next and what can be changed later.

## 10. Secrets

Password, token, and key fields are masked. Say plainly if a value is written
to disk as-is ("use a test account"). Never echo secrets in the receipt.

## 11. Test it headlessly

Every TUI framework worth using has a headless driver (Textual `run_test` +
Pilot, Bubble Tea `teatest`, Ratatui `TestBackend`, prompt_toolkit pipe
input). Keep one test that walks the real flow and asserts:

1. empty submit stays on the step (validation holds);
2. Back returns with the typed value still there;
3. a pick that leaves nothing is refused;
4. resize below the floor shows the too-small state, and resizing back resumes;
5. the final result equals what was entered.

Prove the test bites: break one rule (delete a `raise Invalid`) and watch it
fail. Pin the framework version — widget internals the markers rely on
(Textual's `ToggleButton` class attributes) are private and move.

## Review checklist

- [ ] Every TUI answer also reachable by flag/config
- [ ] One base screen owns chrome, keys, validation
- [ ] Validation on submit, messages say what to do
- [ ] Back keeps answers; first step's Back is Cancel
- [ ] Enter/Escape/Ctrl+C behave on every screen; footer is truthful
- [ ] Focus starts in the first field
- [ ] Chosen state visible without colour
- [ ] Relative sizes, narrow fold, honest size floor
- [ ] Slow work off the UI thread, behind a timed busy screen
- [ ] Done screen + stdout receipt + meaningful exit code
- [ ] Plain wording; OS-appropriate examples; secrets masked
- [ ] Headless flow test that fails when a rule breaks
