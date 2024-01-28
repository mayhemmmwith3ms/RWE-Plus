import subprocess
import traceback

from menus import *
from tkinter.messagebox import askyesno
import argparse
from path_dict import PathDict
from lingotojson import *
from files import ui_settings, path, application_path
import level_handler as lv
import datetime

widgets.keybol = True
run = True
keys = [pg.K_LCTRL, pg.K_LALT, pg.K_LSHIFT]
movekeys = [pg.K_LEFT, pg.K_UP, pg.K_DOWN, pg.K_RIGHT]
fullscreen = ui_settings["global"]["fullscreen"]
file = ""
file2 = ""
undobuffer = []
redobuffer = []
surf: Menu | MenuWithField = None
lv_manager:lv.LevelManager = None
loading = False

def undohistory():
    if not settings["enable_undo"]:
        return
    global undobuffer, redobuffer, file, surf
    if len(undobuffer) == 0:
        return
    print("Undo")
    lastsize = [surf.levelwidth, surf.levelheight]
    historyelem = undobuffer[-1]
    pathdict = PathDict(surf.data)
    for i in historyelem[1:]:
        pathdict[*historyelem[0], *i[0]] = i[1][1]
    surf.data = jsoncopy(pathdict.data)
    file = surf.data
    surf.renderer.data = surf.data
    surf.datalast = jsoncopy(pathdict.data)
    redobuffer.append(jsoncopy(undobuffer.pop()))
    if [surf.levelwidth, surf.levelheight] != lastsize:
        surf.renderer.set_surface([preview_cell_size * surf.levelwidth, preview_cell_size * surf.levelheight])
    surf.onundo()
    if MenuWithField in type(surf).__bases__:
        surf.renderer.render_all(surf.layer)
        surf.rfa()
        if hasattr(surf, "rebuttons"):
            surf.rebuttons()


def redohistory():
    if not settings["enable_undo"]:
        return
    global undobuffer, redobuffer, file, surf
    if len(redobuffer) == 0:
        return
    print("Redo")
    lastsize = [surf.levelwidth, surf.levelheight]
    historyelem = redobuffer[-1]
    pathdict = PathDict(surf.data)
    for i in historyelem[1:]:
        pathdict[*historyelem[0], *i[0]] = i[1][0]
    surf.data = jsoncopy(pathdict.data)
    file = surf.data
    surf.renderer.data = surf.data
    surf.datalast = jsoncopy(pathdict.data)
    undobuffer.append(jsoncopy(redobuffer.pop()))
    if [surf.levelwidth, surf.levelheight] != lastsize:
        surf.renderer.set_surface([preview_cell_size * surf.levelwidth, preview_cell_size * surf.levelheight])
    surf.onredo()
    if MenuWithField in type(surf).__bases__:
        surf.renderer.render_all(surf.layer)
        surf.rfa()
        if hasattr(surf, "rebuttons"):
            surf.rebuttons()

def preload():
    global lv_manager

    with open(application_path + "\\loadLog.txt", "w") as load_log:
        load_log.write("Start launch load!\n")

    with open(application_path + "\\crashLog.txt", "w") as crash_log:
        crash_log.write(f"[START LOG | {datetime.datetime.now().strftime('%H:%M:%S')}]\n")

    pg.display.set_icon(loadimage(path + "icon.png"))
    loadi = loadimage(f"{path}load.png")
    window = pg.display.set_mode(loadi.get_size(), flags=pg.NOFRAME)
    window.blit(loadi, [0, 0])
    pg.display.flip()
    pg.display.update()

    lv_manager = lv.LevelManager()

    lv_manager.init_renderer()

    del loadi


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="RWE+ console", description="Maybe a better, than official LE.")
    parser.version = tag
    parser.add_argument("filename", type=str, nargs="?", help="Level to load")
    parser.add_argument("-n", "--new", help="Opens new file", dest="new", action="store_true")
    parser.add_argument("-v", "--version", help="Shows current version and exits", action="version")
    parser.add_argument("--render", "-r", dest="renderfiles", metavar="file", nargs="*", type=str,
                        help="Renders levels with drizzle.")
    # parser.parse_args()
    args = parser.parse_args()
    if args.new:
        pass
        #launch(-1)
    if args.renderfiles is not None:
        s = f"\"{application_path}/drizzle/Drizzle.ConsoleApp{'' if islinux else '.exe'}\""
        subprocess.run([f"{application_path}/drizzle/Drizzle.ConsoleApp{'' if islinux else '.exe'}", "render", *args.renderfiles], shell=True)
        # os.system(s)
        if not islinux:
            os.system("start " + resolvepath(path2renderedlevels))
        exit(0)
    if args.filename is not None:
        try:
            pass
            #launch(args.filename)
        except (FileNotFoundError, TypeError):
            print("File not found!")
            raise
        except Exception:
            # extra save level in case of eny crashes
            print(traceback.print_exc())
            ex = askyesno("Crash!!!",
                        "Oops! RWE+ seems to be crashed, errorlog showed in console\nDo you want to save Level?")
            if ex:
                surf.savef()
            raise
    else:
        preload()
        lv_manager.start_LD()
