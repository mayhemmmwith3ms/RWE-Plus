import menuclass as menus
from menus import Menu, MenuWithField

import render
from render import Renderer

import lingotojson as lj

import files

import time
import traceback
import tkinter as tk
from tkinter.messagebox import showerror, askyesnocancel
import pygame as pg
import LD
import MN
import HK
import os
import sys
import ujson as json
import widgets
import menus as mns

modifier_keys = [pg.K_LCTRL, pg.K_LALT, pg.K_LSHIFT]

EXIT_COMMAND_SHELVE = 0
EXIT_COMMAND_SWITCH = 1

def keypress(menu):
    pressed = ""
    ctrl = pg.key.get_pressed()[pg.K_LCTRL]
    # shift = pg.key.get_pressed()[pg.K_LSHIFT]
    for i in files.hotkeys["global"].keys():
        key = i.replace("@", "").replace("+", "")
        if i == "unlock_keys":
            continue
        if int(i.find("+") != -1) - int(ctrl) == 0:
            if pg.key.get_pressed()[getattr(pg, key)]:
                pressed = files.hotkeys["global"][i]
    for i in files.hotkeys[menu.menu].keys():
        key = i.replace("@", "").replace("+", "")
        if i == "unlock_keys":
            continue
        if int(i.find("+") != -1) - int(ctrl) == 0:
            if pg.key.get_pressed()[getattr(pg, key)]:
                pressed = files.hotkeys[menu.menu][i]
                menu.send(pressed)
    if len(pressed) > 0 and pressed[0] == "/" and menu.menu != "LD":
        menu.message = pressed[1:]
    return pressed

def load_level(filepath) -> dict():
    if isinstance(filepath, str):
        lj.log_to_load_log(f"Start load of level \"{os.path.basename(filepath)}\"!")

    if isinstance(filepath, str) and (splitfilepath := os.path.splitext(filepath))[1] not in [".wep", ".txt"]:
        filepath = splitfilepath[0] + ".wep"
        if not os.path.exists(filepath):
            filepath = splitfilepath[0] + ".txt"

    files.add_to_recent(filepath)

    try:
        if filepath == -1:
            file = lj.turntoproject(open(files.path + "default.txt", "r").read())
            file["level"] = ""
            file["path"] = ""
            file["dir"] = ""
            file["persistent"] = lj.persistentdata
        elif filepath == "":
            return None
        elif filepath[-3:] == "txt":
            file = lj.turntoproject(open(filepath, "r").read())
            file["level"] = os.path.basename(filepath)
            file["path"] = filepath
            file["dir"] = os.path.abspath(filepath)
            file["persistent"] = lj.persistentdata
        else:
            file = json.load(open(filepath, "r"))
            file["level"] = os.path.basename(filepath)
            file["path"] = filepath
            file["dir"] = os.path.abspath(filepath)
            file["persistent"] = lj.persistentdata

        return file
    except Exception:
        lj.log_to_load_log(f"Failed to load level \"{os.path.basename(filepath)}\"! This may be caused by corrupted or invalid data!", error=True)
        raise

def asktoexit(file, file2):
    global run, surf
    if file2 != file:
        root = tk.Tk()
        root.wm_attributes("-topmost", 1)
        root.withdraw()
        ex = askyesnocancel("Exit from OGSCULEDITOR+", "Do you want to save changes?", parent=root)
        if ex:
            surf.savef()
            sys.exit(0)
        elif ex is None:
            return
        else:
            sys.exit(0)
    else:
        sys.exit(0)

class LevelManager:
    def __init__(self):
        self.renderer:Renderer = None
        self.levels:list = []
        self.active_level:LevelInstance = None
        self.menu:Menu | MenuWithField = None # only used for LD basically
        self.window = None
        self.switch_level = ""

    def init_renderer(self):
        load_tic = time.perf_counter()

        try:
            init_list = lj.inittolist()
            prop_colors = lj.getcolors()
            props = lj.getprops(init_list)

            self.renderer = Renderer(None, init_list, props, prop_colors, False)
        except Exception:
            with open(files.application_path + "\\crashLog.txt", "w") as crash_log:
                crash_log.write(f"[ERROR] Uncaught exception during level load\n{traceback.format_exc()}")

            lj.log_to_load_log(f"Uncaught exception during load\n{traceback.format_exc()}", error=True)

            root = tk.Tk()
            root.wm_attributes("-topmost", 1)
            root.withdraw()
            lj.showerror("OGSCULEDITOR+ Error", "An unhandled exception has occurred during loading\nCheck loadLog.txt for more info", parent=root)

        load_toc = time.perf_counter()   
        lj.log_to_load_log(f"Init loading completed in {(load_tic - load_toc) * 1000:0.6} ms with {lj.errorcount_get()} errors generated")

    def start_LD(self):    
        run = True
        width = 1280
        height = 720
        self.window = pg.display.set_mode([width, height], flags=pg.RESIZABLE)
        pg.display.set_icon(files.loadimage(files.path + "icon.png"))
        self.menu = LD.load(self.window, self.renderer)

        while run:
            pressedkey = ""
            for event in pg.event.get():
                match event.type:
                    case pg.DROPFILE:
                        self.focus_level(event.file)
                    case pg.QUIT:
                        asktoexit(None, None)
                    case pg.WINDOWRESIZED:
                        self.menu.resize()
                    case pg.KEYDOWN:
                        if event.key not in modifier_keys:
                            if widgets.keybol:
                                widgets.keybol = False
                                pressedkey = keypress(self.menu)
                    case pg.KEYUP:
                        if event.key not in modifier_keys:
                            if not widgets.keybol:
                                widgets.keybol = True
            match pressedkey.lower():
                case "quit":
                    asktoexit(None, None)
                case "reload":
                    self.menu.reload()
                case "new":
                    self.focus_level(-1)
                case "open":
                    file = self.menu.open_file_dialog()
                    if file is not None and os.path.exists(file):
                        self.focus_level(file)
            match self.menu.message:
                case "new":
                    self.focus_level(-1)
                case "open":
                    file = self.menu.open_file_dialog()
                    if file is not None and os.path.exists(file):
                        self.focus_level(file)
                case "recent":
                    file = None
                    print(self.menu.msgdata)
                    if self.menu.msgdata is not None:
                        file = self.menu.msgdata
                        
                    if file is not None and os.path.exists(file):
                        self.focus_level(file)
                    else:
                        print("Most recent file either does not exist or was moved/deleted. Open a level normally to create one.")
            self.menu.message = ""
            self.window.fill(pg.color.Color(files.ui_settings["global"]["color"]))
            self.menu.blit()
            self.menu.justChangedZoom = False
            pg.display.flip()
            pg.display.update()

            if self.active_level:
                s = True
                while s:
                    try:
                        self.run_level()
                    except Exception:
                        self.levels.remove(self.active_level)
                        self.switch_level = ""

                    self.shelve_level()

                    if self.switch_level:
                        self.focus_level(self.switch_level)

                    if not self.active_level:
                        s = False

    def get_level(self, filepath):
        # only add a new instance if a level is not already loaded from that filepath
        if not [x for x in self.levels if x.filepath == filepath][:1]:
            newlv = LevelInstance(self, filepath)
            self.levels.append(newlv)
            return newlv
        return [x for x in self.levels if x.filepath == filepath][0]

    def focus_level(self, filepath):
        if self.active_level and not self.active_level.data["dir"]:
            self.levels.remove(self.active_level)
            del(self.active_level)
        self.active_level = self.get_level(filepath)

    def run_level(self):
        run = True
        while run:
            if not self.active_level:
                run = False
            run = self.active_level.update()

    def shelve_level(self):
        if not self.active_level.data["dir"]:
            self.levels.remove(self.active_level)
        self.active_level = None

    def queue_switch_level(self, filepath):
        self.switch_level = filepath

class LevelInstance:
    def __init__(self, parent:LevelManager, filepath:str):
        self.parent:LevelManager = parent
        self.renderer:Renderer = self.parent.renderer
        self.data:dict = {}
        self.old_data:dict = {}
        self.filepath = filepath
        self.menu:Menu | MenuWithField = parent.menu
        self.window = parent.window

        self.load_into_this(filepath)
    
    def load_into_this(self, filepath):    
        try:
            self.data = load_level(filepath)

            self.old_data = files.jsoncopy(self.data)

            width = files.ui_settings["global"]["width"]
            height = files.ui_settings["global"]["height"]

            self.window = pg.display.set_mode([width, height], flags=pg.RESIZABLE | (pg.FULLSCREEN * 0))
            pg.display.set_icon(files.loadimage(files.path + "icon.png"))

            self.renderer = Renderer(self.data, self.renderer.tiles, self.renderer.props, self.renderer.propcolors, True)

            self.menu = MN.MN(self.window, self.renderer)

            os.system("cls")
            if isinstance(filepath, str):
                lj.log_to_load_log(f"Successfully loaded level \"{os.path.basename(filepath)}\"!")
        except Exception:
            with open(files.application_path + "\\crashLog.txt", "w") as crash_log:
                crash_log.write(f"[ERROR] Uncaught exception during level load\n{traceback.format_exc()}")
            lj.log_to_load_log(f"Uncaught exception during load\n{traceback.format_exc()}", error=True)

            root = tk.Tk()
            root.wm_attributes("-topmost", 1)
            root.withdraw()
            showerror("OGSCULEDITOR+ Error", "An unhandled exception has occurred during loading\nCheck loadLog.txt for more info", parent=root)
            raise

    def update(self) -> bool:
        #print(len(self.parent.levels))
        width = files.ui_settings["global"]["width"]
        height = files.ui_settings["global"]["height"]
        pressedkey = ""
        for event in pg.event.get():
            match event.type:
                case pg.DROPFILE:
                    self.parent.queue_switch_level(event.file)
                    return False
                case pg.QUIT:
                    asktoexit(None, None)
                case pg.WINDOWRESIZED:
                    self.menu.resize()
                case pg.KEYDOWN:
                    if event.key not in modifier_keys:
                        if widgets.keybol:
                            widgets.keybol = False
                            pressedkey = keypress(self.menu)
                case pg.KEYUP:
                    if event.key not in modifier_keys:
                        if not widgets.keybol:
                            widgets.keybol = True
                case pg.MOUSEBUTTONDOWN:
                    if event.button == 4:
                        self.menu.send("SU")
                    elif event.button == 5:
                        self.menu.send("SD")
        match pressedkey.lower():
            case "undo":
                pass
            case "redo":
                pass
            case "quit":  
                    asktoexit(self.data, self.old_data)
            case "reload":
                self.menu.reload()
            case "save":
                self.menu.savef()
                self.old_data = files.jsoncopy(self.data)
            case "new":
                print("New")
                self.menu.savef()
                return False
            case "open":
                file = self.menu.open_file_dialog()
                if file is not None and os.path.exists(file):
                    self.parent.queue_switch_level(file)
                    return False
            case "nextl":
                print("asasda")
                for i, j in enumerate(self.parent.levels):
                    if j.filepath == self.filepath:
                        k = i + 1
                        if k >= len(self.parent.levels):
                            k = 0
                        print(k)
                        self.parent.queue_switch_level(self.parent.levels[k].filepath)
                        return False
        if self.menu.message:
            print(self.menu.message)
            match self.menu.message:
                case "undo":
                    pass
                case "redo":
                    pass
                case "%":
                    self.menu = HK(self.window, self.renderer, self.menu.menu)
                case "quit":
                    asktoexit(self.data, self.old_data)
                case "fc":
                    self.window = pg.display.set_mode([width, height], flags=pg.RESIZABLE | (pg.FULLSCREEN * 0))
                    # pg.display.toggle_fullscreen()
                    self.menu.resize()
                case "save":
                    self.menu.savef()
                    self.old_data = files.jsoncopy(self.data)
                case "saveas":
                    self.menu.saveasf()
                    self.old_data = files.jsoncopy(self.data)
                case _:
                    if self.menu.message in mns.menulist:
                        self.menu.on_switch_editor()
                        self.menu = getattr(sys.modules["__main__"], self.menu.message)(self.window, self.renderer)
                    else:
                        self.menu.send(self.menu.message)
            self.menu.message = ""
        #Undo goes here
        if not pg.key.get_pressed()[pg.K_LCTRL]:
            for i in self.menu.uc:
                if pg.key.get_pressed()[i]:
                    keypress(self.window)
        if files.ui_settings[self.menu.menu].get("menucolor") is not None:
            self.window.fill(pg.color.Color(files.ui_settings[self.menu.menu]["menucolor"]))
        else:
            self.window.fill(pg.color.Color(files.ui_settings["global"]["color"]))
        self.menu.blit()
        pg.display.flip()
        pg.display.update()
        return True