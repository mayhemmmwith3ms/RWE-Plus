import copy  # noqa: F401
import render
import widgets
import pyperclip  # noqa: F401
from render import *
import tkinter
from tkinter.messagebox import askyesno
from tkinter.filedialog import askopenfilename, asksaveasfilename  # noqa: F401
import concurrent.futures
import time
from path_dict import PathDict
from pathlib import Path

inputfile = ''
filepath = path2levels


def rotatepoint(point, angle):
    px, py = point
    angle = math.radians(angle)
    qx = math.cos(angle) * px - math.sin(angle) * py
    qy = math.sin(angle) * px + math.cos(angle) * py
    return pg.Vector2([qx, qy])

class MouseTextLine:
    def __init__(self, text:str, priority:float = 0, size:int = 15) -> None:
        self.text = text
        self.priority = priority
        self.size = size
    
    def __str__(self) -> str:
        return self.text

class Menu:
    def __init__(self, surface: pg.surface.Surface, renderer, name):
        self.surface = surface
        self.mname = name
        self.renderer = renderer
        self.data = renderer.data
        if settings["enable_undo"]:
            self.datalast = jsoncopy(renderer.data)
        self.menu_ui_settings = ui_settings[self.mname]
        self.hotkeys = hotkeys[name]
        self.historybuffer = []
        self.uc = []

        self.mouse_text = []

        self.recaption()
        print("Entered " + self.mname)

        self.last_lmb = True
        self.last_mmb = True
        self.last_rmb = True

        self.block_mouse_input = True
        self.justChangedZoom = False
        self.size = preview_cell_size
        self.message = ""
        self.msgdata = None
        self.buttons: list[widgets.button] = []
        self.labels: list[widgets.lable] = []

        widgets.resetpresses()

        for i in self.menu_ui_settings["buttons"]:
            try:
                f = getattr(self, i[3])
            except AttributeError:
                f = self.non
            try:
                f2 = getattr(self, i[4])
            except AttributeError:
                f2 = self.non
            if len(i) == 6:
                self.buttons.append(
                    widgets.button(self.surface, pg.rect.Rect(i[1]), i[2], i[0], onpress=f,
                        onrelease=f2, tooltip=self.returnkeytext(i[5])))
            elif len(i) == 7:
                self.buttons.append(
                    widgets.button(self.surface, pg.rect.Rect(i[1]), i[2], i[0], onpress=f,
                        onrelease=f2, tooltip=self.returnkeytext(i[5]), icon=i[6]))
        for i in self.menu_ui_settings["labels"]:
            if len(i) == 3:
                self.labels.append(widgets.lable(self.surface, self.returnkeytext(i[0]), i[1], i[2]))
            elif len(i) == 4:
                self.labels.append(widgets.lable(self.surface, self.returnkeytext(i[0]), i[1], i[2], i[3]))

        self.unlock_keys()
        self.resize()
        self.recaption()

    def setasname(self, name):
        global inputfile
        inputfile = name
        self.message = "ab"

    def unlock_keys(self):
        self.uc = []
        for i in self.hotkeys["unlock_keys"]:
            self.uc.append(getattr(pg, i))

    def watch_keys(self):
        self.message = "%"

    def recaption(self):
        pg.display.set_caption(f"OGSCULEDITOR+: {self.mname} | {tag}")

    def savef(self, saveas=False):
        if self.data["path"] and not saveas:
            save_to_path = os.path.splitext(self.data["path"])[0] + ".txt"

            if os.path.splitext(self.data["path"])[1] == ".wep":
                root = tkinter.Tk()
                root.wm_attributes("-topmost", 1)
                root.withdraw()
                c = askyesno("Legacy Project Warning", "Saving to .wep files has been removed to reduce file clutter\nThis action will override any data in this level's corresponding .txt file (or will create one if it does not already exist) with the currently loaded level, and will automatically switch the editor to the aforementioned .txt file. The data in the .wep file will not be lost.\n\nDo you still want to continue?")

                if not c:
                    return
                
                add_to_recent(save_to_path)
                remove_wep_from_recent(save_to_path)

            with open(save_to_path, "w") as save_to:
                turntolingo(self.data, save_to)

            self.data["path"] = save_to_path
            print(f"Saved level \"{save_to_path}\"")
        else:
            save_to_path = self.save_file_dialog(filetype=[("Official Editor Project", ".txt"), ("All Files", "*")])

            if save_to_path:
                with open(save_to_path, "w") as save_to:
                    turntolingo(self.data, save_to)
                
                if os.path.exists(os.path.splitext(self.data["path"])[0] + ".png"):
                    lmap = pg.image.load(os.path.splitext(self.data["path"])[0] + ".png") # copy the lightmap image when saving as 
                    pg.image.save(lmap, os.path.splitext(save_to_path)[0] + ".png")

                self.data["level"] = os.path.basename(save_to_path)
                self.data["path"] = save_to_path
                self.data["dir"] = os.path.abspath(save_to_path)

                add_to_recent(save_to_path)
        
        self.recaption()

    #def savef(self, saveas=False):
    #    if self.data["path"] != "" and not saveas:
    #        open(os.path.splitext(self.data["path"])[0] + ".wep", "w").write(json.dumps(self.data))
    #        self.data["path"] = os.path.splitext(self.data["path"])[0] + ".wep"
    #        print(os.path.splitext(self.data["path"])[0] + ".wep")
    #    else:
    #        savedest = self.save_file_dialog(filetype=[("RWE+ Project", ".wep"), ("All Files", "*")])
    #        if savedest != "" and savedest is not None:
    #            open(savedest, "w").write(json.dumps(self.data))

    #            if os.path.exists(os.path.splitext(self.data["path"])[0] + ".png"):
    #                lmap = pg.image.load(os.path.splitext(self.data["path"])[0] + ".png") # copy the lightmap image when saving as 
    #                pg.image.save(lmap, os.path.splitext(savedest)[0] + ".png")
    #                
    #            self.data["level"] = os.path.basename(savedest)
    #            self.data["path"] = savedest
    #            self.data["dir"] = os.path.abspath(savedest)
                
    #            add_to_recent(savedest)

    #    print("Level saved!")
    #    self.recaption()

    def addfolder(self, folder):
        global filepath
        filepath += "/" + folder + "/"
        self.message = "ab"

    def goback(self):
        global filepath
        p = Path(filepath)
        filepath = str(p.parent.absolute())
        self.message = "ab"

    def asksaveasfilename(self, defaultextension=None):
        if defaultextension is None:
            defaultextension = [".wep"]
        global inputfile, filepath
        filepath = path2levels
        buttons = []
        slider = 0
        labeltext = "Use scroll to navigate\nEnter to continue\nType to search\nEscape to exit\n"
        label = widgets.lable(self.surface, labeltext, [50, 0], black, 30)
        label.resize()

        def appendbuttons():
            global filepath
            widgets.resetpresses()
            f = os.listdir(filepath)
            f.reverse()
            buttons.clear()
            buttons.append(widgets.button(self.surface, pg.Rect([0, 20, 50, 5]), color2, "..", onpress=self.goback,
                                          tooltip="Go back"))
            count = 1
            for file in f:
                if inputfile.lower() in file.lower():
                    y = 5 * count - slider * 5
                    if os.path.isfile(os.path.join(filepath, file)) and os.path.splitext(file)[1] in defaultextension:
                        if y > 0:
                            buttons.append(widgets.button(self.surface, pg.Rect([0, 20 + y, 50, 5]), color2, file,
                                                          onpress=self.setasname, tooltip="File"))
                        count += 1
                    elif os.path.isdir(os.path.join(filepath, file)):
                        if y > 0:
                            buttons.append(widgets.button(self.surface, pg.Rect([0, 20 + y, 50, 5]), color2, file,
                                                          onpress=self.addfolder, tooltip="Folder"))
                        count += 1
            for button in buttons:
                button.resize()
            widgets.enablebuttons = True
            widgets.bol = False
            label.set_text(labeltext + filepath)

        inputfile = ''
        r = True
        appendbuttons()
        while r:
            self.surface.fill(color)
            for button in buttons:
                button.blitshadow()
            for button in buttons:
                button.blit()
            for button in buttons:
                if button.blittooltip():
                    continue
            label.blit()
            widgets.fastmts(self.surface, "File name:", 0, 0, fontsize=50)

            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.unicode in allleters:
                        inputfile += event.unicode
                    elif event.key == pg.K_BACKSPACE:
                        inputfile = inputfile[:-1]
                    elif event.key == pg.K_RETURN:
                        if inputfile != "":
                            r = False
                        else:
                            inputfile = "type_something_here"
                    elif event.key == pg.K_ESCAPE:
                        return None
                    appendbuttons()
                    slider = 0
                if event.type == pg.QUIT:
                    return None
                if event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        slider = max(slider - 1, 0)
                        appendbuttons()
                    elif event.button == 5:
                        slider += 1
                        appendbuttons()
                if event.type == pg.WINDOWRESIZED:
                    self.resize()
                    label.resize()
            if self.message == "ab":
                slider = 0
                self.message = ''
                appendbuttons()
            widgets.fastmts(self.surface, inputfile, 0, 50, fontsize=50)
            pg.display.flip()
            pg.display.update()
        # i = input(q + "(leave blank for cancel): ")
        if inputfile == "":
            return None
        try:
            if len(defaultextension) == 1 and os.path.splitext(inputfile)[1] != defaultextension[0]:
                return f"{filepath}{inputfile}{defaultextension[0]}"
            else:
                return f"{filepath}{inputfile}"
        except ValueError:
            print("it's not a string")
            return None

    def askint(self, q, savelevel=True, defaultnumber=0):
        if savelevel:
            self.savef()
        i = ''
        nums = "0123456789-"
        r = True
        while r:
            self.surface.fill(color)
            lws = "(level was saved):" if savelevel else ":"
            widgets.fastmts(self.surface, q + lws, 0, 0, fontsize=50)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return None
                if event.type == pg.KEYDOWN:
                    if event.unicode in nums:
                        i += event.unicode
                    elif event.key == pg.K_BACKSPACE:
                        i = i[:-1]
                    elif event.key == pg.K_RETURN:
                        r = False
                    elif event.key == pg.K_ESCAPE:
                        return None
            widgets.fastmts(self.surface, i, 0, 50, fontsize=50)
            pg.display.flip()
            pg.display.update()
        # i = input(q + "(leave blank for cancel): ")
        if i == "":
            return defaultnumber
        try:
            return int(i)
        except ValueError:
            print("it's not a number")
            return defaultnumber

    def foundthis(self, text):
        global inputfile
        print(text)
        inputfile = text + "\n"

    def find(self, filelist: dict, q):
        global inputfile
        buttons = []
        slider = 0
        label = widgets.lable(self.surface, "Use scroll to navigate\nClick what you need\nType to search\nEscape to exit",
                              [50, 0], black, 30)
        label.resize()
        widgets.bol = True
        widgets.keybol = True

        def appendbuttons():
            buttons.clear()
            count = 1
            # newdict = {}
            count2 = 0
            for item, cat in filelist.items():
                if 25 + 5*count > 100:
                    break
                if inputfile in item.lower() or inputfile in cat.lower():
                    if count2 >= slider:
                        buttons.append(widgets.button(self.surface, pg.Rect([0, 20 + 5*count, 50, 5]), color2, item, onpress=self.foundthis, tooltip=cat))
                        count += 1
                    count2 += 1
            for button in buttons:
                button.resize()
        inputfile = ''
        r = True
        appendbuttons()
        while r:
            self.surface.fill(color)
            for button in buttons:
                button.blitshadow()
            for button in buttons:
                button.blit()
            for button in buttons:
                if button.blittooltip():
                    continue
            label.blit()
            widgets.fastmts(self.surface, f"{q}:", 0, 0, fontsize=50)

            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.unicode in allleters:
                        inputfile += event.unicode
                    elif event.key == pg.K_BACKSPACE:
                        inputfile = inputfile[:-1]
                        # elif event.key == pg.K_RETURN:
                        #     r = False
                    elif event.key == pg.K_ESCAPE:
                        return None
                    appendbuttons()
                    slider = 0
                if event.type == pg.QUIT:
                    return None
                if event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        slider = max(slider - 1, 0)
                        appendbuttons()
                    elif event.button == 5:
                        slider += 1
                        appendbuttons()
                if event.type == pg.WINDOWRESIZED:
                    self.resize()
                    label.resize()
            if self.message == "ab":
                slider = 0
                self.message = ''
                appendbuttons()
            if "\n" in inputfile:
                break
            widgets.fastmts(self.surface, inputfile, 0, 50, fontsize=50)
            pg.display.flip()
            pg.display.update()
        # i = input(q + "(leave blank for cancel): ")
        widgets.bol = False
        widgets.keybol = True
        return inputfile.replace("\n", "")

    def blit(self, fontsize=None):
        if not self.touchesanything:
            self.setcursor()
        if ui_settings["global"]["doublerect"]:
            for i in self.buttons:
                i.blitshadow()
        for i in self.labels:
            i.blit()
        for i in self.buttons:
            i.blit(fontsize)
        for i in self.buttons:
            if i.blittooltip():
                continue
        if not pg.mouse.get_pressed(3)[0] and not widgets.enablebuttons:
            widgets.enablebuttons = True

    def blit_mouse_text(self):
        self.mouse_text = sorted(self.mouse_text, key=lambda tup: tup.priority)
        pixels_down = 0
        for i, text in enumerate(self.mouse_text):
            widgets.fastmts(self.surface, text.text, pg.mouse.get_pos()[0] + 20, pg.mouse.get_pos()[1] + pixels_down, white, text.size)
            pixels_down += text.size + 5
        self.mouse_text.clear()

    def add_mouse_text(self, text, priority=0, size=15):
        self.mouse_text.append(MouseTextLine(text, priority, size))

    def setcursor(self, cursor=pg.SYSTEM_CURSOR_ARROW):
        c = pg.Cursor(cursor)
        if pg.mouse.get_cursor().data[0] != c.data[0]:
            pg.mouse.set_cursor(c)

    @property
    def touchesanything(self):
        for b in self.buttons:
            if b.onmouseover():
                return True
        return False

    def updatehistory(self, paths):
        if self.data != self.datalast:
            h = [[]]
            for historypath in paths:
                ch = PathDict(self.data)[*historypath]
                lastch = PathDict(self.datalast)[*historypath]
                if ch != lastch:
                    h.append([historypath, [ch, lastch]])
            if len(h) > 0:
                self.historybuffer.append(jsoncopy(h))
            self.datalast = jsoncopy(self.data)

    def detecthistory(self, path, savedata=True):
        if self.data != self.datalast:
            pth = PathDict(self.data)[*path]
            pthlast = PathDict(self.datalast)[*path]
            history = [path]
            for xindx, x in enumerate(pth):
                if x != pthlast[xindx]:
                    history.append([[xindx], [x, pthlast[xindx]]])
            if len(history) > 0:
                self.historybuffer.append(jsoncopy(history))
            if savedata:
                self.datalast = jsoncopy(self.data)

    def non(self):
        pass

    @property
    def getmouse(self):
        mbuttons = pg.mouse.get_pressed(5)
        rmbkey = hotkeys["mouseremap"]["RMB"]
        mmbkey = hotkeys["mouseremap"]["MMB"]
        lmbkey = hotkeys["mouseremap"]["LMB"]
        keys = [False, False, False]
        for i, key in enumerate([lmbkey, mmbkey, rmbkey]):
            newkey = key.replace("ctrl", "").replace("shift", "").replace("+", "")
            match newkey.lower():
                case "lmb":
                    keys[i] = mbuttons[0]
                case "mouse1":
                    keys[i] = mbuttons[0]
                case "rmb":
                    keys[i] = mbuttons[2]
                case "mouse3":
                    keys[i] = mbuttons[2]
                case "mmb":
                    keys[i] = mbuttons[1]
                case "mouse2":
                    keys[i] = mbuttons[1]
                case "mouse4":
                    keys[i] = mbuttons[3]
                case "mouse5":
                    keys[i] = mbuttons[4]
                case _:
                    keys[i] = False
            #if key.find("ctrl") >= 0:
            #    keys[i] = keys[i] and pg.key.get_mods() & pg.KMOD_CTRL
            #else:
            #    keys[i] = keys[i] and not (pg.key.get_mods() & pg.KMOD_CTRL)
            #if key.find("shift") >= 0:
            #    keys[i] = keys[i] and pg.key.get_mods() & pg.KMOD_SHIFT
            #else:
            #    keys[i] = keys[i] and not (pg.key.get_mods() & pg.KMOD_SHIFT)
        if (True not in keys):
            self.block_mouse_input = False
        if (self.block_mouse_input):
            return [False, False, False]
        return keys

    def resize(self):
        for i in self.buttons:
            i.resize()
        for i in self.labels:
            i.resize()

    def sendsignal(self, message):
        self.message = message

    def reload(self):
        global ui_settings
        ui_settings = json.load(open(path2ui + settings["ui_theme"], "r"))
        self.__init__(self.surface, self.data, self.mname)

    def send(self, message):
        if message[0] == "-":
            self.mpos = 1
            if hasattr(self, message[1:]):
                getattr(self, message[1:])()

    def findparampressed(self, paramname: str):
        for key, value in self.hotkeys.items():
            if key == "unlock_keys":
                continue
            if value.lower() == paramname.lower():
                if pg.key.get_pressed()[getattr(pg, key.replace("@", "").replace("+", ""))]:
                    return True
                return False
        # if param not found
        return False

    def findkey(self, paramname, manyparams=False, globalkeys=False):
        p = []
        if not globalkeys:
            for key, value in self.hotkeys.items():
                if key == "unlock_keys":
                    continue
                if value.lower() == paramname.lower():
                    k = key.replace("@", "")
                    if not manyparams:
                        return k
                    p.append(k)
            for key, value in hotkeys["global"].items():
                if value.lower() == paramname.lower():
                    k = key.replace("@", "")
                    if not manyparams:
                        return k
                    p.append(k)
            if not manyparams:
                return None
        else:
            for cat, keyval in hotkeys.items():
                for key, value in keyval.items():
                    if key == "unlock_keys":
                        continue
                    if value.lower() == paramname.lower():
                        k = key.replace("@", "")
                        if not manyparams:
                            return k
                        p.append(k)
        return p

    def returnkeytext(self, text):
        pat = r"(<\[([a-z0-9\-\_\/]+)\]>)"
        found = re.findall(pat, text, flags=re.IGNORECASE)
        if found is None:
            return text
        groups = []
        string = text
        for index, fgroup in enumerate(found):
            groups.append(list(set(self.findkey(fgroup[1], manyparams=True, globalkeys=True))))
            groups[-1].sort()
            for i, key in enumerate(groups[-1]):
                k = key.replace("+", "").replace("@", "")
                if key.find("+") != -1:
                    groups[-1][i] = "ctrl + " + pg.key.name(getattr(pg, k))
                else:
                    groups[-1][i] = pg.key.name(getattr(pg, k))
            rep = ",".join(groups[-1]).replace("'", "").replace(" ", "").replace("+",
                                                                                                              " + ")
            rep = " or ".join(rep.rsplit(",", 1))
            rep = rep.replace(",", ", ")
            string = string.replace(fgroup[0], rep)
        # string = re.sub(pat, rep, text, flags=re.IGNORECASE)
        return string
    
    def save_file_dialog(self, extension=[".wep"], filetype=[("RWE+ Project", ".wep"), ("Official Editor Project", ".txt"), ("All Files", "*")]):
        if not settings["native_file_browser"]:
            level = self.asksaveasfilename(defaultextension=extension)
        else:
            root = tkinter.Tk()
            root.wm_attributes("-topmost", 1)
            root.withdraw()
            level = asksaveasfilename(defaultextension=extension, filetypes=filetype, parent=root)
        return level
    
    def open_file_dialog(self, extension=[".txt", ".wep"], filetype=[("Official Editor Project", ".txt"), ("Legacy RWE+ Project", ".wep"), ("All Files", "*")]):
        if not settings["native_file_browser"]:
            level = self.asksaveasfilename(defaultextension=extension)
        else:
            root = tkinter.Tk()
            root.wm_attributes("-topmost", 1)
            root.withdraw()
            level = askopenfilename(defaultextension=extension, filetypes=filetype, initialdir=os.path.dirname(os.path.abspath(__file__)) + "\LevelEditorProjects", parent=root)
        return level

    def on_switch_editor(self):
        self.recaption()

    def new(self):
        self.message = "new"

    @property
    def custom_info(self):
        return ""

    @property
    def levelwidth(self):
        return len(self.data["GE"])

    @property
    def levelheight(self):
        return len(self.data["GE"][0])

    def onundo(self):
        pass

    def onredo(self):
        self.onundo()


class MenuWithField(Menu):
    def __init__(self, surface: pg.Surface, name, renderer: render.Renderer, renderall=True):
        super(MenuWithField, self).__init__(surface, renderer, name)

        self.renderer = renderer

        self.mname = name

        self.drawgeo = True
        self.drawcameras = 0
        self.drawtiles = False
        self.drawprops = False
        self.draweffects = False
        self.drawgrid = False
        self.drawwater = False
        self.selectedeffect = 0
        self.tic = 0
        self.toc = 0

        self.f = pg.Surface([self.levelwidth * preview_cell_size, self.levelheight * preview_cell_size])

        self.suppresslmb = True

        self.field = widgets.window(self.surface, self.menu_ui_settings["d1"])
        self.btiles = self.data["EX2"]["extraTiles"]
        self.fieldmap = self.field.field

        self.fieldadd = self.fieldmap
        self.fieldadd.fill(white)
        self.fieldadd.set_colorkey(white)

        self.offset = self.renderer.offset
        self.size = self.renderer.size
        self.rectdata = [pg.Vector2(0, 0), pg.Vector2(0, 0), pg.Vector2(0, 0)]
        self.layer = self.renderer.lastlayer
        self.lastTileLayer = self.layer
        self.emptyarea()
        self.renderer.rendergrid()
        if renderall:
            self.rfa()

    def reload(self):
        global ui_settings
        ui_settings = json.load(open(path2ui + settings["ui_theme"], "r"))
        self.__init__(self.surface, self.renderer)

    def movemiddle(self, bp):
        if bp[1] == 1 and self.last_mmb and (self.last_rmb and self.last_lmb):
            self.rectdata[0] = self.pos
            self.rectdata[1] = self.offset
            self.last_mmb = False
        elif bp[1] == 1 and not self.last_mmb and (self.last_rmb and self.last_lmb):
            self.offset = self.rectdata[1] - (self.rectdata[0] - self.pos)
        elif bp[1] == 0 and not self.last_mmb and (self.last_rmb and self.last_lmb):
            self.field.field.fill(self.field.color)
            self.last_mmb = True
            self.renderfield()

    def drawborder(self):
        rect = [self.xoffset * self.size, self.yoffset * self.size, self.levelwidth * self.size,
                self.levelheight * self.size]
        pg.draw.rect(self.field.field, border, rect, 1)
        fig = [(self.btiles[0] + self.xoffset) * self.size, (self.btiles[1] + self.yoffset) * self.size,
               (self.levelwidth - self.btiles[2] - self.btiles[0]) * self.size,
               (self.levelheight - self.btiles[3] - self.btiles[1]) * self.size]
        rect = pg.rect.Rect(fig)
        pg.draw.rect(self.field.field, bftiles, rect, 1)
        self.field.blit()

    def drawmap(self):
        self.field.field.fill(self.field.color)
        self.field.field.blit(self.fieldmap, [self.xoffset * self.size, self.yoffset * self.size])
        self.field.field.blit(self.fieldadd, [self.xoffset * self.size, self.yoffset * self.size])
        if self.drawwater:
            self.renderwater()
        self.drawborder()

    def renderwater(self):
        if self.data["WL"]["waterLevel"] > -1:
            height = self.levelheight * self.size
            width = self.levelwidth * self.size
            top = height - ((wladd + self.data["WL"]["waterLevel"]) * self.size)
            h = height - top + 1
            s = pg.Surface([width, h])
            s.fill(blue)
            s.set_alpha(50)
            self.field.field.blit(s, (self.offset) * self.size + pg.Vector2(0, top))

    def renderfield(self):
        self.fieldmap = pg.surface.Surface([self.levelwidth * self.size, self.levelheight * self.size]).convert()

        self.fieldmap.blit(pg.transform.scale(self.f, [self.f.get_width() / preview_cell_size * self.size,
                                                       self.f.get_height() / preview_cell_size * self.size]), [0, 0])
        self.fieldadd = pg.surface.Surface([self.levelwidth * self.size, self.levelheight * self.size])
        self.fieldadd.set_colorkey(white)
        self.fieldadd.fill(white)

    def emptyarea(self):
        self.area = [[True for _ in range(self.levelheight)] for _ in range(self.levelwidth)]

    def rfa(self):
        if self.layer != self.renderer.lastlayer:
            self.rerenderActiveEditors(self.layer)
        self.f = pg.Surface([self.levelwidth * preview_cell_size, self.levelheight * preview_cell_size])
        if self.drawgeo:
            # self.renderer.geo_full_render(self.layer)
            self.f.blit(self.renderer.surf_geo, [0, 0])
        if self.drawtiles:
            # self.renderer.tiles_full_render(self.layer)
            self.f.blit(self.renderer.surf_tiles, [0, 0], special_flags=pg.BLEND_PREMULTIPLIED)
        if self.drawprops:
            # self.renderer.props_full_render()
            self.f.blit(self.renderer.surf_props, [0, 0])
        if self.drawgrid:
            self.f.blit(self.renderer.grid_surface, [0, 0])
        if self.draweffects != 0 and self.draweffects <= len(self.data['FE']['effects']):
            self.f.blit(self.renderer.surf_effect, [0, 0])
            # self.rendermatrix(self.f, image1size, self.data["FE"]["effects"][self.draweffects - 1]["mtrx"])
        self.renderfield()

    def resize(self):
        super().resize()
        if hasattr(self, "field"):
            self.field.resize()
            self.renderfield()

    @property
    def touchesanything(self):
        for b in self.buttons:
            if b.onmouseover():
                return True
        if self.field.onmouseover():
            return True
        for i in ["buttonslist", "buttonslist2", "params", "settingslist"]:
            if hasattr(self, i):
                for b in getattr(self, i):
                    if b.onmouseover():
                        return True
        return False

    def blit(self, draw=True):
        if not self.renderer.color_geo:
            self.renderer.lastlayer = self.layer
        self.renderer.offset = self.offset
        self.renderer.size = self.size
        if draw:
            self.drawmap()
        if self.drawcameras != 0:
            self.rendercameras()
        if self.draweffects != 0 and self.draweffects <= len(self.data['FE']['effects']):
            widgets.fastmts(self.surface,
                            f"Effect({self.draweffects}): {self.data['FE']['effects'][self.draweffects - 1]['nm']}",
                            *self.field.rect.midleft, white)
        #mpos = pg.mouse.get_pos()
        #if self.drawgrid and self.field.rect.collidepoint(mpos):
            #pos2 = self.pos2
            #pg.draw.line(self.surface, cursor2, [self.field.rect.left, pos2[1]],
                         #[self.field.rect.right, pos2[1]])
            #pg.draw.line(self.surface, cursor2, [pos2[0], self.field.rect.top],
                         #[pos2[0], self.field.rect.bottom])

        if not self.getmouse[0]:
            self.suppresslmb = False

        super().blit()

    def recaption(self):
        pg.display.set_caption(f"OGSCULEDITOR+ | {self.mname} | {tag} | {get_project_display_path(self.data['path'])}")

    def swichcameras(self):
        self.drawcameras = (self.drawcameras + 1) % 3

    def rerenderActiveEditors(self, layer):
        self.lastlayer = layer
        if settings["multithreading"]:
            pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            if self.drawgeo:
                pool.submit(self.renderer.geo_full_render, layer)
            if self.drawtiles:
                pool.submit(self.renderer.tiles_full_render, layer)
            if self.drawprops:
                pool.submit(self.renderer.props_full_render, layer)
            if self.draweffects and len(self.data["FE"]["effects"]):
                pool.submit(self.renderer.rendereffect, 0)
            pool.shutdown(wait=True)
        else:
            if self.drawgeo:
                self.renderer.geo_full_render(layer)
            if self.drawtiles:
                self.renderer.tiles_full_render(layer)
            if self.drawprops:
                self.renderer.props_full_render(layer)
            if self.draweffects and len(self.data["FE"]["effects"]):
                self.renderer.rendereffect(0)

    def swichlayers(self):     
        self.layer = (self.layer + 1) % 3
        if self.drawtiles:
            self.lastTileLayer = self.layer
        self.mpos = 1
        if not self.renderer.color_geo:
            self.rerenderActiveEditors(self.layer)
            self.rfa()

    def swichlayers_back(self):
        self.layer -= 1
        if self.layer < 0:
            self.layer = 2
        if self.drawtiles:
            self.lastTileLayer = self.layer
        self.mpos = 1
        if not self.renderer.color_geo:
            self.rerenderActiveEditors(self.layer)
            self.rfa()

    def start_perftimer(self):
        self.tic = time.perf_counter()

    def stop_perftimer(self):
        self.toc = time.perf_counter()
        print(f"Timer took {(self.toc - self.tic) * 1000:0.4} ms")

    def send(self, message):
        super().send(message)
        match message:
            case "SU":
                if not self.onfield:
                    return
                
                if self.scroll_up():
                    pos = self.pos
                    self.size += 1
                    self.offset -= pos - self.pos
                    self.renderfield()
                    self.justChangedZoom = True
            case "SD":
                if not self.onfield:
                    return
                
                if self.scroll_down() and self.size - 1 > 0:
                    pos = self.pos
                    self.size -= 1
                    self.offset -= pos - self.pos
                    self.renderfield()
                    self.justChangedZoom = True
            case "left":
                self.offset.x += 1
            case "right":
                self.offset.x -= 1
            case "up":
                self.offset.y += 1
            case "down":
                self.offset.y -= 1

    def scroll_down(self):
        return True

    def scroll_up(self):
        return True

    def detecthistory(self, path, savedata=True):
        if not settings["enable_undo"]:
            return
        super().detecthistory(path, savedata)
        self.renderer.data = self.data

    def updatehistory(self, paths):
        if not settings["enable_undo"]:
            return
        super().updatehistory(paths)
        self.renderer.data = self.data

    def render_geo_area(self):
        self.renderer.geo_render_area(self.area, self.layer)
        self.f.blit(self.renderer.surf_geo, [0, 0])
        #self.renderfield()

    def render_geo_full(self):
        self.renderer.geo_full_render(self.layer)
        self.f.blit(self.renderer.surf_geo, [0, 0])
        #self.renderfield()

    def render_tiles_area(self):
        self.renderer.tiles_render_area(self.area, self.layer)
        self.f.blit(assets.get_instance().tiles, [0, 0])
        #self.renderfield()

    def render_tiles_full(self):
        self.renderer.tiles_full_render(self.layer)
        self.f.blit(self.renderer.surf_tiles, [0, 0])
        #self.renderfield()

    def togglegeo(self):
        #self.drawgeo = not self.drawgeo
        self.renderer.color_geo = not self.renderer.color_geo
        self.drawgrid = self.renderer.color_geo
        self.render_geo_full()
        self.rfa()

    def toggletiles(self):
        self.drawtiles = not self.drawtiles
        if self.layer != self.lastTileLayer:
            self.renderer.tiles_full_render(self.layer)
        self.rfa()

    def toggleeffects(self):
        self.draweffects += 1
        if self.draweffects > len(self.data["FE"]["effects"]):
            self.draweffects = 0
        if self.draweffects != 0:
            self.renderer.rendereffect(self.draweffects - 1)
        self.rfa()

    def toggleprops(self):
        self.drawprops = not self.drawprops
        self.renderer.props_full_render(self.renderer.lastlayer)
        self.rfa()

    def togglegrid(self):
        self.drawgrid = not self.drawgrid
        self.rfa()

    def togglewater(self):
        self.drawwater = not self.drawwater
        self.rfa()

    def resetzoom(self):
        pos = self.pos
        self.size = preview_cell_size
        self.offset -= pos - self.pos
        self.renderfield()
        self.justChangedZoom = True

    def rendercameras(self):
        closest = 0
        if hasattr(self, "closestcameraindex"):
            closest = self.closestcameraindex()
        for indx, cam in enumerate(self.data["CM"]["cameras"]):

            rect = self.getcamerarect(cam)
            rect2 = pg.Rect(rect.x + self.size, rect.y + self.size, rect.w - self.size * 2, rect.h - self.size * 2)
            rect3 = pg.Rect(rect2.x + self.size * 8, rect2.y, rect2.w - self.size * 16, rect2.h)
            # print(camera_border, rect, self.size)
            pg.draw.rect(self.surface, camera_border, rect, 1)
            pg.draw.rect(self.surface, yellow, rect2, 1)

            pg.draw.rect(self.surface, red, rect3, 1)

            pg.draw.line(self.surface, camera_border, pg.Vector2(rect.center) - pg.Vector2(self.size * 5, 0),
                         pg.Vector2(rect.center) + pg.Vector2(self.size * 5, 0),
                         1)

            pg.draw.line(self.surface, camera_border, pg.Vector2(rect.center) - pg.Vector2(0, self.size * 5),
                         pg.Vector2(rect.center) + pg.Vector2(0, self.size * 5),
                         1)
            pg.draw.circle(self.surface, camera_border, rect.center, self.size * 3, 1)

            if "quads" not in self.data["CM"]:
                self.data["CM"]["quads"] = []
                for _ in self.data["CM"]["cameras"]:
                    self.data["CM"]["quads"].append([[0, 0], [0, 0], [0, 0], [0, 0]])
            col = camera_notheld
            if hasattr(self, "held") and hasattr(self, "heldindex"):
                if indx == self.heldindex and self.held:
                    col = camera_held

            quads = self.data["CM"]["quads"][indx]

            newquads = quads.copy()

            for i, q in enumerate(quads):
                n = [0, 0]
                nq = q[0] % 360
                n[0] = math.sin(math.radians(nq)) * q[1] * self.size * 5
                n[1] = -math.cos(math.radians(nq)) * q[1] * self.size * 5
                newquads[i] = n

            tl = pg.Vector2(rect.topleft) + pg.Vector2(newquads[0])
            tr = pg.Vector2(rect.topright) + pg.Vector2(newquads[1])
            br = pg.Vector2(rect.bottomright) + pg.Vector2(newquads[2])
            bl = pg.Vector2(rect.bottomleft) + pg.Vector2(newquads[3])

            if indx == closest and (hasattr(self, "held") and not self.held) or \
                    (hasattr(self, "mode") and self.mode == "edit" and hasattr(self, "heldindex") and
                    self.heldindex == indx):
                quadindx = self.getquad(closest)
                if hasattr(self, "mode") and self.mode == "edit":
                    quadindx = self.getquad(self.heldindex)

                vec = pg.Vector2([tl, tr, br, bl][quadindx])

                widgets.fastmts(self.surface, f"Order: {indx}", rect.centerx + self.size // 2, rect.centery + self.size // 2, white, ui_settings["global"]["fontsize"] // 2)

                pg.draw.line(self.surface, camera_notheld, rect.center, vec, 1)

                rects = [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft]
                pg.draw.line(self.surface, camera_held, rects[quadindx], vec, 1)

                qlist = [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft]

                pg.draw.circle(self.surface, camera_held, qlist[quadindx], self.size * 5, 1)
                # pg.draw.circle(self.surface, camera_held, rect.topright, self.size * 5, self.size // 3)
                # pg.draw.circle(self.surface, camera_held, rect.bottomleft, self.size * 5, self.size // 3)
                # pg.draw.circle(self.surface, camera_held, rect.bottomright, self.size * 5, self.size // 3)
            elif hasattr(self, "held") and self.held and hasattr(self, "heldindex") and self.heldindex == indx:
                widgets.fastmts(self.surface, f"Order: {indx}", rect.centerx, rect.centery, white)
            if self.drawcameras == 2:
                pg.draw.polygon(self.surface, col, [tl, bl, br, tr], 2)

    def getquad(self, indx):
        mpos = pg.Vector2(pg.mouse.get_pos())
        rect = self.getcamerarect(self.data["CM"]["cameras"][indx])

        dist = [pg.Vector2(i).distance_to(mpos) for i in [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft]]

        closest = dist.index(min(dist))

        return closest

    def saveasf(self):
        self.savef(True)

    def canplaceit(self, x, y, x2, y2):
        return (0 <= x2 and x < self.levelwidth) and (0 <= y2 and y < self.levelheight)

    def rendermatrix(self, field, size, matrix, mix=mixcol_empty):
        for xp, x in enumerate(matrix):
            for yp, cell in enumerate(x):
                col = mix.lerp(mixcol_fill, cell / 100)
                pg.draw.rect(field, col, [xp * size, yp * size, size, size], 0)

    def rendermatrixselective(self, field, size, matrix, changedCells, mix=mixcol_empty):
        for cell in changedCells:
            col = mix.lerp(mixcol_fill, matrix[cell[0]][cell[1]] / 100)
            pg.draw.rect(field, col, [cell[0] * size, cell[1] * size, size, size], 0)

    def getcamerarect(self, cam):
        pos = pg.Vector2(toarr(cam, "point")) // preview_to_render_fac
        p = (pos / preview_cell_size) * self.size + self.field.rect.topleft + self.offset * self.size
        return pg.Rect([p, [camw * self.size, camh * self.size]])

    def findprop(self, name, cat=None):
        if cat is not None:
            for itemi, item in enumerate(assets.get_instance().props[cat]):
                if item["nm"] == name:
                    return item, [list(assets.get_instance().props.keys()).index(cat), itemi]
        for cati, cats in assets.get_instance().props.items():
            for itemi, item in enumerate(cats):
                if item["nm"] == name:
                    return item, [list(assets.get_instance().props.keys()).index(cati), itemi]
        item = {
            "nm": "notfound",
            "tp": "standard",
            "colorTreatment": "bevel",
            "bevel": 3,
            "sz": "point(2, 2)",
            "repeatL": [1],
            "tags": ["randomRotat"],
            "layerExceptions": [],
            "color": white,
            "images": [notfound],
            "notes": []
        }
        return item, [0, 0]

    def togglelayervisible(self):
        self.renderer.geolayers[self.layer] = not self.renderer.geolayers[self.layer]
        print(f"Toggeled layer {self.layer}")
        self.recaption()
        self.render_geo_full()
        self.rfa()

    def toggletileslayervisible(self):
        self.renderer.tilelayers[self.layer] = not self.renderer.tilelayers[self.layer]
        print(f"Toggeled Tiles layer {self.layer}")
        self.recaption()
        self.renderer.tiles_full_render(self.layer)
        self.rfa()

    def mouse2field(self):
        mpos = (pg.Vector2(pg.mouse.get_pos()) - self.field.rect.topleft) / self.size
        # mpos -= pg.Vector2(self.xoffset, self.yoffset)
        return mpos
    @property
    def posoffset(self):
        return self.pos - self.offset

    def mouse2field_sized(self):
        return self.mouse2field() * preview_cell_size

    @property
    def pos(self):
        mpos = self.mouse2field()
        mpos = pg.Vector2(
            math.floor(mpos.x),
            math.floor(mpos.y)
        )
        return mpos

    @property
    def pos2(self):
        return self.pos * self.size + self.field.rect.topleft

    def vec2rect(self, p1: pg.Vector2, p2: pg.Vector2):
        left = min(p1.x, p2.x)
        right = max(p1.x, p2.x)
        top = min(p1.y, p2.y)
        bottom = max(p1.y, p2.y)
        width = right - left
        height = bottom - top
        return pg.Rect(left, top, width, height)

    def field_to_draw_pos(self, pos, _offset = [0, 0]):
        return [((pos[0] + self.offset[0]) * self.size + self.field.rect.topleft[0] + _offset[0]), ((pos[1] + self.offset[1]) * self.size + self.field.rect.topleft[1] + _offset[1])]
    
    def get_tilehead_of_body(self, part):
        if part["tp"] in ["default", "material"]:
            return None
        if part["tp"] == "tileHead":
            return part
        
        headPos = [toarr(part["data"][0], "point"), part["data"][1] - 1]
        headTile = self.data["TE"]["tlMatrix"][int(headPos[0][0] - 1)][int(headPos[0][1] - 1)][headPos[1]]

        if headTile["tp"] == "tileHead":
            return headTile
        else:
            return "stray"

    def get_tilehead_pos_from_body(self, part):
        if part["tp"] != "tileBody":
            return None
        return [toarr(part["data"][0], "point"), part["data"][1] - 1]
    
    @property
    def persistent_data(self):
        if self.mname in self.data["persistent"]:
            return self.data["persistent"][self.mname]
        else:
            return None

    @property
    def xoffset(self):
        return int(self.offset.x)

    @property
    def yoffset(self):
        return int(self.offset.y)

    @property
    def onfield(self):
        return self.field.rect.collidepoint(pg.mouse.get_pos())
    
    @property
    def fieldScale(self):
        return self.size / preview_cell_size

    @property
    def custom_info(self):
        return f"Showed layers: {''.join([['H', 'S'][int(i)] for i in self.renderer.geolayers])}, " \
            f"Tiles: {''.join([['H', 'S'][int(i)] for i in self.renderer.tilelayers])}, " \
            f"current layer[{self.renderer.lastlayer+1}]: {'Showed' if self.renderer.hiddenlayer else 'Hidden'}"