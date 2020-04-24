import sys
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import QByteArray, Qt
from map_tools.api import ApiInteraction
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QCheckBox,
    QGroupBox,
    QLineEdit,
    QWidget,
    QLabel,
)


SCREEN_SIZE = [700, 700]


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


class MapSearcher(QMainWindow):
    def __init__(self):
        self.currentAddress = None
        self.currentPostalCode = None
        super().__init__()
        self.initUI()

    def initUI(self):
        # window settings
        self.setFixedSize(*SCREEN_SIZE)
        self.setWindowTitle("Map Search")

        # main layout
        vertical_layout = QVBoxLayout()

        # main widget
        centralWidget = QWidget(self)
        centralWidget.setLayout(vertical_layout)
        self.setCentralWidget(centralWidget)

        # editing line (search)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("What do you want to find?")
        self.search_input.returnPressed.connect(self.newSearchRequest)

        # button for start search
        search_button = QPushButton()
        search_button.setText("Search")
        search_button.clicked.connect(self.newSearchRequest)

        # layout for search widgets
        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(self.search_input)
        horizontal_layout.addWidget(search_button)

        # map
        self.mapLabel = MapLabel()

        # buttons for change map type
        button_map = QPushButton()
        button_map.setText("Map")

        button_sputnik = QPushButton()
        button_sputnik.setText("Sputnik")

        button_hybrid = QPushButton()
        button_hybrid.setText("Hybrid")

        # button group
        self.map_buttons = QButtonGroup()
        self.map_buttons.addButton(button_map, 0)
        self.map_buttons.addButton(button_sputnik, 1)
        self.map_buttons.addButton(button_hybrid, 2)
        self.map_buttons.buttonPressed[int].connect(self.changeType)

        # layout for map buttons
        map_group_layout = QHBoxLayout()
        map_group_layout.addWidget(button_map)
        map_group_layout.addWidget(button_sputnik)
        map_group_layout.addWidget(button_hybrid)

        # widget group for buttons (changing map type)
        map_type_group = QGroupBox()
        map_type_group.setLayout(map_group_layout)
        map_type_group.setTitle("Map Type")

        # address display options
        self.current_address = QLineEdit()
        self.current_address.setReadOnly(True)
        self.current_address.setPlaceholderText("Current Address")

        self.postalCode_show = QCheckBox()
        self.postalCode_show.setText("Show postalCode")
        self.postalCode_show.clicked[bool].connect(self.showPostalCode)

        # address options widgets layout
        address_group_layout = QHBoxLayout()
        address_group_layout.addWidget(self.current_address)
        address_group_layout.addWidget(self.postalCode_show)

        # widget group for address options
        address_options_group = QGroupBox()
        address_options_group.setLayout(address_group_layout)
        address_options_group.setTitle("Address Details")

        # reset search result button
        reset_search_result_button = QPushButton()
        reset_search_result_button.setText("Reset Search Result")
        reset_search_result_button.setStyleSheet("background-color: #ef2929")
        reset_search_result_button.clicked.connect(self.resetSearchResult)

        # adding all layouts and widgets to main layout
        vertical_layout.addLayout(horizontal_layout)
        vertical_layout.addWidget(self.mapLabel, alignment=Qt.AlignCenter)
        vertical_layout.addWidget(map_type_group, alignment=Qt.AlignBaseline)
        vertical_layout.addWidget(address_options_group, alignment=Qt.AlignBaseline)
        vertical_layout.addWidget(reset_search_result_button, alignment=Qt.AlignCenter)

        # show window
        self.show()
        self.changeType(0)

    def newSearchRequest(self):
        self.mapLabel.execute("setAddress", **{"address": self.search_input.text()})
        status_code = self.mapLabel.getStatusCode()
        if status_code == 404:
            QMessageBox.information(self, "Search Result", "Nothing not found!\nPlease, specify the address")
            return
        elif status_code == 401:
            QMessageBox.critical(self, "Search result", "This area is not allowed to display!")
            return
        self.currentAddress = self.mapLabel.getCurrentAddress()
        self.currentPostalCode = self.mapLabel.getCurrentPostalCode()
        self.updateAddressLine(self.postalCode_show.isChecked())

    def changeType(self, type_id):
        self.mapLabel.execute("setMapType", **{"type_id": type_id})
        for i, btn in enumerate(self.map_buttons.buttons()):
            if i == type_id:
                btn.setCheckable(True)
                btn.setChecked(True)
            else:
                btn.setChecked(False)

    def updateAddressLine(self, show_postal_code):
        if not self.currentAddress:
            return
        address = self.currentAddress
        postalCode = ""
        if show_postal_code:
            if self.currentPostalCode:
                postalCode += f", {self.currentPostalCode}"
            else:
                postalCode += ", no postalCode"
        fullAddress = address + postalCode
        self.current_address.setText(fullAddress)
        self.current_address.setCursorPosition(0)
        self.current_address.setToolTip(fullAddress)
        self.search_input.clearFocus()

    def showPostalCode(self, state):
        self.updateAddressLine(state)

    def resetSearchResult(self):
        self.mapLabel.execute("hideLabel")
        self.currentAddress = None
        self.currentPostalCode = None
        self.current_address.clear()
        self.current_address.setToolTip("")
        self.search_input.clear()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.isAutoRepeat():
            return
        elif event.key() == Qt.Key_PageUp:
            self.mapLabel.execute("scaleUp")
        elif event.key() == Qt.Key_PageDown:
            self.mapLabel.execute("scaleDown")
        elif event.key() == Qt.Key_Up:
            self.mapLabel.execute("mapMove", **{"direction": "up"})
        elif event.key() == Qt.Key_Down:
            self.mapLabel.execute("mapMove", **{"direction": "down"})
        elif event.key() == Qt.Key_Right:
            self.mapLabel.execute("mapMove", **{"direction": "right"})
        elif event.key() == Qt.Key_Left:
            self.mapLabel.execute("mapMove", **{"direction": "left"})


if __name__ == "__main__":
    app = QApplication(sys.argv)
    searcher = MapSearcher()
    sys.exit(app.exec_())
