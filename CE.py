import render
from menuclass import *
from lingotojson import *

error = settings["global"]["snap_error"] # snap error

class CE(MenuWithField):
    def __init__(self, surface: pg.surface.Surface, renderer: render.Renderer):
        self.menu = "CE"
        super().__init__(surface, "CE", renderer, renderall=False)

        self.held = False
        self.heldindex = 0
        self.drawcameras = True
        self.camoffset = pg.Vector2(0, 0)
        self.pressed = [False] * 4

        self.rfa()
        self.blit()
        self.resize()

    def blit(self):
        super().blit()
        self.labels[0].set_text(self.labels[0].originaltext % len(self.data["CM"]["cameras"]))

        if self.onfield and len(self.data["CM"]["cameras"]) > 0:

            bp = self.getmouse
            s = [self.findparampressed("-addup"),
                 self.findparampressed("-adddown"),
                 self.findparampressed("-addleft"),
                 self.findparampressed("-addright")]

            self.if_set(s[0], 0)
            self.if_set(s[1], 1)
            self.if_set(s[2], 2)
            self.if_set(s[3], 3)
            mpos = pg.Vector2(pg.mouse.get_pos()) / self.size * image1size
            if self.held and self.heldindex < len(self.data["CM"]["cameras"]):
                val = list(self.camoffset + mpos)
                val[0] = round(val[0], 4)
                val[1] = round(val[1], 4)
                for indx, camera in enumerate(self.data["CM"]["cameras"]):
                    if indx == self.heldindex:
                        continue
                    xpos, ypos = toarr(camera, "point")
                    valx, valy = val
                    s = False
                    if xpos - error < valx < xpos + error:
                        val[0] = xpos
                        s = True
                    if ypos - error < valy < ypos + error:
                        val[1] = ypos
                        s = True
                    if s:
                        v = pg.Vector2(self.field.rect.topleft) + (pg.Vector2(camw/2, camh/2) * self.size)
                        v += self.offset * self.size
                        startpos = pg.Vector2(val) / image1size * self.size + v
                        endpos = pg.Vector2(xpos, ypos) / image1size * self.size + v
                        pg.draw.line(self.surface, purple, startpos, endpos, 3)
                val = makearr(val, "point")
                self.data["CM"]["cameras"][self.heldindex] = val

            if bp[0] == 1 and self.mousp and (self.mousp2 and self.mousp1):
                self.mousp = False
                if not self.held:
                    self.pickupcamera()
                else:
                    self.placecamera()
            elif bp[0] == 0 and not self.mousp and (self.mousp2 and self.mousp1):
                self.mousp = True
                self.rfa()

            self.movemiddle(bp)

    def camup(self):
        if self.held:
            c = self.data["CM"]["cameras"].pop(self.heldindex)
            q = self.data["CM"]["quads"].pop(self.heldindex)
            self.heldindex += 1
            self.data["CM"]["cameras"].insert(c, self.heldindex)
            self.data["CM"]["quads"].insert(q, self.heldindex)

    def camdown(self):
        if self.held:
            c = self.data["CM"]["cameras"].pop(self.heldindex)
            q = self.data["CM"]["quads"].pop(self.heldindex)
            self.heldindex -= 1
            self.data["CM"]["cameras"].insert(c, self.heldindex)
            self.data["CM"]["quads"].insert(q, self.heldindex)

    def copycamera(self):
        if self.held:
            pyperclip.copy(str(self.data["CM"]["quads"][self.heldindex]))

    def pastedata(self):
        if not self.held:
            try:
                geodata = eval(pyperclip.paste())
                if type(geodata) != list or len(pyperclip.paste()) <= 2:
                    return
                self.data["CM"]["cameras"].append(makearr([0, 0], "point"))
                self.data["CM"]["quads"].append(geodata)
                self.held = True
                self.heldindex = len(self.data["CM"]["cameras"]) - 1
                self.detecthistory(["CM"])
                self.rfa()
            except:
                print("Error pasting data!")

    def if_set(self, pressed, indx):
        if pressed and not self.pressed[indx]:
            self.pressed[indx] = True
        elif pressed and self.pressed[indx]:
            pass
        elif not pressed and self.pressed[indx]:
            self.pressed[indx] = False
            i = self.closestcameraindex()
            self.updatehistory([["CM", "quads", i]])

    def pickupcamera(self):
        mpos = pg.Vector2(pg.mouse.get_pos()) / self.size * image1size
        closeindex = self.closestcameraindex()

        self.heldindex = closeindex
        self.held = True
        self.camoffset = pg.Vector2(toarr(self.data["CM"]["cameras"][self.heldindex], "point")) - mpos

    def placecamera(self):
        self.held = False
        self.updatehistory([["CM"]])

    def deletecamera(self):
        if len(self.data["CM"]["cameras"]) > 0 and self.heldindex < len(self.data["CM"]["cameras"]) and self.held:
            self.data["CM"]["cameras"].pop(self.heldindex)
            self.data["CM"]["quads"].pop(self.heldindex)
            self.held = False
            self.updatehistory([["CM"]])

    def addcamera(self):
        self.data["CM"]["cameras"].append(makearr([0, 0], "point"))
        self.data["CM"]["quads"].append([[0, 0], [0, 0], [0, 0], [0, 0]])
        self.heldindex = len(self.data["CM"]["cameras"]) - 1
        self.held = True
        self.camoffset = pg.Vector2(0, 0)
        self.updatehistory([["CM"]])

    def closestcameraindex(self):
        mpos = pg.Vector2(pg.mouse.get_pos())

        closeindex = 0
        dist = 10000

        for indx, cam in enumerate(self.data["CM"]["cameras"]):
            center = pg.Vector2(self.getcamerarect(cam).center)
            dist2 = center.distance_to(mpos)
            if dist2 < dist:
                dist = dist2
                closeindex = indx
        return closeindex

    def getquad(self, indx):
        mpos = pg.Vector2(pg.mouse.get_pos())
        rect = self.getcamerarect(self.data["CM"]["cameras"][indx])

        dist = [pg.Vector2(i).distance_to(mpos) for i in [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft]]

        closest = dist.index(min(dist))

        return (closest)

    def addup(self):
        if not self.held:
            cam = self.closestcameraindex()
            quadindx = self.getquad(cam)
            self.data["CM"]["quads"][cam][quadindx][1] = round(min(self.data["CM"]["quads"][cam][quadindx][1] + self.settings["addspeed"], 1), 4)

    def adddown(self):  # ddddddddddd
        if not self.held:
            cam = self.closestcameraindex()
            quadindx = self.getquad(cam)
            self.data["CM"]["quads"][cam][quadindx][1] = round(
                max(self.data["CM"]["quads"][cam][quadindx][1] - self.settings["addspeed"], 0), 4)

    def addleft(self):
        if not self.held:
            cam = self.closestcameraindex()
            quadindx = self.getquad(cam)
            self.data["CM"]["quads"][cam][quadindx][0] = math.floor(self.data["CM"]["quads"][cam][quadindx][0] -
                                                          self.settings["rotatespeed"]) % 360

    def addright(self):
        if not self.held:
            cam = self.closestcameraindex()
            quadindx = self.getquad(cam)
            self.data["CM"]["quads"][cam][quadindx][0] = math.ceil(self.data["CM"]["quads"][cam][quadindx][0] + self.settings["rotatespeed"]) % 360