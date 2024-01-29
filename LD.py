from menuclass import *
import level_handler as lv
import widgets2 as w2

class load(Menu):
    def __init__(self, surface: pg.surface.Surface, renderer):
        self.recentbuttons = []
        self.instancebuttons = []
        self.ll = -1
        super().__init__(surface, renderer, "LD")
        self.setup_recent_list()
        self.setup_instance_list()
        self.resize()

    def send(self, message):
        self.message = message

    def blit(self):
        super().blit(30)
        for btn in self.recentbuttons:
            btn.blitshadow()
        for btn in self.recentbuttons:
            btn.blit(sum(pg.display.get_window_size()) // 160)

        for btn in self.instancebuttons:
            btn.update()
        
        if not self.ll == len(lv.LevelManager.instance.levels):
            self.instancebuttons = []
            self.setup_instance_list()
            self.resize()

        self.ll = len(lv.LevelManager.instance.levels)
        #pg.draw.circle(self.surface, red, [0,0], 64, 1)
        #print(self.recentbuttons.__len__())

    def resize(self):
        super().resize()
        for i in self.recentbuttons:
            i.resize()
        for i in self.instancebuttons:
            i.resize()

    def open(self):
        self.message = "open"

    def new(self):
        self.message = "new"

    def report(self):
        report()

    def github(self):
        github()

    def setup_recent_list(self):
        btnrect = pg.rect.Rect(self.menu_ui_settings["recentpos"])
        title:widgets.button = widgets.button(self.surface, btnrect, gray, "Recent Projects")
        self.recentbuttons.append(title)
        
        with open(path + "recent.txt") as recent_level:
            for index, i in enumerate(recent_level.readlines()):
                i = i.replace("\n", "")
                btnrect = btnrect.move(0, btnrect.h + 1)
                btn:widgets.button = widgets.button(self.surface, btnrect, gray, i, onpress=self.pressrecent)
                self.recentbuttons.append(btn)

    def setup_instance_list(self):
        man = lv.LevelManager.instance

        btnrect = pg.rect.Rect(self.menu_ui_settings["instancespos"])
        #title:widgets.button = widgets.button(self.surface, btnrect, gray, "Levels")
        #self.recentbuttons.append(title)

        for i, j in enumerate(man.levels):
            btnrect2 = btnrect.move((btnrect.width + 1)* (i % 3), (btnrect.height + 1) * (i // 3))
            btn = w2.LevelInstanceSelectButton(btnrect2, self.surface, darkgray, j, self.killinstance)
            btn.make_preview()
            self.instancebuttons.append(btn)

    def pressrecent(self, text):
        self.message = "recent"
        self.msgdata = text

    def pressinstance(self, text):
        lv.LevelManager.instance.focus_level(text)

    def killinstance(self, x):
        self.instancebuttons.remove(x)
        self.setup_instance_list()

    @property
    def custom_info(self):
        return "Have fun!"
