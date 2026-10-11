"""POKE'R - roguelike dice poker. Run: python main.py   (needs only pygame)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

import config
from effects import retro

if "--dev" in sys.argv:
    config.DEV_MODE = True

retro.install()


def build_registry():
    from scenes.title import TitleScene
    from scenes.round_select import RoundSelectScene
    from scenes.round_intro import RoundIntroScene
    from scenes.play import PlayScene
    from scenes.round_result import RoundResultScene
    from scenes.shop_scene import ShopScene
    from scenes.game_over import GameOverScene
    from scenes.collection import CollectionScene
    from scenes.settings import SettingsScene
    from scenes.victory import VictoryScene
    from scenes.howto import HowToScene
    return {"title": TitleScene, "round_select": RoundSelectScene, "round_intro": RoundIntroScene,
            "play": PlayScene, "round_result": RoundResultScene, "shop": ShopScene,
            "game_over": GameOverScene, "victory": VictoryScene,
            "collection": CollectionScene, "settings": SettingsScene, "howto": HowToScene}


def main():
    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    pygame.display.set_caption("Poke'R")
    flags = pygame.SCALED | pygame.RESIZABLE
    screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H), flags)
    from game import Game
    game = Game(screen, build_registry())
    game.sfx.start_music()
    game.scenes.goto("title")
    clock = pygame.time.Clock()
    while game.running:
        dt = min(clock.tick(config.FPS) / 1000.0, 0.05)
        for e in pygame.event.get():
            game.handle_event(e)
        game.update(dt, clock.get_fps())
        game.draw()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
