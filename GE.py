from menuclass import *


class GE(MenuWithField):
    def __init__(self, surface: pg.surface.Surface, renderer: render.Renderer):
        self.state = 0
        self.mx = 0

        self.selectedtool = ""
        self.lastselectedtool = ""

        self.tools = toolmenu
        self.tooltiles = tooltiles
        self.toolrender = self.tooltiles

        self.tools.set_alpha(150)
        self.placetile = 0

        self.mirrorp = False
        self.mirrorpos = [0, 0]

        self.replaceair = True

        self.rectDragActive = False

        #self.fillshape = "pencil"  # pencil, brush, fill
        self.bucketTool = False
        self.fillshape2 = "rect"  # rect, rect-hollow, circle, circle-hollow, line
        self.brushsize = 1

        self.toolsized = None

        renderer.color_geo = True
        renderer.geo_full_render(renderer.lastlayer)

        super().__init__(surface, "GE", renderer)
        self.drawwater = True
        self.drawgrid = True
        self.emptyarea()
        self.air()
        self.rs()
        self.replacestate()
        self.blit()
        self.resize()

    def resize(self):
        super().resize()
        if hasattr(self, "field"):
            self.rs()

    def rotate(self):
        if self.mx != 0:
            self.state = (self.state + 1) % self.mx
        else:
            self.state = 0

    def mleft(self):
        if self.mirrorpos[1] == 0:
            self.mirrorpos[0] -= 1
        else:
            self.mirrorpos[1] = 0
            self.mirrorpos[0] = self.levelwidth // 2

    def mright(self):
        if self.mirrorpos[1] == 0:
            self.mirrorpos[0] += 1
        else:
            self.mirrorpos[1] = 0
            self.mirrorpos[0] = self.levelwidth // 2

    def mup(self):
        if self.mirrorpos[1] == 1:
            self.mirrorpos[0] -= 1
        else:
            self.mirrorpos[1] = 1
            self.mirrorpos[0] = self.levelheight // 2

    def mdown(self):
        if self.mirrorpos[1] == 1:
            self.mirrorpos[0] += 1
        else:
            self.mirrorpos[1] = 1
            self.mirrorpos[0] = self.levelheight // 2

    def rs(self):
        self.toolrender = pg.transform.scale(self.tooltiles,
                                             [self.tooltiles.get_width() / graphics["tilesize"][0] * preview_cell_size,
                                              self.tooltiles.get_height() / graphics["tilesize"][1] * preview_cell_size])

    def TE(self):
        self.message = "TE"

    def begin_draw_drag(self):
        if self.selectedtool == "MV":
            self.rectdata[0] = self.pos
            self.rectdata[1] = self.offset
            self.field.field.fill(self.field.color)
        elif self.bucketTool:
            self.bucket(self.posoffset)
        else:
            self.emptyarea()

    def update_draw_drag(self):
        if self.selectedtool == "MV":
            self.offset = self.rectdata[1] - (self.rectdata[0] - self.pos)
        elif self.selectedtool == "CT":
            pass
        elif self.brush_active:
            self.brushpaint(self.posoffset, self.toolsized)
        elif (0 <= self.posoffset.x < self.levelwidth) and (0 <= self.posoffset.y < self.levelheight) and self.area[int(self.posoffset.x)][int(self.posoffset.y)]:
            if self.selectedtool != "SL" or self.get_slope_orientation(self.posoffset):
                self.place(self.posoffset, False)
                self.drawtile(self.posoffset, self.toolsized)
    
    def end_draw_drag(self):
        self.start_perftimer()
        self.fieldadd.fill(white)
        paths = []
        count = 0
        for xindex, xpos in enumerate(self.area):
            for yindex, ypos in enumerate(xpos):
                if not ypos:
                    paths.append(["GE", xindex, yindex, self.layer])
                    count += 1
        if len(paths) > 0:
            if count < 20: # if we changed more than 20 pixels, changing history save method
                self.updatehistory(paths)
            else:
                self.detecthistory(["GE"])
        self.render_geo_area()
        self.rfa()
        self.stop_perftimer()

    def begin_rect_drag(self):
        self.rectdata = [self.posoffset, pg.Vector2(0, 0), self.pos2]
        self.emptyarea()

    def update_rect_drag(self):
        mpos = pg.Vector2(pg.mouse.get_pos())

        self.rectdata[1] = self.posoffset - self.rectdata[0]

        righthalf = mpos.x > self.rectdata[2].x + 10
        upperhalf = mpos.y > self.rectdata[2].y + 10
        
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

        rect = self.vec2rect(pg.Vector2(tl), pg.Vector2(br))

        tx = f"{abs(int(rect.w / self.size))}, {abs(int(rect.h / self.size))}"
        widgets.fastmts(self.surface, tx, *mpos, white)
        if self.fillshape2 in ["rect", "rect-hollow"] or self.selectedtool in ["CP", "CT", "SL"]:
            pg.draw.rect(self.surface, select, rect, 1)
        elif self.fillshape2 in ["circle", "circle-hollow"]:
            pg.draw.ellipse(self.surface, select, rect, 5)
        elif self.fillshape2 == "line":
            pg.draw.line(self.surface, select, self.rectdata[2], self.pos2, 5)

    def end_rect_drag(self):
        mpos = pg.Vector2(pg.mouse.get_pos())

        if self.selectedtool == "CP" or self.selectedtool == "CT":
            rect = self.vec2rect(self.rectdata[0], self.posoffset)
            rect.w += 1 #i'm sure theres a better solution to this :slugmod:
            rect.h += 1
            data1 = self.data["GE"][rect.x:rect.x + rect.w]
            data1 = [i[rect.y:rect.y + rect.h] for i in data1]
            data1 = ["GE", [[y[self.layer] for y in x] for x in data1]]
            pyperclip.copy(str(data1))
            print("Copied!")
        elif self.selectedtool == "SL":
            rect = self.vec2rect(self.rectdata[0], self.posoffset)
            for x in range(int(rect.w)):
                for y in range(int(rect.h)):
                    vec = pg.Vector2(x, y) + rect.topleft
                    self.slopify(vec)
        elif self.fillshape2 in ["circle", "circle-hollow"]:
            rect = self.vec2rect(self.rectdata[0], self.posoffset)
            rect2ellipse(rect, self.fillshape2 == "circle-hollow", self.place)
        elif self.fillshape2 == "line":
            self.linepoints(self.rectdata[0], self.posoffset)
        elif self.fillshape2 in ["rect", "rect-hollow"]:
            righthalf = mpos.x > self.rectdata[2].x + 10
            upperhalf = mpos.y > self.rectdata[2].y + 10
            
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
            for x in range(int(rect.w)):
                for y in range(int(rect.h)):
                    vec = pg.Vector2(x, y)
                    if self.fillshape2 == "rect" or (vec.x == 0 or vec.y == 0 or vec.x == int(rect.w)-1 or vec.y == int(rect.h)-1):
                        self.place(vec + rect.topleft, False)
        if self.selectedtool == "CT":
            rect = self.vec2rect(self.rectdata[0], self.posoffset)
            for x in range(int(rect.w)):
                for y in range(int(rect.h)):
                    vec = pg.Vector2(x, y)
                    self.place(vec + rect.topleft, False)
        self.detecthistory(["GE"])
        self.render_geo_area()
        self.rfa()

    def blit(self):
        cellsize2 = [self.size, self.size]
        super().blit()
        mpos = pg.Vector2(pg.mouse.get_pos())
        #print(mpos)
        if self.selectedtool != self.lastselectedtool:
            self.lastselectedtool = self.selectedtool
            self.s0()
            self.recaption()
        if self.onfield:
            wltx = "Work Layer: " + str(self.layer + 1)
            widgets.fastmts(self.surface, wltx, *(mpos + [10, -10]), white, 15)

            curtool = [graphics["tools"][self.selectedtool][0] * graphics["tilesize"][0],
                       graphics["tools"][self.selectedtool][1] * graphics["tilesize"][1]]
            #nst = self.tools.convert_alpha(self.surface)
            #nst.fill(red, special_flags=pg.BLEND_RGBA_MULT)
            #self.surface.blit(nst, mpos, [curtool, graphics["tilesize"]])

            # cords = [math.floor(pg.mouse.get_pos()[0] / self.size) * self.size, math.floor(pg.mouse.get_pos()[1] / self.size) * self.size]
            # self.surface.blit(self.tools, pos, [curtool, graphics["tilesize"]])
            pos = self.pos
            pos2 = self.pos2
            pg.draw.rect(self.surface, cursor, [pos2, [self.size, self.size]], 1)
            posoffset = self.posoffset

            if self.selectedtool == "SL":
                validSlope = self.get_slope_orientation(self.posoffset)

            self.toolsized = pg.transform.scale(self.toolrender,
                                           pg.Vector2(self.toolrender.get_size()) / preview_cell_size * self.size).convert_alpha(self.surface)
            self.toolsized.fill(red, special_flags=pg.BLEND_RGBA_MULT)
            self.labels[1].set_text(f"X: {int(posoffset.x)}, Y: {int(posoffset.y)} | Work Layer: {self.layer + 1} | Zoom: {(self.size / preview_cell_size) * 100}%")
            #print(self.placetile)
            if self.selectedtool in graphics["codes"].keys():
                if isinstance(self.placetile, int):
                    if graphics["codes"][self.selectedtool] == 1:
                        curtool = [graphics["tileplaceicon"][str(self.placetile + self.state)][0] * self.size,
                                   graphics["tileplaceicon"][str(self.placetile + self.state)][1] * self.size]
                        #print(self.placetile + self.state)
                    else:
                        curtool = [graphics["tileplaceicon"][str(self.placetile - self.state)][0] * self.size,
                                   graphics["tileplaceicon"][str(self.placetile - self.state)][1] * self.size]
                    # print([abs(self.field.rect.x - pos2[0]), abs(self.field.rect.y - pos2[1])])
                    if self.selectedtool == "SL" and not validSlope:
                        curtool = [graphics["tileplaceicon"]["UNDEFINEDSLOPE"][0] * self.size, graphics["tileplaceicon"]["UNDEFINEDSLOPE"][1] * self.size]
                    self.surface.blit(self.toolsized, pos2, [curtool, cellsize2])
            rect = [self.xoffset * self.size, self.yoffset * self.size, self.levelwidth * self.size,
                    self.levelheight * self.size]
            pg.draw.rect(self.field.field, border, rect, self.size // preview_cell_size + 1)
            if (0 <= posoffset.x < self.levelwidth) and (0 <= posoffset.y < self.levelheight):
                tilename = ui_settings["GE"]["names"][
                    str(self.data["GE"][int(posoffset.x)][int(posoffset.y)][self.layer][0])]
                self.labels[0].set_text(
                    f"Tile: {tilename} {self.data['GE'][int(posoffset.x)][int(posoffset.y)][self.layer]}")

            bp = self.getmouse

            if self.brush_active and not self.rectDragActive:
                pg.draw.circle(self.surface, select, pos2+pg.Vector2(self.size/2), self.size * self.brushsize - 0.5, 1)
            
            if settings["hold_key_rect_drag"]:
                if not self.rectDragActive:
                    if bp[0] == 1 and self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.begin_draw_drag()
                        self.last_lmb = False
                    elif bp[0] == 1 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.update_draw_drag()
                    elif bp[0] == 0 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.end_draw_drag()
                        self.last_lmb = True
                else:
                    if bp[0] == 1 and self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.begin_rect_drag()
                        self.last_lmb = False
                    elif bp[0] == 1 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.update_rect_drag()
                    elif bp[0] == 0 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                        self.end_rect_drag()
                        self.last_lmb = True

                if bp[0] != 1:
                    self.rectDragActive = self.findparampressed("alt_func")
            else:
                if bp[0] == 1 and self.last_lmb and (self.last_rmb and self.last_mmb):
                    self.begin_draw_drag()
                    self.last_lmb = False
                elif bp[0] == 1 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                    self.update_draw_drag()
                elif bp[0] == 0 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                    self.end_draw_drag()
                    self.last_lmb = True

                if bp[2] == 1 and self.last_rmb and (self.last_lmb and self.last_mmb):
                    self.begin_rect_drag()
                    self.last_rmb = False
                elif bp[2] == 1 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                    self.update_rect_drag()
                elif bp[2] == 0 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                    self.end_rect_drag()
                    self.last_rmb = True

            self.movemiddle(bp)

            # aaah math
            if self.mirrorp:
                px = pos.x
                py = pos.y
                if self.mirrorpos[1] == 0:
                    px = pos.x - self.xoffset * 2
                    px = self.mirrorpos[0] * 2 + (-px - 1)
                else:
                    py = pos.y - self.yoffset * 2
                    py = self.mirrorpos[0] * 2 + (-py - 1)
                px = px * self.size + self.field.rect.x
                py = py * self.size + self.field.rect.y
                pg.draw.rect(self.surface, cursor, [px, py, self.size, self.size], 1)
        if self.mirrorp:

            px = (self.mirrorpos[0] + self.xoffset) * self.size + self.field.rect.x
            py = (self.mirrorpos[0] + self.yoffset) * self.size + self.field.rect.y
            if self.mirrorpos[1] == 0:
                pg.draw.rect(self.surface, mirror, [px, self.field.rect.y, 3, self.field.field.get_height()])
            else:
                pg.draw.rect(self.surface, mirror, [self.field.rect.x, py, self.field.field.get_width(), 3])
        if pg.key.get_pressed()[pg.K_LCTRL]:
            try:
                geodata = eval(pyperclip.paste())
                if geodata[0] != "GE" or not isinstance(geodata[1], list):
                    return
                pos = self.field.rect.topleft + (self.pos * self.size if self.onfield else pg.Vector2(0, 0))
                rect = pg.Rect([pos, pg.Vector2(len(geodata[1]), len(geodata[1][0])) * self.size])

                pg.draw.rect(self.surface, blue, rect, 1)
            except Exception:
                pass

    def get_slope_orientation(self, pos: pg.Vector2):
        x = int(pos.x)
        y = int(pos.y)
        wallcount = 0
        acell = [0] * 4
        invalidAdjacentSlopes = [[3, 2], [3, 5], [5, 4], [2, 4]]
        if not self.canplaceit(x, y, x, y):
            return
        for count, i in enumerate(col4):
            try:
                cell = self.data["GE"][x+i[0]][y+i[1]][self.layer][0]
            except IndexError:
                cell = self.data["EX"]["defaultTerrain"]
            if cell in invalidAdjacentSlopes[count]:
                return False
            acell[count] = 1 if (cell == 1) else 0
            if cell in [1]:
                wallcount += 1
        if wallcount == 2:
            if acell == [1, 1, 0, 0]:
                self.state = 2
                return True
            elif acell == [1, 0, 1, 0]:
                self.state = 3
                return True
            elif acell == [0, 0, 1, 1]:
                self.state = 1
                return True
            elif acell == [0, 1, 0, 1]:
                self.state = 0
                return True
        return False

    def slopify(self, pos: pg.Vector2):
        x = int(pos.x)
        y = int(pos.y)
        if self.data["GE"][x][y][self.layer][0] != 0:
            return
        if self.get_slope_orientation(pg.Vector2(x, y)):
            self.place(pos, False)

    def drawtile(self, posoffset, toolsized):
        cellsize2 = [self.size, self.size]
        if isinstance(self.placetile, int):
            curtool = [
                graphics["tileplaceicon"][str(self.placetile + self.state)][0] * self.size,
                graphics["tileplaceicon"][str(self.placetile + self.state)][1] * self.size]
            rect = [posoffset[0] * self.size, posoffset[1] * self.size]
            self.fieldadd.blit(toolsized, rect, [curtool, cellsize2])
            if self.mirrorp:
                px = int(posoffset.x)
                py = int(posoffset.y)
                if self.mirrorpos[1] == 0:
                    px = self.mirrorpos[0] * 2 + (-px - 1)
                else:
                    py = self.mirrorpos[0] * 2 + (-py - 1)
                self.area[px][py] = False
                px *= self.size
                py *= self.size
                self.fieldadd.blit(self.toolrender, [px, py], [curtool, cellsize2])

    def brushpaint(self, pos: pg.Vector2, toolsized):
        for xp, xd in enumerate(self.data["GE"]):
            for yp, yd in enumerate(xd):
                vec = pg.Vector2(xp, yp)
                dist = pos.distance_to(vec)
                if dist <= self.brushsize - 0.5 and self.area[xp][yp]:
                    self.place(vec, False)
                    self.drawtile(vec, toolsized)

    def bucket(self, pos: pg.Vector2):
        filterblock = self.data["GE"][int(pos.x)][int(pos.y)][self.layer][0]
        self.emptyarea()
        self.place(pos, False)
        lastarea = [[True for _ in range(self.levelheight)] for _ in range(self.levelwidth)]
        print(filterblock)
        while lastarea != self.area:
            print(lastarea == self.area)
            lastarea = copy.deepcopy(self.area)
            for xp, xd in enumerate(self.area):
                for yp, cell in enumerate(xd):
                    if not self.area[xp][yp]:
                        for i in col4:
                            posx = xp + i[0]
                            posy = yp + i[1]
                            if 0<=posx<len(self.area) and 0<=posy<len(self.area[0]) and \
                                    self.area[posx][posy] and \
                                    self.data["GE"][posx][posy][self.layer][0] == filterblock:
                                self.place(pg.Vector2(posx, posy), False)
                                break
        print("Done filling")

    def linepoints(self, pointa: pg.Vector2, pointb: pg.Vector2):
        plotLine(pointa, pointb, self.place)

    def replacestate(self):
        self.replaceair = not self.replaceair
        self.labels[2].set_text(self.labels[2].originaltext + str(self.replaceair))

    def pastegeo(self):
        try:
            self.emptyarea()
            geodata = eval(pyperclip.paste())
            if geodata[0] != "GE" or not isinstance(geodata[1], list):
                return
            for xi, x in enumerate(geodata[1]):
                for yi, y in enumerate(x):
                    pa = pg.Vector2(0, 0)
                    if self.field.rect.collidepoint(pg.mouse.get_pos()):
                        pa = self.pos
                    xpos = -self.xoffset + xi + int(pa.x)
                    ypos = -self.yoffset + yi + int(pa.y)
                    if (self.replaceair and y[0] == 0) or not self.canplaceit(xpos, ypos, xpos, ypos):
                        continue
                    self.data["GE"][xpos][ypos][self.layer] = y
                    self.area[xpos][ypos] = False
            self.detecthistory(["GE"])
            self.renderer.geo_render_area(self.area, self.layer)
            self.rfa()
        except Exception:
            print("Error pasting data!")

    def s0(self):
        self.state = 0

    def inverse(self):
        self.selectedtool = "IN"
        self.placetile = 0.2
        self.mx = 0

    def walls(self):
        self.selectedtool = "WL"
        self.placetile = 1
        self.mx = 0

    def air(self):
        self.selectedtool = "AR"
        self.placetile = 0
        self.mx = 0

    def slope(self):
        self.selectedtool = "SL"
        self.placetile = 2
        self.mx = 0

    def floor(self):
        self.selectedtool = "FL"
        self.placetile = 6
        self.mx = 0

    def rock(self):
        self.selectedtool = "RK"
        self.placetile = -9
        self.mx = 0

    def spear(self):
        self.selectedtool = "SP"
        self.placetile = -10
        self.mx = 0

    def move(self):
        self.selectedtool = "MV"
        self.placetile = 0.1
        self.mx = 0

    def crack(self):
        self.selectedtool = "CR"
        self.placetile = -11
        self.mx = 0

    def beam(self):
        self.selectedtool = "BM"
        self.placetile = -1
        self.mx = 2

    def glass(self):
        self.selectedtool = "GL"
        self.placetile = 9
        self.mx = 0

    def shortcutentrance(self):
        self.selectedtool = "SE"
        self.placetile = 7
        self.mx = 0

    def shortcut(self):
        self.selectedtool = "SC"
        self.placetile = -5
        self.mx = 0

    def dragonden(self):
        self.selectedtool = "D"
        self.placetile = -7
        self.mx = 0

    def entrance(self):
        self.selectedtool = "E"
        self.placetile = -6
        self.mx = 0

    def mirror(self):
        self.mirrorp = not self.mirrorp
        self.mirrorpos = [self.levelwidth // 2, 0]

    def clearall(self):
        self.selectedtool = "CA"
        self.placetile = 0.3

    def flychains(self):
        self.selectedtool = "FC"
        self.placetile = -12
        self.mx = 0

    def flyhive(self):
        self.selectedtool = "HV"
        self.placetile = -3
        self.mx = 0

    def scavengerhole(self):
        self.selectedtool = "SH"
        self.placetile = -21
        self.mx = 0

    def garbagewormden(self):
        self.selectedtool = "GWD"
        self.placetile = -13
        self.mx = 0

    def whack_a_mole_hole(self):
        self.selectedtool = "WMH"
        self.placetile = -19
        self.mx = 0

    def waterfall(self):
        self.selectedtool = "W"
        self.placetile = -18
        self.mx = 0

    def wormgrass(self):
        self.selectedtool = "WG"
        self.placetile = -20
        self.mx = 0

    def clearlayer(self):
        self.selectedtool = "CL"
        self.placetile = 0.5
        self.mx = 0

    def clearblock(self):
        self.selectedtool = "CB"
        self.placetile = 0.6
        self.mx = 0

    def copylayer(self):
        self.selectedtool = "CP"
        self.placetile = 0.1
        self.mx = 0

    def cutlayer(self):
        self.selectedtool = "CT"
        self.placetile = 0.5
        self.mx = 0

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

    def place(self, pos, render=True):
        x = int(pos.x)
        y = int(pos.y)
        self.mirrorplace(pos, render)
        if x >= self.levelwidth or y >= self.levelheight or x < 0 or y < 0:
            return
        self.area[x][y] = False
        if self.placetile != 0.1:  # dont place
            if self.placetile == 0.2:  # inverse
                if self.data["GE"][x][y][self.layer][0] == 0:
                    self.data["GE"][x][y][self.layer][0] = 1
                else:
                    self.data["GE"][x][y][self.layer][0] = self.reverseslope(self.data["GE"][x][y][self.layer][0])
            elif self.placetile == 0.3:  # clear all
                self.data["GE"][x][y] = [[0, []], [0, []], [0, []]]
            elif self.placetile == 7:  # shortcut entrance
                if self.data["GE"][x][y][self.layer][0] == 7:
                    self.data["GE"][x][y][self.layer][0] = 1
                else:
                    self.data["GE"][x][y][self.layer][0] = 7
                    if 4 not in self.data["GE"][x][y][self.layer][1]:
                        self.data["GE"][x][y][self.layer][1].append(4)
            elif self.placetile == 0.5:  # clear layer
                self.data["GE"][x][y][self.layer] = [0, []]
            elif self.placetile == 0.6:  # clear upper
                self.data["GE"][x][y][self.layer][1] = []
            elif self.selectedtool in graphics["codes"].keys():  # else
                if graphics["codes"][self.selectedtool] == 1:
                    self.data["GE"][x][y][self.layer][0] = self.placetile + self.state
                if graphics["codes"][self.selectedtool] == 0:
                    if (abs(int(self.placetile))) + self.state not in self.data["GE"][x][y][self.layer][1]:                        
                        if abs(int(self.placetile)) + self.state in GEOMETRY_ENTRANCE_NODES:
                            for st in self.data["GE"][x][y][self.layer][1]:
                                if st in GEOMETRY_ENTRANCE_NODES:
                                    self.data["GE"][x][y][self.layer][1].remove(st)

                        self.data["GE"][x][y][self.layer][1].append((abs(int(self.placetile))) + self.state)
                    else:
                        self.data["GE"][x][y][self.layer][1].remove((abs(int(self.placetile))) + self.state)
            else:
                self.data["GE"][x][y][self.layer][0] = self.placetile
        if render:
            self.render_geo_area()
            self.rfa()

    def mirrorplace(self, pos, render=False):
        if not self.mirrorp:
            return
        x = int(pos.x)
        y = int(pos.y)
        if self.mirrorpos[1] == 0:
            x = self.mirrorpos[0] * 2 + (-x - 1)
        else:
            y = self.mirrorpos[0] * 2 + (-y - 1)
        if x >= self.levelwidth or y >= self.levelheight or x < 0 or y < 0:
            return
        self.area[x][y] = False
        if self.placetile != 0.1:
            if self.placetile == 0.2:
                if self.data["GE"][x][y][self.layer][0] == 0:
                    self.data["GE"][x][y][self.layer][0] = 1
                else:
                    self.data["GE"][x][y][self.layer][0] = self.reverseslope(self.data["GE"][x][y][self.layer][0])
            elif self.placetile == 0.3:
                self.data["GE"][x][y] = [[0, []], [0, []], [0, []]]
            elif self.placetile == 7:
                self.data["GE"][x][y][self.layer][0] = 7
                if 4 not in self.data["GE"][x][y][self.layer][1]:
                    self.data["GE"][x][y][self.layer][1].append(4)
            elif self.placetile == 0.5:
                self.data["GE"][x][y][self.layer] = [0, []]
            elif self.placetile == 0.6:
                self.data["GE"][x][y][self.layer][1] = []
            elif self.selectedtool in graphics["codes"].keys():
                if graphics["codes"][self.selectedtool] == 1:
                    self.data["GE"][x][y][self.layer][0] = self.reverseslope(self.placetile + self.state)
                if graphics["codes"][self.selectedtool] == 0:
                    if (abs(int(self.placetile))) + self.state not in self.data["GE"][x][y][self.layer][1]:
                        self.data["GE"][x][y][self.layer][1].append((abs(int(self.placetile))) + self.state)
                    else:
                        self.data["GE"][x][y][self.layer][1].remove((abs(int(self.placetile))) + self.state)
            else:
                self.data["GE"][x][y][self.layer][0] = self.reverseslope(self.placetile)
        if render:
            self.render_geo_area()
            self.rfa()

    def reverseslope(self, slope):
        if slope in [2, 3, 4, 5]:
            if self.selectedtool == "SL":
                if self.mirrorp:
                    if self.mirrorpos[1] == 0:
                        return [3, 2, 5, 4][slope - 2]
                    else:
                        return [4, 5, 2, 3][slope - 2]
            elif self.selectedtool == "IN":
                return [5, 4, 3, 2][slope - 2]
        if self.selectedtool == "IN":
            return 0
        return slope

    def tool_rect(self):
        self.fillshape2 = "rect"
        self.recaption()

    def tool_rect_hollow(self):
        self.fillshape2 = "rect-hollow"
        self.recaption()

    def tool_circle(self):
        self.fillshape2 = "circle"
        self.recaption()

    def tool_circle_hollow(self):
        self.fillshape2 = "circle-hollow"
        self.recaption()

    def tool_line(self):
        self.fillshape2 = "line"
        self.recaption()

    def tool_pencil(self):
        self.brushsize = 1
        self.recaption()

    def tool_brush(self):
        self.brushsize = 2
        self.recaption()

    def tool_fill(self):
        self.bucketTool = True
        self.recaption()

    def brushp(self):
        self.brushsize += 1

    def brushm(self):
        self.brushsize = max(self.brushsize-1, 1)

    @property
    def custom_info(self):
        try:
            return f"{super().custom_info} | Placing: {self.selectedtool} | LMB tool: remind me to reimplement this, RMB tool: {self.fillshape2}"
        except TypeError:
            return super().custom_info
        
    @property
    def brush_active(self):
        return self.brushsize > 1
