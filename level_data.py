import numpy as math
import lingotojson as lj

TILE_PRIO_NONE = 0  # overwrite nothing
TILE_PRIO_REPLACEMATS = 1  # overwrite materials
TILE_PRIO_FORCEPLACE = 2  # overwrite all

def can_replace(tpo, tpn, force=False):
    match tpo:
        case "default":
            return True
        case "material":
            return force or (tpn in ["tileHead", "tileBody"])
        case "tileBody":
            return force and (tpn in ["tileHead", "tileBody"])
        case "tileHead":
            return False

def check_lingo_void(val):
    return (val is None) or (val == 0) or (val == "void")

class LoadedLevelData:
    def __init__(self, data: dict) -> None:
        self.data: dict = data

    def set_geo_cell(self, x, y, ly, type):
        self.data["GE"][x][y][ly][0] = type

    def add_geo_extra(self, x, y, ly, type):
        self.data["GE"][x][y][ly][1].append(type)

    def del_geo_extra(self, x, y, ly, type):
        if type in self.data["GE"][x][y][ly][1]:
            self.data["GE"][x][y][ly][1].remove(type)

    def set_tile_cell(self, x, y, ly, cell):
        self.data["TE"][x][y][ly] = cell

    def get_tile_cell(self, x, y, ly):
        return self.data["TE"][x][y][ly]

    def place_tile(self, x, y, ly, tile, placespecs=False, priority=0) -> bool:
        if not self.in_bounds(x, y, ly):
            return None
        
        w, h = tile["size"]

        bx = x - math.ceil(w / 2) - 1
        by = y - math.ceil(h / 2) - 1

        specs = tile["cols"][0]
        specs2 = tile["cols"][1]

        render_request = [(int, int)]

        for xi in range(bx, bx + w):
            for yi in range(by, by + h):

                xp = int(bx + xi)
                yp = int(by + yi)

                if not self.in_bounds(xp, yp, ly):
                    continue

                catindices = lj.makearr([self.tileimage["cat"][0], self.tileimage["cat"][1]], "point")  
                cellspec = specs[xi, * h + yi]

                cell = None

                if cellspec == -1:
                    pass
                elif "material" in tile["tags"]:
                    cell = {"tp": "material", "data": tile["name"]}
                elif xp == x and yp == y:
                    cell = {"tp": "tileHead", "data": [catindices, tile["name"]]}
                else:
                    headpos = lj.makearr([xp + 1, xp + 1], "point")
                    cell = {"tp": "tileBody", "data": [headpos, ly + 1]}

                oldcell = self.get_tile_cell(xp, yp, ly)

                if not ((priority != TILE_PRIO_NONE and can_replace(oldcell["tp"], cell["tp"], force=(priority==TILE_PRIO_FORCEPLACE)))\
                        or oldcell["tp"] == "default"):
                    continue
                
                if cell is not None:
                    render_request.append((x, y))
                    self.set_tile_cell(xp, yp, ly, cell)

                    if placespecs:
                        self.set_geo_cell(cellspec)
        
        return render_request

    def in_bounds(self, x, y, ly):
        return (0 <= x < len(self.data["GE"]) and 0 <= y < len(self.data["GE"][0]) and 0 <= ly < 3)


