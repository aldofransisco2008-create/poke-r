import math
import random

import pygame

from effects import glow

MAX_PARTICLES = 1400


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max", "color", "size", "kind", "rot", "vr", "grav")


class ParticleSystem:
    """Spark, confetti (spinning quads), coin (squashing disc), shard, star, bubble, trail and ring."""

    def __init__(self):
        self.ps = []

    def emit(self, x, y, vx, vy, life, color, size, kind="spark", grav=0.0):
        if len(self.ps) >= MAX_PARTICLES:
            self.ps.pop(0)
        p = Particle()
        p.x, p.y, p.vx, p.vy, p.life, p.max = x, y, vx, vy, life, life
        p.color, p.size, p.kind, p.grav = color, size, kind, grav
        p.rot, p.vr = random.uniform(0, 6.28), random.uniform(-9, 9)
        self.ps.append(p)

    def burst(self, x, y, n, colors, speed=300, kind="spark", life=(0.5, 1.1), size=(3, 7), grav=300, spread=math.tau,
              angle=0.0):
        for _ in range(n):
            a = angle + random.uniform(-spread / 2, spread / 2)
            s = random.uniform(speed * 0.3, speed)
            self.emit(x, y, math.cos(a) * s, math.sin(a) * s, random.uniform(*life), random.choice(colors),
                      random.uniform(*size), kind, grav)

    def confetti(self, colors, n=90, y=-20):
        for _ in range(n):
            self.emit(random.uniform(0, 1280), y - random.uniform(0, 200), random.uniform(-60, 60),
                      random.uniform(120, 260), random.uniform(2.5, 4.5), random.choice(colors),
                      random.uniform(5, 9), "confetti", 30)

    def update(self, dt):
        alive = []
        for p in self.ps:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.grav * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.rot += p.vr * dt
            alive.append(p)
        self.ps = alive

    def draw(self, surf):
        for p in self.ps:
            k = p.life / p.max
            if p.kind == "spark":
                r = max(2, int(p.size * (0.4 + 0.9 * k) * 2))
                glow.draw_glow_circle(surf, (p.x, p.y), r, p.color)
            elif p.kind == "confetti":
                s = p.size * min(1.0, k * 3)
                c, sn = math.cos(p.rot) * s, math.sin(p.rot) * s
                pts = [(p.x + c, p.y + sn), (p.x - sn, p.y + c), (p.x - c, p.y - sn), (p.x + sn, p.y - c)]
                pygame.draw.polygon(surf, p.color, pts)
            elif p.kind == "shard":                          # a spinning triangle splinter
                s = p.size * (0.5 + 0.8 * k)
                pts = [(p.x + math.cos(p.rot + o) * s * m, p.y + math.sin(p.rot + o) * s * m)
                       for o, m in ((0, 1.6), (2.4, 0.8), (3.9, 0.8))]
                pygame.draw.polygon(surf, p.color, pts)
            elif p.kind == "star":                           # a four-point twinkle
                s = p.size * (0.4 + 1.2 * k) * (0.7 + 0.3 * math.sin(p.rot * 3))
                w = s * .3
                pygame.draw.polygon(surf, p.color, [(p.x, p.y - s * 1.6), (p.x + w, p.y - w), (p.x + s * 1.6, p.y),
                                                    (p.x + w, p.y + w), (p.x, p.y + s * 1.6), (p.x - w, p.y + w),
                                                    (p.x - s * 1.6, p.y), (p.x - w, p.y - w)])
            elif p.kind == "bubble":                         # a rising outlined bubble
                r = max(2, int(p.size * (1.4 - 0.5 * k)))
                pygame.draw.circle(surf, p.color, (int(p.x), int(p.y)), r, 2)
                pygame.draw.rect(surf, (255, 255, 255), (int(p.x - r * .4), int(p.y - r * .5), 2, 2))
            elif p.kind == "trail":                          # a streak along the velocity
                L = 0.05
                pygame.draw.line(surf, p.color, (p.x, p.y), (p.x - p.vx * L, p.y - p.vy * L), max(1, int(p.size * k)))
            elif p.kind == "ring":                           # an expanding hoop
                r = int(p.size * (1 - k) * 10) + 4
                pygame.draw.circle(surf, p.color, (int(p.x), int(p.y)), r, max(1, int(4 * k)))
            else:  # coin
                w = max(2, abs(math.cos(p.rot)) * p.size)
                pygame.draw.ellipse(surf, glow.mix(p.color, (255, 255, 255), 0.3),
                                    (p.x - w, p.y - p.size, w * 2, p.size * 2))
                pygame.draw.ellipse(surf, p.color, (p.x - w, p.y - p.size, w * 2, p.size * 2), 2)
