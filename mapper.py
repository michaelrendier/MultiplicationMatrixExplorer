#!/usr/bin/env python3
"""
mapper.py -- the constructor function / matrix-space evolution mapper.

The exhaustive space (10**10 x 10**10 pairs, ~8.1e19) cannot be
pre-rendered -- not "very large," actually larger than any render job
could ever finish. What this gives you instead: a constructor you hand a
starting pair plus an evolution rule, and it renders frames ON DEMAND,
one multiplication at a time, along whatever bounded path through that
space you actually want to watch -- the same posture as navigating
Ultra Fractal live rather than pre-rendering the whole parameter plane.

Every evolution mode is a generator of (num1, num2) pairs. Rendering is
lazy -- render_gif() only computes frames for the pairs you ask to see.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator, List, Optional, Tuple

from matrix_math import N_DIGITS, trace_multiplication
from render import render_frame

MAX_VAL = 10 ** N_DIGITS - 1

PairStream = Iterator[Tuple[int, int]]


def _clip(n: int) -> int:
    return max(0, min(MAX_VAL, n))


@dataclass
class MatrixSpaceEvolutionMapper:
    """Constructor: give it a starting (num1, num2) and an evolution
    mode. It's a generator factory, not a pre-computed list -- nothing
    is rendered until you actually iterate or export."""
    num1_start: int
    num2_start: int

    # ── evolution modes: each returns a fresh generator of (num1, num2) ──

    def sweep_num2(self, count: int, step: int = 1) -> PairStream:
        """num1 fixed, num2 walks forward (or back, if step<0) from the
        start -- watch one number's row of multiplication tables evolve."""
        n1 = self.num1_start
        n2 = self.num2_start
        for _ in range(count):
            yield n1, _clip(n2)
            n2 += step

    def sweep_num1(self, count: int, step: int = 1) -> PairStream:
        n1 = self.num1_start
        n2 = self.num2_start
        for _ in range(count):
            yield _clip(n1), n2
            n1 += step

    def diagonal(self, count: int, step: int = 1) -> PairStream:
        """Both numbers walk together -- num1*num1-ish territory, the
        diagonal of the multiplication plane."""
        n1 = self.num1_start
        n2 = self.num2_start
        for _ in range(count):
            yield _clip(n1), _clip(n2)
            n1 += step
            n2 += step

    def digit_drive(self, count: int, target: str = "num2", place: int = 0, step: int = 1) -> PairStream:
        """'Drive' a single decimal place of one number, like turning one
        odometer wheel -- everything else held fixed. `place`=0 is the
        units digit, 9 is the leading digit. This is the closest analog
        to nudging one Ultra-Fractal parameter while the rest of the
        view stays put."""
        n1, n2 = self.num1_start, self.num2_start
        base = n2 if target == "num2" else n1
        pv = 10 ** place
        for i in range(count):
            val = base + step * i * pv
            val = _clip(val)
            if target == "num2":
                yield n1, val
            else:
                yield val, n2

    def custom(self, fn: Callable[[int], Tuple[int, int]], count: int) -> PairStream:
        """Escape hatch: fn(i) -> (num1, num2) for i in range(count).
        For any evolution rule not covered above."""
        for i in range(count):
            yield fn(i)

    def explicit(self, pairs: List[Tuple[int, int]]) -> PairStream:
        """A hand-picked list of pairs, in order -- for 'go look at
        exactly these specific multiplications' rather than a sweep."""
        for p in pairs:
            yield p

    # ── rendering: lazy, frame by frame ──

    def frames(self, stream: PairStream, dpi: int = 150, **render_kw):
        """Yields (num1, num2, PIL.Image) one at a time -- doesn't hold
        the whole animation in memory unless the caller does."""
        for n1, n2 in stream:
            tr = trace_multiplication(n1, n2)
            img = render_frame(tr, dpi=dpi, **render_kw)
            yield n1, n2, img

    # a GIF asks PIL to hold every frame in RAM at once (save_all wants a
    # real list, there's no streaming multi-frame GIF writer) -- 3MB/frame
    # x thousands is exactly how a computer locks up. This cap is a real
    # guarantee, not a suggestion: render_gif refuses silently-huge counts
    # instead of trying and hanging. Use render_sequence_to_dir for
    # anything bigger -- it writes one PNG at a time and never holds more
    # than one frame in memory, so it has no upper bound on count.
    GIF_FRAME_CAP = 1000

    def render_gif(self, stream: PairStream, out_path: str, dpi: int = 120,
                    ms_per_frame: int = 400, loop: int = 0,
                    max_frames: Optional[int] = None, **render_kw) -> dict:
        """Materializes ONE bounded animation to disk. Refuses to even
        start past GIF_FRAME_CAP frames (override with max_frames, but
        know that's `frames * ~3MB` of RAM held at once by construction
        of animated-GIF writing -- there's no way around that for this
        output format). For anything large, use render_sequence_to_dir
        instead, which has no such limit."""
        cap = self.GIF_FRAME_CAP if max_frames is None else max_frames
        imgs = []
        for i, (n1, n2, img) in enumerate(self.frames(stream, dpi=dpi, **render_kw)):
            if i >= cap:
                raise ValueError(
                    f"stream produced more than {cap} frames -- refusing to keep "
                    f"buffering (animated GIFs hold every frame in RAM at once, "
                    f"~3MB each at typical dpi). Pass max_frames=N to raise the "
                    f"cap deliberately, or use render_sequence_to_dir(stream, dir) "
                    f"instead, which streams to disk one frame at a time and has "
                    f"no count limit."
                )
            imgs.append(img)
        if not imgs:
            raise ValueError("empty pair stream -- nothing to render")
        imgs[0].save(
            out_path, save_all=True, append_images=imgs[1:],
            duration=ms_per_frame, loop=loop,
        )
        return {"path": out_path, "n_frames": len(imgs), "size": imgs[0].size}

    def render_sequence_to_dir(self, stream: PairStream, out_dir: str, dpi: int = 150,
                                name_fmt: str = "frame_{i:06d}_{n1}x{n2}.png",
                                progress_every: Optional[int] = 100, **render_kw) -> dict:
        """Streams frames to disk one at a time -- each image is saved
        and dropped immediately, so memory use is O(1) in frame count no
        matter how long the stream runs. This is the one to use for
        anything past a few hundred frames; assemble into video after
        with ffmpeg (e.g. `ffmpeg -framerate 5 -pattern_type glob -i
        '*.png' out.mp4`) rather than holding it all as one GIF."""
        import os
        os.makedirs(out_dir, exist_ok=True)
        n = 0
        for n1, n2, img in self.frames(stream, dpi=dpi, **render_kw):
            path = os.path.join(out_dir, name_fmt.format(i=n, n1=n1, n2=n2))
            img.save(path)
            n += 1
            if progress_every and n % progress_every == 0:
                print(f"  ...{n} frames written")
        return {"dir": out_dir, "n_frames": n}


if __name__ == "__main__":
    m = MatrixSpaceEvolutionMapper(num1_start=1234567890, num2_start=9876543210)
    # small, fast sanity animation: drive num2's units digit through 0..9
    stream = m.digit_drive(count=10, target="num2", place=0, step=1)
    info = m.render_gif(stream, "/tmp/mma_test_drive.gif", dpi=90, ms_per_frame=350)
    print(info)
