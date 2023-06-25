from menuclass import *
from tkinter.filedialog import asksaveasfilename


class LE(MenuWithField):

    def __init__(self, surface: pg.surface.Surface, renderer):
        self.menu = "LE"
        super().__init__(surface, "LE", renderer)
        self.field2 = widgets.window(self.surface, self.settings["d1"])
        self.field3 = self.field2.copy()

        self.ofstop = ofstop
        self.ofsleft = ofsleft

        sc = [(len(self.data["GE"]) + self.ofsleft) * image1size, (len(self.data["GE"][0]) + self.ofstop) * image1size]
        try:
            lev = os.path.splitext(self.data["path"])[0] + ".png"
            self.field2.field = pg.transform.scale(loadimage(lev), sc)
        except FileNotFoundError:
            self.field2.field = pg.surface.Surface(sc)
            self.field2.field.fill(white)

        self.shadowhistory = []
        self.redohistory = []
        self.oldshadow = self.field2.field.copy()

        self.size = image1size

        self.message = ''
        self.n = 0

        self.imagerect = [375, 375]
        self.direction = 0
        self.selectedimage = 0
        self.mode = True
        self.tileimage = None
        self.tileimage2 = None

        self.pressed = [False] * 4

        self.images = {True: [], False: []}

        for i in self.settings["images"]:
            img = loadimage(path2cast + i)
            img.set_colorkey(white)
            self.images[True].append(img)

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

        fieldpos = [xos - (self.ofsleft * self.size), yos - (self.ofstop * self.size)]
        fieldpos2 = [fieldpos[0] + math.sin(math.radians(self.data[self.menu]["lightAngle"])) * self.data[self.menu]["flatness"] * (self.size),
                     fieldpos[1] - math.cos(math.radians(self.data[self.menu]["lightAngle"])) * self.data[self.menu]["flatness"] * (self.size)]

        self.field.field.blit(self.field3.field, fieldpos)
        if not pg.key.get_pressed()[pg.K_LSHIFT]:
            self.field.field.blit(self.field3.field, fieldpos2)
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

            self.labels[0].set_text("Image: " + self.settings["images"][self.selectedimage])
            self.labels[1].set_text(f"X: {curpos_on_field[0]}, Y: {curpos_on_field[1]}")

            self.surface.blit(self.tileimage, curpos)
            bp = self.getmouse

            if bp[0] == 1 and self.mousp and (self.mousp2 and self.mousp1):
                self.mousp = False
                self.n = 1
            elif bp[0] == 1 and not self.mousp and (self.mousp2 and self.mousp1) and self.n == 1:
                sizepr = self.map_to_field(self.tileimage.get_width(), self.tileimage.get_height())
                self.field3.field.blit(self.tileimage, curpos_on_field)
                self.fieldadd.blit(self.field3.field, fieldpos)
                self.field2.field.blit(pg.transform.scale(self.tileimage, sizepr), curpos_on_field2)
            elif bp[0] == 0 and not self.mousp and (self.mousp2 and self.mousp1):
                self.fieldadd.fill(white)
                self.mousp = True
                self.updateshadowhistory()
                self.save()
                self.renderfield()
            self.movemiddle(bp)

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
        return [x / ((len(self.data["GE"]) + self.ofsleft) * self.size) * self.field2.field.get_width(),
                y / ((len(self.data["GE"][0]) + self.ofstop) * self.size) * self.field2.field.get_height()]

    def rs(self):
        if not hasattr(self, "field2"):
            return
        self.field3 = self.field2.copy()
        self.field3.field = pg.transform.scale(self.field2.field,
                                               [(len(self.data["GE"]) + self.ofsleft) * self.size,
                                                (len(self.data["GE"][0]) + self.ofstop) * self.size])
        self.field3.field.set_alpha(100)
        self.field3.field.set_colorkey(white)

    def renderfield(self):
        self.rs()
        super().renderfield()

    def save(self):
        if self.data["path"] == "":
            level = asksaveasfilename(defaultextension="wep")
            self.data["level"] = os.path.basename(level)
            self.data["path"] = level
            self.data["dir"] = os.path.abspath(level)
            self.message = "save"
            lev = os.path.splitext(self.data["path"])[0] + ".png"
            pg.image.save(self.field2.field, lev)
        else:
            lev = os.path.splitext(self.data["path"])[0] + ".png"
            pg.image.save(self.field2.field, lev)

    def retile(self):
        self.tileimage2 = self.images[self.mode][self.selectedimage].copy()
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

    def rotate(self):
        self.tileimage = pg.transform.rotate(self.tileimage2, self.direction)

    def setwh(self):
        rect = [abs(self.imagerect[0]), abs(self.imagerect[1])]
        self.tileimage2 = pg.transform.scale(self.tileimage2, rect)

    def updateTile(self):
        self.tileimage = self.tileimage2.copy()
        self.rotate()

    def inverse(self):
        self.mode = not self.mode
        self.retile()

    def rl(self):
        self.direction += 1
        self.rotate()

    def rr(self):
        self.direction -= 1
        self.rotate()

    def hp(self):
        self.imagerect[1] += 1
        if self.imagerect[1] == 0:
            self.imagerect[1] = 1
        self.setwh()
        self.retile()

    def hm(self):
        self.imagerect[1] -= 1
        if self.imagerect[1] == 0:
            self.imagerect[1] = -1
        self.setwh()
        self.retile()

    def wp(self):
        self.imagerect[0] += 1
        if self.imagerect[0] == 0:
            self.imagerect[0] = 1
        self.setwh()
        self.retile()

    def wm(self):
        self.imagerect[0] -= 1
        if self.imagerect[0] == 0:
            self.imagerect[0] = -1
        self.setwh()
        self.retile()

    def fp(self):
        self.data[self.menu]["flatness"] = min(self.data[self.menu]["flatness"] + 1, 10)

    def fm(self):
        self.data[self.menu]["flatness"] = max(self.data[self.menu]["flatness"] - 1, 1)

    def lp(self):
        self.data[self.menu]["lightAngle"] = min(self.data[self.menu]["lightAngle"] + 1, 180)

    def lm(self):
        self.data[self.menu]["lightAngle"] = max(self.data[self.menu]["lightAngle"] - 1, 90)

    def lightmod(self):
        if self.mode:
            self.inverse()

    def darkmod(self):
        if not self.mode:
            self.inverse()
