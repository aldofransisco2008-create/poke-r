import pygame

from effects.tween import in_out


class Scene:
    def __init__(self, game, **kw):
        self.g = game
        self.kw = kw

    def enter(self): pass
    def exit(self): pass
    def handle_event(self, e): pass
    def update(self, dt): pass
    def draw(self, surf): pass


class SceneManager:
    """Fade-out -> switch -> fade-in scene changes."""

    def __init__(self, game, registry):
        self.g, self.registry = game, registry
        self.current = None
        self.pending = None
        self.fade = 1.0
        self.phase = "in"

    def goto(self, name, **kw):
        if self.current is None:
            self._switch(name, kw)
        elif self.pending is None:
            self.pending, self.phase = (name, kw), "out"

    def _switch(self, name, kw):
        if self.current:
            self.current.exit()
        self.current = self.registry[name](self.g, **kw)
        self.current.enter()
        self.g.sfx.set_track(getattr(self.current, "music", None))
        self.phase, self.fade = "in", 1.0

    def handle_event(self, e):
        if self.current and self.pending is None:
            self.current.handle_event(e)

    def update(self, dt):
        if self.phase == "out":
            self.fade = min(1.0, self.fade + dt / 0.18)
            if self.fade >= 1.0:
                name, kw = self.pending
                self.pending = None
                self._switch(name, kw)
        else:
            self.fade = max(0.0, self.fade - dt / 0.25)
        if self.current:
            self.current.update(dt)

    def draw(self, surf):
        if self.current:
            self.current.draw(surf)

    def draw_fade(self, surf):
        if self.fade > 0.01:
            ov = pygame.Surface(surf.get_size())
            ov.set_alpha(int(255 * in_out(self.fade)))
            surf.blit(ov, (0, 0))
