import sys
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt, QByteArray
from map_tools.api import ApiInteraction
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QButtonGroup,
    QGroupBox,
    QCheckBox,
    QMessageBox,
    QSizePolicy,
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
        self.new_address = False
        self.api_interaction = ApiInteraction()
        self.map_types = {
            0: "map",
            1: "sat",
            2: "sat,skl",
        }
        self.methods = {
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
        print(f"Found new toponym: {new_toponym}")
        if new_toponym is None:
            return
        self.toponym = new_toponym
        self.object_label = True
        self.new_address = True
        print("Map address was update")

    def setMapType(self, type_id):
        print(f"Set new map type ({self.map_types[type_id]})")
        if type_id in self.map_types:
            self.map_type = type_id

    def scaleUp(self):
        if self.scale == self.MAX_SCALE:
            return
        self.scale += 1
        print("Scale was up")

    def scaleDown(self):
        if self.scale == self.MIN_SCALE:
            return
        self.scale -= 1
        print("Scale was down")

    def hideLabel(self):
        self.object_label = False
        print("Label reset")

    def updateView(self):
        if self.toponym is None:
            print("no address")
            return
        if self.first_result:
            self.first_result = False
            self.clear()
        args = [
            self.toponym.getCoordinates(),
            self.map_types[self.map_type],
            self.scale,
            self.object_label,
        ]
        pixmap = QPixmap()
        pixmap.loadFromData(self.api_interaction.get_image(*args))
        self.setPixmap(pixmap)
        print("View was updated")

    def getCurrentAddress(self):
        if self.toponym:
            return self.toponym.getAddress()
        return None

    def getCurrentPostalCode(self):
        if self.toponym:
            return self.toponym.getPostalCode()
        return None

    def isAddressUpdated(self):
        if self.new_address:
            self.new_address = False
            return True
        return False


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
        reset_search_result_button.setStyleSheet("background-color: red")
        reset_search_result_button.clicked.connect(self.resetSearchResult)

        # adding all layouts and widgets to main layout
        vertical_layout.addLayout(horizontal_layout)
        vertical_layout.addWidget(self.mapLabel, alignment=Qt.AlignCenter)
        vertical_layout.addWidget(map_type_group, alignment=Qt.AlignBaseline)
        vertical_layout.addWidget(address_options_group, alignment=Qt.AlignBaseline)
        vertical_layout.addWidget(reset_search_result_button, alignment=Qt.AlignCenter)

        # # message box (if nothing not found)
        # self.errorMessage = QMessageBox(self)
        # self.errorMessage.setIcon(QMessageBox.Critical)
        # self.errorMessage.setWindowModality(Qt.ApplicationModal)

        # show window
        self.show()
        self.changeType(0)

    def newSearchRequest(self):
        self.mapLabel.execute("setAddress", **{"address": self.search_input.text()})
        if not self.mapLabel.isAddressUpdated():
            QMessageBox.information(self, "Search Result", "Nothing not found!\nPlease, specify the address")
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
        self.current_address.setText(address + postalCode)

    def showPostalCode(self, state):
        self.updateAddressLine(state)

    def resetSearchResult(self):
        self.mapLabel.execute("hideLabel")
        self.currentAddress = None
        self.currentPostalCode = None
        self.current_address.clear()
        self.search_input.clear()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.isAutoRepeat():
            return
        if event.key() == Qt.Key_PageUp:
            self.mapLabel.execute("scaleUp")
        elif event.key() == Qt.Key_PageDown:
            self.mapLabel.execute("scaleDown")
        elif event.key() == Qt.Key_Up:
            pass
        elif event.key() == Qt.Key_Down:
            pass
        elif event.key() == Qt.Key_Left:
            pass
        elif event.key() == Qt.Key_Right:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    searcher = MapSearcher()
    sys.exit(app.exec_())
