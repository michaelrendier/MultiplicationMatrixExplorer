#!/usr/bin/env python3
"""
driver.py -- "drive it around like Ultra Fractal": a live Tkinter viewer.
Each of the 20 digits (10 for num1, 10 for num2) is its own odometer
wheel -- scroll or click +/- on a digit and the frame re-renders
immediately with the new pair. No pre-rendering, no range to configure
first; you're just turning dials and watching the addition/carry
matrices update in real time.

Run: python3 driver.py [num1] [num2]
"""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

from PIL import ImageTk

from matrix_math import N_DIGITS, trace_multiplication
from render import render_frame

MAX_VAL = 10 ** N_DIGITS - 1


class DigitWheel(ttk.Frame):
    """One decimal digit, one place value. Scroll wheel or +/- buttons
    change it; carries/borrows ripple into the neighbor wheel you hand
    it via on_overflow."""

    def __init__(self, parent, initial: int, on_change, on_overflow=None, on_underflow=None):
        super().__init__(parent)
        self.value = initial
        self.on_change = on_change
        self.on_overflow = on_overflow
        self.on_underflow = on_underflow

        self.up_btn = ttk.Button(self, text="+", width=2, command=self._inc)
        self.label = ttk.Label(self, text=str(self.value), width=2, anchor="center",
                                font=("DejaVu Sans Mono", 14, "bold"))
        self.down_btn = ttk.Button(self, text="-", width=2, command=self._dec)

        self.up_btn.pack()
        self.label.pack()
        self.down_btn.pack()

        self.label.bind("<MouseWheel>", self._on_wheel)         # Windows/macOS
        self.label.bind("<Button-4>", lambda e: self._inc())    # Linux scroll up
        self.label.bind("<Button-5>", lambda e: self._dec())    # Linux scroll down

    def _on_wheel(self, event):
        if event.delta > 0:
            self._inc()
        else:
            self._dec()

    def _inc(self):
        self.value += 1
        if self.value > 9:
            self.value = 0
            if self.on_overflow:
                self.on_overflow()
        self._refresh()

    def _dec(self):
        self.value -= 1
        if self.value < 0:
            self.value = 9
            if self.on_underflow:
                self.on_underflow()
        self._refresh()

    def set(self, v: int, notify: bool = True):
        self.value = v
        self._refresh(notify=notify)

    def _refresh(self, notify: bool = True):
        self.label.config(text=str(self.value))
        if notify:
            self.on_change()


class NumberDial(ttk.Frame):
    """N_DIGITS DigitWheels making one number, most-significant on the
    left, with overflow/underflow rippling between neighbors like a real
    odometer."""

    def __init__(self, parent, label: str, initial: int, on_change):
        super().__init__(parent)
        if not (0 <= initial <= MAX_VAL):
            raise ValueError(
                f"{label}={initial} needs {len(str(initial))} digits -- this tool "
                f"is built for exactly {N_DIGITS}-digit numbers (0 to {MAX_VAL}). "
                f"An extra or missing digit here used to silently misbuild the "
                f"dial instead of erroring -- fixed to fail loudly instead."
            )
        self.on_change = on_change
        ttk.Label(self, text=label, font=("DejaVu Sans Mono", 11, "bold")).pack(side="top", anchor="w")
        row = ttk.Frame(self)
        row.pack(side="top")

        digits = [int(c) for c in f"{initial:0{N_DIGITS}d}"]  # msb first
        self.wheels = []
        for i, d in enumerate(digits):
            w = DigitWheel(
                row, d,
                on_change=self._changed,
                on_overflow=lambda i=i: self._carry(i, +1),
                on_underflow=lambda i=i: self._carry(i, -1),
            )
            w.pack(side="left", padx=1)
            self.wheels.append(w)

    def _carry(self, i: int, direction: int):
        # i is msb-first index; carry into the wheel to the LEFT (i-1)
        if i - 1 < 0:
            return  # overflowed past the leading digit -- clamp, no wraparound
        left = self.wheels[i - 1]
        if direction > 0:
            left._inc()
        else:
            left._dec()

    def _changed(self):
        self.on_change()

    def value(self) -> int:
        return int("".join(str(w.value) for w in self.wheels))

    def set_value(self, n: int):
        digits = [int(c) for c in f"{max(0, min(MAX_VAL, n)):0{N_DIGITS}d}"]
        for w, d in zip(self.wheels, digits):
            w.set(d, notify=False)
        self.on_change()


class DriverApp:
    def __init__(self, root, num1_init: int, num2_init: int, dpi: int = 130):
        self.root = root
        self.dpi = dpi
        root.title("Multiplication Matrix Animator -- drive mode")

        controls = ttk.Frame(root, padding=8)
        controls.pack(side="top", fill="x")

        self.dial1 = NumberDial(controls, "num1", num1_init, self._redraw)
        self.dial1.pack(side="top", pady=4)
        self.dial2 = NumberDial(controls, "num2", num2_init, self._redraw)
        self.dial2.pack(side="top", pady=4)

        hint = ttk.Label(controls, text="scroll or +/- on any digit to drive that place value; "
                                          "carries ripple left like an odometer",
                          font=("DejaVu Sans Mono", 9))
        hint.pack(side="top", pady=(4, 0))

        self.canvas_label = ttk.Label(root)
        self.canvas_label.pack(side="top", padx=8, pady=8)

        self._tk_img = None
        self._redraw()

    def _redraw(self):
        n1, n2 = self.dial1.value(), self.dial2.value()
        tr = trace_multiplication(n1, n2)
        img = render_frame(tr, dpi=self.dpi)
        self._tk_img = ImageTk.PhotoImage(img)
        self.canvas_label.config(image=self._tk_img)


def main():
    num1 = int(sys.argv[1]) if len(sys.argv) > 1 else 1234567890
    num2 = int(sys.argv[2]) if len(sys.argv) > 2 else 9876543210
    root = tk.Tk()
    DriverApp(root, num1, num2)
    root.mainloop()


if __name__ == "__main__":
    main()
