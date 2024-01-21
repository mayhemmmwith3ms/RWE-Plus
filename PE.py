from menuclass import *
import random as rnd
from rope import RopeModel

values = {
    "release": {
        -1: "left",
        1: "right",
        "def": "none"
    },
    "renderTime": {
        0: "Pre Effcts",  # ?
        "def": "Post Effcts"
    },
    "variation": {
        0: "random"
    },
    "applyColor": {
        0: "NO",
        "def": "YES"
    },
    "color": {
        0: "NONE"
    },
}


class PECursorData():
    def __init__(self):
        self.rotation = 0
        self.scale = pg.Vector2() # unfortunately not an actual multiplicative scale number

class PE(MenuWithField):
    def __init__(self, surface: pg.surface.Surface, renderer):
        self.menu = "PE"

        self.props = renderer.props
        self.propcolors = renderer.propcolors

        self.reset_settings()

        self.buttonslist = []
        self.settingslist = []
        self.matshow = False

        self.currentcategory = 0
        self.toolindex = 0

        self.depth = 0

        self.normheight = 0

        self.cursor:PECursorData = PECursorData()

        self.selectedprop = self.props[list(self.props.keys())[self.currentcategory]][0]
        self.selectedimage: pg.Surface = self.selectedprop["images"][0]
        self.ropeobject = None
        self.snap = False
        self.notes = []

        self.quads = [[0, 0], [0, 0], [0, 0], [0, 0]]
        self.quadsnor = self.quads.copy() # quad's default position
        self.lastpos = pg.Vector2(0, 0)

        self.prop_settings = {}

        self.helds = [False] * 4
        self.helppoins = pg.Vector2(0, 0)
        self.helppoins2 = pg.Vector2(0, 0)

        self.delmode = False
        self.copymode = False
        self.renderprop = True
        self.modpress = False
        self.block_next_placement = False

        self.lastPropPivotPressed = False
        self.propPivotPoint = []
        self.lastPropPivotRot = 0
        self.hasPropPivotBaseRot = False
        self.propPivotBaseRot = 0            

        super().__init__(surface, "PE", renderer)
        self.drawtiles = True
        self.catlist = [[]]
        for category in self.props.keys():
            self.catlist[-1].append(category)
            if len(self.catlist[-1]) >= self.menu_ui_settings["category_count"]:
                self.catlist.append([])
        self.drawprops = True
        cat = list(self.props.keys())[self.currentcategory]
        self.setprop(self.props[cat][0]["nm"], cat)
        self.resize()
        self.rebuttons()

        if renderer.color_geo:
            renderer.color_geo = False
        self.rerenderActiveEditors(renderer.lastlayer)
        renderer.props_full_render(renderer.lastlayer)

        self.rfa()

        if "selectedProp" in self.persistent_data:
            self.setprop(self.persistent_data["selectedProp"])

        if "cursorData" in self.persistent_data:
            self.cursor.rotation = self.persistent_data["cursorData"][0]
            self.cursor.scale = pg.Vector2(self.persistent_data["cursorData"][1])
            self.match_cursor()

        if "depth" in self.persistent_data:
            self.depth = self.persistent_data["depth"]

    def renderfield(self):
        super().renderfield()
        self.updateproptransform()

    def getval(self, params, value):
        if params not in values.keys():
            return value
        if value in values[params].keys():
            return values[params][value]
        elif "def" in values[params].keys():
            return values[params]["def"]
        else:
            if params == "color":
                return self.propcolors[value]
            return value

    def rebuttons(self):
        self.buttonslist = []
        self.matshow = False
        btn2 = None
        itemcat = list(self.props.keys())[self.currentcategory]
        for count, item in enumerate(self.props[itemcat]):
            cat = pg.rect.Rect(self.menu_ui_settings["catpos"])
            btn2 = widgets.button(self.surface, cat, item["color"], itemcat, onpress=self.changematshow,
                tooltip=self.returnkeytext("Select category(<[-changematshow]>)"))
            rect = pg.rect.Rect(self.menu_ui_settings["itempos"])
            rect = rect.move(0, rect.h * count)

            col = gray
            if (count - 1) % 2 == 0:
                mul = 0.93
                col = pg.Color(int(col.r * mul),int(col.g * mul),int(col.b * mul))

            btn = widgets.button(self.surface, rect, col, item["nm"], onpress=self.setprop)
            self.buttonslist.append(btn)
        if btn2 is not None:
            self.buttonslist.append(btn2)
        if self.toolindex > len(self.props[itemcat]):
            self.toolindex = 0
        for i in self.menu_ui_settings["hide"]:
            self.buttons[i].visible = True
        self.resize()
        self.settingsupdate()

    def cats(self):
        self.buttonslist = []
        self.settingslist = []
        btn2 = None
        if not self.matshow:
            self.currentcategory = self.toolindex // self.menu_ui_settings["category_count"]
            self.toolindex %= self.menu_ui_settings["category_count"]
        self.matshow = True
        for count, item in enumerate(self.catlist[self.currentcategory]):
            # rect = pg.rect.Rect([0, count * self.settings["itemsize"], self.field2.field.get_width(), self.settings["itemsize"]])
            # rect = pg.rect.Rect(0, 0, 100, 10)
            cat = pg.rect.Rect(self.menu_ui_settings["catpos"])
            btn2 = widgets.button(self.surface, cat, ui_settings["global"]["color"], f"Categories {self.currentcategory}", onpress=self.changematshow)
            rect = pg.rect.Rect(self.menu_ui_settings["itempos"])
            rect = rect.move(0, rect.h * count)
            try:
                col = pg.Color([90, 90, 90])
                if (count - 1) % 2 == 0:
                    mul = 0.93
                    col = pg.Color(int(col.r * mul),int(col.g * mul),int(col.b * mul))
            except IndexError:
                col = gray
            btn = widgets.button(self.surface, rect, col, item, indicatorcol=self.props[item][0]["color"], onpress=self.selectcat)
            self.buttonslist.append(btn)
        if btn2 is not None:
            self.buttonslist.append(btn2)
        for i in self.menu_ui_settings["hide"]:
            self.buttons[i].visible = False
        self.resize()

    def selectcat(self, name):
        self.currentcategory = list(self.props.keys()).index(name)
        self.toolindex = 0
        self.rebuttons()

    def settingsupdate(self):
        self.settingslist = []
        for count, item in enumerate(self.prop_settings.items()):
            name, val = item
            rect = pg.rect.Rect(self.menu_ui_settings["settingspos"])
            rect = rect.move(0, rect.h * count)
            btn = widgets.button(self.surface, rect, self.menu_ui_settings["settingscolor"], name, onpress=self.changesettings,
                tooltip=str(self.getval(name, val)))
            self.settingslist.append(btn)
        self.resize()

    def changesettings(self, name):
        try:
            match name:
                case "release":
                    val = (self.prop_settings[name] + 2) % 3 - 1
                case "renderTime":
                    val = (self.prop_settings[name] + 1) % 2
                case "customDepth":
                    val = self.prop_settings[name] % 30 + 1
                case "variation":
                    val = (self.prop_settings[name] + 1) % len(self.selectedprop["images"])
                    self.updateproptransform()
                case "thickness":
                    val = self.prop_settings[name] % 5 + 1
                case "applyColor":
                    val = (self.prop_settings[name] + 1) % 2
                case "color":
                    val = (self.prop_settings[name] + 1) % len(self.propcolors)
                case _:
                    val = self.askint(f"value for {name} property({self.prop_settings[name]})", defaultnumber=self.prop_settings[name])
                    val = int(val)
            self.prop_settings[name] = val
        except (ValueError, TypeError):
            print("non-valid value!")
        self.settingsupdate()

    def change_variation_up(self):
        if self.prop_settings.get("variation") is None:
            return
        val = (self.prop_settings["variation"] + 1) % len(self.selectedprop["images"])
        self.prop_settings["variation"] = val
        self.updateproptransform()

    def change_variation_down(self):
        if self.prop_settings.get("variation") is None:
            return
        val = (self.prop_settings["variation"] - 1)
        if val < 0:
            val = len(self.selectedprop["images"]) - 1
        self.prop_settings["variation"] = val
        self.updateproptransform()

    def resize(self):
        super().resize()
        if hasattr(self, "field"):
            self.field.resize()
            for i in self.buttonslist:
                i.resize()
            for i in self.settingslist:
                i.resize()
            self.renderfield()

    def blit(self):
        if len(self.buttonslist) > 1:
            pg.draw.rect(self.surface, ui_settings["TE"]["menucolor"], pg.rect.Rect(self.buttonslist[0].xy, [self.buttonslist[0].rect.w, len(self.buttonslist[:-1]) * self.buttonslist[0].rect.h + 1]))
            for button in self.buttonslist:
                button.blitshadow()
            for button in self.buttonslist[:-1]:
                button.blit(sum(pg.display.get_window_size()) // 120)
            self.buttonslist[-1].blit(sum(pg.display.get_window_size()) // 100)

            for button in self.settingslist:
                button.blitshadow()
            for button in self.settingslist:
                button.blit(sum(pg.display.get_window_size()) // 120)
        super().blit()
        self.labels[2].set_text(self.labels[2].originaltext + str(self.prop_settings) + f" | Zoom: {(self.size / preview_cell_size) * 100}%")
        self.labels[0].set_text(self.labels[0].originaltext + "\n".join(self.notes))
        ciroff = 16 if self.buttonslist[self.toolindex].indicatorcol != pg.Color(black) else 10
        cir = [self.buttonslist[self.toolindex].rect.x + ciroff,
            self.buttonslist[self.toolindex].rect.y + self.buttonslist[self.toolindex].rect.h / 2]
        pg.draw.circle(self.surface, cursor, cir, self.buttonslist[self.toolindex].rect.h / 3)
        mpos = pg.Vector2(pg.mouse.get_pos())
        if self.onfield or any(self.helds):

            realpos = mpos - self.field.rect.topleft

            posonfield = ((mpos - pg.Vector2(self.field.rect.topleft)) / self.size - pg.Vector2(self.xoffset, self.yoffset)) * spritesize
            if self.snap:
                posonfield = pg.Vector2(
                    round(math.floor(realpos.x / (self.size / 2)) * (spritesize / 2) - self.xoffset * spritesize, 4),
                    round(math.floor(realpos.y / (self.size / 2)) * (spritesize / 2) - self.yoffset * spritesize, 4))

            posoffset = self.posoffset * spritesize
            bp = self.getmouse
            self.delmode = self.findparampressed("delete_mode")
            self.copymode = self.findparampressed("copy_mode")
            self.renderprop = not self.delmode and not self.copymode
            if self.lastpos != mpos and self.selectedprop["tp"] == "rope":
                self.lastpos = mpos.copy()
                ropepos = (mpos - pg.Vector2(self.field.rect.topleft)) / self.size * preview_cell_size - pg.Vector2(self.xoffset, self.yoffset) * preview_cell_size
                pA = pg.Vector2((self.quads[0][0] + self.quads[3][0]) / 2,
                                (self.quads[0][1] + self.quads[3][1]) / 2) + ropepos
                pB = pg.Vector2((self.quads[1][0] + self.quads[2][0]) / 2,
                                (self.quads[1][1] + self.quads[2][1]) / 2) + ropepos
                collDep = ((self.layer - 1) * 10) + self.depth + self.selectedprop["collisionDepth"]
                if collDep < 10:
                    cd = 0
                elif collDep < 20:
                    cd = 1
                else:
                    cd = 2
                fac = (pg.Vector2(self.quads[0]).distance_to(pg.Vector2(self.quads[3]))) / self.normheight
                self.ropeobject = RopeModel(self.data, pA, pB, self.selectedprop, fac, cd,
                                            self.prop_settings["release"])

            # pg.draw.circle(self.fieldmap, red, pg.Vector2(posoffset) / image1size * self.size, 20)
            
            s = [
                self.findparampressed("stretch_topleft"),
                self.findparampressed("stretch_topright"),
                self.findparampressed("stretch_bottomright"),
                self.findparampressed("stretch_bottomleft")
                ]

            qd = quadsize(self.quads)
            mosts = qd[2]

            self.if_set(s[0], 0)
            self.if_set(s[1], 1)
            self.if_set(s[2], 2)
            self.if_set(s[3], 3)

            rotPress = self.findparampressed("mouserotate")
            drawPivotInfo = False

            if(rotPress and not self.lastPropPivotPressed):
                self.propPivotPoint = mpos if not self.snap else self.get_snapped_pos(mpos)
                self.lastPropPivotRot = 0
            if(rotPress and self.lastPropPivotPressed):
                rot = -(pg.Vector2(self.propPivotPoint) - pg.Vector2(mpos)).angle_to(pg.Vector2(1, 0))
                if self.hasPropPivotBaseRot:
                    self.rotate(rot - self.lastPropPivotRot)
                self.lastPropPivotRot = rot
                if mpos != self.propPivotPoint and not self.hasPropPivotBaseRot:
                    self.hasPropPivotBaseRot = True
                #pg.draw.circle(self.surface, red, self.rotPressHoldPos, 4)
                drawPivotInfo = True

            self.lastPropPivotPressed = rotPress

            drawlong = False

            if bp[0] == 1 and self.last_lmb and (self.last_rmb and self.last_mmb):
                self.last_lmb = False
                if not self.block_next_placement:
                    if self.findparampressed("propvariation_change"):
                        self.change_variation_up()
                        self.settingsupdate()
                    elif self.delmode:
                        self.modpress = True
                        if len(self.data["PR"]["props"]) > 0:
                            *_, near = self.find_nearest(*posoffset)
                            self.data["PR"]["props"].pop(near)
                            self.renderer.props_full_render(self.layer)
                            self.rfa()
                            self.updatehistory([["PR", "props"]])
                    elif self.copymode:
                        self.modpress = True
                        if len(self.data["PR"]["props"]) > 0:
                            name, _, near = self.find_nearest(*posoffset)
                            self.setprop(name[1])
                            self.depth = -name[0]
                            quad = []
                            for q in name[3]:
                                quad.append(pg.Vector2(toarr(q, "point")))
                            quads2 = quad.copy()
                            qv = sum(quad, start=pg.Vector2(0, 0)) / 4
                            for i, q in enumerate(quad):
                                vec = pg.Vector2(q) - qv
                                vec = [round(vec.x, 4), round(vec.y, 4)]
                                quads2[i] = vec
                            self.quads = quads2
                            self.cursor.rotation = -(pg.Vector2(self.quads[2]) - pg.Vector2(self.quads[3])).angle_to(pg.Vector2(1, 0))
                            self.prop_settings = name[4]["settings"]
                            self.updateproptransform()
                    elif self.selectedprop["tp"] == "long":
                        self.rectdata[0] = posonfield.copy()
                        self.rectdata[1] = mpos.copy()
                        self.transform_reset()
                    else:
                        self.place()
            elif bp[0] == 1 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                if self.selectedprop["tp"] == "long" and self.renderprop and not self.block_next_placement:
                    self.transform_reset()
                    p1 = self.rectdata[0]
                    p2 = posonfield
                    vec = p2 - p1
                    if vec.length() != 0:
                        vecNormal = vec.normalize()
                    else:
                        vecNormal = pg.Vector2(0, 0)
                    vecPerpendicularNormal = vecNormal.rotate(90)
                    q = []
                    #print(self.selectedimage.get_size())
                    pWidth = (self.selectedimage.get_height() / 2) / self.fieldScale
                    q.append(posonfield + vecPerpendicularNormal * pWidth)
                    q.append(self.rectdata[0] + vecPerpendicularNormal * pWidth)
                    q.append(self.rectdata[0] - vecPerpendicularNormal * pWidth)
                    q.append(posonfield - vecPerpendicularNormal * pWidth)
                    #angle = math.degrees(math.atan2(vec.y, vec.x))
                    #distance = p1.distance_to(p2)
                    #newquads = self.quadsnor.copy()
                    #newquads[1][0] = distance + newquads[0][0]
                    #newquads[2][0] = distance + newquads[0][0]
                    #q = []
                    #point = pg.Vector2(newquads[0])
                    #for quad in newquads:
                    #    newq = pg.Vector2(quad).rotate(angle)
                    #    if quad[0] < point.x:
                    #        point.x = quad[0]
                    #    if quad[1] < point.y:
                    #        point.y = quad[1]
                    #    q.append(newq)
                    self.quads = q
                    avgX = []
                    avgY = []
                    for quad in self.quads:
                        avgX.append(quad[0])
                        avgY.append(quad[1])
                    avgX = sum(avgX) // len(avgX)
                    avgY = sum(avgY) // len(avgY)
                    i, *_, ww, wh = quadtransform(q, self.selectedimage)
                    self.rectdata[2] = pg.Vector2(i.get_size())
                    i = pg.transform.scale(i, [ww / spritesize * self.size, wh / spritesize * self.size])
                    i.set_colorkey(white)

                    if self.snap:
                        dpos = self.get_snapped_pos(mpos) - pg.Vector2(self.size / 4)
                    else:
                        dpos = mpos

                    #dpos = (((pg.Vector2(avgX, avgY) + pg.Vector2(self.field.rect.topleft)) * self.size) + pg.Vector2(self.xoffset, self.yoffset)) // spritesize
                    self.surface.blit(i, (self.rectdata[1] + dpos) / 2 - pg.Vector2(i.get_size()) / 2)

                    drawlong = True

            elif bp[0] == 0 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                self.last_lmb = True
                if self.selectedprop["tp"] == "long" and self.renderprop and not self.modpress and not self.block_next_placement:
                    self.place((self.rectdata[0] + posonfield) / 2)
                    self.transform_reset()
                self.modpress = False
                self.block_next_placement = False

            if bp[2] == 1 and self.last_rmb and (self.last_lmb and self.last_mmb):
                self.last_rmb = False
                if self.findparampressed("propvariation_change"):
                    self.change_variation_down()
                    self.settingsupdate()
                elif self.findparampressed("cursor_propdepth_inverse"):
                    self.depth_down()
                else:
                    self.depth_up()
            elif bp[2] == 0 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                self.last_rmb = True

            drawPreviewPos = mpos - pg.Vector2(self.selectedimage.get_size()) / 2
            if not any(self.helds):
                if rotPress:
                    drawPreviewPos = self.propPivotPoint - pg.Vector2(self.selectedimage.get_size()) / 2
                if self.snap:
                    drawPreviewPos = self.get_snapped_pos(drawPreviewPos + pg.Vector2(self.selectedimage.get_size()) / 2) - pg.Vector2(self.selectedimage.get_size()) / 2
            else:
                q2s = pg.Vector2(mosts[0], mosts[1])
                drawPreviewPos = self.helppoins + q2s

            if self.renderprop:
                self.surface.blit(self.selectedimage, drawPreviewPos)

                if self.selectedprop["tp"] == "rope":
                    if not self.findparampressed("pauseropephysics"):
                        self.ropeobject.modelRopeUpdate()
                    color = toarr(self.ropeobject.prop["previewColor"], "color")
                    for sIndex, segment in enumerate(self.ropeobject.segments):
                        posofwire = ((pg.Vector2(self.xoffset, self.yoffset) + (segment["pos"]) / preview_cell_size) * self.size) + pg.Vector2(self.field.rect.topleft)
                        posofnext = ((pg.Vector2(self.xoffset, self.yoffset) + (self.ropeobject.segments[min(sIndex + 1, len(self.ropeobject.segments) - 1)]["pos"]) / preview_cell_size) * self.size) + pg.Vector2(self.field.rect.topleft)
                        pg.draw.line(self.surface, [200, 200, 200], posofwire, posofnext, 1)
                        pg.draw.circle(self.surface, color, posofwire, 4)
                        #pg.draw.circle(self.surface, color, posofwire, self.ropeobject.segRad * self.fieldScale, 1)
            depthpos = [mpos[0] + 20, mpos[1]]
            if self.findparampressed("propvariation_change"):
                varpos = [mpos[0] + 20, mpos[1] + 20]
                if self.prop_settings.get('variation') == 0:
                    widgets.fastmts(self.surface, "Variation: Random", *varpos, white)
                else:
                    widgets.fastmts(self.surface, f"Variation: {self.prop_settings.get('variation')}", *varpos, white)
            rl = sum(self.selectedprop["repeatL"]) if self.selectedprop.get("repeatL") else self.selectedprop["depth"]
            widgets.fastmts(self.surface, f"Depth: {self.depth} to {rl + self.depth}", *depthpos, white, fontsize= ui_settings["global"]["fontsize"] // 2)
            if self.copymode or self.delmode:
                _, _, indx = self.find_nearest(*posoffset)
                if indx != -1:
                    for nearp in self.data["PR"]["props"][indx][3]:
                        near = pg.Vector2(toarr(nearp, "point"))
                        ofc = pg.Vector2(self.xoffset, self.yoffset)
                        pos2 = (near / spritesize + ofc) * self.size + self.field.rect.topleft
                        if self.copymode:
                            selectLineCol = blue
                        if self.delmode:
                            selectLineCol = red
                        pg.draw.line(self.surface, selectLineCol, mpos, pos2, 1)
            
            drawPreviewPos += pg.Vector2(self.selectedimage.get_size()) / 2
            
            if self.snap:
                pg.draw.line(self.surface, blue, pg.Vector2(self.get_snapped_pos(mpos).x, self.field.rect.top), pg.Vector2(self.get_snapped_pos(mpos).x, self.field.rect.bottom))
                pg.draw.line(self.surface, blue, pg.Vector2(self.field.rect.left, self.get_snapped_pos(mpos).y), pg.Vector2(self.field.rect.right, self.get_snapped_pos(mpos).y))

            if drawPivotInfo:
                pg.draw.line(self.surface, red, self.propPivotPoint, mpos)
                pg.draw.line(self.surface, red, self.propPivotPoint, pg.Vector2(self.propPivotPoint) - pg.Vector2(16, 0))

            if settings["PE_advanced_cursor"]:
                if self.findparampressed("moreinfo"):
                    cursorCol = purple
                else:
                    cursorCol = yellow
                cRotVec = pg.Vector2(0, 1).rotate(self.cursor.rotation)
                pg.draw.line(self.surface, cursorCol, drawPreviewPos + cRotVec * 8, drawPreviewPos + cRotVec * 16)
                pg.draw.line(self.surface, cursorCol, drawPreviewPos - cRotVec * 8, drawPreviewPos - cRotVec * 16)
                cRotVec = cRotVec.rotate(90)
                pg.draw.line(self.surface, cursorCol, drawPreviewPos + cRotVec * 8, drawPreviewPos + cRotVec * 12)
                pg.draw.line(self.surface, cursorCol, drawPreviewPos - cRotVec * 8, drawPreviewPos - cRotVec * 12)
                pg.draw.circle(self.surface, cursorCol, drawPreviewPos, 8, 1)

            if settings["PE_quad_display"] and not drawlong:
                for q in self.quads:
                    pg.draw.circle(self.surface, red, [q[0] * self.fieldScale, q[1] * self.fieldScale] + drawPreviewPos, 2)

            self.movemiddle(bp)
        else:
            if not self.matshow:
                for index, button in enumerate(self.buttonslist[:-1]):
                    if button.onmouseover():
                        cat = list(self.props.keys())[self.currentcategory]
                        item = self.props[cat][index]
                        if len(item["images"]) > 0:
                            w, h = item["images"][0].get_size()
                            preview_pos = button.rect.topright if not ui_settings["global"]["previewleftside"] else button.rect.topleft + pg.Vector2(-w, 0)
                            self.surface.blit(pg.transform.scale(item["images"][0], [w, h]), preview_pos)
                        break

        for button in self.buttonslist:
            button.blittooltip()
        for button in self.settingslist:
            button.blittooltip()

    def get_snapped_pos(self, rawpos):
            realpos = rawpos - self.field.rect.topleft
            s2 = self.size / 2
            pos2 = pg.Vector2(round(math.floor(realpos.x / s2) * s2, 4),
                              round(math.floor(realpos.y / s2) * s2, 4))
            pos2 += self.field.rect.topleft
            return pos2

    def find_nearest(self, x, y):
        mpos = pg.Vector2(x, y)
        near = pg.Vector2(bignum, bignum)
        propnear = []
        nindx = -1
        for indx, prop in enumerate(self.data["PR"]["props"]):
            vec = pg.Vector2(0, 0)
            for point in prop[3]:
                vec += pg.Vector2(toarr(point, "point"))
            vec /= 4
            if vec.distance_to(mpos) < near.distance_to(mpos):
                near = vec
                nindx = indx
                propnear = prop
        return propnear, near, nindx

    def depth_up(self):
        maxdepth = self.layer * 10 + 10
        self.depth = (self.depth + 1) % maxdepth
        self.add_warning()

    def depth_down(self):
        maxdepth = self.layer * 10 + 10
        self.depth -= 1
        if self.depth < 0:
            self.depth = maxdepth - 1
        self.add_warning()

    def add_warning(self):
        if self.selectedprop["tp"] not in ["simpleDecal", "variedDecal"]:
            rl = sum(self.selectedprop["repeatL"]) if self.selectedprop.get("repeatL") else self.selectedprop["depth"]
            if self.layer * 10 + self.depth <= 5 and self.layer * 10 + self.depth + rl >= 6:
                self.labels[1].set_text(self.labels[1].originaltext + "this prop will intersect with the play layer!")
                if self.selectedprop["tp"] == "antimatter":
                    self.labels[1].set_text(self.labels[1].originaltext + "Antimatter prop intersecting play layer - remember to use a restore effect on affected play relevant terrain")
            else:
                self.labels[1].set_text(self.labels[1].originaltext)

    def swichlayers(self):
        super().swichlayers()
        self.depth = self.depth % 10 + self.layer * 10
        self.add_warning()

    def swichlayers_back(self):
        super().swichlayers_back()
        self.depth = self.depth % 10 + self.layer * 10
        self.add_warning()

    def if_set(self, pressed, quadindx):
        if pressed and not self.helds[quadindx]:
            self.helds[quadindx] = True
            self.helppoins = pg.Vector2(pg.mouse.get_pos())
        elif pressed and self.helds[quadindx]:
            self.quads[quadindx] = list(pg.Vector2(pg.mouse.get_pos()) - self.helppoins)
            self.quads[quadindx] = [round(self.quads[quadindx][0], 4), round(self.quads[quadindx][1], 4)]
            self.updateproptransform()
        elif not pressed and self.helds[quadindx]:
            self.helds[quadindx] = False
            self.updateproptransform()

    def browse_next(self):
        self.toolindex += 1
        if self.toolindex > len(self.buttonslist) - 2:
            self.toolindex = 0
        if not self.matshow:
            self.setprop(self.buttonslist[self.toolindex].text)

    def browse_prev(self):
        self.toolindex -= 1
        if self.toolindex < 0:
            self.toolindex = len(self.buttonslist) - 2
        if not self.matshow:
            self.setprop(self.buttonslist[self.toolindex].text)

    def changematshow(self):
        if self.matshow:
            self.currentcategory = self.toolindex + self.currentcategory * self.menu_ui_settings["category_count"]
            self.toolindex = 0
            cat = list(self.props.keys())[self.currentcategory]
            self.setprop(self.props[cat][0]["nm"], cat)
            self.rebuttons()
        else:
            self.toolindex = self.currentcategory
            self.cats()

    def changerelease(self):
        if self.selectedprop["tp"] == "rope":
            self.changesettings("release")
            self.lastpos += pg.Vector2(1, 0) # hacky solution to trick the editor into resetting the rope model
        #print(self.selectedprop["release"])

    def cat_next_propupdate(self):
        self.cat_next()
        if not self.matshow:
            self.setprop(self.buttonslist[self.toolindex].text)

    def cat_prev_propupdate(self):
        self.cat_prev()
        if not self.matshow:
            self.setprop(self.buttonslist[self.toolindex].text)

    def cat_next(self):
        if self.matshow:
            self.currentcategory = (self.currentcategory + 1) % len(self.catlist)
            self.cats()
            self.toolindex = self.toolindex if len(self.buttonslist) - 1 > self.toolindex else 0
        else:
            self.toolindex = 0
            self.currentcategory = (self.currentcategory + 1) % len(self.props)
            self.rebuttons()

    def cat_prev(self):
        if self.matshow:
            if self.currentcategory - 1 < 0:
                self.currentcategory = len(self.catlist) - 1
            else:
                self.currentcategory = self.currentcategory - 1
            self.cats()
            self.toolindex = self.toolindex if len(self.buttonslist) - 1 > self.toolindex else 0
        else:
            self.toolindex = 0
            self.currentcategory -= 1
            if self.currentcategory < 0:
                self.currentcategory = len(self.props) - 1
            self.rebuttons()

    def setprop(self, name, cat=None):
        prop, ci = self.findprop(name, cat)
        if prop is None:
            print("Prop not found in memory! Try relaunch the app")
            return
        self.lastpos = 0
        self.selectedprop = prop.copy()
        self.currentcategory = ci[0]
        self.toolindex = ci[1]
        self.snap = "snapToGrid" in self.selectedprop["tags"]
        self.recaption()
        self.add_warning()
        self.reset_settings()
        self.applysettings()
        #self.transform_reset()
        self.match_cursor()
        self.applytags()
        self.rebuttons()

    def togglesnap(self):
        self.snap = not self.snap

    def rotate(self, a, ucursor = True):
        if ucursor:
            self.cursor.rotation += a
        if (not self.findparampressed("moreinfo")) or not settings["PE_advanced_cursor"]:
            for indx, quad in enumerate(self.quads):
                rot = rotatepoint(quad, a)
                qx, qy = rot.x, rot.y
                self.quads[indx] = [round(qx, 4), round(qy, 4)]
            self.updateproptransform()

    def flipx(self):
        #for indx, quad in enumerate(self.quads):
        #    ax = pg.Vector2(1, 0).rotate(self.cursorRotation - 90)
        #    vec = ax * abs(self.getDistAlongAxis(pg.Vector2(quad), ax))
        #    print(self.getDistAlongAxis(pg.Vector2(quad), ax))
        #    self.quads[indx] -= (quad - vec) * 2
        #self.updateproptransform()

        ax = pg.Vector2(0, 1).rotate(self.cursor.rotation)
        long = 0

        for i, q in enumerate(self.quads):
            qVec = pg.Vector2(q)
            distanceAlongAxis = self.getDistAlongAxis(qVec, ax)
            if distanceAlongAxis > long:
                long = distanceAlongAxis
        
        self.stretch(0, -long * 2)

    def flipy(self):
        #for indx, quad in enumerate(self.quads):
        #    ax = pg.Vector2(1, 0).rotate(self.cursorRotation)
        #    vec = ax * self.getDistAlongAxis(pg.Vector2(quad), ax)
        #    self.quads[indx] -= (quad - vec) * 2
        #self.updateproptransform()

        ax = pg.Vector2(1, 0).rotate(self.cursor.rotation)
        long = 0

        for i, q in enumerate(self.quads):
            qVec = pg.Vector2(q)
            distanceAlongAxis = self.getDistAlongAxis(qVec, ax)
            if distanceAlongAxis > long:
                long = distanceAlongAxis
        
        self.stretch(1, -long * 2)


    def applytags(self):
        tags = self.selectedprop["tags"]
        for tag in tags:
            match tag:
                case "randomRotat":
                    self.set_rotation(rnd.randint(0, 360))
                case "randomFlipX":
                    self.flipx() if rnd.choice([True, False]) else False
                case "randomFlipY":
                    self.flipy() if rnd.choice([True, False]) else False

    def reset_settings(self):
        self.prop_settings = {"renderorder": 0, "seed": 500, "renderTime": 0}

    def applysettings(self):
        self.prop_settings = {"renderorder": 0, "seed": rnd.randint(0, 1000), "renderTime": 0}
        random = self.selectedprop["random"] if self.selectedprop.get("random") is not None else 1
        notes = self.selectedprop["notes"].copy()
        if self.selectedprop["tp"] in ["standard", "variedStandard"]:
                if self.selectedprop["colorTreatment"] == "bevel":
                    notes.append("The highlights and shadows on this prop are generated by code,\nso it can be rotated to any degree and they will remain correct.\n")
                else:
                    notes.append("Be aware that shadows and highlights will not rotate with the prop,\nso extreme rotations may cause incorrect shading.\n")
                if self.selectedprop["tp"] == "variedStandard":
                    self.prop_settings["variation"] = 0 if random else 1

                if random:
                    notes.append("Will put down a random variation.\nA specific variation can be selected from settings.\n")
                else:
                    notes.append("This prop comes with many variations.\nWhich variation can be selected from settings.\n")
        elif self.selectedprop['tp'] == "rope":
                self.prop_settings["release"] = 0
        elif self.selectedprop["tp"] in ["variedDecal", "variedSoft"]:
            self.prop_settings["variation"] = 0 if random else 1
            self.prop_settings["customDepth"] = self.selectedprop["depth"]
            if self.selectedprop["tp"] == "variedSoft" and self.selectedprop.get("colorize"):
                self.prop_settings["applyColor"] = 1
                notes.append("It's recommended to render this prop after the effects\nif the color is activated, as the effects won't affect the color layers.\n")
        elif self.selectedprop["tp"] in ["simpleDecal", "soft", "softEffect", "antimatter"]:
            self.prop_settings["customDepth"] = self.selectedprop["depth"]

        if self.selectedprop["tp"] == "soft" or self.selectedprop["tp"] == "softEffect" or self.selectedprop["tp"] == "variedSoft":
            if self.selectedprop.get("selfShade") == 1:
                notes.append("The highlights and shadows on this prop are generated by code,\nso it can be rotated to any degree and they will remain correct.\n")
            else:
                notes.append("Be aware that shadows and highlights will not rotate with the prop,\nso extreme rotations may cause incorrect shading.\n")
        if self.selectedprop["nm"].lower() in ["wire", "zero-g wire"]:
            self.prop_settings["thickness"] = 2
            notes.append("The thickness of the wire can be set in settings.\n")
        elif self.selectedprop["nm"].lower() in ["zero-g tube"]:
            self.prop_settings["applyColor"] = 0
            notes.append("The tube can be colored white through the settings.\n")
        for tag in self.selectedprop["tags"]:
            match tag:
                case "customColor":
                    self.prop_settings["color"] = 0
                    notes.append("Custom color available\n")
                case "customColorRainBow":
                    self.prop_settings["color"] = 1
                    notes.append("Custom color available\n")
        newnotes = []
        for note in self.notes:
            if note in newnotes:
                pass
            else:
                newnotes.append(note)
        self.notes = notes
        self.settingsupdate()

    def updateproptransform(self):
        self.loadimage()
        self.selectedimage = quadtransform(self.quads, self.selectedimage)[0]
        self.selectedimage = pg.transform.scale(self.selectedimage, pg.Vector2(self.selectedimage.get_size()) / spritesize * self.size)
        self.selectedimage.set_colorkey(white)
        self.selectedimage.set_alpha(190)

    def loadimage(self):
        var = rnd.randint(0, len(self.selectedprop["images"]) - 1)
        if self.prop_settings.get("variation") not in [None, 0]:
            var = self.prop_settings["variation"] - 1
        self.selectedimage: pg.Surface = self.selectedprop["images"][var]

    def transform_resetk(self):
        self.reset_cursor()
        self.match_cursor()

    def transform_reset(self):
        self.loadimage()

        w, h = self.selectedimage.get_size()
        w = w // preview_to_render_fac
        h = h // preview_to_render_fac
        wd, hd = w / 2, h / 2
        self.quads = [[-wd, -hd], [wd, -hd], [wd, hd], [-wd, hd]]
        self.normheight = pg.Vector2(self.quads[0]).distance_to(pg.Vector2(self.quads[3]))
        self.quadsnor = self.quads.copy()
        self.updateproptransform()

    def findpropmenu(self):
        nd = {}
        for cat, item in self.props.items():
            for i in item:
                nd[i["nm"]] = cat
        name = self.find(nd, "Select a prop")
        if name is None:
            return
        self.setprop(name)
        self.block_next_placement = True

    def place(self, longpos=None):
        if not self.renderprop:
            return 
        quads = self.quads.copy()
        quads2 = quads.copy()
        mousepos = pg.Vector2(pg.mouse.get_pos())
        posonfield = ((mousepos - pg.Vector2(self.field.rect.topleft)) / self.size - pg.Vector2(self.xoffset, self.yoffset)) * spritesize
        if self.snap:
            realpos = mousepos - self.field.rect.topleft
            posonfield = pg.Vector2(
                round(math.floor(realpos.x / (self.size / 2)) * (spritesize / 2) - self.xoffset * spritesize, 4),
                round(math.floor(realpos.y / (self.size / 2)) * (spritesize / 2) - self.yoffset * spritesize, 4))
        qv = []
        for i, q in enumerate(quads):
            vec = pg.Vector2(q)
            qv.append(vec)
        qv = sum(qv, start=pg.Vector2(0, 0)) / 4
        for i, q in enumerate(quads):
            vec = pg.Vector2(q) - qv * 2 + posonfield
            if longpos:
                vec = pg.Vector2(q) - qv + longpos  # I literally have no idea how this works
            vec = [round(vec.x, 4), round(vec.y, 4)]
            quads2[i] = makearr(vec, "point")
        newpropsettings = self.prop_settings.copy()
        if self.prop_settings.get("variation") is not None:
            if self.prop_settings["variation"] == 0:  # random
                newpropsettings["variation"] = rnd.randint(1, len(self.selectedprop["images"]))
        prop = [-self.depth, self.selectedprop["nm"], makearr([self.currentcategory + 1, self.toolindex + 1], "point"), quads2, {"settings": newpropsettings}]
        if self.selectedprop["tp"] == "rope":
            points = []
            for segment in self.ropeobject.segments:
                point = [segment["pos"].x * preview_to_render_fac, segment["pos"].y * preview_to_render_fac] #i love bandaid fix
                point = makearr([round(point[0], 4), round(point[1], 4)], "point")
                points.append(point)
            prop[4]["points"] = points
        self.data["PR"]["props"].append(prop.copy())
        self.applytags()
        self.renderer.props_full_render(self.layer)
        self.rfa()
        self.updatehistory([["PR", "props"]])

    def rotate_right(self):
        if self.findparampressed("rotate_speedup"):
            self.rotate(settings["PE_prop_rotate_extra_speed"])
        else:
            self.rotate(settings["PE_prop_rotate_speed"])

    def rotate_left(self):
        if self.findparampressed("rotate_speedup"):
            self.rotate(-settings["PE_prop_rotate_extra_speed"])
        else:
            self.rotate(-settings["PE_prop_rotate_speed"])

    def rotate0(self):
        self.set_rotation(0)

    def rotate90(self):
        self.set_rotation(90)

    def rotate180(self):
        self.set_rotation(180)

    def rotate270(self):
        self.set_rotation(270)

    def set_rotation(self, rot):
        self.cursor.rotation = rot
        self.match_cursor()

    def getDistAlongAxis(self, vector, axis):
        return math.sin(axis.angle_to(vector) * 0.0174533) * vector.magnitude()

    def stretch(self, axis, pos, ucursor = True):
        if axis == 0:
            stretchVector = pg.Vector2(pos, 0)
        else:
            stretchVector = pg.Vector2(0, pos)

        absStretchVector = pg.Vector2(abs(stretchVector.x), abs(stretchVector.y))

        #sz = toarr(self.selectedprop["sz"], "point")
        #self.cursor.scale += pg.Vector2(stretchVector.x / (sz[0] * preview_cell_size), stretchVector.y / (sz[1] * preview_cell_size))
        if ucursor:
            self.cursor.scale += stretchVector

        absStretchVector = absStretchVector.rotate(self.cursor.rotation + 90)
        stretchVector = stretchVector.rotate(self.cursor.rotation)
        long = 0

        for i, q in enumerate(self.quads):
            qVec = pg.Vector2(q)
            distanceAlongAxis = self.getDistAlongAxis(qVec, absStretchVector)
            if distanceAlongAxis > long:
                long = distanceAlongAxis

        for i, q in enumerate(self.quads):
            qVec = pg.Vector2(q)
            distanceAlongAxis = self.getDistAlongAxis(qVec, absStretchVector)
            self.quads[i] -= stretchVector * (distanceAlongAxis / long)

        
        self.updateproptransform()

    def stretchy_up(self):
        self.stretch(1, settings["PE_prop_scale_speed"])

    def stretchy_down(self):
        self.stretch(1, -settings["PE_prop_scale_speed"])

    def stretchx_up(self):
        self.stretch(0, settings["PE_prop_scale_speed"])

    def stretchx_down(self):
        self.stretch(0, -settings["PE_prop_scale_speed"])

    def on_switch_editor(self):
        self.persistent_data["selectedProp"] = self.selectedprop["nm"]
        self.persistent_data["cursorData"] = [self.cursor.rotation, self.cursor.scale]
        self.persistent_data["depth"] = self.depth

    def match_cursor(self):
        self.transform_reset()
        self.rotate(self.cursor.rotation, False)
        self.stretch(0, self.cursor.scale.x, False)
        self.stretch(1, self.cursor.scale.y, False)

    def reset_cursor(self):
        self.cursor.rotation = 0
        self.cursor.scale = pg.Vector2()

    @property
    def custom_info(self):
        try:
            return f"{super().custom_info} | Selected prop: {self.selectedprop['nm']}"
        except TypeError:
            return super().custom_info
