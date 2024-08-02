import lingotojson as lj
import files

def get_instance():
    return ExternalAssetManager.instance()

class ExternalAssetManager:
    __instance = None

    def __init__(self) -> None:
        self.tiles = None
        self.props = None
        self.prop_colors = None
        self.effects = None

    def initialize(self):
        self.tiles = lj.inittolist()
        self.props = lj.getprops(self.tiles)
        self.prop_colors = lj.getcolors()
        self.effects = lj.solveeffects(files.e)

    def instance():
        if ExternalAssetManager.__instance is None:
            ExternalAssetManager.__instance = ExternalAssetManager()
        return ExternalAssetManager.__instance