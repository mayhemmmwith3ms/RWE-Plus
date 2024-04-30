import re
import subprocess
from files import *
import math
import datetime

notfound = loadimage(path + "notfound.png")
notfound.set_colorkey(pg.Color(255, 255, 255))
notfoundtile = {
    "name": "unloaded tile",
    "tp": "notfound",
    "repeatL": [1],
    "bfTiles": 0,
    "image": notfound,
    "size": [2, 2],
    "category": "material",
    "color": pg.Color(255, 255, 255),
    "cols": [[-1], 0],
    "cat": [1, 1],
    "tags": [""]
}
persistentdata = {
    "GE": {},
    "TE": {},
    "LE": {},
    "FE": {},
    "PE": {}
}
defaultlevel = open(path + "default.txt", "r").readlines()
load_error_count = 0

def clean_lingo_struct(string:str, mark:str): # this is unused (for now)
    s = [m.start() for m in re.finditer(mark, string)]
    print(s)
    for i in s:
        start = i + len(mark)
        for c in range(start, len(string)):
            if string[c] == " ":
                string.replace(string[c], "")
            if string[c] == "(":
                break
    string.replace(f"{mark}(", f"\"{mark}(")
    return string
    ...

def tojson(string:str, replacement:str = None):
    try:
        closebracketscount = string.count("]")
        openbracketscount = string.count("[")
        t = string
        if closebracketscount > openbracketscount:
            t = t[:-1]
        t = t.replace("#Data:", "#data:")\
            .replace("#Options:", "#options:")\
            .replace("[#", "{#")\
            .replace("point(", "\"point(")\
            .replace("rect(", "\"rect(")\
            .replace("color(", "\"color(")\
            .replace(")\"", ")")\
            .replace(")", ")\"")\
            .replace("void", "\"void\"")
        count = 0
        m = list(t)
        brcount = 0
        for i in m:
            if i == "{":
                localcount = 0
                v = count
                while v < len(m):
                    if m[v] == "[" or m[v] == "{":
                        localcount += 1
                    elif m[v] == "]" or m[v] == "}":
                        localcount -= 1
                        if localcount == 0:
                            m[v] = "}"
                            break
                    v += 1
            count += 1
            if i in ["{", "["]:
                brcount += 1
            elif i in ["}", "]"]:
                brcount -= 1
                if brcount == 0:
                    m = m[:count+1]
                    break
        t = "".join(m)
        t = t.replace("#", "\"").replace(":", "\":").replace("1\":st", "1':st").replace("2\":nd", "2':nd").replace("3\":rd", "3':rd")
        # print(t)
        if t.replace(" ", "") != "":
            if replacement is not None:
                return {**tojson(replacement), **json.loads(t)}
            return json.loads(t)
        else:
            if replacement is not None:
                return tojson(replacement)
            return {}
    except Exception:
        if replacement is None:
            raise
        log_to_load_log(f"Missing or bad data in editor \"{replacement[2:4]}\"! Inserting default data!")
        return tojson(replacement)


def turntoproject(string: str):
    proj = {}
    lines = string.split("\n")
    print("Loading level...")
    proj["GE"] = eval(lines[0])  # geometry
    proj["TE"] = tojson(lines[1])  # tile editor and his settings
    proj["FE"] = tojson(lines[2])  # effect editor params
    
    for effect in proj["FE"]["effects"]:
        for xp, x in enumerate(effect['mtrx']):
            for yp, y in enumerate(x):
                effect["mtrx"][xp][yp] = float(y)

    proj["LE"] = tojson(lines[3], defaultlevel[3])  # light editor and presets
    proj["EX"] = tojson(lines[4], defaultlevel[4])  # map settings
    proj["EX2"] = tojson(lines[5], defaultlevel[5])  # light and level settings
    proj["CM"] = tojson(lines[6], defaultlevel[6])  # camera settigs
    proj["WL"] = tojson(lines[7], defaultlevel[7])  # water level
    proj["PR"] = tojson(lines[8], defaultlevel[8])  # props and settingsw
    proj["persistent"] = persistentdata
    return proj


def tolingo(string: dict):
    s = json.dumps(string)
    t = s.replace("\"point(", "point(").replace("\"rect(", "rect(").replace("\"color(", "color(")\
        .replace(")\"", ")").replace("{", "[").replace("}", "]").replace("'", "")
    t = re.sub(r"\"([a-zA-Z]+[0-9]*)\":", r"#\1:", t)
    #print(t)
    return t


def toarr(col: str, mark):
    s = col.replace(mark + "(", "")
    s = s.replace(",", " ")
    s = s.replace(")", "")
    a = []
    for i in s.split():
        n = float(i)
        if float(i) == int(float(i)):
            n = int(float(i))
        a.append(n)
    return a


def makearr(col: list | pg.Vector2, mark):
    return f"{mark}({col[0]}, {col[1]})"


def init_solve(files: list[str,]):
    a = {}
    for file in files:
        s = open(file, "r").readlines()
        a2 = []
        cat = ''
        counter = 0
        counter2 = 2
        findcategory = True #if true, all non-category lines will be ignored until a category line is found
        for ln, i in enumerate(s):
            i = i.replace("\n", "")
            if len(i) > 1:
                if i[0] == "-":
                    if i[1] == "-": #lines starting with -- are comments
                        continue
                    try:
                        counter2 += 1
                        a[cat] = a2
                        js = tojson(i[1:])
                        a2 = [js]
                        cat = js[0]
                        counter = 0
                        findcategory = False
                    except json.JSONDecodeError:
                        log_to_load_log(f"Failed to convert init CATEGORY line \"{i}\" (line number: {ln}) in file \"{os.path.relpath(file, application_path)}\"! Skipping line and all subsequent items!", True)
                        findcategory = True
                        continue
                elif not findcategory:
                    try:
                        js = tojson(i)
                        item = {}
                        for p, val in js.items():
                            item[p] = val
                        a2.append(item)
                        counter += 1
                    except json.JSONDecodeError:
                        log_to_load_log(f"Failed to convert init ITEM line \"{i}\" (line number: {ln}) in file \"{os.path.relpath(file, application_path)}\"! Skipping line!", True)
                        continue
        a[cat] = a2
    return a


def inittolist():
    inv = ui_settings["TE"]["LEtiles"]
    tilefiles = [path2graphics + i for i in graphics["tileinits"]]
    solved = init_solve(tilefiles)
    solved = dict(i for i in solved.items() if len(i[1]) > 1) #remove categories with no tiles (prevents crash when loading TE)
    #log_to_load_log(solved)
    #del solved['']
    print(solved)
    solved_copy = solved.copy()
    for catnum, catitem in enumerate(solved.items()):
        cat, items = catitem
        colr = pg.Color(toarr(items[0][1], "color"))
        solved_copy[cat] = []
        for indx, item in enumerate(items[1:]):
            try:
                img = loadimage(f"{path2graphics}{item['nm']}.png")
            except (FileNotFoundError, TypeError):
                log_to_load_log(f"Failed to load graphics for item \"{item['nm']}\"! Skipping!", True)
                continue
            sz = toarr(item["sz"], "point")
            try:
                ln = len(item["repeatL"])
            except KeyError:
                ln = 1
                if(item["tp"] not in ("voxelStructRockType", "box")):
                    log_to_load_log(f"Failed to get repeatL for item \"{item['nm']}\"! This may cause issues when rendering!", True)
                # sz:point(x,y) + ( #bfTiles * 2 )) * 20
            try:
                tp = item["tp"]
            except KeyError:
                tp = ""
                log_to_load_log(f"Failed to get type for item \"{item['nm']}\"! This may cause issues when rendering!", True)
            if tp == "box":  # math
                ln = 4
                size = (ln * sz[1] + (item["bfTiles"] * 2)) * render_cell_size
                rect = pg.rect.Rect([0, size, sz[0] * spritesize, sz[1] * spritesize])
            elif ((ln * sz[1] + (item["bfTiles"] * 2 * ln)) * render_cell_size + 1) > img.get_height():
                rect = pg.rect.Rect([0, img.get_height() - sz[1] * spritesize, sz[0] * spritesize, sz[1] * spritesize])
            else:
                size = (sz[1] + (item["bfTiles"] * 2)) * ln * render_cell_size
                rect = pg.rect.Rect([0, size + 1, sz[0] * spritesize, sz[1] * spritesize])

            try:
                img = img.subsurface(rect)
            except ValueError:
                try:
                    rect = pg.rect.Rect([0, img.get_height() - sz[1] * spritesize, sz[0] * spritesize, sz[1] * spritesize])
                    img = img.subsurface(rect)
                except ValueError:
                    rect = pg.rect.Rect([0, 0, 1, 1])
                    img = img.subsurface(rect)
                    log_to_load_log(f"Failed to separate preview image for item \"{item['nm']}\"! This may cause issues when rendering!", True)
            # srf = img.copy()
            # srf.fill(colr)
            # img.set_colorkey(pg.Color(0, 0, 0))
            # srf.blit(img, [0, 0])
            # img.fill(colr)
            if not inv:
                img.set_colorkey(pg.color.Color(255, 255, 255))
            if inv:
                s = pg.Surface(img.get_size())
                s.blit(img, [0, 0])
                arr = pg.pixelarray.PixelArray(s.copy())
                arr.replace(pg.Color(0, 0, 0), colr, 0.5)
                img = arr.make_surface()
                img.set_colorkey(pg.Color(255, 255, 255))

            newitem = {
                "name": item["nm"],
                "tp": item.get("tp"),
                "repeatL": item["repeatL"] if item.get("repeatL") is not None else [1],
                "bfTiles": item["bfTiles"],
                "image": img,
                "size": sz,
                "category": cat,
                "color": colr,
                "cols": [item["specs"], item["specs2"]],
                "cat": [catnum + 1, indx + 1],
                "tags": item["tags"]
            }
            solved_copy[cat].append(newitem)
        if len(solved_copy[cat]) == 0:
            log_to_load_log("Category \"" + cat + "\" was empty and will not be loaded!")
            solved_copy.pop(cat)
        else:
            log_to_load_log("Successfully loaded tile category \"" + cat + "\" with items:\n[")
            log_to_load_log(''.join([f"{it['name']}\n" for it in solved_copy[cat]]), nl=False)
            log_to_load_log("]")
    matcat = "materials 0"
    matcatcount = 0
    mat_dict = dict()
    mat_dict[matcat] = []
    counter = 1
    for k, v in graphics["matposes"].items():
        col = pg.Color(v)
        img = pg.Surface([preview_cell_size, preview_cell_size], pg.SRCALPHA)
        img.fill(pg.Color(0, 0, 0, 0))
        ms = graphics["matsize"]
        pg.draw.rect(img, v, pg.Rect(ms[0], ms[0], ms[1], ms[1]))
        try:
            preview = loadimage(path2materialPreviews + k + ".png")
        except (FileNotFoundError, TypeError):
            preview = pg.Surface([preview_cell_size, preview_cell_size])
            preview.set_alpha(0)
        preview.set_colorkey(pg.Color(255, 255, 255))
        mat_dict[matcat].append(
            {
                "name": k,
                "tp": None,
                "repeatL": [1],
                "bfTiles": 0,
                "image": img,
                "size": [1, 1],
                "category": matcat,
                "color": col,
                "cols": [[-1], 0],
                "cat": [1, counter],
                "tags": ["material"],
                "preview": preview
            })
        if len(mat_dict[matcat]) > 30:
            matcatcount += 1
            matcat = f"materials {matcatcount}"
            mat_dict[matcat] = []
        counter += 1
    mat_dict.update(solved_copy)
    solved_copy = mat_dict
    return solved_copy


def renderlevel(data):
    fl = os.path.splitext(data["path"])[0] + ".txt"
    file = open(fl, "w")
    turntolingo(data, file)
    #print(f"\"{application_path}/drizzle/Drizzle.ConsoleApp{'' if islinux else '.exe'}")
    #os.system(f"{application_path}\\drizzle\\Drizzle.ConsoleApp.exe render {fl}")
    if not islinux:
        subprocess.Popen([f"{application_path}/drizzle/Drizzle.ConsoleApp{'' if islinux else '.exe'}", "render", fl], shell=True)
    else:
        subprocess.Popen(f"\"{application_path}/drizzle/Drizzle.ConsoleApp\" render \"{fl}\"", shell=True)
    if settings["native_file_browser"]:
        os.system("start " + resolvepath(path2renderedlevels))


def getcolors():
    solved = open(resolvepath(application_path + '/drizzle/Data/Props/propColors.txt'), 'r').readlines()
    cols = []
    for line in solved:
        if line[0] != '[':
            continue
        ln = tojson(line)
        ln[1] = toarr(ln[1], "color")
        cols.append(ln)
    return cols


def getprops(tiles: dict):
    # turning tiles to props and then add them to all other props
    propfiles = [path2props + i for i in graphics["propinits"]]
    propfiles.append(path + "additionprops.txt")
    solved = init_solve(propfiles)
    del solved['']
    solved_copy = solved.copy()
    for catnum, catitem in enumerate(solved.items()):
        cat, items = catitem
        colr = pg.Color(toarr(items[0][1], "color"))
        solved_copy[cat] = []
        for indx, item in enumerate(items[1:]):
            try:
                img = loadimage(path2props + item["nm"] + ".png")
            except (FileNotFoundError, TypeError):
                log_to_load_log(f"Failed to load graphics for item \"{item['nm']}\"! Skipping!", True)
                continue
            img.set_colorkey(pg.color.Color(255, 255, 255))
            img = img.convert(pg.Surface([preview_cell_size, preview_cell_size]))
            images = []
            if item.get("vars") is not None:
                item["vars"] = max(item["vars"], 1)

            try:
                ws, hs = img.get_size()
                if item.get("pxlSize") is not None:
                    w, h = toarr(item["pxlSize"], "point")
                else:
                    w, h = ws, hs
                    if item.get("vars") is not None:
                        w = round(ws / item["vars"])
                    if item.get("repeatL") is not None:
                        h = math.floor((hs / len(item["repeatL"])))
                        if item.get("sz") is not None:
                            sz = toarr(item["sz"], "point")
                            w = min(sz[0] * render_cell_size, ws)
                            h = min(sz[1] * render_cell_size, hs // len(item["repeatL"]))

                        bpix = img.get_at([0, 0]).r == 0
                        img = img.subsurface([0, 1 if bpix else 0, min(w * (item["vars"] if item.get("vars") is not None else 1), ws), min(h * len(item["repeatL"]), hs - (1 if bpix else 0))]) # this would be so much cleaner if random props weren't missing the black pixel
                        ws, hs = img.get_size()

                        cons = 0.4
                        wh = pg.Color("#ffffff")
                        gr = pg.Color("#dddddd")
                        bl = pg.Color("#000000")

                        vars = 1
                        if item.get("vars") is not None:
                            vars = item["vars"]

                        for varindx in range(vars):
                            curcol = gr

                            for iindex in range(len(item["repeatL"])):
                                # print(img, item["nm"], varindx * w, hs - h, w, h)
                                if item["repeatL"][len(item["repeatL"]) - 1 - iindex] == 0:
                                    continue

                                curcol = curcol.lerp(bl, cons) 
                                h2 = min(hs, (len(item["repeatL"]) - 1 - iindex) * h + h) - (len(item["repeatL"]) - 1 - iindex) * h # curse you MSC prop makers
                                ss = img.subsurface(varindx * w, (len(item["repeatL"]) - 1 - iindex) * h, w, h2).copy()
                                if item["colorTreatment"] == "standard":
                                    ss = ss.convert(pg.Surface([preview_cell_size, preview_cell_size]))
                                    depthTintWhite = min((len(item["repeatL"]) - 1 - iindex) * min(25, 255 // len(item["repeatL"])), 254)
                                    ss.fill(pg.Color(depthTintWhite, depthTintWhite, depthTintWhite), special_flags=pg.BLEND_RGB_ADD)
                                if item["colorTreatment"] == "bevel":
                                    pxl = pg.PixelArray(ss)
                                    pxl.replace(bl, curcol)
                                    ss = pxl.make_surface()
                                ss.set_colorkey(wh)
                                img.blit(ss, [w * varindx, hs - h])

                hz = hs - h if item["tp"] not in ["soft", "variedSoft"] else 0

                if item.get("vars") is not None:
                    for iindex in range(item["vars"]):
                        images.append(img.subsurface(iindex * w, hz, w, h))
                else:
                    images.append(img.subsurface(0, hz, w, h))

                newitem = solved[cat][indx + 1]
                newitem["images"] = images
                newitem["color"] = list(colr)
                solved_copy[cat].append(newitem)
            except Exception:
                log_to_load_log(f"Failed to load \"{item['nm']}\" for due to unhandled exception! Skipping!", True)

        if not solved_copy[cat]:
            log_to_load_log("Category \"" + cat + "\" was empty and will not be loaded!")
            solved_copy.pop(cat)
        else:
            log_to_load_log("Successfully loaded prop category \"" + cat + "\" with items:\n[")
            log_to_load_log(''.join([f"{it['nm']}\n" for it in solved_copy[cat]]), nl=False)
            log_to_load_log("]")
    # solved_copy["material"] = []
    # for cat in tiles:
    #     pass
    for cat, items in tiles.items():
        print(items[0]["category"])
        if not items:
            log_to_load_log(f"Category \"{cat}\" was found empty while trying to load tiles into props!", True)
            continue
        #else:
        #    log_to_load_log(f"{cat}: {[j['name'] for _, j in enumerate(items)]}")
        title = ""
        itemlist = []
        if "material" in items[0]["tags"]:
            continue
        title = f"{items[0]['category']} + as prop"
        for indx, tile in enumerate(items[0:]):
            if tile["tp"] == "voxelStruct" and "notProp" not in tile["tags"]:
                # returnimage = pg.Surface(pg.Vector2(tile["image"].get_width(), tile["image"].get_height()) + pg.Vector2(spritesize, spritesize) * tile["bfTiles"] * 2)
                # returnimage.fill(pg.Color(255, 255, 255))
                # returnimage.blit(tile["image"], pg.Vector2(spritesize, spritesize) * tile["bfTiles"])
                # returnimage.set_colorkey(pg.Color(255, 255, 255))
                size = (pg.Vector2(tile["size"]) + pg.Vector2(tile["bfTiles"], tile["bfTiles"]) * 2) * render_cell_size
                returnimage = pg.Surface(size)
                returnimage.fill(pg.Color(255, 255, 255))
                try:
                    img = loadimage(path2graphics + tile["name"] + ".png")
                except Exception:
                    img = pg.transform.scale(notfound, size)
                    returnimage.blit(pg.transform.scale(notfound, size), [0, 0])
                    print(f"{tile['name']} is not Loaded properly")
                img.set_colorkey(pg.Color(255, 255, 255))
                truewidth = size.x
                if truewidth > img.get_width():
                    truewidth = img.get_width()
                for layer in range(len(tile["repeatL"]) - 1, -1, -1):
                    rect = pg.Rect(0, layer * size.y + 1, truewidth, size.y)
                    try:
                        currentLayerSurface = img.subsurface(rect)
                        currentLayerSurface = currentLayerSurface.convert(pg.Surface([preview_cell_size, preview_cell_size]))
                        depthTintWhite = min(layer * min(30, 255 // len(tile["repeatL"])), 254)
                        currentLayerSurface.fill(pg.Color(depthTintWhite, depthTintWhite, depthTintWhite), special_flags=pg.BLEND_RGB_ADD)
                        returnimage.blit(currentLayerSurface, [0, 0])
                    except ValueError:
                        if layer < 3:
                            errorimg = pg.transform.scale(notfound, size)
                            errorimg.set_colorkey(pg.Color(255, 255, 255))
                            returnimage.blit(errorimg, [0, 0])
                            log_to_load_log(f"Failed to slice graphics of tile as prop \"{item['nm']}\"! This may be caused by a size mismatch between a tile's init and its image!", True)
                #returnimage = pg.transform.scale(returnimage, pg.Vector2(returnimage.get_size()) / renderedCellSize * spritesize)
                returnimage.set_colorkey(pg.Color(255, 255, 255))
                returnimage = returnimage.convert_alpha(pg.Surface([preview_cell_size, preview_cell_size]))
                pxl = pg.PixelArray(returnimage)
                pxl.replace(wh, pg.Color(0,0,0,0))
                returnimage = pxl.make_surface()
                itemlist.append({
                    "nm": tile["name"],
                    "tp": "standard",
                    "images": [returnimage],
                    "colorTreatment": "standard",
                    "color": ui_settings["PE"]["elements_as_tiles_color"],
                    "sz": list(pg.Vector2(tile["size"]) + pg.Vector2(tile["bfTiles"] * 2, tile["bfTiles"] * 2)),
                    "depth": 10 + int(tile["cols"][1] != []),
                    "repeatL": tile["repeatL"],
                    "tags": ["tile"],
                    "layerExceptions": [],
                    "notes": ["Tile as prop"]
                })
        if itemlist:
            solved_copy[title] = itemlist
    return solved_copy


def turntolingo(string: dict, file):
    with file as fl:
        fl.write(str(string["GE"]) + "\r")
        fl.write(tolingo(string["TE"]) + "\r")
        fl.write(tolingo(string["FE"]) + "\r")
        fl.write(tolingo(string["LE"]) + "\r")
        fl.write(tolingo(string["EX"]) + "\r")
        fl.write(tolingo(string["EX2"]) + "\r")
        fl.write(tolingo(string["CM"]) + "\r")
        fl.write(tolingo(string["WL"]) + "\r")
        fl.write(tolingo(string["PR"]) + "\r")

def log_to_load_log(message, error=False, nl=True):
    global load_error_count
    with open(application_path + "\\loadLog.txt", "a") as load_log:
        load_log.write(f"{'[ERROR]: ' if error else ''}{message}")
        if nl:
            load_log.write("\n")
    print(message)
    if error:
        load_error_count += 1

def log_to_crash_log(message):
    with open(application_path + "\\crashLog.txt", "a") as crash_log:
        crash_log.write(f"[ERROR | {datetime.datetime.now().strftime('%H:%M:%S')}]: {message}\n")

def errorcount_get():
    return load_error_count