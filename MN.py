from lingotojson import turntolingo  # noqa: F401
from menuclass import *
import random

class MN(MenuWithField):
    def __init__(self, surface: pg.surface.Surface, renderer: Renderer):
        
        super().__init__(surface, "MN", renderer)

        self.drawwater = True

        if renderer.color_geo:
            renderer.color_geo = False
        self.rerenderActiveEditors(renderer.lastlayer)

        tips = set(open(path + "tips.txt", "r").readlines())
        self.tips = list(tips)
        self.last_lmb = True
        self.last_mmb = True
        self.last_rmb = True
        self.tips.remove("\n")
        self.nexttip()
        self.resize()
        self.rfa()

    def blit(self):
        super().blit()
        if self.onfield:
            bp = self.getmouse
            self.movemiddle(bp)

    def tiles(self):
        self.drawtiles = not self.drawtiles
        self.rfa()

    def GE(self):
        self.message = "GE"

    def TE(self):
        self.message = "TE"

    def LE(self):
        self.message = "LE"

    def FE(self):
        self.message = "FE"

    def CE(self):
        self.message = "CE"

    def LP(self):
        self.message = "LP"

    def PE(self):
        self.message = "PE"

    def HK(self):
        self.message = "HK"

    def save(self):
        self.savef()

    def saveas(self):
        self.saveasf()

    def render(self):
        self.savef()
        renderlevel(self.data)

    def quit(self):
        self.message = "quit"

    def nexttip(self):
        self.labels[0].set_text(self.returnkeytext(random.choice(self.tips).replace("\n", "").replace("\\n", "\n")))

    def report(self):
        report()

    def github(self):
        github()