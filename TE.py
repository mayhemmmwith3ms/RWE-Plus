from menuclass import *
from lingotojson import *
import random

blocks = [
    {"tiles": ["A"], "upper": "dense", "lower": "dense", "tall":1, "freq":5},
    {"tiles": ["B1"], "upper": "espaced", "lower": "dense", "tall": 1, "freq": 5},
    {"tiles": ["B2"], "upper": "dense", "lower": "espaced", "tall": 1, "freq": 5},
    {"tiles": ["B3"], "upper": "ospaced", "lower": "dense", "tall": 1, "freq": 5},
    {"tiles": ["B4"], "upper": "dense", "lower": "ospaced", "tall": 1, "freq": 5},
    {"tiles": ["C1"], "upper": "espaced", "lower": "espaced", "tall": 1, "freq": 5},
    {"tiles": ["C2"], "upper": "ospaced", "lower": "ospaced", "tall": 1, "freq": 5},
    {"tiles": ["E1"], "upper": "ospaced", "lower": "espaced", "tall": 1, "freq": 5},
    {"tiles": ["E2"], "upper": "espaced", "lower": "ospaced", "tall": 1, "freq": 5},
    {"tiles": ["F1"], "upper": "dense", "lower": "dense", "tall": 2, "freq": 1},
    {"tiles": ["F2"], "upper": "dense", "lower": "dense", "tall": 2, "freq": 1},
    {"tiles": ["F1", "F2"], "upper": "dense", "lower": "dense", "tall": 2, "freq": 5},
    {"tiles": ["F3"], "upper": "dense", "lower": "dense", "tall": 2, "freq": 5},
    {"tiles": ["F4"], "upper": "dense", "lower": "dense", "tall": 2, "freq": 5},
    {"tiles": ["G1", "G2"], "upper": "dense", "lower": "ospaced", "tall": 2, "freq": 5},
    {"tiles": ["I"], "upper": "espaced", "lower": "dense", "tall": 1, "freq": 4},
    {"tiles": ["J1"], "upper": "ospaced", "lower": "ospaced", "tall": 2, "freq": 1},
    {"tiles": ["J2"], "upper": "ospaced", "lower": "ospaced", "tall": 2, "freq": 1},
    {"tiles": ["J1", "J2"], "upper": "ospaced", "lower": "ospaced", "tall": 2, "freq": 2},
    {"tiles": ["J3"], "upper": "espaced", "lower": "espaced", "tall": 2, "freq": 1},
    {"tiles": ["J4"], "upper": "espaced", "lower": "espaced", "tall": 2, "freq": 1},
    {"tiles": ["J3", "J4"], "upper": "espaced", "lower": "espaced", "tall": 2, "freq": 2},
    {"tiles": ["B1", "I"], "upper": "espaced", "lower": "dense", "tall": 1, "freq": 2}
]


class TE(MenuWithField):

    def __init__(self, surface: pg.surface.Surface, renderer: render.Renderer):
        self.menu = "TE"
        self.tool = 0 # 0 - place, 1 - destroy, 2 - copy

        self.matshow = False

        self.items = renderer.tiles
        p = json.load(open(path + "patterns.json", "r"))
        self.items["special"] = p["patterns"]
        for indx, pattern in enumerate(p["patterns"]):
            self.items["special"][indx]["cat"] = [len(self.items), indx + 1]
        self.blocks = p["blocks"]
        self.buttonslist = []
        self.toolindex = 0
        self.brushmode = False
        self.squarebrush = False

        self.tileimage = None
        self.tileimage2 = None
        self.mpos = [0, 0]
        self.cols = False

        self.lastfg = False
        self.lastfp = False
        self.brushsize = 1

        renderer.commsgeocolors = False
        renderer.geo_full_render(renderer.lastlayer)

        super().__init__(surface, "TE", renderer, False)
        self.catlist = [[]]
        for category in self.items.keys():
            self.catlist[-1].append(category)
            if len(self.catlist[-1]) >= self.settings["category_count"]:
                self.catlist.append([])
        self.drawtiles = True
        self.set("materials 0", "Standard")
        self.currentcategory = len(self.items) - 2
        self.labels[2].set_text("Default material: " + self.data["TE"]["defaultMaterial"])
        self.rfa()
        self.rebuttons()
        self.blit()
        self.resize()

    def brush(self):
        self.brushmode = True

    def pencil(self):
        self.squarebrush = not self.squarebrush

    def togglebrush(self):
        self.brushmode = not self.brushmode
        self.squarebrush = True
        self.tool = 0
        self.brushsize = 3

    def brushp(self):
        self.brushsize += 1

    def brushm(self):
        self.brushsize = max(self.brushsize-1, 1)

    def GE(self):
        self.message = "GE"

    def blit(self):
        pg.draw.rect(self.surface, settings["TE"]["menucolor"], pg.rect.Rect(self.buttonslist[0].xy, [self.buttonslist[0].rect.w, len(self.buttonslist[:-1]) * self.buttonslist[0].rect.h + 1]))
        for button in self.buttonslist:
            button.blitshadow()
        for i, button in enumerate(self.buttonslist[:-1]):
            button.blit(sum(pg.display.get_window_size()) // 120)
        self.buttonslist[-1].blit(sum(pg.display.get_window_size()) // 100)
        try:
            cir = [self.buttonslist[self.toolindex].rect.x + 3, self.buttonslist[self.toolindex].rect.y + self.buttonslist[self.toolindex].rect.h / 2]
        except IndexError:
            self.toolindex = 0
            cir = [self.buttonslist[self.toolindex].rect.x + 3, self.buttonslist[self.toolindex].rect.y + self.buttonslist[self.toolindex].rect.h / 2]
        pg.draw.circle(self.surface, cursor, cir, self.buttonslist[self.toolindex].rect.h / 2)
        super().blit()
        mpos = pg.mouse.get_pos()
        bp = self.getmouse
        if self.onfield and self.tileimage is not None:
            # cords = [math.floor(pg.mouse.get_pos()[0] / self.size) * self.size, math.floor(pg.mouse.get_pos()[1] / self.size) * self.size]
            # self.surface.blit(self.tools, pos, [curtool, graphics["tilesize"]])
            pos2 = self.pos2
            posoffset = self.posoffset
            fg = self.findparampressed("force_geometry")
            fp = self.findparampressed("force_place")

            self.movemiddle(bp)

            if settings["TE"]["officialMouseControlStyle"]:
                if self.tileimage["tp"] != "pattern":
                    cposx = int(pos2.x) - int((self.tileimage["size"][0] * .5) + .5) * self.size + self.size
                    cposy = int(pos2.y) - int((self.tileimage["size"][1] * .5) + .5) * self.size + self.size

                    cposxo = int(posoffset.x) - int((self.tileimage["size"][0] * .5) + .5) + 1
                    cposyo = int(posoffset.y) - int((self.tileimage["size"][1] * .5) + .5) + 1

                    if posoffset != self.mpos or self.lastfg != fg or self.lastfp != fp:
                        self.cols = self.test_cols(cposxo, cposyo)
                        self.mpos = posoffset
                        self.lastfg = fg
                        self.lastfp = fp
                        self.labels[1].set_text(f"X: {int(posoffset.x)}, Y: {int(posoffset.y)}, Work Layer: {self.layer + 1}")
                        if self.canplaceit(posoffset.x, posoffset.y, posoffset.x, posoffset.y):
                            self.labels[0].set_text(
                                "Tile: " + str(self.data["TE"]["tlMatrix"][int(posoffset.x)][int(posoffset.y)][self.layer]))
                    bord = (self.size // image1size + 1) // 2
                    selectrect = [
                        [cposx - bord, cposy - bord],
                        [self.tileimage["image"].get_width() + bord * 2, self.tileimage["image"].get_height() + bord * 2]
                        ]
                    drawTilePreview = True
                    if not (self.tool == 1 and (bp[0] or bp[2])):
                        if self.cols and not bp[2] and self.tool == 0:
                            rectCol = canplace
                        elif self.tool == 1:
                            rectCol = purple
                        elif self.tool == 2:
                            rectCol = blue
                        else:
                            rectCol = cannotplace

                        if(self.brushmode):
                            if self.squarebrush:
                                rect = pg.Rect([pos2 - [(self.brushsize // 2) * self.size, (self.brushsize // 2) * self.size], [self.brushsize * self.size, self.brushsize * self.size]])
                                pg.draw.rect(self.surface, rectCol, rect, 1)
                            else:
                               pg.draw.circle(self.surface, select, pos2+pg.Vector2(self.size/2), self.size * self.brushsize, 1)
                        else:
                            pg.draw.rect(self.surface, rectCol, selectrect, 1)

                    if bp[2]:
                        drawTilePreview = False

                    if drawTilePreview:
                        self.tileimage["image"].set_colorkey([255, 255, 255])
                        self.surface.blit(self.tileimage["image"], [cposx, cposy])
                        self.printcols(cposxo, cposyo, self.tileimage)
                
                def singlefirstframe(place):
                    if(place):
                        self.mousp = False
                    else:
                        self.mousp2 = False
                    self.emptyarea()

                def singleheld(place):
                    if place:
                        if self.tileimage["tp"] != "pattern" or self.tool == 0:
                            if self.brushmode:
                                self.brushpaint(pg.Vector2(cposxo, cposyo))
                            elif self.cols:
                                self.place(cposxo, cposyo)
                                self.fieldadd.blit(self.tileimage["image"],
                                                [cposxo * self.size, cposyo * self.size])
                    else:
                        if self.tileimage["tp"] != "pattern" or self.tool == 0:
                            if self.brushmode:
                                self.brushpaint(pg.Vector2(cposxo, cposyo), False)
                            else:
                                self.destroy(posoffset.x, posoffset.y)
                                pg.draw.rect(self.fieldadd, red, [posoffset.x * self.size, posoffset.y * self.size, self.size, self.size])

                def singlelastframe(place):
                        self.detecthistory(["TE", "tlMatrix"], not fg)
                        if fg:
                            self.detecthistory(["GE"])
                        self.fieldadd.fill(white)
                        if(place):
                            self.mousp = True
                        else:
                            self.mousp2 = True
                        self.renderer.tiles_render_area(self.area, self.layer)
                        self.renderer.geo_render_area(self.area, self.layer)
                        self.rfa()
                        self.cols = self.test_cols(cposxo, cposyo)

                def rectfirstframe(place):
                    if(place):
                        self.mousp = False
                    else:
                        self.mousp2 = False
                    self.rectdata = [posoffset, pg.Vector2(0, 0), pos2]
                    self.emptyarea()

                def rectheld(place):
                    self.rectdata[1] = posoffset - self.rectdata[0]

                    righthalf = mpos[0] > self.rectdata[2].x + 10
                    upperhalf = mpos[1] > self.rectdata[2].y + 10
                    
                    tl = [0, 0]
                    br = [0, 0]

                    if not righthalf:
                        tl[0] = pos2.x
                        br[0] = self.rectdata[2].x + self.size
                    else:
                        tl[0] = self.rectdata[2].x
                        br[0] = pos2.x + self.size

                    if upperhalf:
                        tl[1] = pos2.y + self.size
                        br[1] = self.rectdata[2].y
                    else:
                        tl[1] = self.rectdata[2].y + self.size
                        br[1] = pos2.y
                    
                    rectColor = purple
                    if not place:
                        rectColor = select

                    rect = self.vec2rect(pg.Vector2(tl), pg.Vector2(br))
                    tx = f"{int(rect.w / self.size)}, {int(rect.h / self.size)}"
                    widgets.fastmts(self.surface, tx, *mpos, white)
                    pg.draw.rect(self.surface, rectColor, rect, 1)

                def rectlastframe(place):
                    righthalf = mpos[0] > self.rectdata[2].x + 10
                    upperhalf = mpos[1] > self.rectdata[2].y + 10
                    
                    tl = [0, 0]
                    br = [0, 0]

                    if not righthalf:
                        tl[0] = posoffset.x
                        br[0] = self.rectdata[0].x + 1
                    else:
                        tl[0] = self.rectdata[0].x
                        br[0] = posoffset.x + 1

                    if upperhalf:
                        tl[1] = posoffset.y + 1
                        br[1] = self.rectdata[0].y
                    else:
                        tl[1] = self.rectdata[0].y + 1
                        br[1] = posoffset.y

                    rect = self.vec2rect(pg.Vector2(tl), pg.Vector2(br))
                    if self.tileimage["tp"] != "pattern" and self.tool != 2:
                        for x in range(int(rect.w)):
                            for y in range(int(rect.h)):
                                if place:
                                    self.place(x + rect.x, y + rect.y)
                                else:
                                    self.destroy(x + rect.x, y + rect.y)
                    elif self.tool == 2:  # copy
                        history = []
                        for x in range(int(rect.w)):
                            for y in range(int(rect.h)):
                                xpos, ypos = x + rect.x, y + rect.y
                                block = self.data["TE"]["tlMatrix"][xpos][ypos][self.layer]
                                if block["tp"] == "material" or block["tp"] == "tileHead":
                                    history.append([x, y, block])
                        pyperclip.copy(str(history))
                    elif place and self.tileimage["tp"] == "pattern":
                        saved = self.tileimage
                        savedtool = saved["name"]
                        savedcat = saved["category"]
                        save = self.currentcategory
                        for y in range(int(rect.h)):
                            for x in range(int(rect.w)):
                                if x == 0 and y == 0:
                                    self.set(self.blocks["cat"], self.blocks["NW"])
                                elif x == rect.w - 1 and y == 0:
                                    self.set(self.blocks["cat"], self.blocks["NE"])
                                elif x == 0 and y == rect.h - 1:
                                    self.set(self.blocks["cat"], self.blocks["SW"])
                                elif x == rect.w - 1 and y == rect.h - 1:
                                    self.set(self.blocks["cat"], self.blocks["SE"])

                                elif x == 0:
                                    self.set(self.blocks["cat"], self.blocks["W"])
                                elif y == 0:
                                    self.set(self.blocks["cat"], self.blocks["N"])
                                elif x == rect.w - 1:
                                    self.set(self.blocks["cat"], self.blocks["E"])
                                elif y == rect.h - 1:
                                    self.set(self.blocks["cat"], self.blocks["S"])
                                else:
                                    continue
                                self.place(x + rect.x, y + rect.y)
                        skip = False
                        lastch = random.choice(blocks)
                        for y in range(1, int(rect.h) - 1):
                            if skip:
                                skip = False
                                continue
                            ch = random.choice(blocks)
                            while ch["upper"] != lastch["lower"] or ch["tiles"] == lastch["tiles"]:
                                ch = random.choice(blocks)
                            if y == self.rectdata[1].y - 2 and ch["tall"] == 2:
                                while ch["upper"] != lastch["lower"] or ch["tall"] == 2 or ch["tiles"] == lastch["tiles"]:
                                    ch = random.choice(blocks)
                            lastch = ch.copy()
                            if ch["tall"] == 2:
                                skip = True
                            for x in range(1, int(rect.w) - 1):
                                n = 0
                                if len(ch["tiles"]) > 1:
                                    n = x % len(ch["tiles"]) - 1
                                self.set(saved["patcat"], saved["prefix"] + ch["tiles"][n])
                                self.place(x + rect.x, y + rect.y)
                        self.set(savedcat, savedtool)
                        self.currentcategory = save
                        self.rebuttons()
                    self.detecthistory(["TE", "tlMatrix"])
                    if fg:
                        self.detecthistory(["GE"])
                    self.renderer.tiles_render_area(self.area, self.layer)
                    self.renderer.geo_render_area(self.area, self.layer)
                    self.rfa()
                    self.cols = self.test_cols(cposxo, cposyo)
                    if(place):
                        self.mousp = True
                    else:
                        self.mousp2 = True
                        
                if self.tool == 0:
                    if bp[0] == 1 and self.mousp and (self.mousp2 and self.mousp1):
                        singlefirstframe(True)
                    elif bp[0] == 1 and not self.mousp and (self.mousp2 and self.mousp1):
                        singleheld(True)
                    elif bp[0] == 0 and not self.mousp and (self.mousp2 and self.mousp1):
                        singlelastframe(True)

                    if bp[2] == 1 and self.mousp2 and (self.mousp and self.mousp1):
                        singlefirstframe(False)
                    elif bp[2] == 1 and not self.mousp2 and (self.mousp and self.mousp1):
                        singleheld(False)
                    elif bp[2] == 0 and not self.mousp2 and (self.mousp and self.mousp1):
                        singlelastframe(False)
                else:
                    if bp[0] == 1 and self.mousp and (self.mousp2 and self.mousp1):
                        rectfirstframe(True)
                    elif bp[0] == 1 and not self.mousp and (self.mousp2 and self.mousp1):
                        rectheld(True)
                    elif bp[0] == 0 and not self.mousp and (self.mousp2 and self.mousp1):
                        rectlastframe(True)

                    if bp[2] == 1 and self.mousp2 and (self.mousp and self.mousp1):
                        rectfirstframe(False)
                    elif bp[2] == 1 and not self.mousp2 and (self.mousp and self.mousp1):
                        rectheld(False)
                    elif bp[2] == 0 and not self.mousp2 and (self.mousp and self.mousp1):
                        rectlastframe(False)
            else:
                if self.tileimage["tp"] != "pattern":
                    cposx = int(pos2.x) - int((self.tileimage["size"][0] * .5) + .5) * self.size + self.size
                    cposy = int(pos2.y) - int((self.tileimage["size"][1] * .5) + .5) * self.size + self.size

                    cposxo = int(posoffset.x) - int((self.tileimage["size"][0] * .5) + .5) + 1
                    cposyo = int(posoffset.y) - int((self.tileimage["size"][1] * .5) + .5) + 1

                    if posoffset != self.mpos or self.lastfg != fg:
                        self.cols = self.test_cols(cposxo, cposyo)
                        self.mpos = posoffset
                        self.lastfg = fg
                        self.labels[1].set_text(f"X: {int(posoffset.x)}, Y: {int(posoffset.y)}, Work Layer: {self.layer + 1}")
                        if self.canplaceit(posoffset.x, posoffset.y, posoffset.x, posoffset.y):
                            self.labels[0].set_text(
                                "Tile: " + str(self.data["TE"]["tlMatrix"][int(posoffset.x)][int(posoffset.y)][self.layer]))
                    bord = 1#self.size // image1size + 1
                    if self.cols and self.tool == 0:
                        pg.draw.rect(self.surface, canplace, [[cposx - bord, cposy - bord],
                                                            [self.tileimage["image"].get_width() + bord * 2,
                                                            self.tileimage["image"].get_height() + bord * 2]], bord)
                    elif self.tool == 2:
                        pg.draw.rect(self.surface, blue, [[cposx - bord, cposy - bord],
                                                                [self.tileimage["image"].get_width() + bord * 2,
                                                                self.tileimage["image"].get_height() + bord * 2]], bord)
                    else:
                        pg.draw.rect(self.surface, cannotplace, [[cposx - bord, cposy - bord],
                                                                [self.tileimage["image"].get_width() + bord * 2,
                                                                self.tileimage["image"].get_height() + bord * 2]], bord)
                    if self.tool == 0:
                        self.tileimage["image"].set_colorkey([255, 255, 255])
                        self.surface.blit(self.tileimage["image"], [cposx, cposy])
                        self.printcols(cposxo, cposyo, self.tileimage)
                if self.brushmode:
                    if self.squarebrush:
                        rect = pg.Rect([pos2, [self.brushsize * self.size, self.brushsize * self.size]])
                        pg.draw.rect(self.surface, select, rect, 3)
                    else:
                        pg.draw.circle(self.surface, select, pos2+pg.Vector2(self.size/2), self.size * self.brushsize, 5)
                if bp[0] == 1 and self.mousp and (self.mousp2 and self.mousp1):
                    self.mousp = False
                    self.emptyarea()
                elif bp[0] == 1 and not self.mousp and (self.mousp2 and self.mousp1):
                    # if (0 <= posoffset[0] < self.levelwidth) and (0 <= posoffset[1] < self.levelheight):
                    #     pass
                    if self.tileimage["tp"] != "pattern" or self.tool == 0:
                        if self.tool == 0:
                            if self.cols:
                                    self.place(cposxo, cposyo)
                                    self.fieldadd.blit(self.tileimage["image"],
                                                    [cposxo * self.size, cposyo * self.size])
                        elif self.tool == 1:
                            self.destroy(posoffset.x, posoffset.y)
                            pg.draw.rect(self.fieldadd, red, [posoffset.x * self.size, posoffset.y * self.size, self.size, self.size])
                elif bp[0] == 0 and not self.mousp and (self.mousp2 and self.mousp1):
                    self.detecthistory(["TE", "tlMatrix"], not fg)
                    if fg:
                        self.detecthistory(["GE"])
                    self.fieldadd.fill(white)
                    self.mousp = True
                    self.renderer.tiles_render_area(self.area, self.layer)
                    self.renderer.geo_render_area(self.area, self.layer)
                    self.rfa()

                if bp[2] == 1 and self.mousp2 and (self.mousp and self.mousp1):
                    self.mousp2 = False
                    self.rectdata = [posoffset, pg.Vector2(0, 0), pos2]
                    self.emptyarea()
                elif bp[2] == 1 and not self.mousp2 and (self.mousp and self.mousp1):
                    self.rectdata[1] = posoffset - self.rectdata[0]

                    righthalf = mpos[0] > self.rectdata[2].x + 10
                    upperhalf = mpos[1] > self.rectdata[2].y + 10
                    
                    tl = [0, 0]
                    br = [0, 0]

                    if not righthalf:
                        tl[0] = pos2.x
                        br[0] = self.rectdata[2].x + self.size
                    else:
                        tl[0] = self.rectdata[2].x
                        br[0] = pos2.x + self.size

                    if upperhalf:
                        tl[1] = pos2.y + self.size
                        br[1] = self.rectdata[2].y
                    else:
                        tl[1] = self.rectdata[2].y + self.size
                        br[1] = pos2.y

                    rect = self.vec2rect(pg.Vector2(tl), pg.Vector2(br))
                    tx = f"{int(rect.w / self.size)}, {int(rect.h / self.size)}"
                    widgets.fastmts(self.surface, tx, *mpos, white)
                    pg.draw.rect(self.surface, select, rect, 1)
                elif bp[2] == 0 and not self.mousp2 and (self.mousp and self.mousp1):
                    # self.rectdata = [self.rectdata[0], posoffset]
                    righthalf = mpos[0] > self.rectdata[2].x + 10
                    upperhalf = mpos[1] > self.rectdata[2].y + 10
                    
                    tl = [0, 0]
                    br = [0, 0]

                    if not righthalf:
                        tl[0] = posoffset.x
                        br[0] = self.rectdata[0].x + 1
                    else:
                        tl[0] = self.rectdata[0].x
                        br[0] = posoffset.x + 1

                    if upperhalf:
                        tl[1] = posoffset.y + 1
                        br[1] = self.rectdata[0].y
                    else:
                        tl[1] = self.rectdata[0].y + 1
                        br[1] = posoffset.y

                    rect = self.vec2rect(pg.Vector2(tl), pg.Vector2(br))
                    if self.tileimage["tp"] != "pattern" and self.tool != 2:
                        for x in range(int(rect.w)):
                            for y in range(int(rect.h)):
                                if self.tool == 0:
                                    self.place(x + rect.x, y + rect.y)
                                elif self.tool == 1:
                                    self.destroy(x + rect.x, y + rect.y)
                    elif self.tool == 2:  # copy
                        history = []
                        for x in range(int(rect.w)):
                            for y in range(int(rect.h)):
                                xpos, ypos = x + rect.x, y + rect.y
                                block = self.data["TE"]["tlMatrix"][xpos][ypos][self.layer]
                                if block["tp"] == "material" or block["tp"] == "tileHead":
                                    history.append([x, y, block])
                        pyperclip.copy(str(history))
                    elif self.tool == 0 and self.tileimage["tp"] == "pattern":
                        saved = self.tileimage
                        savedtool = saved["name"]
                        savedcat = saved["category"]
                        save = self.currentcategory
                        for y in range(int(rect.h)):
                            for x in range(int(rect.w)):
                                if x == 0 and y == 0:
                                    self.set(self.blocks["cat"], self.blocks["NW"])
                                elif x == rect.w - 1 and y == 0:
                                    self.set(self.blocks["cat"], self.blocks["NE"])
                                elif x == 0 and y == rect.h - 1:
                                    self.set(self.blocks["cat"], self.blocks["SW"])
                                elif x == rect.w - 1 and y == rect.h - 1:
                                    self.set(self.blocks["cat"], self.blocks["SE"])

                                elif x == 0:
                                    self.set(self.blocks["cat"], self.blocks["W"])
                                elif y == 0:
                                    self.set(self.blocks["cat"], self.blocks["N"])
                                elif x == rect.w - 1:
                                    self.set(self.blocks["cat"], self.blocks["E"])
                                elif y == rect.h - 1:
                                    self.set(self.blocks["cat"], self.blocks["S"])
                                else:
                                    continue
                                self.place(x + rect.x, y + rect.y)
                        skip = False
                        lastch = random.choice(blocks)
                        for y in range(1, int(rect.h) - 1):
                            if skip:
                                skip = False
                                continue
                            ch = random.choice(blocks)
                            while ch["upper"] != lastch["lower"] or ch["tiles"] == lastch["tiles"]:
                                ch = random.choice(blocks)
                            if y == self.rectdata[1].y - 2 and ch["tall"] == 2:
                                while ch["upper"] != lastch["lower"] or ch["tall"] == 2 or ch["tiles"] == lastch["tiles"]:
                                    ch = random.choice(blocks)
                            lastch = ch.copy()
                            if ch["tall"] == 2:
                                skip = True
                            for x in range(1, int(rect.w) - 1):
                                n = 0
                                if len(ch["tiles"]) > 1:
                                    n = x % len(ch["tiles"]) - 1
                                self.set(saved["patcat"], saved["prefix"] + ch["tiles"][n])
                                self.place(x + rect.x, y + rect.y)
                        self.set(savedcat, savedtool)
                        self.currentcategory = save
                        self.rebuttons()
                    self.detecthistory(["TE", "tlMatrix"])
                    if fg:
                        self.detecthistory(["GE"])
                    self.renderer.tiles_render_area(self.area, self.layer)
                    self.renderer.geo_render_area(self.area, self.layer)
                    self.rfa()
                    self.mousp2 = True
        else:
            if not self.matshow:
                for index, button in enumerate(self.buttonslist[:-1]):
                    if button.onmouseover():
                        cat = list(self.items.keys())[self.currentcategory]
                        item = self.items[cat][index]
                        if item.get("preview"):
                            previewPos = button.rect.bottomright
                            if settings["global"]["previewleftside"]:
                                previewPos = [button.rect.bottomleft[0] - item["preview"].get_width(), button.rect.bottomleft[1]]
                            self.surface.blit(item["preview"], previewPos)
                        if item["tp"] == "pattern":
                            break
                        w, h = item["size"]
                        w *= self.size
                        h *= self.size
                        if not settings["TE"]["LEtiles"]:
                            pg.draw.rect(self.surface, item["color"], [self.field.rect.x, self.field.rect.y, w, h])
                        self.surface.blit(pg.transform.scale(item["image"], [w, h]), [self.field.rect.x, self.field.rect.y])
                        self.printcols(0, 0, item, True)
                        break
        for button in self.buttonslist:
            button.blittooltip()
        if pg.key.get_pressed()[pg.K_LCTRL]:
            try:
                geodata: list = eval(pyperclip.paste())
                if type(geodata) != list:
                    return
                pos = self.field.rect.topleft + (self.pos * self.size if self.onfield else pg.Vector2(0, 0))
                geodata.sort(key=lambda x: x[0])
                sizex = geodata[-1][0] + 1
                geodata.sort(key=lambda y: y[1])
                sizey = geodata[-1][1] + 1
                rect = pg.Rect([pos, pg.Vector2(sizex, sizey) * self.size])
                pg.draw.rect(self.surface, blue, rect, 1)
            except:
                pass

    def brushpaint(self, pos: pg.Vector2, place = True):
        if self.squarebrush:
            for xp in range(self.brushsize):
                for yp in range(self.brushsize):
                    vecx = int(pos.x) + xp - self.brushsize // 2
                    vecy = int(pos.y) + yp - self.brushsize // 2
                    if place:
                        self.place(vecx, vecy, True)
                    else:
                        self.destroy(vecx, vecy)
            if not place:
                pg.draw.rect(self.fieldadd, red, [(int(pos.x) - self.brushsize // 2) * self.size, (int(pos.y) - self.brushsize // 2) * self.size, self.brushsize * self.size, self.brushsize * self.size])
        else:
            for xp, xd in enumerate(self.data["GE"]):
                for yp, yd in enumerate(xd):
                    vec = pg.Vector2(xp, yp)
                    dist = pos.distance_to(vec)
                    if dist <= self.brushsize and self.area[xp][yp]:
                        if place:
                            self.place(int(vec.x), int(vec.y), True)
                        else:
                            self.destroy(int(vec.x), int(vec.y))

    def cats(self):
        self.buttonslist = []
        if not self.matshow: # if cats not already used
            self.currentcategory = self.toolindex // self.settings["category_count"]
            self.toolindex %= self.settings["category_count"]
        btn2 = None
        self.matshow = True
        for count, item in enumerate(self.catlist[self.currentcategory]):
            # rect = pg.rect.Rect([0, count * self.settings["itemsize"], self.field2.field.get_width(), self.settings["itemsize"]])
            # rect = pg.rect.Rect(0, 0, 100, 10)
            cat = pg.rect.Rect(self.settings["catpos"])
            btn2 = widgets.button(self.surface, cat, settings["global"]["color"], f"Categories {self.currentcategory}", onpress=self.changematshow)

            rect = pg.rect.Rect(self.settings["itempos"])
            rect = rect.move(0, rect.h * count)
            col = self.items[item][0]["color"]
            if count == self.toolindex:
                col = darkgray
            btn = widgets.button(self.surface, rect, col, item, onpress=self.selectcat)
            self.buttonslist.append(btn)
        if btn2 is not None:
            self.buttonslist.append(btn2)
        self.resize()

    def pastedata(self):
        try:
            geodata = eval(pyperclip.paste())
            if type(geodata) != list or len(pyperclip.paste()) <= 2:
                print("Error pasting data!")
                return
            self.emptyarea()
            for block in geodata:
                blockx, blocky, data = block
                if data["tp"] == "material":
                    name = data["data"]
                else:
                    name = data["data"][1]
                cat = self.findcat(name)
                self.set(cat, name, False)
                # w, h = self.tileimage["size"]
                # px = blockx - int((w * .5) + .5) - 1
                # py = blocky - int((h * .5) + .5) - 1
                pa = pg.Vector2(0, 0)
                if self.field.rect.collidepoint(pg.mouse.get_pos()):
                    pa = self.pos
                self.place(blockx - self.xoffset + int(pa.x), blocky - self.yoffset + int(pa.y))
            else:
                self.selectcat(cat)
            self.detecthistory(["TE", "tlMatrix"])
            self.renderer.tiles_render_area(self.area, self.layer)
            self.rfa()
        except:
            print("Error pasting data!")

    def findcat(self, itemname):
        for name, listdata in self.items.items():
            for bl in listdata:
                if bl["name"] == itemname:
                    return name
        return None

    def copytool(self):
        self.tool = 2

    def selectcat(self, name):
        self.currentcategory = list(self.items.keys()).index(name)
        self.toolindex = 0
        self.rebuttons()

    def rebuttons(self):
        self.buttonslist = []
        self.matshow = False
        btn2 = None
        for count, item in enumerate(self.items[list(self.items.keys())[self.currentcategory]]):
            # rect = pg.rect.Rect([0, count * self.settings["itemsize"], self.field2.field.get_width(), self.settings["itemsize"]])
            # rect = pg.rect.Rect(0, 0, 100, 10)
            cat = pg.rect.Rect(self.settings["catpos"])
            btn2 = widgets.button(self.surface, cat, settings["global"]["color"], item["category"], onpress=self.changematshow,
                                  tooltip=self.returnkeytext("Select category(<[-changematshow]>)"))

            rect = pg.rect.Rect(self.settings["itempos"])
            rect = rect.move(0, rect.h * count)
            if item["category"] == "special" or "material" in item["tags"]:
                btn = widgets.button(self.surface, rect, item["color"], item["name"], onpress=self.getmaterial)
            else:
                tooltip = "Size: " + str(item["size"])
                btn = widgets.button(self.surface, rect, item["color"], item["name"], onpress=self.getblock, tooltip=tooltip)
            self.buttonslist.append(btn)
        if btn2 is not None:
            self.buttonslist.append(btn2)
        self.resize()

    def resize(self):
        super().resize()
        if hasattr(self, "field"):
            self.field.resize()
            for i in self.buttonslist:
                i.resize()
            self.renderfield()

    def renderfield(self):
        self.fieldadd = pg.transform.scale(self.fieldadd,
                                           [self.levelwidth * self.size, self.levelheight * self.size])
        self.fieldadd.fill(white)
        super().renderfield()
        if self.tileimage is not None and self.tileimage["tp"] != "pattern":
            self.tileimage["image"] = pg.transform.scale(self.tileimage2["image"], [self.size * self.tileimage2["size"][0],
                                                                                self.size * self.tileimage2["size"][1]])
            self.tileimage["image"].set_colorkey(None)

    def lt(self):
        if self.matshow:
            if self.currentcategory - 1 < 0:
                self.currentcategory = len(self.catlist) - 1
            else:
                self.currentcategory = self.currentcategory - 1
            self.cats()
            self.toolindex = self.toolindex if len(self.buttonslist) - 1 > self.toolindex else 0
        else:
            if self.currentcategory - 1 < 0:
                self.currentcategory = len(self.items) - 1
            else:
                self.currentcategory = self.currentcategory - 1
            self.set(list(self.items)[self.currentcategory], self.items[list(self.items)[self.currentcategory]][0]["name"])
            self.rebuttons()

    def rt(self):
        if self.matshow:
            self.currentcategory = (self.currentcategory + 1) % len(self.catlist)
            self.cats()
            self.toolindex = self.toolindex if len(self.buttonslist) - 1 > self.toolindex else 0
        else:
            self.currentcategory = (self.currentcategory + 1) % len(self.items)
            self.set(list(self.items)[self.currentcategory], self.items[list(self.items)[self.currentcategory]][0]["name"])
            self.rebuttons()

    def dt(self):
        self.toolindex += 1
        if self.toolindex > len(self.buttonslist) - 2:
            self.toolindex = 0
        if not self.matshow:
            cat = list(self.items.keys())[self.currentcategory]
            self.set(cat, self.items[cat][self.toolindex]["name"])

    def ut(self):
        self.toolindex -= 1
        if self.toolindex < 0:
            self.toolindex = len(self.buttonslist) - 2
        if not self.matshow:
            cat = list(self.items.keys())[self.currentcategory]
            self.set(cat, self.items[cat][self.toolindex]["name"])

    def changematshow(self):
        if self.matshow:
            self.currentcategory = self.toolindex + self.currentcategory * self.settings["category_count"]
            self.toolindex = 0
            cat = list(self.items.keys())[self.currentcategory]
            self.set(cat, self.items[cat][0]["name"])
            self.rebuttons()
        else:
            self.toolindex = self.currentcategory
            self.cats()

    def getblock(self, text):
        cat = self.buttonslist[-1].text
        self.set(cat, text)

    def getmaterial(self, text):
        cat = self.buttonslist[-1].text
        self.set(cat, text)

    def set(self, cat, name, render=True):
        if not settings["TE"]["officialMouseControlStyle"]:
            self.tool = 0
        for num, i in enumerate(self.items[cat]):
            if i["name"] == name:
                self.toolindex = num
                self.tileimage2 = i.copy()
                if self.tileimage2["tp"] != "pattern" and render:
                    self.tileimage2["image"] = i["image"].copy()
                    self.tileimage2["image"].set_alpha(255)
                    self.tileimage = self.tileimage2.copy()

                    self.tileimage["image"] = pg.transform.scale(self.tileimage2["image"],
                                                                 [self.size * self.tileimage2["size"][0],
                                                                  self.size * self.tileimage2["size"][1]])
                    self.tileimage["image"].set_colorkey(None)
                else:
                    self.tileimage = self.tileimage2.copy()
                self.recaption()
                return

    def test_cols(self, x, y):
        force_place = self.findparampressed("force_place")
        force_geo = self.findparampressed("force_geometry") or force_place
        w, h = self.tileimage["size"]
        sp = self.tileimage["cols"][0]
        sp2 = self.tileimage["cols"][1]
        px = x + int((w * .5) + .5) - 1  # center coordinates
        py = y + int((h * .5) + .5) - 1
        if px >= self.levelwidth or py >= self.levelheight or px < 0 or py < 0:
            return False
        #if x + w > self.levelwidth or y + h > self.levelheight or x < 0 or y < 0:
        #    return False
        if "material" in self.tileimage["tags"]:
            return (self.data["GE"][x][y][self.layer][0] not in [0] or force_geo) \
                and self.data["TE"]["tlMatrix"][x][y][self.layer]["tp"] == "default"
        for x2 in range(w):
            for y2 in range(h):
                csp = sp[x2 * h + y2]
                xpos = int(x + x2)
                ypos = int(y + y2)
                if xpos >= self.levelwidth or ypos >= self.levelheight or xpos < 0 or ypos < 0:
                    continue
                if csp != -1:
                    if self.data["TE"]["tlMatrix"][xpos][ypos][self.layer]["tp"] not in ["default", "material"] and not (self.data["TE"]["tlMatrix"][xpos][ypos][self.layer]["tp"] in ["default", "material", "tileBody"] and force_place):
                        return False
                    if self.data["GE"][xpos][ypos][self.layer][0] != csp and not force_geo:
                        return False
                if sp2 != 0:
                    if self.layer + 1 <= 2:
                        csp2 = sp2[x2 * h + y2]
                        if csp2 != -1:
                            if self.data["TE"]["tlMatrix"][xpos][ypos][self.layer + 1]["tp"] not in ["default", "material"] and not (self.data["TE"]["tlMatrix"][xpos][ypos][self.layer + 1]["tp"] in ["default", "material", "tileBody"] and force_place):
                                return False
                            if self.data["GE"][xpos][ypos][self.layer + 1][0] != csp2 and not force_geo:
                                return False

        return True
        # self.data["TE"]

    def printcols(self, x, y, tile, prev=False):
        def printtile(sft, color):
            if prev:
                px = x2 * self.size + self.field.rect.x + sft
                py = y2 * self.size + self.field.rect.y + sft
            else:
                px = (x + x2 + self.xoffset) * self.size + self.field.rect.x + sft
                py = (y + y2 + self.yoffset) * self.size + self.field.rect.y + sft
            match csp:
                case 1:
                    pg.draw.rect(self.surface, color, [px, py, self.size + 1, self.size + 1], 1)
                case 0:
                    pg.draw.circle(self.surface, color, [px + self.size / 2, py + self.size / 2], self.size / 2, 1)
                case 2:
                    pg.draw.polygon(self.surface, color,
                                    [[px, py], [px, py + self.size], [px + self.size, py + self.size]], 1)
                case 3:
                    pg.draw.polygon(self.surface, color,
                                    [[px, py + self.size], [px + self.size, py + self.size], [px + self.size, py]],
                                    1)
                case 4:
                    pg.draw.polygon(self.surface, color,
                                    [[px, py], [px, py + self.size], [px + self.size, py]], 1)
                case 5:
                    pg.draw.polygon(self.surface, color,
                                    [[px, py], [px + self.size, py + self.size], [px + self.size, py]], 1)

        w, h = tile["size"]
        sp = tile["cols"][0]
        sp2 = tile["cols"][1]
        shift = self.size // image1size + 1
        px = x + int((w * .5) + .5) - 1  # center coordinates
        py = y + int((h * .5) + .5) - 1
        if px >= self.levelwidth or py >= self.levelheight or px < 0 or py < 0:
            return
        if self.findparampressed("movepreview"):
            if prev:
                pg.draw.rect(self.surface, black, [self.field.rect.x, self.field.rect.y, w * self.size, h * self.size], 0)
            else:
                px = (x + self.xoffset) * self.size + self.field.rect.x
                py = (y + self.yoffset) * self.size + self.field.rect.y
                pg.draw.rect(self.surface, black, [px, py, w * self.size, h * self.size], 0)
        for x2 in range(w):
            for y2 in range(h):
                csp = sp[x2 * h + y2]
                if sp2 != 0:
                    try:
                        csp = sp2[x2 * h + y2]
                    except IndexError:
                        csp = -1
                    printtile(shift, layer2)
                    csp = sp[x2 * h + y2]
                    printtile(shift * 2, layer1)
                else:
                    printtile(shift, layer1)



    def place(self, x, y, render=False):
        fg = self.findparampressed("force_geometry")
        w, h = self.tileimage["size"]
        px = x + int((w * .5) + .5) - 1 # center coordinates
        py = y + int((h * .5) + .5) - 1
        p = makearr(self.tileimage["cat"], "point")
        sp = self.tileimage["cols"][0]
        sp2 = self.tileimage["cols"][1]
        if not self.test_cols(x, y):
            return
        if px > self.levelwidth or py > self.levelheight or px < 0 or py < 0:
            return
        if render:
            self.fieldadd.blit(self.tileimage["image"],
                               [x * self.size, y * self.size])
        for x2 in range(w):
            for y2 in range(h):
                csp = sp[x2 * h + y2]
                xpos = int(x + x2)
                ypos = int(y + y2)
                if xpos >= self.levelwidth or ypos >= self.levelheight or xpos < 0 or ypos < 0:
                    continue
                if "material" in self.tileimage["tags"]:
                    self.area[xpos][ypos] = False
                    self.data["TE"]["tlMatrix"][xpos][ypos][self.layer] = {"tp": "material",
                                                                           "data": self.tileimage["name"]}
                elif xpos == px and ypos == py:
                    self.area[xpos][ypos] = False
                    self.data["TE"]["tlMatrix"][xpos][ypos][self.layer] = {"tp": "tileHead",
                                                                           "data": [p, self.tileimage["name"]]}
                elif csp != -1:
                    p = makearr([px + 1, py + 1], "point")
                    # self.area[xpos][ypos] = False
                    self.data["TE"]["tlMatrix"][xpos][ypos][self.layer] = {"tp": "tileBody",
                                                                           "data": [p, self.layer + 1]}
                if fg and csp != -1 or fg and "material" in self.tileimage["tags"]:
                    if csp == -1:
                        csp = 1
                    self.area[xpos][ypos] = False
                    self.data["GE"][xpos][ypos][self.layer][0] = csp

                if sp2 != 0:
                    csp = sp2[x2 * h + y2]
                    if self.layer + 1 <= 2 and csp != -1:
                        p = makearr([px + 1, py + 1], "point")
                        self.data["TE"]["tlMatrix"][xpos][ypos][self.layer + 1] = {"tp": "tileBody",
                                                                                   "data": [p, self.layer + 1]}
                        if fg:
                            self.data["GE"][xpos][ypos][self.layer + 1][0] = csp
        self.mpos = 1
        #if fg:
        #    self.rfa()

    def sad(self):
        if "material" in self.tileimage["tags"]:
            self.data["TE"]["defaultMaterial"] = self.tileimage["name"]
        self.labels[2].set_text("Default material: " + self.data["TE"]["defaultMaterial"])

    def cleartool(self):
        self.tool = 1

    def changetools(self):
        self.tool = abs(1 - self.tool)
        self.brushmode = False

    def findtile(self):
        nd = {}
        for cat, item in self.items.items():  # cursed
            for i in item:
                nd[i["name"]] = cat
        name = self.find(nd, "Select a tile")
        if name is None:
            return
        cat = self.findcat(name)
        self.selectcat(cat)
        self.set(cat, name)

    def copytile(self):
        posoffset = self.posoffset
        if not 0 <= posoffset.x < self.levelwidth or not 0 <= posoffset.y < self.levelheight:
            return
        tile = self.data["TE"]["tlMatrix"][int(posoffset.x)][int(posoffset.y)][self.layer]
        name = "Standard"

        match tile["tp"]:
            case "default":
                return
            case "material":
                name = tile["data"]
            case "tileBody":
                pos = toarr(tile["data"][0], "point")
                pos[0] -= 1
                pos[1] -= 1
                tile = self.data["TE"]["tlMatrix"][pos[0]][pos[1]][tile["data"][1] - 1]

        if tile["tp"] == "tileHead":
            i = 0
            for catname, items in self.items.items():
                for item in items:
                    if item["name"] == tile["data"][1]:
                        cat = catname
                        name = tile["data"][1]
                        self.currentcategory = i
                        self.rebuttons()
                        self.set(cat, name)
                        return
                i += 1
        for catname, items in self.items.items():
            for item in items:
                if item["name"] == name:
                    self.currentcategory = list(self.items.keys()).index(item["category"])
                    self.rebuttons()
                    self.getmaterial(name)
                    return
        print("couldn't find tile")

    @property
    def custom_info(self):
        try:
            return f"{super().custom_info} | Selected tile: {self.tileimage['name']}"
        except TypeError:
            return super().custom_info
