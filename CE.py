import render
from menuclass import *
from lingotojson import *

error = settings["snap_error"] # snap error

class CE(MenuWithField):
    def __init__(self, surface: pg.surface.Surface, renderer: render.Renderer):
        self.mname = "CE"
        self.mode = "move"  # move, edit
        super().__init__(surface, "CE", renderer, renderall=False)

        self.held = False
        self.cameraSnapActive = True
        self.heldindex = 0
        self.drawcameras = 2
        self.camoffset = pg.Vector2(0, 0)
        self.pressed = [False] * 4
        self.heldpointindex = 0
        
        if renderer.color_geo:
            renderer.color_geo = False
        self.rerenderActiveEditors(renderer.lastlayer)

        self.rfa()
        self.blit()
        self.resize()

    def blit(self):
        super().blit()
        self.labels[0].set_text(self.labels[0].originaltext % len(self.data["CM"]["cameras"]) + f" | Snap: {'Active' if self.cameraSnapActive else 'Inactive'} | Zoom: {(self.size / preview_cell_size) * 100}%")

        if self.onfield and len(self.data["CM"]["cameras"]) > 0:

            bp = self.getmouse
            s = [
                self.findparampressed("-addup"),
                self.findparampressed("-adddown"),
                self.findparampressed("-addleft"),
                self.findparampressed("-addright")
            ]

            self.if_set(s[0], 0)
            self.if_set(s[1], 1)
            self.if_set(s[2], 2)
            self.if_set(s[3], 3)
            mpos = pg.Vector2(pg.mouse.get_pos()) / self.size * preview_cell_size
            if self.held and self.heldindex < len(self.data["CM"]["cameras"]) and self.mode == "move":
                val = list(self.camoffset + mpos)
                val[0] = round(val[0] * preview_to_render_fac, 4)
                val[1] = round(val[1] * preview_to_render_fac, 4)
                for indx, camera in enumerate(self.data["CM"]["cameras"]):
                    if indx == self.heldindex:
                        continue
                    xpos, ypos = toarr(camera, "point")
                    valx, valy = val
                    if self.cameraSnapActive:
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
                            startpos = pg.Vector2(val) / preview_cell_size * self.size + v
                            endpos = pg.Vector2(xpos, ypos) / preview_cell_size * self.size + v
                            pg.draw.line(self.surface, purple, startpos, endpos, 1)
                val = makearr(val, "point")
                self.data["CM"]["cameras"][self.heldindex] = val

            if not self.suppresslmb:
                if bp[0] == 1 and self.last_lmb and (self.last_rmb and self.last_mmb):
                    self.last_lmb = False
                    if self.mode == "move":
                        if not self.held:
                            self.pickupcamera()
                        else:
                            self.placecamera()
                    else:
                        self.setcursor(pg.SYSTEM_CURSOR_SIZEALL)
                elif bp[0] == 1 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                    if self.mode == "edit" and self.held:
                        quadindx = self.getquad(self.heldindex)
                        rect = self.getcamerarect(self.data["CM"]["cameras"][self.heldindex])
                        qlist = [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft]
                        mouse = pg.Vector2(pg.mouse.get_pos()) - qlist[quadindx]
                        r, o = mouse.rotate(90).as_polar()
                        if settings["CE_unlock_angle"]:
                            self.data["CM"]["quads"][self.heldindex][quadindx] = \
                                [o, round(r / 100 / self.size * preview_cell_size, 4)]
                        else:
                            self.data["CM"]["quads"][self.heldindex][quadindx] = \
                                [o, round(min(r / 100 / self.size * preview_cell_size, 1), 4)]

                elif bp[0] == 0 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                    self.setcursor()
                    self.detecthistory(["CM", "quads", self.heldindex])
                    self.last_lmb = True
                    self.rfa()

            self.movemiddle(bp)
            #print(self.offset)

    def togglemode(self):
        if self.mode == "move":
            self.edit()
        else:
            self.move()

    def togglesnap(self):
        self.cameraSnapActive = not self.cameraSnapActive

    def edit(self):
        if self.held:
            self.mode = "edit"
            self.recaption()
        else:
            print("First pick up camera!")

    def move(self):
        self.mode = "move"
        self.recaption()

    def camup(self):
        if self.held and self.heldindex + 1 < len(self.data["CM"]["cameras"]):
            c = self.data["CM"]["cameras"].pop(self.heldindex)
            q = self.data["CM"]["quads"].pop(self.heldindex)
            self.heldindex += 1
            self.data["CM"]["cameras"].insert(self.heldindex, c)
            self.data["CM"]["quads"].insert(self.heldindex, q)
            self.updatehistory(["CM"])

    def camdown(self):
        if self.held and self.heldindex - 1 >= 0:
            c = self.data["CM"]["cameras"].pop(self.heldindex)
            q = self.data["CM"]["quads"].pop(self.heldindex)
            self.heldindex -= 1
            self.data["CM"]["cameras"].insert(self.heldindex, c)
            self.data["CM"]["quads"].insert(self.heldindex, q)
            self.updatehistory(["CM"])

    def copycamera(self):
        if self.held:
            pyperclip.copy(str(["CE", self.data["CM"]["quads"][self.heldindex]]))

    def pastedata(self):
        if not self.held:
            try:
                geodata = eval(pyperclip.paste())
                if geodata[0] != "CE" or not isinstance(geodata[1], list) or len(pyperclip.paste()) <= 2:
                    return
                self.data["CM"]["cameras"].append(makearr([0, 0], "point"))
                self.data["CM"]["quads"].append(geodata[1])
                self.held = True
                self.heldindex = len(self.data["CM"]["cameras"]) - 1
                self.detecthistory(["CM"])
                self.rfa()
            except Exception:
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
        mpos = pg.Vector2(pg.mouse.get_pos()) / self.size * preview_cell_size
        closeindex = self.closestcameraindex()

        self.heldindex = closeindex
        self.held = True
        self.camoffset = pg.Vector2(toarr(self.data["CM"]["cameras"][self.heldindex], "point")) // preview_to_render_fac - mpos
        print(self.camoffset)
        print(self.offset)

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
        #mpos = pg.Vector2(pg.mouse.get_pos()) / self.size * previewCellSize
        self.data["CM"]["cameras"].append(makearr([0, 0], "point"))
        self.data["CM"]["quads"].append([[0, 0], [0, 0], [0, 0], [0, 0]])
        self.heldindex = len(self.data["CM"]["cameras"]) - 1
        self.held = True
        self.camoffset = pg.Vector2(0, 0) - self.offset * preview_cell_size - pg.Vector2(720, 480)
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

    def addup(self):
        if not self.held:
            cam = self.closestcameraindex()
            quadindx = self.getquad(cam)
            if settings["CE_unlock_angle"]:
                self.data["CM"]["quads"][cam][quadindx][1] = round(self.data["CM"]["quads"][cam][quadindx][1] + settings["CE_angle_add_speed"], 4)
            else:
                self.data["CM"]["quads"][cam][quadindx][1] = round(min(self.data["CM"]["quads"][cam][quadindx][1] + settings["CE_angle_add_speed"], 1), 4)

    def adddown(self):  # ddddddddddd
        if not self.held:
            cam = self.closestcameraindex()
            quadindx = self.getquad(cam)
            self.data["CM"]["quads"][cam][quadindx][1] = round(
                max(self.data["CM"]["quads"][cam][quadindx][1] - settings["CE_angle_add_speed"], 0), 4)

    def addleft(self):
        if not self.held:
            cam = self.closestcameraindex()
            quadindx = self.getquad(cam)
            self.data["CM"]["quads"][cam][quadindx][0] = math.floor(self.data["CM"]["quads"][cam][quadindx][0] -
                settings["CE_angle_rotate_speed"]) % 360

    def addright(self):
        if not self.held:
            cam = self.closestcameraindex()
            quadindx = self.getquad(cam)
            self.data["CM"]["quads"][cam][quadindx][0] = math.ceil(
                self.data["CM"]["quads"][cam][quadindx][0] + settings["CE_angle_rotate_speed"]) % 360

    @property
    def custom_info(self):
        return f"{super().custom_info} | Mode: {self.mode}"