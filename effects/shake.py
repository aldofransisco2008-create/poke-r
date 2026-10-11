import random

import config


class Shake:
    """Trauma-based screen shake (offset ~ trauma^2)."""

    def __init__(self):
        self.trauma = 0.0

    def add(self, amount):
        if config.SHAKE:
            self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt):
        self.trauma = max(0.0, self.trauma - dt * 1.6)

    def offset(self):
        if self.trauma <= 0.001:
            return 0, 0
        m = 22 * self.trauma ** 2
        return int(random.uniform(-m, m)), int(random.uniform(-m, m))
