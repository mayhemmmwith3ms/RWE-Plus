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
        self.pathtiles = p["path_tiles"]
        self.buttonslist = []
        self.toolindex = 0
        #self.brush_active = False
        self.squarebrush = True

        self.tileimage = None
        self.tileimage2 = None
        self.mpos = [0, 0]
        self.cols = False

        self.lastfg = False
        self.lastfp = False
        self.brushsize = 1

        self.justPlacedChainHolders = []
        self.blockNextPlacement = False
        self.currentPathDrag = []

        super().__init__(surface, "TE", renderer, False)
        self.catlist = [[]]
        for category in self.items.keys():
            self.catlist[-1].append(category)
            if len(self.catlist[-1]) >= self.menu_ui_settings["category_count"]:
                self.catlist.append([])
        self.drawtiles = True
        self.set("materials 0", "Standard")
        self.currentcategory = 0
        self.labels[2].set_text("Default material: " + self.data["TE"]["defaultMaterial"])

        if renderer.color_geo:
            renderer.color_geo = False
            self.rerenderActiveEditors(renderer.lastlayer)

        self.rfa()
        self.rebuttons()
        self.toolindex = self.currentcategory
        self.cats()
        self.blit()
        self.resize()

    def brush(self):
        self.brushsize = 2

    def pencil(self):
        self.squarebrush = not self.squarebrush

    def GE(self):
        self.message = "GE"

    def begin_drag(self, place):
        if not place:
            self.justPlacedChainHolders.clear()
        self.emptyarea()

    def update_drag(self, place):
        if not self.is_macro(self.tileimage):
            cposxo = int(self.posoffset.x) - int((self.tileimage["size"][0] * .5) + .5) + 1
            cposyo = int(self.posoffset.y) - int((self.tileimage["size"][1] * .5) + .5) + 1
        else:
            cposxo = int(self.posoffset.x)
            cposyo = int(self.posoffset.y)
        if place:
            if not self.is_macro(self.tileimage):
                if self.brush_active:
                    self.brushpaint(pg.Vector2(cposxo, cposyo))
                elif self.cols:
                    if not self.blockNextPlacement:
                        self.place(cposxo, cposyo)
                        self.fieldadd.blit(self.tileimage["image"],
                                        [cposxo * self.size, cposyo * self.size])
            if self.is_macro(self.tileimage):
                match self.tileimage["tp"]:
                    case "path":
                        if (not self.currentPathDrag or self.posoffset != self.currentPathDrag[len(self.currentPathDrag) - 1]) \
                        and (not self.currentPathDrag or self.is_adjacent_cell(pg.Vector2(self.posoffset.x, self.posoffset.y), self.currentPathDrag[len(self.currentPathDrag) - 1]))\
                        and (not self.currentPathDrag or self.posoffset != self.currentPathDrag[len(self.currentPathDrag) - 2]):
                            self.currentPathDrag.append(pg.Vector2(self.posoffset.x, self.posoffset.y))
                            #pg.draw.rect(self.fieldadd, red, [self.posoffset.x * self.size, self.posoffset.y * self.size, self.size, self.size])
                            self.draw_path_preview()
        else:
            if self.brush_active:
                self.brushpaint(pg.Vector2(cposxo, cposyo), False)
            else:
                self.destroy(self.posoffset.x, self.posoffset.y)
                pg.draw.rect(self.fieldadd, red, [self.posoffset.x * self.size, self.posoffset.y * self.size, self.size, self.size])

    def end_drag(self, place):
        if self.is_macro(self.tileimage):
            match self.tileimage["tp"]:
                case "path":
                    self.finalize_macro()
        else:
            self.cols = self.test_cols(int(self.posoffset.x), int(self.posoffset.y))

        self.detecthistory(["TE", "tlMatrix"], not self.findparampressed("force_geometry"))
        if self.findparampressed("force_geometry"):
            self.detecthistory(["GE"])
        self.fieldadd.fill(white)
        self.renderer.tiles_render_area(self.area, self.layer)
        self.renderer.geo_render_area(self.area, self.layer)
        self.rfa()
        #self.cols = self.test_cols(cposxo, cposyo)
        if not self.justPlacedChainHolders:
            self.blockNextPlacement = False

    def begin_rect_drag(self, place):
        self.rectdata = [self.posoffset, pg.Vector2(0, 0), self.pos2]
        self.emptyarea()

    def update_rect_drag(self, place):
        mpos = pg.mouse.get_pos()
        self.rectdata[1] = self.posoffset - self.rectdata[0]

        righthalf = mpos[0] > self.rectdata[2].x + 10
        upperhalf = mpos[1] > self.rectdata[2].y + 10
        
        tl = [0, 0]
        br = [0, 0]

        if not righthalf:
            tl[0] = self.pos2.x
            br[0] = self.rectdata[2].x + self.size
        else:
            tl[0] = self.rectdata[2].x
            br[0] = self.pos2.x + self.size

        if upperhalf:
            tl[1] = self.pos2.y + self.size
            br[1] = self.rectdata[2].y
        else:
            tl[1] = self.rectdata[2].y + self.size
            br[1] = self.pos2.y
        
        rectColor = purple if self.tool != 2 else blue
        if not place:
            rectColor = select

        rect = self.vec2rect(pg.Vector2(tl), pg.Vector2(br))
        tx = f"{int(rect.w / self.size)}, {int(rect.h / self.size)}"
        widgets.fastmts(self.surface, tx, *(mpos + pg.Vector2(15, 4)), white)
        pg.draw.rect(self.surface, rectColor, rect, 1)

    def end_rect_drag(self, place):
        mpos = pg.mouse.get_pos()
        righthalf = mpos[0] > self.rectdata[2].x + 10
        upperhalf = mpos[1] > self.rectdata[2].y + 10
        
        tl = [0, 0]
        br = [0, 0]

        if not righthalf:
            tl[0] = self.posoffset.x
            br[0] = self.rectdata[0].x + 1
        else:
            tl[0] = self.rectdata[0].x
            br[0] = self.posoffset.x + 1

        if upperhalf:
            tl[1] = self.posoffset.y + 1
            br[1] = self.rectdata[0].y
        else:
            tl[1] = self.rectdata[0].y + 1
            br[1] = self.posoffset.y

        rect = self.vec2rect(pg.Vector2(tl), pg.Vector2(br))
        if not self.is_macro(self.tileimage) and self.tool != 2:
            cposxo = int(self.posoffset.x) - int((self.tileimage["size"][0] * .5) + .5) + 1
            cposyo = int(self.posoffset.y) - int((self.tileimage["size"][1] * .5) + .5) + 1
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
            pyperclip.copy(str(["TE", history]))
        elif place and self.is_macro(self.tileimage):
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
        elif not place and self.is_macro(self.tileimage): #this should be rewritten at some point i cant be fucked rn
            for x in range(int(rect.w)):
                for y in range(int(rect.h)):
                    self.destroy(x + rect.x, y + rect.y)
        self.detecthistory(["TE", "tlMatrix"])
        if self.findparampressed("force_geometry"):
            self.detecthistory(["GE"])
        self.renderer.tiles_render_area(self.area, self.layer)
        self.renderer.geo_render_area(self.area, self.layer)
        self.rfa()
        if not self.is_macro(self.tileimage) and not self.tool == 2:
            self.cols = self.test_cols(cposxo, cposyo)

    def blit(self):
        pg.draw.rect(self.surface, ui_settings["TE"]["menucolor"], pg.rect.Rect(self.buttonslist[0].xy, [self.buttonslist[0].rect.w, len(self.buttonslist[:-1]) * self.buttonslist[0].rect.h + 1]))
        for button in self.buttonslist:
            button.blitshadow()
        for i, button in enumerate(self.buttonslist[:-1]):
            button.blit(sum(pg.display.get_window_size()) // 120)
        self.buttonslist[-1].blit(sum(pg.display.get_window_size()) // 100)
        ciroff = 16 if self.buttonslist[self.toolindex].colorsquare != pg.Color(black) else 10
        try:
            cir = [self.buttonslist[self.toolindex].rect.x + ciroff, self.buttonslist[self.toolindex].rect.y + self.buttonslist[self.toolindex].rect.h / 2]
        except IndexError:
            self.toolindex = 0
            cir = [self.buttonslist[self.toolindex].rect.x + ciroff, self.buttonslist[self.toolindex].rect.y + self.buttonslist[self.toolindex].rect.h / 2]
        pg.draw.circle(self.surface, cursor, cir, self.buttonslist[self.toolindex].rect.h / 3)
        super().blit()
        bp = self.getmouse
        if self.onfield and self.tileimage is not None:
            # cords = [math.floor(pg.mouse.get_pos()[0] / self.size) * self.size, math.floor(pg.mouse.get_pos()[1] / self.size) * self.size]
            # self.surface.blit(self.tools, pos, [curtool, graphics["tilesize"]])
            try_clipboard = False
            try:
                if pg.key.get_pressed()[pg.K_LCTRL]:
                    clipboard = eval(pyperclip.paste())
                    if clipboard[0] == "TE" and isinstance(clipboard[1], list):
                        try_clipboard = True
            except Exception:
                pass

            pos2 = self.pos2
            posoffset = self.posoffset
            bord = (self.size // preview_cell_size + 1) // 2
            fg = self.findparampressed("force_geometry")
            fp = self.findparampressed("force_place")

            cposx = int(pos2.x)
            cposy = int(pos2.y)

            cposxo = int(posoffset.x)
            cposyo = int(posoffset.y)

            if not self.is_macro(self.tileimage):
                cposx = int(pos2.x) - int((self.tileimage["size"][0] * .5) + .5) * self.size + self.size
                cposy = int(pos2.y) - int((self.tileimage["size"][1] * .5) + .5) * self.size + self.size

                cposxo = int(posoffset.x) - int((self.tileimage["size"][0] * .5) + .5) + 1
                cposyo = int(posoffset.y) - int((self.tileimage["size"][1] * .5) + .5) + 1

            self.movemiddle(bp)

            if posoffset != self.mpos or self.lastfg != fg or self.lastfp != fp or self.justChangedZoom:
                if not self.is_macro(self.tileimage):
                    self.cols = self.test_cols(cposxo, cposyo)
                self.mpos = posoffset
                self.lastfg = fg
                self.lastfp = fp
                self.labels[1].set_text(f"X: {int(posoffset.x)}, Y: {int(posoffset.y)} | Work Layer: {self.layer + 1} | Zoom: {(self.size / preview_cell_size) * 100}%")

                if self.canplaceit(posoffset.x, posoffset.y, posoffset.x, posoffset.y):
                    tl = self.data["TE"]["tlMatrix"][int(posoffset.x)][int(posoffset.y)][self.layer]
                    #try:
                    if (tlh := self.get_tilehead_of_body(tl)) not in [None, "stray"]:
                        tlLabel = tlh["data"][1]
                    elif tlh is None and tl["tp"] == "material":
                        tlLabel = tl["data"]
                    elif tlh is None and tl["tp"] == "default":
                        tlLabel = "default"
                    elif tlh == "stray":
                        tlLabel = "STRAY TILE FRAGMENT"
                    #except:
                    #    tlLabel = "ERROR"
                    #    print(f"Error occurred determining tile display type at mpos {int(posoffset.x)}, {int(posoffset.y)}")
                    self.labels[0].set_text("Tile: " + tlLabel + " | Tile Data: " + str(tl))   

            if not self.is_macro(self.tileimage):
                if self.tileimage["size"][0] != 1 or self.tileimage["size"][1] != 1:
                    self.brushsize = 1

                if settings["hold_key_rect_drag"] and not (self.last_lmb == 0 or self.last_rmb == 0) and not self.tool == 2: #this may cause issues
                    if self.findparampressed("alt_func"):
                        self.tool = 1
                    else:
                        self.tool = 0         

                selectrect = [
                    [cposx - bord, cposy - bord],
                    [self.tileimage["image"].get_width() + bord * 2, self.tileimage["image"].get_height() + bord * 2]
                    ]
                drawTilePreview = True

                if not (self.tool == 1 and (bp[0] or bp[2])):
                    if self.cols and self.place_mode and self.tool == 0:
                        rectCol = canplace
                    elif self.rect_mode:
                        rectCol = purple
                    elif self.tool == 2:
                        rectCol = blue
                        drawTilePreview = False
                    else:
                        rectCol = cannotplace
                    
                    if self.brush_active:
                        if self.squarebrush or self.brushsize <= 1:
                            rect = pg.Rect([pos2 - [(self.brushsize // 2) * self.size, (self.brushsize // 2) * self.size], [self.brushsize * self.size, self.brushsize * self.size]])
                            pg.draw.rect(self.surface, rectCol, rect, 1)
                        else:
                            pg.draw.circle(self.surface, select, pos2+pg.Vector2(self.size/2), self.size * self.brushsize, 1)
                    elif not (self.rect_mode and (bp[0] or bp[2])) and not try_clipboard:
                        pg.draw.rect(self.surface, rectCol, selectrect, 1)
                if not self.place_mode or try_clipboard:
                    drawTilePreview = False

                if drawTilePreview:
                    self.tileimage["image"].set_colorkey([255, 255, 255])
                    self.surface.blit(self.tileimage["image"], [cposx, cposy])
                    self.print_cols_at_coord(pg.Vector2(cposxo, cposyo), self.tileimage)

                if self.justPlacedChainHolders:
                    for chPos in self.justPlacedChainHolders:
                        pg.draw.line(self.surface, red, self.field_to_draw_pos(chPos, _offset = [self.size, self.size]),
                                                            [pos2.x + self.size // 2, pos2.y + self.size // 2])
                #try:
                #    if (tlType := self.data["TE"]["tlMatrix"][int(posoffset.x)][int(posoffset.y)][self.layer]["tp"]) not in ["material", "default"]:
                #        if tlType == "tileHead":
                #            #chainEnd = toarr(self.data["TE"]["tlMatrix"][int(posoffset.x)][int(posoffset.y)][self.layer]["data"][2], "point")
                #            chHeadPos = [[int(posoffset.x + 1), int(posoffset.y + 1)], self.layer]
                #        if tlType == "tileBody":
                #            chHeadPos = [toarr(self.data["TE"]["tlMatrix"][int(posoffset.x)][int(posoffset.y)][self.layer]["data"][0], "point"),
                #                        self.data["TE"]["tlMatrix"][int(posoffset.x)][int(posoffset.y)][self.layer]["data"][1] - 1]
                #        if self.data["TE"]["tlMatrix"][int(chHeadPos[0][0] - 1)][int(chHeadPos[0][1] - 1)][chHeadPos[1]]["data"].__len__() == 3:
                #            chainEnd = toarr(self.data["TE"]["tlMatrix"][int(chHeadPos[0][0] - 1)][int(chHeadPos[0][1] - 1)][chHeadPos[1]]["data"][2], "point")
                #            pg.draw.circle(self.surface, red, self.FieldCoordToDrawPos(chainEnd, [self.size // 2, self.size // 2]), self.size // 3, 1)
                #except IndexError:
                #    pass

                if (chainHolderHead := self.get_tilehead_of_body(self.data["TE"]["tlMatrix"][int(max(0, min(posoffset.x, self.levelwidth - 1)))][int(max(0, min(posoffset.y, self.levelheight - 1)))][self.layer])) not in [None, "stray"]:
                    if chainHolderHead["data"][1] == "Chain Holder" and chainHolderHead["data"].__len__() == 3:
                        chainEnd = toarr(chainHolderHead["data"][2], "point")
                        pg.draw.circle(self.surface, red, self.field_to_draw_pos(chainEnd, [self.size // 2, self.size // 2]), self.size // 3, 1)
                try:
                    if self.canplaceit(posoffset.x, posoffset.y, posoffset.x, posoffset.y):
                        hoveredTile = self.data["TE"]["tlMatrix"][int(posoffset.x)][int(posoffset.y)][self.layer]
                        if self.findparampressed("force_place") and hoveredTile["tp"] not in ["default", "material"]:
                            if hoveredTile["tp"] == "tileBody" and (tlhPos := [toarr(hoveredTile["data"][0], "point"), hoveredTile["data"][1]]) is not None:
                                tlhDrawPos = tlhPos[0]
                            else:
                                tlhDrawPos = [int(posoffset.x + 1), int(posoffset.y + 1)]
                            pg.draw.circle(self.surface, blue, self.field_to_draw_pos(tlhDrawPos, [-self.size // 2, -self.size // 2]), self.size // 3, 1)
                except Exception:
                    print("Error occurred determining tileHead position")
            else:
                patternPrevCol = False
                if self.tileimage["tp"] == "pattern":
                    self.tool = 1
                    if not (self.tool == 1 and (bp[0] or bp[2])):
                        patternPrevCol = purple
                if(self.tileimage["tp"] == "path"):
                    self.tool = 0
                    if not (self.tool == 0 and (bp[0] or bp[2])):
                        patternPrevCol = purple
                if patternPrevCol:
                    pg.draw.rect(self.surface, patternPrevCol, [pos2.x - bord, pos2.y - bord, self.size + bord * 2, self.size + bord * 2], 1)

            if try_clipboard:
                try:
                    clipboard = eval(pyperclip.paste())
                    if clipboard[0] != "TE" or not isinstance(clipboard[1], list):
                        return
                    pos = self.field.rect.topleft + (self.pos * self.size if self.onfield else pg.Vector2(0, 0))
                    clipboard[1].sort(key=lambda x: x[0])
                    sizex = clipboard[1][-1][0] + 1
                    clipboard[1].sort(key=lambda y: y[1])
                    sizey = clipboard[1][-1][1] + 1
                    rect = pg.Rect([pos, pg.Vector2(sizex, sizey) * self.size])
                    pg.draw.rect(self.surface, blue, rect, 1)
                except Exception:
                    pass

            if not settings["TE_legacy_RWE_placement_controls"]:
                if self.tool == 0:
                    if bp[0] == 1 and self.last_lmb and (self.last_rmb and self.last_mmb):
                        if self.justPlacedChainHolders:
                            for chPos in self.justPlacedChainHolders:
                                self.data["TE"]["tlMatrix"][chPos[0]][chPos[1]][chPos[2]]["data"].append(makearr([cposxo, cposyo], "point"))
                                #self.data["TE"]["tlMatrix"][chPos[0]][chPos[1]][chPos[2]]["data"][0] = makearr([15, 22], "point") #dont fucking ask me why this works
                            self.justPlacedChainHolders.clear()
                        else:
                            self.begin_drag(True)
                            self.last_lmb = False
                    elif bp[0] == 1 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.update_drag(True)
                    elif bp[0] == 0 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.end_drag(True)
                        self.last_lmb = True

                    if bp[2] == 1 and self.last_rmb and (self.last_lmb and self.last_mmb):
                        self.begin_drag(False)
                        self.last_rmb = False
                    elif bp[2] == 1 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                        self.update_drag(False)
                    elif bp[2] == 0 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                        self.end_drag(False)
                        self.last_rmb = True
                else:
                    if bp[0] == 1 and self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.begin_rect_drag(True)
                        self.last_lmb = False
                    elif bp[0] == 1 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.update_rect_drag(True)
                    elif bp[0] == 0 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.end_rect_drag(True)
                        self.last_lmb = True

                    if bp[2] == 1 and self.last_rmb and (self.last_lmb and self.last_mmb):
                        self.begin_rect_drag(False)
                        self.last_rmb = False
                    elif bp[2] == 1 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                        self.update_rect_drag(False)
                    elif bp[2] == 0 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                        self.end_rect_drag(False)
                        self.last_rmb = True
            else:
                if self.tool == 0:
                    if bp[0] == 1 and self.last_lmb and self.last_mmb and self.last_rmb:
                        self.begin_drag(True)
                        self.last_lmb = False
                    elif bp[0] == 1 and not self.last_lmb and self.last_mmb and self.last_rmb:
                        self.update_drag(True)
                    elif bp[0] == 0 and not self.last_lmb and self.last_mmb and self.last_rmb:
                        self.end_drag(True)
                        self.last_lmb = True

                    if bp[2] == 1 and self.last_rmb and self.last_mmb and self.last_lmb:
                        self.begin_rect_drag(True)
                        self.last_rmb = False
                    elif bp[2] == 1 and not self.last_rmb and self.last_mmb and self.last_lmb:
                        self.update_rect_drag(True)
                    elif bp[2] == 0 and not self.last_rmb and self.last_mmb and self.last_lmb:
                        self.end_rect_drag(True)
                        self.last_rmb = True
                else:
                    if bp[0] == 1 and self.last_lmb and self.last_mmb and self.last_rmb:
                        self.begin_drag(False)
                        self.last_lmb = False
                    elif bp[0] == 1 and not self.last_lmb and self.last_mmb and self.last_rmb:
                        self.update_drag(False)
                    elif bp[0] == 0 and not self.last_lmb and self.last_mmb and self.last_rmb:
                        self.end_drag(False)
                        self.last_lmb = True

                    if bp[2] == 1 and self.last_rmb and self.last_mmb and self.last_lmb:
                        self.begin_rect_drag(False)
                        self.last_rmb = False
                    elif bp[2] == 1 and not self.last_rmb and self.last_mmb and self.last_lmb:
                        self.update_rect_drag(False)
                    elif bp[2] == 0 and not self.last_rmb and self.last_mmb and self.last_lmb:
                        self.end_rect_drag(False)
                        self.last_rmb = True             
        else:
            if not self.matshow:
                for index, button in enumerate(self.buttonslist[:-1]):
                    if button.onmouseover():
                        cat = list(self.items.keys())[self.currentcategory]
                        item = self.items[cat][index]
                        if item.get("preview"):
                            previewPos = button.rect.bottomright
                            if ui_settings["global"]["previewleftside"]:
                                previewPos = [button.rect.topleft[0] - item["preview"].get_width(), button.rect.topleft[1]]
                            self.surface.blit(item["preview"], previewPos)
                        if self.is_macro(item):
                            break
                        w, h = item["size"]
                        w *= preview_cell_size
                        h *= preview_cell_size
                        margin = pg.Vector2(16, 16)
                        preview_pos = pg.Vector2(self.field.x + margin.x, self.field.y + margin.y) if not ui_settings["global"]["previewleftside"] else\
                        pg.Vector2(self.field.rect.x + self.field.rect.width - w - margin.x, self.field.rect.y + margin.y)
                        pg.draw.rect(self.surface, black, [*preview_pos - margin / 2, w + margin.x, h + margin.y])
                        if not ui_settings["TE"]["LEtiles"]:
                            pg.draw.rect(self.surface, item["color"], [*preview_pos, w, h])
                        self.surface.blit(pg.transform.scale(item["image"], [w, h]), [preview_pos.x, preview_pos.y])
                        self.printcols(preview_pos, preview_cell_size, item)
                        break
        for button in self.buttonslist:
            button.blittooltip()
    
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
            self.currentcategory = self.toolindex // self.menu_ui_settings["category_count"]
            self.toolindex %= self.menu_ui_settings["category_count"]
        btn2 = None
        self.matshow = True
        for count, item in enumerate(self.catlist[self.currentcategory]):
            # rect = pg.rect.Rect([0, count * self.settings["itemsize"], self.field2.field.get_width(), self.settings["itemsize"]])
            # rect = pg.rect.Rect(0, 0, 100, 10)
            cat = pg.rect.Rect(self.menu_ui_settings["catpos"])
            btn2 = widgets.button(self.surface, cat, ui_settings["global"]["color"], f"Categories {self.currentcategory}", onpress=self.changematshow)

            rect = pg.rect.Rect(self.menu_ui_settings["itempos"])
            rect = rect.move(0, rect.h * count)
            col = pg.Color([90, 90, 90])
            if (count - 1) % 2 == 0:
                mul = 0.93
                col = pg.Color(int(col.r * mul),int(col.g * mul),int(col.b * mul))
            if count == self.toolindex:
                col = darkgray
            btn = widgets.button(self.surface, rect, col, item, indicatorcol=self.items[item][0]["color"], onpress=self.selectcat)
            self.buttonslist.append(btn)
        if btn2 is not None:
            self.buttonslist.append(btn2)
        self.resize()

    def pastedata(self):
        try:
            geodata = eval(pyperclip.paste())
            if geodata[0] != "TE" or not isinstance(geodata[1], list) or len(pyperclip.paste()) <= 2:
                print("Error pasting data!")
                return
            self.emptyarea()
            for block in geodata[1]:
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

                cposxo = int(pa.x) - int((self.tileimage["size"][0] * .5) + .5) + 1
                cposyo = int(pa.y) - int((self.tileimage["size"][1] * .5) + .5) + 1

                self.place(blockx - self.xoffset + cposxo, blocky - self.yoffset + cposyo)
            else:
                self.selectcat(cat)
            self.detecthistory(["TE", "tlMatrix"])
            self.renderer.tiles_render_area(self.area, self.layer)
            self.rfa()
        except Exception:
            print("Error pasting data!")

    def findcat(self, itemname):
        for name, listdata in self.items.items():
            for bl in listdata:
                if bl["name"] == itemname:
                    return name
        return None

    def copytool(self):
        self.tool = 2 if self.tool != 2 else 0

    def selectcat(self, name):
        self.currentcategory = list(self.items.keys()).index(name)
        self.toolindex = 0
        self.rebuttons()

    def rebuttons(self):
        self.buttonslist = []
        self.matshow = False
        btn2 = None
        for count, item in enumerate(self.items[list(self.items.keys())[self.currentcategory]]):
            #print(item["category"])
            # rect = pg.rect.Rect([0, count * self.settings["itemsize"], self.field2.field.get_width(), self.settings["itemsize"]])
            # rect = pg.rect.Rect(0, 0, 100, 10)
            cat = pg.rect.Rect(self.menu_ui_settings["catpos"])
            btn2 = widgets.button(self.surface, cat, item["color"], item["category"], onpress=self.changematshow,
                tooltip=self.returnkeytext("Select category(<[-changematshow]>)"))

            rect = pg.rect.Rect(self.menu_ui_settings["itempos"])
            rect = rect.move(0, rect.h * count)

            col = gray
            if (count - 1) % 2 == 0:
                mul = 0.93
                col = pg.Color(int(col.r * mul),int(col.g * mul),int(col.b * mul))

            if item["category"] == "special" or "material" in item["tags"]:
                btn = widgets.button(self.surface, rect, col, item["name"], indicatorcol=item["color"], onpress=self.getmaterial)
            else:
                tooltip = "Size: " + str(item["size"])
                btn = widgets.button(self.surface, rect, col, item["name"], onpress=self.getblock, tooltip=tooltip)
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
        if self.tileimage is not None and not self.is_macro(self.tileimage):
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
            self.currentcategory = self.toolindex + self.currentcategory * self.menu_ui_settings["category_count"]
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
        if settings["TE_legacy_RWE_placement_controls"]:
            self.tool = 0
        for num, i in enumerate(self.items[cat]):
            if i["name"] == name:
                self.toolindex = num
                self.tileimage2 = i.copy()
                if self.tileimage is not None and self.is_macro(self.tileimage) and not self.is_macro(self.tileimage2):
                    self.tool = 0
                if not self.is_macro(self.tileimage2) and render:
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
                and (self.data["TE"]["tlMatrix"][x][y][self.layer]["tp"] == "default" or (force_place and self.data["TE"]["tlMatrix"][x][y][self.layer]["tp"] == "material"))
        for x2 in range(w):
            for y2 in range(h):
                csp = sp[x2 * h + y2]
                xpos = int(x + x2)
                ypos = int(y + y2)
                if xpos >= self.levelwidth or ypos >= self.levelheight or xpos < 0 or ypos < 0:
                    continue
                if csp != -1:
                    if self.data["TE"]["tlMatrix"][xpos][ypos][self.layer]["tp"] not in ["default", "material"] and not (force_place):
                        return False
                    if self.data["GE"][xpos][ypos][self.layer][0] != csp and not force_geo:
                        return False
                if sp2 != 0 and sp2 != "void": #thanks Crane House Tile
                    if self.layer + 1 <= 2:
                        csp2 = sp2[x2 * h + y2]
                        if csp2 != -1:
                            if self.data["TE"]["tlMatrix"][xpos][ypos][self.layer + 1]["tp"] not in ["default", "material"] and not (force_place):
                                return False
                            if self.data["GE"][xpos][ypos][self.layer + 1][0] != csp2 and not force_geo:
                                return False

        return True
        # self.data["TE"]
    
    def printcell(self, screen_pos:pg.Vector2, scale:float, tp:int, color:pg.Color):
        match tp:
            case 1:
                pg.draw.rect(self.surface, color, [*screen_pos, scale + 1, scale + 1], 1)
            case 0:
                pg.draw.circle(self.surface, color, [screen_pos.x + scale / 2, screen_pos.y + scale / 2], scale / 2, 1)
            case 2:
                pg.draw.polygon(self.surface, color,
                                [[*screen_pos], [screen_pos.x, screen_pos.y + scale], [screen_pos.x + scale, screen_pos.y + scale]], 1)
            case 3:
                pg.draw.polygon(self.surface, color,
                                [[screen_pos.x, screen_pos.y + scale], [screen_pos.x + scale, screen_pos.y + scale], [screen_pos.x + scale, screen_pos.y]],
                                1)
            case 4:
                pg.draw.polygon(self.surface, color,
                                [[screen_pos.x, screen_pos.y], [screen_pos.x, screen_pos.y + scale], [screen_pos.x + scale, screen_pos.y]], 1)
            case 5:
                pg.draw.polygon(self.surface, color,
                                [[screen_pos.x, screen_pos.y], [screen_pos.x + scale, screen_pos.y + scale], [screen_pos.x + scale, screen_pos.y]], 1)
            case 6:
                pg.draw.rect(self.surface, color,
                                [*screen_pos, scale, scale/2], 1)

    def printcols(self, screen_pos:pg.Vector2, scale:float, tile):
        w,h = tile["size"]
        specsL1 = tile["cols"][0]
        specsL2 = tile["cols"][1]
        shift = scale // preview_cell_size + 1
        
        if specsL2 != 0 and specsL2 != "void":
            for x2 in range(w):
                for y2 in range(h):        
                    self.printcell(screen_pos + pg.Vector2([shift]*2) + pg.Vector2(x2, y2) * scale, scale, specsL1[x2 * h + y2], layer2)
            shift *= 2

        for x2 in range(w):
            for y2 in range(h):
                self.printcell(screen_pos + pg.Vector2([shift]*2) + pg.Vector2(x2, y2) * scale, scale, specsL1[x2 * h + y2], layer1)
    
    def print_cols_at_coord(self, field_coord, tile):
        self.printcols(self.field_to_draw_pos(field_coord), self.size, tile)

    def scroll_up(self):
        if self.findparampressed("brush_size_scroll"):
            self.brushp()
            return False
        return True
    
    def scroll_down(self):
        if self.findparampressed("brush_size_scroll"):
            self.brushm()
            return False
        return True

    def brushp(self):
        self.brushsize += 1

    def brushm(self):
        self.brushsize = max(self.brushsize-1, 1)

    def togglebrush(self):
        self.brushsize = 3 if not self.brush_active else 1

    def place(self, x, y, render=False):
        if self.blockNextPlacement:
            return
        fg = self.findparampressed("force_geometry")
        w, h = self.tileimage["size"]
        px = x + int((w * .5) + .5) - 1 # center coordinates
        py = y + int((h * .5) + .5) - 1
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
                p = makearr([self.tileimage["cat"][0] + 4, self.tileimage["cat"][1]], "point")  # very bandaid fix, RWE loads tiles and materials in a different order than Drizzle,                                                                         
                csp = sp[x2 * h + y2]                                                           # so whenever the tilehead category index is actually required for something to function
                xpos = int(x + x2)                                                              # it Won't, because all of the tile category indices will be wrong
                ypos = int(y + y2)                                                              # luckily, i don't know of much else that requires the head's category index other than chain holders,
                if xpos >= self.levelwidth or ypos >= self.levelheight or xpos < 0 or ypos < 0 or (self.data["TE"]["tlMatrix"][xpos][ypos][self.layer]["tp"] == "tileHead"): # which aren't the end of the world if they don't work. this fix should work unless material categories are added or removed
                    continue
                if self.data["TE"]["tlMatrix"][xpos][ypos][self.layer]["tp"] not in ("default", "tileBody"):
                    self.area[xpos][ypos] = False
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

                if sp2 != 0 and sp2 != "void":
                    csp = sp2[x2 * h + y2]
                    if self.layer + 1 <= 2 and csp != -1:
                        p = makearr([px + 1, py + 1], "point")
                        self.data["TE"]["tlMatrix"][xpos][ypos][self.layer + 1] = {"tp": "tileBody",
                            "data": [p, self.layer + 1]}
                        self.area[xpos][ypos] = False
                        if fg:
                            self.data["GE"][xpos][ypos][self.layer + 1][0] = csp
        self.mpos = 1

        if "Chain Holder" in self.tileimage["tags"]:
            self.justPlacedChainHolders.append([x, y, self.layer])
            self.blockNextPlacement = True
        #if fg:
        #    self.rfa()

    def destroy(self, xp, yp):
            x = int(xp)
            y = int(yp)
            if not self.canplaceit(x, y, x, y):
                return
            self.area[x][y] = False
            def clearitem(mx, my, layer):
                val = self.data["TE"]["tlMatrix"][mx][my][layer]
                if val["data"] == 0:
                    return
                name = val["data"][1]
                itm = None
                for i in self.items.keys():
                    for i2 in self.items[i]:
                        if i2["name"] == name:
                            itm = i2
                            break
                    if itm is not None:
                        break
                if itm is None:
                    self.data["TE"]["tlMatrix"][mx][my][layer] = {"tp": "default", "data": 0}
                    return
                backx = mx - int((itm["size"][0] * .5) + .5) + 1
                backy = my - int((itm["size"][1] * .5) + .5) + 1
                #if backx + itm["size"][0] > len(self.data["TE"]["tlMatrix"])-1 or backy + itm["size"][1] > len(
                #        self.data["TE"]["tlMatrix"][0])-1:
                #    return
                # startcell = self.data["TE"]["tlMatrix"][backx][backy][layer]
                sp = itm["cols"][0]
                sp2 = itm["cols"][1]
                w, h = itm["size"]
                pg.draw.rect(self.fieldadd, red, [backx * self.size,
                                                backy * self.size,
                                                w * self.size, h * self.size])
                for x2 in range(w):
                    for y2 in range(h):
                        posx = backx + x2
                        posy = backy + y2
                        if posy >= self.levelheight or posx >= self.levelwidth:
                            continue
                        csp = sp[x2 * h + y2]
                        self.area[posx][posy] = False
                        if csp != -1:
                            # pg.draw.rect(self.fieldadd, red, [posx * self.size, posy * self.size, self.size, self.size])
                            self.data["TE"]["tlMatrix"][posx][posy][layer] = {"tp": "default", "data": 0}
                        if sp2 != 0:
                            try:
                                csp = sp2[x2 * h + y2]
                            except IndexError:
                                csp = -1
                            if csp != -1 and layer + 1 <= 2:
                                self.data["TE"]["tlMatrix"][posx][posy][layer + 1] = {"tp": "default", "data": 0}

            if not self.canplaceit(x, y, x, y):
                return
            tile = self.data["TE"]["tlMatrix"][x][y][self.layer]
            if tile["tp"] != "default":
                if not self.findparampressed("force_place"):
                    match tile["tp"]:
                        case "tileBody":
                            posx, posy = toarr(tile["data"][0], "point")
                            clearitem(posx - 1, posy - 1, tile["data"][1] - 1)
                        case "tileHead":
                            clearitem(x, y, self.layer)
                        case "material":
                            self.area[x][y] = False
                            self.data["TE"]["tlMatrix"][x][y][self.layer] = {"tp": "default", "data": 0}
                else:
                    self.area[x][y] = False
            self.data["TE"]["tlMatrix"][x][y][self.layer] = {"tp": "default", "data": 0}

    def sad(self):
        if "material" in self.tileimage["tags"]:
            self.data["TE"]["defaultMaterial"] = self.tileimage["name"]
        self.labels[2].set_text("Default material: " + self.data["TE"]["defaultMaterial"])

    def cleartool(self):
        self.tool = 1

    def changetools(self):
        if not settings["hold_key_rect_drag"] and self.last_lmb and self.last_rmb:
            self.tool = abs(1 - self.tool)
        self.brushsize = 1

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
        self.blockNextPlacement = True

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
                        self.tool = 0
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

    def get_next_path_tile(self, init, path, indx):
        tile = path[indx]
        last = path[max(indx - 1, 0)]
        next = path[min(indx + 1, len(path) - 1)]
        diff = [last - tile, next - tile]

        pathTile = "H"

        if all(x in [[1, 0], [-1, 0]] for x in diff) or all(x in [[1, 0], [0, 0]] for x in diff) or all(x in [[-1, 0], [0, 0]] for x in diff):
            pathTile = "H"
        elif all(x in [[0, 1], [0, -1]] for x in diff) or all(x in [[0, 1], [0, 0]] for x in diff) or all(x in [[0, -1], [0, 0]] for x in diff):
            pathTile = "V"
        elif [0, -1] in diff and [1, 0] in diff:
            pathTile = "NE"
        elif [0, 1] in diff and [1, 0] in diff:
            pathTile = "SE"
        elif [0, -1] in diff and [-1, 0] in diff:
            pathTile = "NW"
        elif [0, 1] in diff and [-1, 0] in diff:
            pathTile = "SW"

        return self.pathtiles[init["name"]]["cat"], self.pathtiles[init["name"]][pathTile]

    def finalize_macro(self):
        macroInit = copy.deepcopy(self.tileimage)
        match macroInit["tp"]:
            case "path":
                for indx, tile in enumerate(self.currentPathDrag):
                    tile = pg.Vector2(tile)
                    nCat, nName = self.get_next_path_tile(macroInit, self.currentPathDrag, indx)

                    self.set(nCat, nName)
                    self.place(tile.x, tile.y)

        self.set("special", macroInit["name"])
        self.currentPathDrag.clear()

    def draw_path_preview(self):
        self.fieldadd.fill(white)
        for indx, tile in enumerate(self.currentPathDrag):
            tile = pg.Vector2(tile)
            nCat, nName = self.get_next_path_tile(self.tileimage, self.currentPathDrag, indx)
            for i in self.items[nCat]:
                if i["name"] == nName:
                    i_img_c:pg.Surface = i["image"].copy()
                    i_img_c.set_colorkey(white)
                    i_img_c = i_img_c.convert_alpha() #i hate pygame
                    i_img_c.fill((254, 254, 254), special_flags=pg.BLEND_RGB_ADD)
                    i_img_c.fill((150, 255, 255) if indx != len(self.currentPathDrag) - 1 else (254, 255, 255), special_flags=pg.BLEND_RGB_MULT)
                    self.fieldadd.blit(i_img_c,
                        [tile.x * self.size, tile.y * self.size])
                    break

    def is_macro(self, item):
        return ["pattern", "path"].__contains__(item["tp"])

    def is_adjacent_cell(self, c1, c2):
        return (c1 - c2) in [[1, 0], [0, 1], [-1, 0], [0, -1]]

    @property
    def rect_mode(self):
        return self.tool == 1 if not settings["TE_legacy_RWE_placement_controls"] else self.getmouse[2]

    @property
    def place_mode(self):
        return not self.getmouse[2] if not settings["TE_legacy_RWE_placement_controls"] else self.tool == 0

    @property
    def brush_active(self):
        return self.brushsize > 1

    @property
    def custom_info(self):
        try:
            return f"{super().custom_info} | Selected tile: {self.tileimage['name']}"
        except TypeError:
            return super().custom_info
