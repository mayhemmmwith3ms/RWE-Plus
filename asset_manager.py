import lingotojson as lj

class ExternalAssetManager:
    __instance = None

    def __init__(self) -> None:
        self.tiles = None
        self.props = None
        self.prop_colors = None

    def initialize(self):
        init_list = lj.inittolist()
        prop_colors = lj.getcolors()
        props = lj.getprops(init_list)

        self.tiles = init_list
        self.props = props
        self.prop_colors = prop_colors

    @property
    def instance():
        if ExternalAssetManager.__instance is None:
            ExternalAssetManager.__instance = ExternalAssetManager()
        return ExternalAssetManager.__instance