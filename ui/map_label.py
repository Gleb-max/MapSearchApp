from PyQt5.QtTest import QTest
from map_tools.api import ApiInteraction
from PyQt5.QtCore import QByteArray, pyqtSignal
from PyQt5.QtWidgets import QSizePolicy, QLabel
from PyQt5.QtGui import QPixmap, QMouseEvent, QMovie


class MapLabel(QLabel):
    MIN_SCALE = 1
    MAX_SCALE = 17
    GIF_BACKGROUND = "img/default.gif"
    clicked = pyqtSignal([QMouseEvent])

    def __init__(self):
        super().__init__()
        self.first_result = True
        self.map_url = None
        self.toponym = None
        self.scale = self.MAX_SCALE
        self.map_type = 0
        self.object_label = True
        self.map_center = None
        self.result_code = 0
        self.api_interaction = ApiInteraction()
        self.map_types = {
            0: "map",
            1: "sat",
            2: "sat,skl",
        }
        self.methods = {
            "mapMove": self.mapMove,
            "scaleUp": self.scaleUp,
            "scaleDown": self.scaleDown,
            "hideLabel": self.hideLabel,
            "setAddress": self.setAddress,
            "setMapType": self.setMapType,
        }
        self.initUI()

    def initUI(self):
        movie = QMovie(self.GIF_BACKGROUND, QByteArray(), self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        movie.setCacheMode(QMovie.CacheAll)
        movie.setSpeed(100)
        self.setMovie(movie)
        movie.start()

    def execute(self, method_name, **params):
        method = self.methods.get(method_name, None)
        if not method:
            return False
        method.__call__(**params)
        self.updateView()

    def setAddress(self, address):
        new_toponym = self.api_interaction.get_geocode(address)
        if new_toponym is None:
            self.result_code = 404
            return
        self.result_code = 200
        self.toponym = new_toponym
        self.scale = self.MAX_SCALE
        self.object_label = True
        self.map_center = self.toponym.getCoordinates()
        self.point = self.toponym.getCoordinates()

    def setMapType(self, type_id):
        if type_id in self.map_types:
            self.map_type = type_id

    def scaleUp(self):
        if self.scale == self.MAX_SCALE:
            return
        self.scale += 1

    def scaleDown(self):
        if self.scale == self.MIN_SCALE:
            return
        self.scale -= 1

    def hideLabel(self):
        self.object_label = False

    def updateView(self):
        if self.toponym is None:
            return
        args = [
            ",".join(map(str, self.map_center)),
            self.map_types[self.map_type],
            self.scale,
        ]
        if self.object_label:
            args.append(self.toponym.getCoordinates())
        new_map = self.api_interaction.get_image(*args)
        if new_map is None:
            self.result_code = 401
            return
        pixmap = QPixmap()
        pixmap.loadFromData(new_map)
        if self.first_result:
            self.first_result = False
            self.clear()
        self.setPixmap(pixmap)
        QTest.qWait(10)

    def getCurrentAddress(self):
        if self.toponym:
            return self.toponym.getName()
        return None

    def getCurrentPostalCode(self):
        if self.toponym:
            return self.toponym.getPostalCode()
        return None

    def getStatusCode(self):
        return self.result_code

    def mapMove(self, direction):
        if not self.toponym or self.scale == 1:
            return
        long, lat = self.map_center
        delta_lat = self.toponym.getDeltaLatitude() * 2 ** (self.MAX_SCALE - self.scale) * 0.8
        delta_long = self.toponym.getDeltaLongitude() * 2 ** (self.MAX_SCALE - self.scale) * 0.8
        if direction == "up":
            lat += delta_lat
        elif direction == "down":
            lat -= delta_lat
        elif direction == "right":
            long += delta_long
        elif direction == "left":
            long -= delta_long
        start = self.toponym.getCoordinates()
        if (self.map_center[0] < start[0] < long) or (self.map_center[0] > start[0] > long):
            long = start[0]
        elif long < -180:
            long = -180 + (delta_long % 180) / 2
        elif long > 180:
            long = 180 - (delta_long % 180) / 2
        if (self.map_center[1] < start[1] < lat) or (self.map_center[1] > start[1] > lat):
            lat = start[1]
        elif lat < -90:
            lat = -90 + (delta_lat % 90) / 2
        elif lat > 90:
            lat = 90 - (delta_lat % 90) / 2
        self.map_center = round(long, 6), round(lat, 6)

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit(event)
