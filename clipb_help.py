class FieldGridCopyData:
    def __init__(self, geodata:list = None, tiledata:list = None):
        self.data:dict = {"GE":geodata,"TE":tiledata}

    def __str__(self):
        return str(self.to_list())

    def to_list(self):
        out = [[], []]
        out[0] = self.data["GE"]
        out[1] = self.data["TE"]

        return out

    def from_clipboard_string(str):
        indata = None
        try:
            indata = eval(str)
            if not isinstance(indata, list):
                return None
        except Exception:
            return None

        return FieldGridCopyData(indata[0], indata[1])

    @property
    def modes(self): #whether the GE and TE data (respectively) contain 3 layers or 1 layer
        return [self.data["GE"] is not None and len(self.data["GE"]) == 3,\
                self.data["TE"] is not None and len(self.data["TE"]) == 3]