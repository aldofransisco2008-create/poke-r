import math


def out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def out_back(t):
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2


def in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def approach(cur, target, rate, dt):
    """Frame-rate independent exponential smoothing."""
    return cur + (target - cur) * (1 - math.exp(-rate * dt))


class Sequence:
    """Timeline of (time, callable). update(dt) fires everything that came due."""

    def __init__(self):
        self.events, self.t, self.i = [], 0.0, 0

    def at(self, t, fn):
        self.events.append((t, fn))

    @property
    def done(self):
        return self.i >= len(self.events)

    def update(self, dt):
        self.t += dt
        while self.i < len(self.events) and self.events[self.i][0] <= self.t:
            fn = self.events[self.i][1]
            self.i += 1
            fn()
