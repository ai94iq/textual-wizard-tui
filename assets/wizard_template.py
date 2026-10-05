"""A minimal Textual wizard with every pattern from SKILL.md wired in.

Copy it, rename the steps, keep the chrome. Run it:

    python wizard_template.py            the wizard, then a receipt on stdout
    python wizard_template.py selftest   headless Pilot run, exit 0 on pass
"""

from __future__ import annotations

import asyncio
import sys
import time

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button, Checkbox, Footer, Header, Input, Label, LoadingIndicator,
    RadioButton, RadioSet, SelectionList, Static,
)
from textual.widgets.selection_list import Selection
# Private module: SelectionList reads its markers off this class. Pin textual.
from textual.widgets._toggle_button import ToggleButton

# State in text, not only colour: [X] / [ ] / (*) survive any theme.
ToggleButton.BUTTON_LEFT, ToggleButton.BUTTON_INNER, ToggleButton.BUTTON_RIGHT = "[", "X", "]"


class Tick(Checkbox):
    BUTTON_LEFT, BUTTON_RIGHT = "[", "]"

    @property
    def BUTTON_INNER(self) -> str:            # noqa: N802 - Textual's name
        return "X" if self.value else " "


class Radio(RadioButton):
    BUTTON_LEFT, BUTTON_RIGHT = "(", ")"

    @property
    def BUTTON_INNER(self) -> str:            # noqa: N802
        return "*" if self.value else " "


class Ticks(SelectionList):
    """Per-row [X] / [ ]: the row is the only thing that knows its state."""

    def render_line(self, y: int):
        try:
            option = self.get_option_at_index(self.scroll_offset[1] + y)
            ticked = option.value in self.selected
        except Exception:                     # past the last row
            ticked = False
        ToggleButton.BUTTON_INNER = "X" if ticked else " "
        try:
            return super().render_line(y)
        finally:
            ToggleButton.BUTTON_INNER = "X"


MIN_WIDTH, MIN_HEIGHT = 46, 20

CSS = """
#form { padding: 1 2; height: 1fr; }
#buttons { height: auto; padding: 1 2; }
Button { margin-right: 2; }
Label { padding: 1 0 0 1; }
Input { width: 1fr; max-width: 72; }
.step { padding: 0 2; text-style: bold; }
.hint { color: $text-muted; padding: 0 2 1 2; }
#busy, #too-small { align: center middle; height: 1fr; }
SelectionList > .selection-list--button,
SelectionList > .selection-list--button-highlighted,
ToggleButton > .toggle--button { background: transparent; color: $text; }
SelectionList > .selection-list--button-selected,
SelectionList > .selection-list--button-selected-highlighted,
ToggleButton.-on > .toggle--button { background: transparent; color: $text; text-style: bold; }
"""


class Invalid(Exception):
    """Raised by submit() to keep the user on the step."""


class WizardScreen(Screen):
    """One step. Subclasses give form() and submit(); everything else is here."""

    BINDINGS = [Binding("escape", "back", "Back"), Binding("ctrl+c", "app.quit", "Quit")]
    AUTO_FOCUS = "Input, RadioSet, SelectionList"   # else the scroll box eats keys
    step = question = hint = ""
    back_label = "Back"

    def compose(self) -> ComposeResult:
        yield Header(icon="")
        yield Static(f"Step {self.step} - {self.question}" if self.step else self.question,
                     classes="step")
        if self.hint:
            yield Static(self.hint, classes="hint")
        with VerticalScroll(id="form"):
            yield from self.form()
        with Horizontal(id="buttons"):
            yield Button("Next", variant="primary", id="next")
            yield Button(self.back_label, id="back")
        yield Footer()

    def form(self) -> ComposeResult:
        yield from ()

    def submit(self):
        raise NotImplementedError

    def action_next(self) -> None:
        try:
            value = self.submit()
        except Invalid as problem:            # on submit, never per keystroke
            self.notify(str(problem), severity="error", timeout=8)
            return
        self.dismiss(value)

    def action_back(self) -> None:
        self.dismiss(None)                    # None means Back, always

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.action_back() if event.button.id == "back" else self.action_next()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_next()


class BusyScreen(Screen):
    """A frozen screen reads as a hang; show what is running and for how long."""

    def __init__(self, what: str) -> None:
        super().__init__()
        self.what, self.started = what, time.monotonic()

    def compose(self) -> ComposeResult:
        with Vertical(id="busy"):
            yield Static(f"Fetching {self.what}", classes="step")
            yield LoadingIndicator()
            yield Static("", id="elapsed", classes="hint")

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        seconds = int(time.monotonic() - self.started)
        if seconds >= 2:                      # no stopwatch flash on fast work
            self.query_one("#elapsed", Static).update(f"{seconds}s")


class TooSmallScreen(Screen):
    def compose(self) -> ComposeResult:
        with Vertical(id="too-small"):
            yield Static(f"This window is too small.\n\nIt needs {MIN_WIDTH} columns "
                         f"by {MIN_HEIGHT} rows. Make it bigger and it carries on.",
                         classes="step")


# -- the steps: replace these ---------------------------------------------------


class NameScreen(WizardScreen):
    step, question, back_label = "1 of 3", "what is it called?", "Cancel"
    hint = "Naming only. You can change it later."

    def __init__(self, previous: str | None = None) -> None:
        super().__init__()
        self.previous = previous

    def form(self) -> ComposeResult:
        yield Label("Name")
        yield Input(value=self.previous or "", id="name")

    def submit(self):
        name = self.query_one("#name", Input).value.strip()
        if not name:
            raise Invalid("Give it a name.")
        return name


class KindScreen(WizardScreen):
    step, question = "2 of 3", "which kind?"

    def __init__(self, kinds: list[str], previous: str | None = None) -> None:
        super().__init__()
        self.kinds, self.previous = kinds, previous or kinds[0]

    def form(self) -> ComposeResult:
        with RadioSet(id="kind"):
            for kind in self.kinds:
                yield Radio(kind, value=kind == self.previous, name=kind)
        yield Tick("Also make a copy", id="copy")

    def submit(self):
        pressed = self.query_one("#kind", RadioSet).pressed_button
        return {"kind": pressed.name if pressed else self.kinds[0],
                "copy": self.query_one("#copy", Tick).value}


class ExtrasScreen(WizardScreen):
    step, question = "3 of 3", "which extras?"
    BINDINGS = [*WizardScreen.BINDINGS, Binding("a", "toggle_all", "Tick / untick all")]

    def __init__(self, extras: list[str], previous: list[str] | None = None) -> None:
        super().__init__()
        self.extras = extras
        self.previous = previous if previous is not None else extras

    def form(self) -> ComposeResult:
        yield Ticks(*[Selection(e, e, e in self.previous) for e in self.extras], id="extras")

    def action_toggle_all(self) -> None:
        widget = self.query_one("#extras", Ticks)
        if len(widget.selected) == len(self.extras):
            widget.deselect_all()
        else:
            widget.select_all()

    def submit(self):
        picked = list(self.query_one("#extras", Ticks).selected)
        if not picked:
            raise Invalid("Tick at least one.")
        return picked


def load_options() -> tuple[list[str], list[str]]:
    """Stand-in for the slow, blocking work (a download, a parse)."""
    return ["small", "large"], ["docs", "tests", "ci"]


# -- the app --------------------------------------------------------------------


class Wizard(App):
    CSS = CSS
    TITLE = "wizard"

    def __init__(self) -> None:
        super().__init__()
        self.result: dict | None = None
        self._too_small = False

    def action_help_quit(self) -> None:
        self.exit()                           # ctrl+c quits, as the footer says

    def on_mount(self) -> None:
        self.run_worker(self.flow(), exclusive=True)

    def on_resize(self, event) -> None:
        small = event.size.width < MIN_WIDTH or event.size.height < MIN_HEIGHT
        if small != self._too_small:
            self._too_small = small
            self.push_screen(TooSmallScreen()) if small else self.pop_screen()

    async def _busy(self, what: str, fn, *args):
        await self.push_screen(BusyScreen(what))
        try:
            return await asyncio.to_thread(fn, *args)   # never on the UI thread
        finally:
            self.pop_screen()

    def steps(self, kinds, extras, answers) -> list:
        """Rebuilt every pass: later steps may depend on earlier answers."""
        return [
            ("name", lambda: NameScreen(answers.get("name"))),
            ("kind", lambda: KindScreen(kinds, (answers.get("kind") or {}).get("kind"))),
            ("extras", lambda: ExtrasScreen(extras, answers.get("extras"))),
        ]

    async def flow(self) -> None:
        kinds, extras = await self._busy("the options", load_options)
        answers: dict = {}
        step = 0
        while True:
            plan = self.steps(kinds, extras, answers)
            if step >= len(plan):
                break
            name, make = plan[step]
            value = await self.push_screen_wait(make())
            if value is None:                 # Back keeps every answer so far
                step -= 1
                if step < 0:
                    self.exit()               # Cancel on the first step
                    return
                continue
            answers[name] = value
            step += 1
        self.result = {"name": answers["name"], **answers["kind"], "extras": answers["extras"]}
        self.exit()


def run_wizard() -> dict | None:
    app = Wizard()
    app.run()
    return app.result


async def selftest() -> None:
    app = Wizard()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, NameScreen), app.screen
        await pilot.press("enter")                        # empty name: stays
        await pilot.pause()
        assert isinstance(app.screen, NameScreen), "Invalid did not hold the step"
        await pilot.press(*"demo", "enter")
        await pilot.pause()
        assert isinstance(app.screen, KindScreen)
        await pilot.press("escape")                       # Back keeps the answer
        await pilot.pause()
        assert app.screen.query_one("#name", Input).value == "demo"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#next")
        await pilot.pause()
        assert isinstance(app.screen, ExtrasScreen)
        await pilot.press("a")                            # all ticked -> none
        await pilot.click("#next")
        await pilot.pause()
        assert isinstance(app.screen, ExtrasScreen), "empty pick was accepted"
        await pilot.resize_terminal(30, 10)               # below the floor
        await pilot.pause()
        assert isinstance(app.screen, TooSmallScreen)
        await pilot.resize_terminal(80, 24)               # back where it was
        await pilot.pause()
        assert isinstance(app.screen, ExtrasScreen)
        await pilot.press("a")
        await pilot.click("#next")
        await pilot.pause()
    assert app.result == {"name": "demo", "kind": "small", "copy": False,
                          "extras": ["docs", "tests", "ci"]}, app.result


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        asyncio.run(selftest())
        print("ok")
    else:
        result = run_wizard()
        # The alternate screen is gone now; the receipt is what survives.
        print("Cancelled - nothing was done." if result is None else f"Done: {result}")
        sys.exit(0 if result else 1)
