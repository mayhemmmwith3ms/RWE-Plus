import subprocess
import traceback

import requests
from menus import *
from tkinter.messagebox import askyesnocancel, askyesno
from tkinter.filedialog import askopenfilename, asksaveasfilename
import argparse
from path_dict import PathDict
from lingotojson import *
from files import uiSettings, hotkeys, path, application_path

widgets.keybol = True
run = True
keys = [pg.K_LCTRL, pg.K_LALT, pg.K_LSHIFT]
movekeys = [pg.K_LEFT, pg.K_UP, pg.K_DOWN, pg.K_RIGHT]
fullscreen = uiSettings["global"]["fullscreen"]
file = ""
file2 = ""
undobuffer = []
redobuffer = []
surf: Menu | MenuWithField = None


def openlevel(level, window):
    global run, file, file2, redobuffer, undobuffer, surf
    surf.savef()
    file = level
    if file is not None and os.path.exists(file):
        launchload(file)
        undobuffer = []
        redobuffer = []
        surf.renderer.data = file
        surf.data = file
        surf.renderer.set_surface()
        surf.renderer.render_all(0)
        surf = MN(window, surf.renderer)
        os.system("cls")
    print("Open")


def keypress(window):
    global run, file, file2, redobuffer, undobuffer, surf
    pressed = ""
    ctrl = pg.key.get_pressed()[pg.K_LCTRL]
    # shift = pg.key.get_pressed()[pg.K_LSHIFT]
    for i in hotkeys["global"].keys():
        key = i.replace("@", "").replace("+", "")
        if i == "unlock_keys":
            continue
        if int(i.find("+") != -1) - int(ctrl) == 0:
            if pg.key.get_pressed()[getattr(pg, key)]:
                pressed = hotkeys["global"][i]
    for i in hotkeys[surf.menu].keys():
        key = i.replace("@", "").replace("+", "")
        if i == "unlock_keys":
            continue
        if int(i.find("+") != -1) - int(ctrl) == 0:
            if pg.key.get_pressed()[getattr(pg, key)]:
                pressed = hotkeys[surf.menu][i]
                surf.send(pressed)
    if len(pressed) > 0 and pressed[0] == "/" and surf.menu != "LD":
        surf.message = pressed[1:]
    match pressed.lower():
        case "undo":
            undohistory()
        case "redo":
            redohistory()
        case "quit":
            asktoexit(file, file2)
        case "reload":
            surf.reload()
        case "save":
            surf.savef()
            file2 = jsoncopy(file)
        case "new":
            print("New")
            surf.savef()
            run = False
        case "open":
            if not settings["native_file_browser"]:
                openlevel(surf.asksaveasfilename(defaultextension=[".txt", ".wep"]), window)
            else:
                openlevel(askopenfilename(defaultextension=[".txt", ".wep"], initialdir=os.path.dirname(os.path.abspath(__file__)) + "\LevelEditorProjects"), window)


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
        surf.renderer.set_surface([previewCellSize * surf.levelwidth, previewCellSize * surf.levelheight])
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
        surf.renderer.set_surface([previewCellSize * surf.levelwidth, previewCellSize * surf.levelheight])
    surf.onredo()
    if MenuWithField in type(surf).__bases__:
        surf.renderer.render_all(surf.layer)
        surf.rfa()
        if hasattr(surf, "rebuttons"):
            surf.rebuttons()


def asktoexit(file, file2):
    global run, surf
    if file2 != file:
        ex = askyesnocancel("Exit from RWE+", "Do you want to save Changes?")
        if ex:
            surf.savef()
            sys.exit(0)
        elif ex is None:
            return
        else:
            sys.exit(0)
    else:
        sys.exit(0)


def launchload(level):
    global surf, fullscreen, undobuffer, redobuffer, file, file2, run

    if level is str and (splitfilepath := os.path.splitext(level))[1] not in [".wep", ".txt"]:
        level = splitfilepath[0] + ".wep"
        if not os.path.exists(level):
            level = splitfilepath[0] + ".txt"

    recent = open(path + "recent.txt", "w")
    recent.write(str(level))
    recent.close()
    if level == -1:
        file = turntoproject(open(path + "default.txt", "r").read())
        file["level"] = ""
        file["path"] = ""
        file["dir"] = ""
    elif level == "":
        return
    elif level[-3:] == "txt":
        file = turntoproject(open(level, "r").read())
        file["level"] = os.path.basename(level)
        file["path"] = level
        file["dir"] = os.path.abspath(level)
    else:
        file = json.load(open(level, "r"))
        file["level"] = os.path.basename(level)
        file["path"] = level
        file["dir"] = os.path.abspath(level)
    undobuffer = []
    redobuffer = []


def doevents(window):
    for event in pg.event.get():
        match event.type:
            case pg.DROPFILE:
                openlevel(event.file, window)
            case pg.QUIT:
                asktoexit(file, file2)
            case pg.WINDOWRESIZED:
                surf.resize()
            case pg.KEYDOWN:
                if event.key not in keys:
                    if widgets.keybol:
                        widgets.keybol = False
                        keypress(window)
            case pg.KEYUP:
                if event.key not in keys:
                    if not widgets.keybol:
                        widgets.keybol = True
            case pg.MOUSEBUTTONDOWN:
                if event.button == 4:
                    surf.send("SU")
                elif event.button == 5:
                    surf.send("SD")


def launch(level):
    global surf, fullscreen, undobuffer, redobuffer, file, file2, run

    # loading image
    loadi = loadimage(f"{path}load.png")
    window = pg.display.set_mode(loadi.get_size(), flags=pg.NOFRAME)
    window.blit(loadi, [0, 0])
    pg.display.flip()
    pg.display.update()

    launchload(level)
    items = inittolist()
    propcolors = getcolors()
    props = getprops(items)
    file2 = jsoncopy(file)
    width = uiSettings["global"]["width"]
    height = uiSettings["global"]["height"]

    window = pg.display.set_mode([width, height], flags=pg.RESIZABLE | (pg.FULLSCREEN * fullscreen))
    pg.display.set_icon(loadimage(path + "icon.png"))
    renderer = Renderer(file, items, props, propcolors)
    renderer.render_all(0)
    surf = MN(window, renderer)
    os.system("cls")
    del loadi
    try:
        request = requests.get("https://api.github.com/repos/methylredd/RWE-Plus/releases/latest", timeout=2)
        if request.status_code == 200:
            gittag = request.json()["tag_name"]
            if tag != gittag:
                print("A new version of RWE+ is available!")
                print(f"Current Version: {tag}, latest: {gittag}")
                print("https://github.com/methylredd/RWE-Plus/releases/latest")
    except requests.exceptions.ConnectionError:
        print("Cannot find new RWE+ versions")
    except requests.exceptions.ReadTimeout:
        print("Cannot find new RWE+ versions")
    run = True
    while run:
        doevents(window)
        if surf.message != "":
            match surf.message:
                case "undo":
                    undohistory()
                case "redo":
                    redohistory()
                case "%":
                    surf = HK(window, renderer, surf.menu)
                case "quit":
                    asktoexit(file, file2)
                case "fc":
                    fullscreen = not fullscreen
                    window = pg.display.set_mode([width, height], flags=pg.RESIZABLE | (pg.FULLSCREEN * fullscreen))
                    # pg.display.toggle_fullscreen()
                    surf.resize()
                case "save":
                    surf.savef()
                    file2 = jsoncopy(file)
                case "saveas":
                    surf.saveasf()
                    file2 = jsoncopy(file)
                case "savetxt":
                    surf.savef_txt()
                    file2 = jsoncopy(file)
                case _:
                    if surf.message in menulist:
                        surf = getattr(sys.modules[__name__], surf.message)(window, renderer)
                    else:
                        surf.send(surf.message)
            surf.message = ""
        if len(surf.historybuffer) > 0:
            surf.historybuffer.reverse()
            undobuffer.extend(surf.historybuffer)
            surf.historybuffer = []
            redobuffer = []
            undobuffer = undobuffer[-settings["undo_history_limit"]:]

        if not pg.key.get_pressed()[pg.K_LCTRL]:
            for i in surf.uc:
                if pg.key.get_pressed()[i]:
                    keypress(window)
        if uiSettings[surf.menu].get("menucolor") is not None:
            window.fill(pg.color.Color(uiSettings[surf.menu]["menucolor"]))
        else:
            window.fill(pg.color.Color(uiSettings["global"]["color"]))
        surf.blit()
        pg.display.flip()
        pg.display.update()


def loadmenu():
    global surf
    run = True
    width = 1280
    height = 720
    window = pg.display.set_mode([width, height], flags=pg.RESIZABLE)
    renderer = Renderer({"path": ""}, None, None, None, False)
    surf = load(window, renderer)
    pg.display.set_icon(loadimage(path + "icon.png"))
    while run:
        for event in pg.event.get():
            match event.type:
                case pg.DROPFILE:
                    if event.file is not None and os.path.exists(event.file):
                        launch(event.file)
                    surf = load(window, renderer)
        doevents(window)
        match surf.message:
            case "new":
                launch(-1)
            case "open":
                if not settings["native_file_browser"]:
                    file = surf.asksaveasfilename(defaultextension=[".txt", ".wep"])
                else:
                    file = askopenfilename(defaultextension=[".txt", ".wep"], initialdir=os.path.dirname(os.path.abspath(__file__)) + "\LevelEditorProjects")
                if file is not None and os.path.exists(file):
                    launch(file)
                    surf = load(window, renderer)
            case "tutorial":
                file = turntoproject(open(path2tutorial + "tutorial.txt", "r").read())
                file["path"] = "tutorial"
                renderer = Renderer(file, None, None, None, True)
                surf = TT(window, renderer)
            case "load":
                renderer = Renderer({"path": ""}, None, None, None, False)
                surf = load(window, renderer)
            case "recent":
                file = None

                if(os.path.exists(path + "recent.txt")):
                    file = open(path + "recent.txt").read()
                    
                if file is not None and os.path.exists(file):
                    launch(file)
                    surf = load(window, renderer)
                else:
                    print("Most recent file either does not exist or was moved/deleted. Open a level normally to create one.")

        surf.message = ""
        if not pg.key.get_pressed()[pg.K_LCTRL]:
            for i in surf.uc:
                if pg.key.get_pressed()[i]:
                    keypress(window)
        window.fill(pg.color.Color(uiSettings["global"]["color"]))
        surf.blit()
        surf.justChangedZoom = False
        pg.display.flip()
        pg.display.update()
    pg.quit()
    exit(0)


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
        launch(-1)
    if args.renderfiles is not None:
        s = f"\"{application_path}/drizzle/Drizzle.ConsoleApp{'' if islinux else '.exe'}\""
        subprocess.run([f"{application_path}/drizzle/Drizzle.ConsoleApp{'' if islinux else '.exe'}", "render", *args.renderfiles], shell=True)
        # os.system(s)
        if not islinux:
            os.system("start " + resolvepath(path2renderedlevels))
        exit(0)
    if args.filename is not None:
        try:
            launch(args.filename)
        except (FileNotFoundError, TypeError):
            print("File not found!")
            raise
        except Exception as e:
            # extra save level in case of eny crashes
            print(traceback.print_exc())
            ex = askyesno("Crash!!!",
                          "Oops! RWE+ seems to be crashed, errorlog showed in console\nDo you want to save Level?")
            if ex:
                surf.savef()
            raise
    else:
        loadmenu()
