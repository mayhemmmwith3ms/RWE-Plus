from menuclass import *
import requests

class load(Menu):
    def __init__(self, surface: pg.surface.Surface, renderer):
        self.recentbuttons = []
        super().__init__(surface, renderer, "LD")
        self.setup_recent_list()
        self.resize()

        try:
            request = requests.get("https://api.github.com/repos/mayhemmmwith3ms/RWE-Plus/releases", timeout=2)
            if request.status_code == 200:
                gittag = request.json()[0]["tag_name"].split("-")[0]
                if tag != gittag:
                    print("A new version of RWE+ is available!")
                    print(f"Current Version: {tag}, latest: {gittag}")
                    print("https://github.com/mayhemmmwith3ms/RWE-Plus/releases/latest")

                    self.labels[0].set_text(f"A new version is available ({gittag}, you are currently using {tag})")
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            print("Cannot find new RWE+ versions")

    def send(self, message):
        self.message = message

    def blit(self):
        super().blit(30)
        for btn in self.recentbuttons:
            btn.blitshadow()
        for btn in self.recentbuttons:
            btn.blit(sum(pg.display.get_window_size()) // 120)
        #pg.draw.circle(self.surface, red, [0,0], 64, 1)
        #print(self.recentbuttons.__len__())

    def resize(self):
        super().resize()
        for i in self.recentbuttons:
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
        
        if not os.path.exists(path + "recent.txt"):
            f = open(path + "recent.txt", "x")
            f.close()

        with open(path + "recent.txt") as recent_level:
            for index, i in enumerate(recent_level.readlines()):
                i = i.replace("\n", "")
                btnrect = btnrect.move(0, btnrect.h + 1)
                btn:widgets.button = widgets.button(self.surface, btnrect, gray, i, onpress=self.pressrecent)
                self.recentbuttons.append(btn)

    def pressrecent(self, text):
        self.message = "recent"
        self.msgdata = text

    @property
    def custom_info(self):
        return "Have fun!"
