"""
Core Animation Engine for SecureVault
Provides easing functions and a reusable animation framework
for smooth, 60fps GUI transitions.
"""
import math
import time

class Easing:
    """Industry-standard easing functions for smooth animations."""

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1 - (1 - t) ** 3

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2

    @staticmethod
    def ease_out_back(t: float) -> float:
        c1, c3 = 1.70158, 2.70158
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

    @staticmethod
    def ease_out_elastic(t: float) -> float:
        if t == 0 or t == 1:
            return t
        return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1

    @staticmethod
    def ease_out_bounce(t: float) -> float:
        n1, d1 = 7.5625, 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375

    @staticmethod
    def linear(t: float) -> float:
        return t


class AnimationController:
    """
    Manages frame-by-frame animations using Tkinter's .after() method.
    Supports chaining, callbacks, and custom easing.
    """

    def __init__(self, widget, duration_ms: int = 400, fps: int = 60):
        self.widget = widget
        self.duration_ms = duration_ms
        self.frame_delay = max(1, 1000 // fps)
        self._running = False
        self._after_id = None

    def animate(self, update_fn, easing=Easing.ease_out_cubic, on_complete=None):
        """
        Run an animation.
        update_fn(progress): called each frame with eased progress 0.0 → 1.0
        """
        self._running = True
        start_time = time.time()

        def _step():
            if not self._running:
                return
            elapsed = (time.time() - start_time) * 1000
            raw_progress = min(elapsed / self.duration_ms, 1.0)
            eased_progress = easing(raw_progress)

            try:
                update_fn(eased_progress)
            except Exception:
                self.stop()
                return

            if raw_progress < 1.0:
                self._after_id = self.widget.after(self.frame_delay, _step)
            else:
                self._running = False
                if on_complete:
                    on_complete()

        _step()

    def stop(self):
        self._running = False
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass


class AnimationSequence:
    """Chain multiple animations in sequence."""

    def __init__(self):
        self._queue = []

    def add(self, controller: AnimationController, update_fn, easing=Easing.ease_out_cubic):
        self._queue.append((controller, update_fn, easing))
        return self

    def play(self, on_complete=None):
        self._play_next(0, on_complete)

    def _play_next(self, index, on_complete):
        if index >= len(self._queue):
            if on_complete:
                on_complete()
            return
        controller, update_fn, easing = self._queue[index]
        controller.animate(update_fn, easing, on_complete=lambda: self._play_next(index + 1, on_complete))