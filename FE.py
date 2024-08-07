from menuclass import *
from lingotojson import *
import random


class FE(MenuWithField):
    def __init__(self, surface: pg.surface.Surface, renderer):
        self.mname = "FE"

        self.currentcategory = 0
        self.currentindex = 0
        self.selectedeffect = 0
        self.paramindex = 0

        self.matshow = False

        self.mpos = [0, 0]
        self.mmove = False

        self.innew = True # if you in new effects tab or in added effects tab

        self.buttonslist = [] # effects to be added
        self.buttonslist2 = [] # added effects
        self.params = [] # parameters of effects as buttons

        self.brushsize = 5

        self.copymode = False

        super().__init__(surface, "FE", renderer)
        self.drawtiles = True
        #self.fieldadd.set_colorkey(None)
        self.fieldadd.set_alpha(180)

        if renderer.color_geo:
            renderer.color_geo = False
        self.rerenderActiveEditors(renderer.lastlayer)

        self.makeparams()
        self.rfa()
        self.rebuttons()
        self.blit()
        self.resize()

    def blit(self):
        pg.draw.rect(self.surface, ui_settings["TE"]["menucolor"], pg.rect.Rect(self.buttonslist[:-1][0].xy,
                                                                            [self.buttonslist[:-1][0].rect.w,
                                                                            len(self.buttonslist[:-1]) *
                                                                            self.buttonslist[:-1][0].rect.h + 1]))
        ts = sum(pg.display.get_window_size()) // 120
        super().blit()
        for i in self.buttonslist:
            i.blitshadow()
        for i in self.buttonslist2:
            i.blitshadow()
        for i in self.params:
            i.blitshadow()
        self.buttonslist[-1].blit(sum(pg.display.get_window_size()) // 100)

        for i in self.params:
            i.blit()
        for i in self.buttonslist[:-1]:
            i.blit(ts)
            if i.onmouseover():
                effect = self.geteffect(i.text)
                if effect is not None and effect.get("preview"):
                    if ui_settings["global"]["previewleftside"]:
                        previewPos = [i.rect.bottomleft[0] - effect["preview"].get_width(), i.rect.bottomleft[1]]
                    self.surface.blit(effect["preview"], previewPos)
        for i in self.buttonslist2:
            i.blit(ts)
            if i.onmouseover():
                effect = self.geteffect(i.text)
                if effect is not None and effect.get("preview"):
                    if effect["preview"].get_height() + i.rect.y > self.surface.get_height():
                        previewPos = [i.rect.x + i.rect.w, self.surface.get_height()-effect["preview"].get_height()]
                        if ui_settings["global"]["previewleftside"]:
                            previewPos = [i.rect.bottomleft[0] - effect["preview"].get_width(), self.surface.get_height()-effect["preview"].get_height()]
                        self.surface.blit(effect["preview"], previewPos)
                    else:
                        previewPos = i.rect.bottomright
                        if ui_settings["global"]["previewleftside"]:
                            previewPos = [i.rect.bottomleft[0] - effect["preview"].get_width(), i.rect.bottomleft[1]]
                        self.surface.blit(effect["preview"], previewPos)
        
        feCursor = ui_settings["global"]["colors"]["FECursor"]

        ciroff = 16 if self.buttonslist[self.currentindex].indicatorcol != pg.Color(black) else 10
        cir = [self.buttonslist[self.currentindex].rect.x + ciroff,
            self.buttonslist[self.currentindex].rect.y + self.buttonslist[self.currentindex].rect.h / 2]
        pg.draw.circle(self.surface, cursor if self.innew else cursor2, cir, self.buttonslist[self.currentindex].rect.h / 3)  
        if len(self.buttonslist2) > 0:
            cir2 = [self.buttonslist2[self.selectedeffect].rect.x + 10,
                    self.buttonslist2[self.selectedeffect].rect.y + self.buttonslist2[self.selectedeffect].rect.h / 2]
            pg.draw.circle(self.surface, cursor2 if self.innew else cursor, cir2, self.buttonslist2[self.selectedeffect].rect.h / 3)

        mpos = pg.Vector2(pg.mouse.get_pos())
        bp = self.getmouse

        if self.onfield and len(self.data["FE"]["effects"]) > 0:         
            posoffset = self.posoffset
            pos2 = self.pos2

            if not self.copymode:
                if self.brushsize <= 1:
                    maxstrrect = [[pos2.x, pos2.y], [self.size, self.size]]
                    pg.draw.rect(self.surface, feCursor, maxstrrect, 1)
                else:
                    pg.draw.circle(self.surface, feCursor, mpos, self.brushsize * self.size - (self.size // 2), 1)

            if posoffset != self.mpos:
                self.mpos = posoffset
                self.mmove = True
            updatedCells = []

            if not self.suppresslmb:
                if bp[0] == 1 and self.last_lmb and (self.last_rmb and self.last_mmb):
                    self.last_lmb = False
                    self.mmove = True
                    self.rectdata = [posoffset, pg.Vector2(0, 0), pos2]
                elif bp[0] == 1 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                    self.rectdata[1] = posoffset - self.rectdata[0]
                    if (0 <= posoffset.x < self.levelwidth) and (0 <= posoffset.y < self.levelheight) and self.mmove:
                        if not self.copymode:
                            updatedCells = self.paint(posoffset.x, posoffset.y, 1)
                        self.mmove = False
                    if self.copymode:
                        rect = self.vec2rect(self.rectdata[2], pos2)
                        tx = f"{int(rect.w / self.size)}, {int(rect.h / self.size)}"
                        widgets.fastmts(self.surface, tx, *(mpos + pg.Vector2(15, 4)), white)
                        pg.draw.rect(self.surface, blue, rect, 5)
                elif bp[0] == 0 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                    rect = self.vec2rect(self.rectdata[0], posoffset)
                    if self.copymode:
                        data1 = self.data["FE"]["effects"][self.selectedeffect]["mtrx"][rect.x:rect.w + rect.x]
                        data1 = [i[rect.y:rect.w + rect.y] for i in data1]
                        pyperclip.copy(str(["FE", data1]))
                        print("Copied!")
                    self.updatehistory([["FE", "effects", self.selectedeffect, "mtrx"]])
                    #self.detecthistory(["FE", "effects", self.selectedeffect, "mtrx"])
                    self.last_lmb = True
                    self.renderfield()
                    self.renderer.rendereffectselective(self.selectedeffect, updatedCells)

                if bp[2] == 1 and self.last_rmb and (self.last_lmb and self.last_mmb):
                    self.last_rmb = False
                    self.mmove = True
                elif bp[2] == 1 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                    if (0 <= posoffset[0] < self.levelwidth) and (0 <= posoffset[1] < self.levelheight) and self.mmove:
                        if not self.copymode:
                            updatedCells = self.paint(posoffset[0], posoffset[1], -1)
                            self.mmove = False
                elif bp[2] == 0 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                    self.updatehistory([["FE", "effects", self.selectedeffect, "mtrx"]])
                    self.last_rmb = True
                    self.renderfield()
                    self.renderer.rendereffectselective(self.selectedeffect, updatedCells)

            self.movemiddle(bp)
        for i in self.buttonslist:
            i.blittooltip()
        for i in self.buttonslist2:
            i.blittooltip()
        for i in self.buttons:
            i.blittooltip()

    def geteffect(self, text):
        for cat in assets.get_instance().effects:
            for c, i in enumerate(cat["efs"]):
                if i["nm"] == text:
                    return i
        return None

    def rebuttons(self):
        self.buttonslist = []
        self.matshow = False
        btn2 = None
        for count, item in enumerate(assets.get_instance().effects[self.currentcategory]["efs"]):
            cat = pg.rect.Rect(self.menu_ui_settings["catpos"])
            btn2 = widgets.button(self.surface, cat, ui_settings["global"]["color"], assets.get_instance().effects[self.currentcategory]["nm"], onpress=self.cats,
                tooltip=self.returnkeytext("Select category(<[-changematshow]>)"))

            rect = pg.rect.Rect(self.menu_ui_settings["itempos"])
            rect = rect.move(0, rect.h * count)

            col = pg.Color(ui_settings["global"]["color2"])
            if (count - 1) % 2 == 0:
                mul = 0.93
                col = pg.Color(int(col.r * mul),int(col.g * mul),int(col.b * mul))

            btn = widgets.button(self.surface, rect, col, item["nm"], onpress=self.addeffect)
            self.buttonslist.append(btn)
        if btn2 is not None:
            self.buttonslist.append(btn2)

        self.buttonslist2 = []
        #instead of scroll
        split2 = self.menu_ui_settings["itempos2"][1] + self.menu_ui_settings["itempos2"][3] * len(self.data["FE"]["effects"]) >= 100
        count2 = 0
        for count, item in enumerate(self.data["FE"]["effects"]):
            rect = pg.rect.Rect(self.menu_ui_settings["itempos2"])
            rect = rect.move(0, rect.h * count)
            if rect.y >= 100 and split2:
                rect = rect.move(rect.width / 2, 0)
                rect.y = self.menu_ui_settings["itempos2"][1] + self.menu_ui_settings["itempos2"][3] * count2
                count2 += 1
            if split2:
                rect.width = rect.width / 2

            col = pg.Color(ui_settings["global"]["color2"])
            if (count - 1) % 2 == 0:
                mul = 0.93
                col = pg.Color(int(col.r * mul),int(col.g * mul),int(col.b * mul))

            btn = widgets.button(self.surface, rect, col, item["nm"], onpress=self.selectmouseeffect)
            self.buttonslist2.append(btn)
        self.resize()
        self.chtext()

    def duplicate(self):
        self.data["FE"]["effects"].append(jsoncopy(self.data["FE"]["effects"][self.selectedeffect]))
        self.updatehistory([["FE", "effects"]])
        self.rebuttons()

    def copytool(self):
        self.copymode = not self.copymode

    def pastedata(self):
        try:
            geodata = eval(pyperclip.paste())
            if geodata[0] != "FE" or not isinstance(geodata[1], list):
                return
            for xi, x in enumerate(geodata[1]):
                for yi, y in enumerate(x):
                    pa = pg.Vector2(0, 0)
                    if self.field.rect.collidepoint(pg.mouse.get_pos()):
                        pa = self.pos
                    xpos = -self.xoffset + xi + int(pa.x)
                    ypos = -self.yoffset + yi + int(pa.y)
                    if not self.canplaceit(xpos, ypos, xpos, ypos):
                        continue
                    self.data["FE"]["effects"][self.selectedeffect]["mtrx"][xpos][ypos] = y
            self.detecthistory(["FE", "effects", self.selectedeffect, "mtrx"])
            self.rfa()
        except Exception:
            print("Error pasting data!")

    def cats(self):
        self.buttonslist = []
        self.settignslist = []
        self.matshow = True
        btn2 = None
        for count, item in enumerate(assets.get_instance().effects):
            cat = pg.rect.Rect(self.menu_ui_settings["catpos"])
            btn2 = widgets.button(self.surface, cat, ui_settings["global"]["color"], "Categories",
                onpress=self.changematshow)
            rect = pg.rect.Rect(self.menu_ui_settings["itempos"])
            rect = rect.move(0, rect.h * count)
            col = pg.Color([90, 90, 90])
            if (count - 1) % 2 == 0:
                mul = 0.93
                col = pg.Color(int(col.r * mul),int(col.g * mul),int(col.b * mul))
            if col is None:
                col = gray
            if count == self.currentcategory:
                col = darkgray
            btn = widgets.button(self.surface, rect, col, item["nm"], indicatorcol=item["color"], onpress=self.selectcat)
            self.buttonslist.append(btn)
        if btn2 is not None:
            self.buttonslist.append(btn2)
        self.resize()

    def changematshow(self):
        if self.matshow:
            self.currentcategory = self.currentindex
            self.currentindex = 0
            self.rebuttons()
        else:
            self.currentindex = self.currentcategory
            self.innew = True
            self.cats()

    def selectcat(self, name):
        for indx, effect in enumerate(assets.get_instance().effects):
            if effect["nm"] == name:
                self.currentcategory = indx
                self.currentindex = 0
                self.rebuttons()
                return

    def makeparams(self):
        self.params = []
        if len(self.data["FE"]["effects"]) > 0:
            self.paramindex = min(len(self.data["FE"]["effects"][self.selectedeffect]["options"]) - 1, self.paramindex)
        self.chtext()
        if len(self.data["FE"]["effects"]) == 0:
            return
        ws = pg.display.get_window_size()
        addspace = self.menu_ui_settings["additionspace"] / 100 * ws[0]
        ppos = self.menu_ui_settings["paramspos"]

        if len(self.data["FE"]["effects"][self.selectedeffect]["options"][self.paramindex][1]) < 1:
            rect = pg.Rect([ppos, self.menu_ui_settings["seedchange_size"]])
            btn = widgets.button(self.surface, rect, pg.Color(ui_settings["global"]["color2"]), "Set seed",
                onpress=self.changeseed)
            btn.resize()
            self.params.append(btn)
            return

        for c, i in enumerate(self.data["FE"]["effects"][self.selectedeffect]["options"][self.paramindex][1]):
            w, h = fs(sum(pg.display.get_window_size()) // 70)[0].size(i)
            try:
                rect = pg.Rect(self.params[-1].rect.topright[0], ppos[1] / 100 * ws[1], w + addspace, h + addspace)
            except IndexError:
                rect = pg.Rect(ppos[0] / 100 * ws[0], ppos[1] / 100 * ws[1], w + addspace, h + addspace)
            btn = widgets.button(self.surface, rect, pg.Color(ui_settings["global"]["color2"]), i, onpress=self.changeparam)
            self.params.append(btn)
        self.buttons[self.menu_ui_settings['currentparamindex']].set_text(str(self.paramindex))

    def chtext(self):
        if len(self.data["FE"]["effects"]) > 0:
            self.labels[0].set_text(self.labels[0].originaltext % (self.data["FE"]["effects"][self.selectedeffect]["options"][self.paramindex][0], self.data["FE"]["effects"][self.selectedeffect]["options"][self.paramindex][2]))
            self.labels[1].set_text(self.labels[1].originaltext + self.data["FE"]["effects"][self.selectedeffect]["nm"] + f" | Zoom: {(self.size / preview_cell_size) * 100}%")
            self.buttons[self.menu_ui_settings["currentparamindex"]].set_text(str(self.paramindex))
        else:
            self.labels[0].set_text("")
            self.labels[1].set_text(f"Zoom: {(self.size / preview_cell_size) * 100}%")
            self.buttons[self.menu_ui_settings["currentparamindex"]].set_text("0")

    def changeparam(self, text): # "Delete", "Move Back", "Move Forth"
        match text:
            case "Delete":
                self.deleteeffect()
                return
            case "Move Back":
                se = self.selectedeffect - 1
                if se < 0:
                    se = 0
                self.data["FE"]["effects"].insert(se, self.data["FE"]["effects"].pop(self.selectedeffect))
                self.updatehistory([["FE"]])
                self.selectedeffect = se
                self.rebuttons()
                self.makeparams()
                self.renderer.rerendereffect()
                return
            case "Move Forth":
                se = self.selectedeffect + 1
                if se < len(self.data["FE"]["effects"]):
                    self.data["FE"]["effects"].insert(se, self.data["FE"]["effects"].pop(self.selectedeffect))
                    self.updatehistory([["FE"]])
                    self.selectedeffect = se
                    self.rebuttons()
                    self.makeparams()
                    self.renderer.rerendereffect()
                return

        self.data["FE"]["effects"][self.selectedeffect]["options"][self.paramindex][2] = text
        self.updatehistory([["FE", "effects", self.selectedeffect, "options", self.paramindex, 2]])
        self.chtext()

    def changeseed(self):
        try:
            value = self.askint("Enter value (type -1 for random)", False)
            if value == -1:
                self.data["FE"]["effects"][self.selectedeffect]["options"][self.paramindex][2] = random.randint(0, 500)
            if 0 <= value <= 500:
                print("Seed changed!")
            self.data["FE"]["effects"][self.selectedeffect]["options"][self.paramindex][2] = value
            self.updatehistory([["FE", "effects", self.selectedeffect, "options", self.paramindex, 2]])
            self.makeparams()
            return
        except ValueError:
            print("Invalid input!")

    def findeffect(self):
        nd = {}
        for cat in assets.get_instance().effects:
            for item in cat["efs"]:
                nd[item["nm"]] = cat["nm"]
        name = self.find(nd, "Select a prop")
        if name is None:
            return
        self.addeffect(name)

    def prevparam(self):
        if len(self.data["FE"]["effects"]) < 1:
            return
        if self.paramindex - 1 >= 0:
            self.paramindex -= 1
        else:
            self.paramindex = len(self.data["FE"]["effects"][self.selectedeffect]["options"]) - 1
        self.makeparams()

    def nextparam(self):
        if len(self.data["FE"]["effects"]) < 1:
            return
        if self.paramindex + 1 < len(self.data["FE"]["effects"][self.selectedeffect]["options"]):
            self.paramindex += 1
        else:
            self.paramindex = 0
        self.makeparams()

    def nextcat(self):
        #self.innew = True
        self.currentindex = 0
        if self.currentcategory + 1 >= len(assets.get_instance().effects):
            self.currentcategory = 0
            self.rebuttons()
            return
        self.currentcategory += 1
        self.rebuttons()

    def prevcat(self):
        #self.innew = True
        self.currentindex = 0
        if self.currentcategory - 1 < 0:
            self.currentcategory = len(assets.get_instance().effects) - 1
            self.rebuttons()
            return
        self.currentcategory -= 1
        self.rebuttons()

    def navnext(self):
        if self.innew:
            self.nextcat()
        else:
            self.nextparam()
        
    def navprev(self):
        if self.innew:
            self.prevcat()
        else:
            self.prevparam()

    def resize(self):
        super().resize()
        if hasattr(self, "field"):
            for i in self.buttonslist:
                i.resize()
            for i in self.buttonslist2:
                i.resize()
            self.makeparams()

    def renderfield(self):
        super().renderfield()
        self.fieldadd.set_alpha(180)
        self.rf3()
        self.recaption()
        self.makeparams()

    def rf3(self):
        if len(self.data["FE"]["effects"]) > 0:
            fillcol = mixcol_empty
            if self.draweffects != 0:
                fillcol = pg.Color(mixcol_empty.r, mixcol_empty.g, mixcol_empty.b, 0)
            #self.fieldadd.fill(white)
            self.rendermatrix(self.fieldadd, self.size, self.data["FE"]["effects"][self.selectedeffect]["mtrx"], fillcol)

    def deleteeffect(self):
        try:
            self.data["FE"]["effects"].pop(self.selectedeffect)
            if self.draweffects > len(self.data['FE']['effects']):
                self.draweffects = 0
                self.rfa()
        except IndexError:
            print("No elements in list!")
        self.selectedeffect = 0
        self.paramindex = 0

        if len(self.data["FE"]["effects"]) <= 0:
            self.innew = True

        self.updatehistory([["FE"]])
        self.rebuttons()
        self.makeparams()

    def addordeleteselectedeffect(self):
        if self.innew:
            self.addeffect(self.buttonslist[self.currentindex].text)
            return
        #self.innew = True
        #self.deleteeffect()

    def addeffect(self, text):
        self.innew = True
        for cat in assets.get_instance().effects:
            for effect in cat["efs"]:
                if effect["nm"] == text:
                    image = effect.get("preview")
                    if image:
                        del effect["preview"]
                        ef = copy.deepcopy(effect)
                        effect["preview"] = image
                    else:
                        ef = copy.deepcopy(effect)
                    mtrx = [[0 for _ in range(self.levelheight)] for _ in range(self.levelwidth)]
                    ef["mtrx"] = mtrx
                    for n, i in enumerate(ef["options"]):
                        if i[0].lower() == "seed":
                            ef["options"][n][2] = random.randint(0, 500)
                    self.data["FE"]["effects"].append(ef.copy())
                    self.innew = False
                    self.selectedeffect = len(self.data["FE"]["effects"]) - 1
                    self.recaption()
                    self.updatehistory([["FE"]])
                    self.renderfield()
                    self.rebuttons()
                    return

    def selectmouseeffect(self):
        self.innew = False
        for indx, i in enumerate(self.buttonslist2):
            if i.onmouseover():
                self.selectedeffect = indx
                self.paramindex = 0
                self.renderfield()
                return

    def paint(self, x, y, st):
        currenteffect = self.data["FE"]["effects"][self.selectedeffect]["nm"]
        strength = 10 + (90 * self.findparampressed("str100"))
        if currenteffect in e["maxstr"]:
            strength = 10000
        updatedCells = []
        for xp, xd in enumerate(self.data["FE"]["effects"][self.selectedeffect]['mtrx']):
            if abs(x - xp) > self.brushsize: # very rough condition to skip cells outside of brush range
                continue
            for yp, yd in enumerate(xd):
                if abs(y - yp) > self.brushsize:
                    continue
                val = yd
                dist = 1.0 - (pg.Vector2(xp, yp).distance_to(pg.Vector2(x, y)) / self.brushsize)

                if dist > 0 and dist < self.brushsize + 1:

                    val = float(min(max(val + strength * dist * st, 0), 100))
                    
                    self.data["FE"]["effects"][self.selectedeffect]['mtrx'][xp][yp] = val
                    updatedCells.append([xp, yp])

        #self.rf3()
        self.rendermatrixselective(self.fieldadd, self.size, self.data["FE"]["effects"][self.selectedeffect]["mtrx"], updatedCells)
        return updatedCells

    def scroll_up(self):
        if self.findparampressed("brush_size_scroll"):
            self.bsup()
            return False
        return True
    
    def scroll_down(self):
        if self.findparampressed("brush_size_scroll"):
            self.bsdown()
            return False
        return True

    def bsup(self):
        self.brushsize += 1

    def bsdown(self):
        self.brushsize = max(self.brushsize - 1, 1)

    def innewtab(self):
        self.innew = True

    def notinnewtab(self):
        if len(self.data["FE"]["effects"]) <= 0:
            self.innew = True
        else:
            self.innew = not self.innew

    def scrl_up_new(self):
        self.innewtab()
        self.currentindex -= 1
        if self.currentindex < 0:
            self.currentindex = len(self.buttonslist) - 2

    def scrl_up_menu(self):
        #self.paramindex = 0
        self.innew = False
        self.selectedeffect -= 1
        if self.selectedeffect < 0:
            self.selectedeffect = len(self.data["FE"]["effects"]) - 1
        self.renderfield()

    def scrl_down_new(self):
        self.innewtab()
        self.currentindex += 1
        if self.currentindex > len(self.buttonslist) - 2:
            self.currentindex = 0

    def scrl_down_menu(self):
        #self.paramindex = 0
        self.innew = False
        self.selectedeffect += 1
        if self.selectedeffect > len(self.data["FE"]["effects"]) - 1:
            self.selectedeffect = 0
        self.renderfield()

    def scrl_up(self):
        if self.innew:
            self.scrl_up_new()
            return
        self.scrl_up_menu()
    def scrl_down(self):
        if self.innew:
            self.scrl_down_new()
            return
        self.scrl_down_menu()

    @property
    def custom_info(self):
        try:
            return f"{super().custom_info} | Selected effect: {self.data['FE']['effects'][self.selectedeffect]['nm']}[{self.selectedeffect}]"
        except TypeError:
            return super().custom_info
        except IndexError:
            return super().custom_info
