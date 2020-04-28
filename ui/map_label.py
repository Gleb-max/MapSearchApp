from map_tools.api import ApiInteraction
from PyQt5.QtWidgets import QSizePolicy, QLabel
from PyQt5.QtCore import QByteArray, Qt, QPointF
from PyQt5.QtGui import QPixmap, QMouseEvent, QMovie


class MapLabel(QLabel):
    MIN_SCALE = 0
    MAX_SCALE = 17
    GIF_BACKGROUND = "img/default.gif"

    def __init__(self):
        super().__init__()
        self.first_result = True
        self.map_url = None
        self.toponym = None
        self.scale = 5
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
        # print(f"Found new toponym: {new_toponym}")
        if new_toponym is None:
            self.result_code = 404
            return
        self.result_code = 200
        self.toponym = new_toponym
        self.object_label = True
        self.map_center = self.toponym.getCoordinates()
        # print("Map address was update")

    def setMapType(self, type_id):
        # print(f"Set new map type ({self.map_types[type_id]})")
        if type_id in self.map_types:
            self.map_type = type_id

    def scaleUp(self):
        if self.scale == self.MAX_SCALE:
            return
        self.scale += 1
        # print("Scale was up")

    def scaleDown(self):
        if self.scale == self.MIN_SCALE:
            return
        self.scale -= 1
        # print("Scale was down")

    def hideLabel(self):
        self.object_label = False
        # print("Label reset")

    def updateView(self):
        if self.toponym is None:
            # print("no address")
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
        # print("View was updated")

    def getCurrentAddress(self):
        if self.toponym:
            return self.toponym.getAddress()
        return None

    def getCurrentPostalCode(self):
        if self.toponym:
            return self.toponym.getPostalCode()
        return None

    def getStatusCode(self):
        return self.result_code

    def mapMove(self, direction):
        if not self.toponym:
            return
        lat, long = self.map_center
        if direction == "up":
            long += self.toponym.getDeltaLatitude()
            # print("Move up")
        elif direction == "down":
            long -= self.toponym.getDeltaLatitude()
            # print("Move down")
        elif direction == "right":
            lat += self.toponym.getDeltaLongitude()
            # print("Move right")
        elif direction == "left":
            lat -= self.toponym.getDeltaLongitude()
            # print("Move left")
        if long < -180:
            long = -180
        elif long > 180:
            long = 180
        if lat < -180:
            lat = -180
        elif lat > 180:
            lat = 180
        self.map_center = lat, long

    def mousePressEvent(self, event: QMouseEvent):
        if not self.toponym:
            return
        pos = event.localPos()
        x, y = pos.x(), pos.y()
        print(x, y)
        if event.button() == Qt.LeftButton:
            print("search address")
        elif event.button() == Qt.RightButton:
            print("search organisation")
