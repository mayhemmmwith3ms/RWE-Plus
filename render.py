from files import *
import cv2
import numpy as np
from lingotojson import *
import pygame as pg
import time
import asset_manager as assets

LAYER_COLOR_EXTRA = [1, 2, 3, 11]

colors = ui_settings["global"]["colors"]  # NOQA

color = pg.Color(ui_settings["global"]["color"])
color2 = pg.Color(ui_settings["global"]["color2"])

dc = pg.Color(0, 0, 0, 0)

cursor = dc
cursor2 = dc
mirror = dc
bftiles = dc
border = dc
canplace = dc
cannotplace = dc
select = dc
layer1 = dc
layer2 = dc
mixcol_empty = dc
mixcol_fill = dc

camera_border = dc
camera_held = dc
camera_notheld = dc

slidebar = dc
rope = dc

grid = dc

for key, value in colors.items():
    exec(f"{key} = pg.Color({value})")

red = pg.Color([255, 0, 0])
darkred = pg.Color([100, 0, 0])
blue = pg.Color([50, 0, 255])
green = pg.Color([0, 255, 0])
black = pg.Color([0, 0, 0])
white = pg.Color([255, 255, 255])
gray = pg.Color([110, 110, 110])
darkgray = pg.Color([80, 80, 80])
darkergray = pg.Color([60, 60, 60])
purple = pg.Color([255, 0, 255])
yellow = pg.Color([255, 255, 0])
alpha = dc

col8 = [
    [-1, -1], [0, -1], [1, -1],
    [-1, 0], [1, 0],
    [-1, 1], [0, 1], [1, 1]
]

col4 = [[0, -1], [-1, 0], [1, 0], [0, 1]]

color = pg.Color(ui_settings["global"]["color"])
color2 = pg.Color(ui_settings["global"]["color2"])

renderedimage = pg.transform.scale(tooltiles, [
            (tooltiles.get_width() / graphics["tilesize"][0]) * preview_cell_size,
            (tooltiles.get_height() / graphics["tilesize"][1]) * preview_cell_size])

def lerp(val1:float, val2:float, amt:float):
    return val1 + float(val2 - val1) * amt

def color_mul(color:pg.Color, amt:float):
    return pg.Color(min(max(int(color.r * amt), 0), 255),\
                    min(max(int(color.g * amt), 0), 255),\
                    min(max(int(color.b * amt), 0), 255))

def gExtra_slice_from_type(type):
    return [graphics["shows2"][f"{type}"][0] * preview_cell_size, graphics["shows2"][f"{type}"][1] * preview_cell_size]

def gCell_slice_from_type(type):
    return [graphics["shows"][f"{type}"][0] * preview_cell_size, graphics["shows"][f"{type}"][1] * preview_cell_size]

def gTool_slice_from_typeandstate(type_and_state):
    c = []
    if str(type_and_state) in graphics["tileplaceicon"]:
        c = graphics["tileplaceicon"][str(type_and_state)]
    else:
        c = graphics["tileplaceicon"]["0"]
        
    return [c[0] * preview_cell_size, c[1] * preview_cell_size]

def draw_geo_list(surface, geotools, size, data, pos, color, alpha = 130, drawair = True):
    scaled_tool_image = pg.transform.scale(geotools,
                                    pg.Vector2(geotools.get_size()) / preview_cell_size * size).convert_alpha(surface)

    scaled_tool_image.set_alpha(alpha)
    scaled_tool_image.fill(pg.Color(254, 254, 254), special_flags=pg.BLEND_RGB_ADD)
    scaled_tool_image.fill(color, special_flags=pg.BLEND_RGBA_MULT)
    
    rect2 = [size]*2

    for x, xc in enumerate(data):
        for y, yc in enumerate(xc):
            if (not drawair) and yc[0] == 0:
                continue

            rect1 = [z * (size / preview_cell_size) for z in gCell_slice_from_type(yc[0])]
            surface.blit(scaled_tool_image, pos + [x * size, y * size], [rect1, rect2])

            for st in yc[1]:
                if st in LAYER_COLOR_EXTRA:
                    rect1 = [z * (size / preview_cell_size) for z in gExtra_slice_from_type(st)]
                    surface.blit(scaled_tool_image, pos + [x * size, y * size], [rect1, rect2]) 

    scaled_tool_image.fill(pg.Color(254, 254, 254), special_flags=pg.BLEND_RGB_ADD)
    scaled_tool_image.fill(white, special_flags=pg.BLEND_RGBA_MULT)

    for x, xc in enumerate(data):
        for y, yc in enumerate(xc):
            for st in yc[1]:
                if st not in LAYER_COLOR_EXTRA:
                    rect1 = [z * (size / preview_cell_size) for z in gExtra_slice_from_type(st)]
                    rect2 = [size]*2
                    surface.blit(scaled_tool_image, pos + [x * size, y * size], [rect1, rect2])

def quadsize(quad):
    mostleft = bignum
    mostright = 0
    mosttop = bignum
    mostbottom = 0
    for q in quad:
        x, y = q
        if x < mostleft:
            mostleft = x
        if x > mostright:
            mostright = x

        if y < mosttop:
            mosttop = y
        if y > mostbottom:
            mostbottom = y
    ww = round(mostright - mostleft)
    wh = round(mostbottom - mosttop)
    return ww, wh, [mostleft, mosttop, mostright, mostbottom]

def quadtransform(quads, image: pg.Surface):
    ww, wh, mosts = quadsize(quads)
    
    colkey = image.get_colorkey()
    image = image.convert_alpha()
    view = pg.surfarray.array3d(image)
    view = view.transpose([1, 0, 2])

    img = cv2.cvtColor(view, cv2.COLOR_RGB2RGBA) # NOQA
    ws, hs = img.shape[1::-1]
    pts1 = np.float32([[0, 0], [ws, 0],
        [ws, hs], [0, hs]])
    q2 = []
    for q in quads:
        q2.append([q[0] - mosts[0], q[1] - mosts[1]])

    pts2 = np.float32(q2)
    persp = cv2.getPerspectiveTransform(pts1, pts2) # NOQA
    result = cv2.warpPerspective(img, persp, (ww, wh)) # NOQA

    img = pg.image.frombuffer(result.tostring(), result.shape[1::-1], "RGBA")
    img.set_colorkey(colkey)

    return [img, mosts[0], mosts[1], ww, wh]


class Renderer:
    def __init__(self, data, render=True):
        self.data = data
        self.effect_index = 0

        self.lastlayer = 0
        self.offset = pg.Vector2(0, 0)
        self.size = preview_cell_size
        self.color_geo = False
        self.grid_surface: pg.surface = pg.Surface((preview_cell_size, preview_cell_size))

        if render:
            size = [len(data["GE"]) * preview_cell_size, len(data["GE"][0]) * preview_cell_size]
            self.surf_geo = pg.Surface(size)
            self.geolayers = [True, True, True]
            self.tilelayers = [True, True, True]
            self.geosurfaces = [
                renderedimage.convert_alpha(pg.Surface([preview_cell_size, preview_cell_size])),
                renderedimage.convert_alpha(pg.Surface([preview_cell_size, preview_cell_size])),
                renderedimage.convert_alpha(pg.Surface([preview_cell_size, preview_cell_size]))
            ]
            self.geosurfaces[0].fill(ui_settings["GE"]["layerColors"][0], special_flags=pg.BLEND_MULT)
            self.geosurfaces[1].fill(ui_settings["GE"]["layerColors"][1], special_flags=pg.BLEND_MULT)
            self.geosurfaces[2].fill(ui_settings["GE"]["layerColors"][2], special_flags=pg.BLEND_MULT)
            self.surf_tiles = pg.Surface(size)
            self.surf_tiles = self.surf_tiles.convert_alpha()
            self.surf_props = pg.Surface(size)
            self.surf_props = self.surf_props.convert_alpha()
            self.surf_effect = pg.Surface(size)
            self.surf_effect.set_alpha(190)

    def set_surface(self, size=None):
        if size is None:  # auto
            size = [self.levelwidth * preview_cell_size, self.levelheight * preview_cell_size]
        self.surf_geo = pg.Surface(size)
        self.geolayers = [True, True, True]
        self.tilelayers = [True, True, True]
        self.surf_tiles = pg.Surface(size)
        self.surf_tiles = self.surf_tiles.convert_alpha()
        self.surf_props = pg.Surface(size)
        self.surf_props = self.surf_props.convert_alpha()
        self.surf_effect = pg.Surface(size)
        self.surf_effect.set_alpha(190)

    def tiles_full_render(self, layer):
        self.surf_tiles.fill(dc)
        area = [[False for _ in range(self.levelheight)] for _ in range(self.levelwidth)]
        self.tiles_render_area(area, layer)

    def tiles_render_area(self, area, layer, allLayers = True):
        level_tile_images:dict = dict()
        for xp, x in enumerate(area):
            for yp, y in enumerate(x):
                if y:
                    continue
                for lr in self.data["TE"]["tlMatrix"][xp][yp]:
                    if lr["tp"] == "tileHead" and not level_tile_images.__contains__(lr["data"][1]):
                        level_tile_images[lr["data"][1]] = self.findtileimage(lr["data"][1])

        for xp, x in enumerate(area):
            for yp, y in enumerate(x):
                if y:
                    continue
                self.surf_tiles.fill(pg.Color(0, 0, 0, 0), [xp * preview_cell_size, yp * preview_cell_size, preview_cell_size, preview_cell_size])
        for drawLayer in range(2, -1, -1):
            for xp, x in enumerate(area):
                for yp, y in enumerate(x):
                    if y:
                        continue
                    if (not (drawLayer != layer)) or allLayers:
                        self.render_tile_pixel(xp, yp, layer, (drawLayer + layer) % 3, level_tile_images)

    def render_tile_pixel(self, xp, yp, selectedLayer, drawL, imgs):
        self.lastlayer = selectedLayer
        tiledata = self.data["TE"]["tlMatrix"]

        cell = tiledata[xp][yp][drawL]
        posx = xp * preview_cell_size
        posy = yp * preview_cell_size

        datcell = cell["tp"]
        datdata = cell["data"]

        layer_alpha = ui_settings["global"]["tiles_secondarylayeralpha"]

        alpha_index = (drawL - selectedLayer) % 3

        if alpha_index == 0:
            layer_alpha = ui_settings["global"]["tiles_primarylayeralpha"]
        if alpha_index == 1: 
            layer_alpha = ui_settings["global"]["tiles_secondarylayeralpha"]
        if alpha_index == 2:
            layer_alpha = ui_settings["global"]["tiles_thirdlayeralpha"]

        if not self.tilelayers[drawL]:
            return
        if datcell == "default":
            # self.surf_tiles.fill(pg.Color(0, 0, 0, 0), [posx, posy, image1size, image1size])
            # pg.draw.rect(field.field, red, [posx, posy, size, size], 3)
            return
        elif datcell == "material":
            if self.data["GE"][xp][yp][drawL][0] != 0:
                try:
                    #it = findtileimage(datdata)
                    ms = graphics["matsize"]
                    rect = pg.Rect(ms[0] + posx, ms[0] + posy, ms[1], ms[1])
                    col = [graphics["matposes"][datdata][0], graphics["matposes"][datdata][1], graphics["matposes"][datdata][2], 255]
                    if(drawL != selectedLayer):
                        for s in range(4):
                            col[s] = int(col[s] * layer_alpha // 255)
                    pg.draw.rect(self.surf_tiles, col, rect)
                    #if layer != l:
                    #    it["image"].set_alpha(settings["global"]["tiles_secondarylayeralpha"])
                    #else:
                    #    it["image"].set_alpha(settings["global"]["tiles_primarylayeralpha"])
                    #self.surf_tiles.blit(it["image"], [posx, posy])
                    #it["image"].set_alpha(255)
                except ValueError:
                    self.surf_tiles.blit(notfound, [posx, posy], special_flags=pg.BLEND_PREMULTIPLIED)

        elif datcell == "tileHead":
            it = imgs[datdata[1]]
            cposx = posx - int((it["size"][0] * .5) + .5) * preview_cell_size + preview_cell_size
            cposy = posy - int((it["size"][1] * .5) + .5) * preview_cell_size + preview_cell_size
            siz = pg.rect.Rect([cposx, cposy, it["size"][0] * preview_cell_size, it["size"][1] * preview_cell_size])
            if not ui_settings["TE"]["LEtiles"]:
                pg.draw.rect(self.surf_tiles, it["color"], siz, 0)
            it["image"].set_alpha(layer_alpha)
            self.surf_tiles.blit(it["image"], [cposx, cposy], special_flags=pg.BLEND_ALPHA_SDL2)
            it["image"].set_alpha(255)
        elif datcell == "tileBody":
            tl = self.data["TE"]["tlMatrix"][xp][yp][drawL]
            if self.get_tilehead_of_body(tl) == "stray":
                self.geosurfaces[2].set_alpha(layer_alpha)

                self.surf_tiles.blit(self.geosurfaces[2], [xp * preview_cell_size, yp * preview_cell_size], [gCell_slice_from_type(0), [preview_cell_size, preview_cell_size]], special_flags=pg.BLEND_PREMULTIPLIED)

                self.geosurfaces[2].set_alpha(255)
        # self.surf_tiles.fill(pg.Color(0, 0, 0, 0), [posx, posy, image1size, image1size])

    def findtileimage(self, name):
        it = None
        for i in assets.get_instance().tiles.keys():
            for i2 in assets.get_instance().tiles[i]:
                if i2["name"] == name:
                    img = i2.copy()
                    img["image"] = pg.transform.scale(img["image"], [img["image"].get_width() / 16 * preview_cell_size,
                                                                        img["image"].get_height() / 16 * preview_cell_size])
                    it = img
                    break
            if it is not None:
                break
        if it is None:
            it = notfoundtile
        return it

    def geo_full_render(self, layer):
        self.surf_geo.fill(color2)
        area = [[False for _ in range(self.levelheight)] for _ in range(self.levelwidth)]     
        self.geo_render_area(area, layer)

    def geo_render_area(self, area, layer):
        for xp, x in enumerate(area):
            for yp, y in enumerate(x):
                if y:
                    continue
                for i in col8:
                    try:
                        if not area[xp + i[0]][yp + i[1]]:
                            continue
                        self.surf_geo.blit(self.render_geo_pixel(xp + i[0], yp + i[1], layer), [(xp + i[0]) * preview_cell_size, (yp + i[1]) * preview_cell_size])
                    except IndexError:
                        continue
                self.surf_geo.blit(self.render_geo_pixel(xp, yp, layer), [xp * preview_cell_size, yp * preview_cell_size])

    def render_all(self, layer):
        self.lastlayer = layer
        self.geo_full_render(layer)
        self.tiles_full_render(layer)
        self.props_full_render(layer)
        if len(self.data["FE"]["effects"]):
            self.rendereffect(0)

    def render_geo_pixel(self, xp, yp, layer):
        self.lastlayer = layer

        def incorner(x, y):
            try:
                return self.data["GE"][x][y][i][1]
            except IndexError:
                return []

        def incornerblock(x, y):
            try:
                return self.data["GE"][x][y][i][0]
            except IndexError:
                return 0
        cellsize2 = [preview_cell_size, preview_cell_size]
        pixel = pg.Surface(cellsize2)
        pixel.fill(color)

        stackables = pg.Surface(cellsize2)
        stackables.set_colorkey([0, 0, 0, 0])
        #stackables.fill([0, 0, 0, 0])
        
        geoRange = range(2, -1, -1)
        if self.color_geo:
            geoRange = range(0, 3, 1)
        
        for i in geoRange:
            if not self.geolayers[i]:
                continue
            
            imageIndex = i
            if not self.color_geo:
                imageIndex = 0

            convrender = self.geosurfaces[imageIndex]
            convrender.set_alpha(50)

            if not self.color_geo:
                if i != layer:
                    if i == 0:
                        convrender.set_alpha(ui_settings["global"]["primarylayeralpha"])
                    if i == 1: 
                        convrender.set_alpha(ui_settings["global"]["secondarylayeralpha"])
                    if i == 2:
                        convrender.set_alpha(ui_settings["global"]["thirdlayeralpha"])
                else:
                    convrender.set_alpha(ui_settings["global"]["primarylayeralpha"] + 50)
            if i == 0 and self.color_geo:
                convrender.set_alpha(255)

            self.data["GE"][xp][yp][i][1] = list(set(self.data["GE"][xp][yp][i][1]))
            cell = self.data["GE"][xp][yp][i][0]

            over: list = self.data["GE"][xp][yp][i][1]
            if cell == 7 and 4 not in over:
                self.data["GE"][xp][yp][i][0] = 0
                cell = self.data["GE"][xp][yp][i][0]
            curtool = gCell_slice_from_type(cell)
            
            if(cell not in [0, 7] and not (cell == 1 and 11 in over)):
                pixel.blit(convrender, [0, 0], [curtool, cellsize2])

            if cell in [7]:
                pixel.blit(convrender, [0, 0], [gExtra_slice_from_type("SEMITR"), cellsize2])

            if 4 in over and self.data["GE"][xp][yp][i][0] != 7:
                self.data["GE"][xp][yp][i][1].remove(4)
            if 11 in over and over.index(11) != 0:
                over.remove(11)
                over.insert(0, 11)
            for addsindx, adds in enumerate(over):
                invalid = False
                try:
                    curtool = gExtra_slice_from_type(adds)
                except KeyError:
                    invalid = True
                    curtool = gExtra_slice_from_type("SEMITR")
                bufftiles = self.data["EX2"]["extraTiles"]
                bufftiles = pg.Rect(bufftiles[0], bufftiles[1],
                                    self.levelwidth - bufftiles[0] - bufftiles[2],
                                    self.levelheight - bufftiles[1] - bufftiles[3])
                if bufftiles.collidepoint(xp, yp):
                    if adds == 11:  # cracked terrain search
                        inputs = 0
                        pos = -1
                        for tile in col4:
                            curhover = incorner(xp + tile[0], yp + tile[1])
                            if 11 in curhover:
                                inputs += 1
                                if inputs == 1:
                                    match tile:
                                        case [0, 1]:  # N
                                            pos = graphics["crackv"]
                                        case [0, -1]:  # S
                                            pos = graphics["crackv"]
                                        case [-1, 0]:  # E
                                            pos = graphics["crackh"]
                                        case [1, 0]:  # W
                                            pos = graphics["crackh"]
                                elif inputs > 1:
                                    pos = -1
                        if inputs == 2:
                            pos = -1
                            if 11 in incorner(xp + 1, yp) and 11 in incorner(xp - 1, yp):
                                pos = graphics["crackh"]
                            elif 11 in incorner(xp, yp + 1) and 11 in incorner(xp, yp - 1):
                                pos = graphics["crackv"]
                        if pos != -1:
                            curtool = [pos[0] * preview_cell_size, pos[1] * preview_cell_size]
                    if adds == 4:  # shortcut entrance validation
                        # checklist
                        foundair = False
                        foundwire = False
                        tilecounter = 0
                        pathcount = 0
                        pos = -1
                        for tile in col8:
                            curtile = incornerblock(xp + tile[0], yp + tile[1])
                            curhover = incorner(xp + tile[0], yp + tile[1])
                            if curtile == 1:
                                tilecounter += 1
                            if curtile in [0, 6] and tile in col4:  # if we found air in 4 places near
                                foundair = True
                                if any(x in [5, 6, 7, 21, 19] for x in incorner(xp - tile[0], yp - tile[1])) :  # if opposite of air is wire
                                    foundwire = True
                                    match tile:
                                        case [0, 1]:  # N
                                            pos = graphics["shortcutentrancetexture"]["N"]
                                        case [0, -1]:  # S
                                            pos = graphics["shortcutentrancetexture"]["S"]
                                        case [-1, 0]:  # E
                                            pos = graphics["shortcutentrancetexture"]["E"]
                                        case [1, 0]:  # W
                                            pos = graphics["shortcutentrancetexture"]["W"]
                                else:
                                    break
                            if any(x in [5, 6, 7, 21, 19] for x in curhover) and tile in col4:  # if wire in 4 places near
                                pathcount += 1
                                if pathcount > 1:
                                    break
                        else:  # if no breaks
                            if tilecounter == 7 and foundwire and foundair and pos != -1:  # if we found the right one
                                curtool = [pos[0] * preview_cell_size, pos[1] * preview_cell_size]
                if adds in LAYER_COLOR_EXTRA:
                    if(adds == 11 and cell in [2, 3, 4, 5]):
                        pixel.blit(convrender, [0, 0], gExtra_slice_from_type("SEMITR"))
                    else:
                        pixel.blit(convrender, [0, 0], [curtool, cellsize2])
                else:
                    stackableSurf = renderedimage.convert_alpha(stackables)
                    if i != 0 or invalid:
                        stackableSurf.fill(red, special_flags=pg.BLEND_MULT)
                        
                    stackables.blit(stackableSurf, [0, 0], [curtool, cellsize2])
        pixel.blit(stackables, [0, 0])
        return pixel

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

    def props_full_render(self, selectedlayer):
        self.surf_props.fill(dc)
        for indx, prop in enumerate(self.data["PR"]["props"]):
            var = 0
            if prop[4]["settings"].get("variation") is not None:
                var = prop[4]["settings"]["variation"] - 1
            found, _ = self.findprop(prop[1])
            if found is None:
                print(f"Prop {prop[1]} not Found! image not loaded")
            try:
                image = found["images"][var] # .save(path2hash + str(id(self.data["PR"]["props"][indx][1])) + ".png")
            except IndexError:
                image = found["images"][0]
                if prop[4]["settings"].get("variation") is not None:
                    self.data["PR"]["props"][indx][4]["settings"]["variation"] = 1
            qd = prop[3]
            quads = []
            for q in qd:
                quads.append(toarr(q, "point"))

            # surf = pg.image.fromstring(string, [ws, hs], "RGBA")
            surf, mostleft, mosttop, ww, wh = quadtransform(quads, image)
            surf = pg.transform.scale(surf, [ww * sprite2image, wh * sprite2image])
            surf.set_colorkey(white)
            layer_depth = selectedlayer * 10
            dist_to_layer = abs(-self.data["PR"]["props"][indx][0] - layer_depth)
            dist_factor = (35 - dist_to_layer) / 35
            surf.set_alpha(190 * dist_factor)
            self.surf_props.blit(surf, [mostleft / spritesize * preview_cell_size, mosttop / spritesize * preview_cell_size])
            if prop[4].get("points") is not None:
                cgrey = [200, 200, 200, 255]
                propcolor = toarr(self.findprop(prop[1])[0]["previewColor"], "color")  # wires
                propcolor.append(255)
                for c in range(4):
                    cgrey[c] = int(cgrey[c] * dist_factor)
                    propcolor[c] = int(propcolor[c] * dist_factor)
                for pIndex, point in enumerate(prop[4]["points"]):
                    px, py = toarr(point, "point")
                    pxn, pyn = toarr(prop[4]["points"][min(pIndex + 1, len(prop[4]["points"]) - 1)], "point")
                    pg.draw.line(self.surf_props, cgrey, [px // preview_to_render_fac, py // preview_to_render_fac], [pxn // preview_to_render_fac, pyn // preview_to_render_fac])
                    pg.draw.circle(self.surf_props, propcolor, [px // preview_to_render_fac, py // preview_to_render_fac], 4)


    def rerendereffect(self):
        self.rendereffect(self.effect_index)

    def rendereffect(self, indx, mix=mixcol_empty):
        self.effect_index = indx
        for xp, x in enumerate(self.data["FE"]["effects"][indx]["mtrx"]):
            for yp, cell in enumerate(x):
                #surf = pg.surface.Surface([size, size])
                col = mix.lerp(mixcol_fill, cell / 100)
                #surf.set_alpha(col.a)
                #surf.fill(col)
                #self.surf_effect.blit(surf, [xp * size, yp * size])
                self.surf_effect.fill(col, [xp * preview_cell_size, yp * preview_cell_size, preview_cell_size, preview_cell_size])
                # pg.draw.rect(f, col, [xp * size, yp * size, size, size], 0)

    def rendereffectselective(self, indx, cells2refresh, mix=mixcol_empty):
        for coord in cells2refresh:
            cell = self.data["FE"]["effects"][indx]["mtrx"][coord[0]][coord[1]]
            col = mix.lerp(mixcol_fill, cell / 100)
            self.surf_effect.fill(col, [coord[0] * preview_cell_size, coord[1] * preview_cell_size, preview_cell_size, preview_cell_size])

    def rendergrid(self):
        w, h = [self.levelwidth * preview_cell_size, self.levelheight * preview_cell_size]
        self.grid_surface = pg.Surface([w, h]).convert_alpha()
        self.grid_surface.fill([0, 0, 0, 0])
        col = [255, 255, 255]
        col2 = [180, 180, 180]
        for x in range(0, w, preview_cell_size):
            if x % (preview_cell_size * 2) == 0:
                pg.draw.line(self.grid_surface, col, [x, 0], [x, h])
            else:
                pg.draw.line(self.grid_surface, col2, [x, 0], [x, h])
        for y in range(0, h, preview_cell_size):
            if y % (preview_cell_size * 2) == 0:
                pg.draw.line(self.grid_surface, col, [0, y], [w, y])
            else:
                pg.draw.line(self.grid_surface, col2, [0, y], [w, y])
        self.grid_surface.set_alpha(30)
    
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

    def start_perftimer(self):
        self.tic = time.perf_counter()

    def stop_perftimer(self):
        self.toc = time.perf_counter()
        print(f"Timer took {(self.toc - self.tic) * 1000:0.4} ms")

    @property
    def hiddenlayer(self):
        return self.geolayers[self.lastlayer]

    @property
    def levelwidth(self):
        return len(self.data["GE"])

    @property
    def levelheight(self):
        return len(self.data["GE"][0])