from menuclass import *

class LE(MenuWithField):

    def __init__(self, surface: pg.surface.Surface, renderer):
        self.menu = "LE"
        super().__init__(surface, "LE", renderer)
        self.field2 = widgets.window(self.surface, self.menu_ui_settings["d1"])
        self.field3 = self.field2.copy()

        sc = [(self.levelwidth + ofsleft) * render_cell_size, (self.levelheight + ofstop) * render_cell_size]
        try:
            lev = os.path.splitext(self.data["path"])[0] + ".png"
            #self.field2.field = pg.transform.scale(loadimage(lev), sc)
            self.field2.field = pg.Surface(sc)
            self.field2.field.blit(loadimage(lev), [0, 0])
        except (FileNotFoundError, TypeError):
            self.field2.field = pg.surface.Surface(sc)
            self.field2.field.fill(white)

        self.shadowhistory = []
        self.redohistory = []
        self.oldshadow = self.field2.field.copy()

        self.message = ''
        self.n = 0

        self.imagerect = [375, 375]
        self.direction = 0
        self.selectedimage = 0
        self.mode = True
        self.tileimage = None
        self.tileimage2 = None
        self.preview = None
        self.preview2 = None

        self.mouse_pivot_anchor = None
        self.last_cur_pos = None

        self.pressed = [False] * 4

        self.images = {True: [], False: []}
        self.previewimages = {True: [], False: []}

        if renderer.color_geo:
            renderer.color_geo = False
        self.rerenderActiveEditors(renderer.lastlayer)

        for i in graphics["shadowimages"]:
            img = loadimage(path2cast + i)
            img.set_colorkey(white)
            self.images[True].append(img)

            img = loadimage(path2cast + i)
            arr = pg.pixelarray.PixelArray(img)
            arr.replace(black, pg.Color(180, 180, 255))
            img = arr.make_surface()
            img.set_colorkey(white)
            img.set_alpha(150)
            self.previewimages[False].append(img)

            img = loadimage(path2cast + i)
            arr = pg.pixelarray.PixelArray(img)
            arr.replace(black, pg.Color(0, 0, 120))
            img = arr.make_surface()
            img.set_colorkey(white)
            img.set_alpha(150)
            self.previewimages[True].append(img)

            img = loadimage(path2cast + i)
            arr = pg.pixelarray.PixelArray(img)
            arr.replace(black, red)
            arr.replace(white, black)
            arr.replace(red, white)
            img = arr.make_surface()
            img.set_colorkey(black)

            self.images[False].append(img)
        self.rs()
        self.retile()
        self.blit()
        self.resize()
        self.renderfield()

    def blit(self): # NOQA
        self.fieldadd.fill(white)
        self.field.field.fill(self.field.color)
        super().blit(not pg.key.get_pressed()[pg.K_LCTRL])

        xos = self.xoffset * self.size
        yos = self.yoffset * self.size

        fieldpos = [xos - (ofsleft * self.size), yos - (ofstop * self.size)]
        fieldpos2 = [fieldpos[0] + math.sin(math.radians(self.data[self.menu]["lightAngle"])) * self.data[self.menu]["flatness"] * (self.size),
                     fieldpos[1] - math.cos(math.radians(self.data[self.menu]["lightAngle"])) * self.data[self.menu]["flatness"] * (self.size)]

        self.field.field.blit(self.field3.field, fieldpos)
        if not pg.key.get_pressed()[pg.K_LSHIFT]:
            self.field3.field.set_alpha(60)
            self.field.field.blit(self.field3.field, fieldpos2)
            self.field3.field.set_alpha(200)
        self.field.blit(False)
        super().blit(False)
        mouspos = pg.mouse.get_pos()

        if self.onfield:
            #  pos2 = [pos[0] * self.size + self.field.rect.x, pos[1] * self.size + self.field.rect.y]
            mouspos_onfield = [mouspos[0] - self.field.rect.x - fieldpos[0], mouspos[1] - self.field.rect.y - fieldpos[1]]
            curpos = [mouspos[0] - self.tileimage.get_width() / 2, mouspos[1] - self.tileimage.get_height() / 2]

            curpos_on_field = [mouspos_onfield[0] - self.tileimage.get_width() / 2,
                                mouspos_onfield[1] - self.tileimage.get_height() / 2]

            curpos_on_field2 = self.map_to_field(curpos_on_field[0], curpos_on_field[1])

            s = [self.findparampressed("-fp"),
                self.findparampressed("-fm"),
                self.findparampressed("-lp"),
                self.findparampressed("-lm")]

            self.if_set(s[0], 0)
            self.if_set(s[1], 1)
            self.if_set(s[2], 2)
            self.if_set(s[3], 3)

            self.labels[0].set_text("Image: " + graphics["shadowimages"][self.selectedimage])
            self.labels[1].set_text(f"X: {curpos_on_field[0]}, Y: {curpos_on_field[1]} | Zoom: {(self.size / preview_cell_size) * 100}%")

            held_draw_pos = curpos

            bp = self.getmouse

            if bp[2] == 1 and self.last_rmb and (self.last_lmb and self.last_mmb):
                self.last_rmb = False
                self.mouse_pivot_anchor = mouspos
                self.last_cur_pos = mouspos
            elif bp[2] == 1 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                self.direction = (pg.Vector2(self.mouse_pivot_anchor) - pg.Vector2(mouspos)).angle_to(pg.Vector2(1, 0)) + 90
                self.rotate()
                held_draw_pos = self.mouse_pivot_anchor
                held_draw_pos = [held_draw_pos[0] - self.tileimage.get_width() / 2, held_draw_pos[1] - self.tileimage.get_height() / 2]
                self.last_cur_pos = mouspos
            elif bp[2] == 0 and not self.last_rmb and (self.last_lmb and self.last_mmb):
                self.last_rmb = True

            self.surface.blit(self.preview, held_draw_pos)

            pg.draw.rect(self.field2.field, black, [0, 0, 1, 1])
            pg.draw.rect(self.field2.field, black, [self.field2.field.get_width() - 1, self.field2.field.get_height() - 1, 1, 1])

            if bp[0] == 1 and self.last_lmb and (self.last_rmb and self.last_mmb):
                self.last_lmb = False
                self.n = 1
            elif bp[0] == 1 and not self.last_lmb and (self.last_rmb and self.last_mmb) and self.n == 1:
                sizepr = self.map_to_field(self.tileimage.get_width(), self.tileimage.get_height())
                self.field3.field.blit(self.tileimage, curpos_on_field)
                self.fieldadd.blit(self.field3.field, fieldpos)
                self.field2.field.blit(pg.transform.scale(self.tileimage, sizepr), curpos_on_field2)
            elif bp[0] == 0 and not self.last_lmb and (self.last_rmb and self.last_mmb):
                self.fieldadd.fill(white)
                self.last_lmb = True
                self.updateshadowhistory()
                self.save()
                self.renderfield()
            self.movemiddle(bp)

        lapreviewpos = self.field.rect.bottomright - pg.Vector2(240, 160)

        pg.draw.circle(self.surface, red, lapreviewpos, 6 * 5, 1)
        pg.draw.circle(self.surface, red, lapreviewpos, 6 * self.data[self.menu]["flatness"], 1)
        pg.draw.circle(self.surface, red, lapreviewpos + pg.Vector2(0, (6 * self.data[self.menu]["flatness"]) - 1).rotate(self.data[self.menu]["lightAngle"]), 6)

    def if_set(self, pressed, indx):
        if pressed and not self.pressed[indx]:
            self.pressed[indx] = True
        elif pressed and self.pressed[indx]:
            pass
        elif not pressed and self.pressed[indx]:
            self.pressed[indx] = False
            self.updatehistory([[self.menu]])

    def updateshadowhistory(self):
        if self.oldshadow != self.field2.field:
            self.shadowhistory.append([self.field2.field.copy(), self.oldshadow.copy()])
            self.oldshadow = self.field2.field.copy()
            self.redohistory = []


    def undoshadow(self):
        if len(self.shadowhistory) == 0:
            return
        f = self.shadowhistory.pop()
        self.field2.field = f[1].copy()
        self.oldshadow = self.field2.field.copy()
        self.redohistory.append([f[0].copy(), f[1].copy()])
        self.renderfield()
        self.save()

    def redoshadow(self):
        if len(self.redohistory) == 0:
            return
        f = self.redohistory.pop()
        self.field2.field = f[0].copy()
        self.oldshadow = self.field2.field.copy()
        self.shadowhistory.append([f[0].copy(), f[1].copy()])
        self.renderfield()
        self.save()


    def map_to_field(self, x, y):
        return [x / ((self.levelwidth + ofsleft) * self.size) * self.field2.field.get_width(),
                y / ((self.levelheight + ofstop) * self.size) * self.field2.field.get_height()]

    def rs(self):
        if not hasattr(self, "field2"):
            return
        self.field3 = self.field2.copy()
        self.field3.field = pg.transform.scale(self.field2.field,
                                               [(self.levelwidth + ofsleft) * self.size,
                                                (self.levelheight + ofstop) * self.size])
        self.field3.field.set_alpha(150)
        self.field3.field.set_colorkey(white)

    def renderfield(self):
        self.rs()
        super().renderfield()

    def save(self):
        if self.data["path"] == "":
            level = self.save_file_dialog()
            try:
                self.data["level"] = os.path.basename(level)
                self.data["path"] = level
                self.data["dir"] = os.path.abspath(level)
                self.message = "save"
                lev = os.path.splitext(self.data["path"])[0] + ".png"
                pg.image.save(self.field2.field, lev)
            except TypeError:
                self.message = "MN"
        else:
            lev = os.path.splitext(self.data["path"])[0] + ".png"
            pg.image.save(self.field2.field, lev)

    def retile(self):
        self.tileimage2 = self.images[self.mode][self.selectedimage].copy()
        self.preview2 = self.previewimages[self.mode][self.selectedimage].copy()
        self.setwh()
        self.updateTile()

    def changeup(self):
        self.selectedimage = (self.selectedimage + 1) % len(self.images[self.mode])
        self.retile()
        self.updateTile()

    def changedown(self):
        self.selectedimage = (self.selectedimage - 1)
        if self.selectedimage == -1:
            self.selectedimage = len(self.images[self.mode]) - 1
        self.retile()
        self.updateTile()

    def scroll_up(self):
        if self.findparampressed("brush_type_scroll"):
            self.changeup()
            return False
        return True

    def scroll_down(self):
        if self.findparampressed("brush_type_scroll"):
            self.changedown()
            return False
        return True

    def rotate(self):
        self.tileimage = pg.transform.rotate(self.tileimage2, self.direction)
        self.preview = pg.transform.rotate(self.preview2, self.direction)

    def setwh(self):
        rect = [abs(self.imagerect[0]), abs(self.imagerect[1])]
        self.tileimage2 = pg.transform.scale(self.tileimage2, rect)
        self.preview2 = pg.transform.scale(self.preview2, rect)

    def updateTile(self):
        self.tileimage = self.tileimage2.copy()
        self.preview = self.preview2.copy()
        self.rotate()

    def inverse(self):
        self.mode = not self.mode
        self.retile()

    def rl(self):
        self.direction += self.speed_mul
        self.rotate()

    def rr(self):
        self.direction -= self.speed_mul
        self.rotate()

    def hp(self):
        self.imagerect[1] += self.speed_mul
        if self.imagerect[1] == 0:
            self.imagerect[1] = 1
        self.setwh()
        self.retile()

    def hm(self):
        self.imagerect[1] -= self.speed_mul
        if self.imagerect[1] == 0:
            self.imagerect[1] = -1
        self.setwh()
        self.retile()

    def wp(self):
        self.imagerect[0] += self.speed_mul
        if self.imagerect[0] == 0:
            self.imagerect[0] = 1
        self.setwh()
        self.retile()

    def wm(self):
        self.imagerect[0] -= self.speed_mul
        if self.imagerect[0] == 0:
            self.imagerect[0] = -1
        self.setwh()
        self.retile()

    def fp(self):
        self.data[self.menu]["flatness"] = min(self.data[self.menu]["flatness"] + 1, 10)

    def fm(self):
        self.data[self.menu]["flatness"] = max(self.data[self.menu]["flatness"] - 1, 1)

    def lp(self):
        self.data[self.menu]["lightAngle"] = self.data[self.menu]["lightAngle"] + 1

    def lm(self):
        self.data[self.menu]["lightAngle"] = self.data[self.menu]["lightAngle"] - 1

    def lightmod(self):
        if self.mode:
            self.inverse()

    def darkmod(self):
        if not self.mode:
            self.inverse()

    @property
    def speed_mul(self):
        return 4 if self.findparampressed("speedup") else 1
