import sys
import math
from math import cos
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from ui.map_label import MapLabel
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QCheckBox,
    QGroupBox,
    QLineEdit,
    QWidget,
)


SCREEN_SIZE = [700, 700]


def lonlat_distance(a, b):

    degree_to_meters_factor = 111 * 1000
    a_lon, a_lat = a
    b_lon, b_lat = b

    radians_latitude = math.radians((a_lat + b_lat) / 2.)
    lat_lon_factor = math.cos(radians_latitude)

    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor

    distance = math.sqrt(dx * dx + dy * dy)

    return distance


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
        self.mapLabel.clicked.connect(self.clickAddress)

        # show window
        self.show()
        self.changeType(0)

    def newSearchRequest(self):
        self.mapLabel.execute("setAddress", **{"address": self.search_input.text()})
        self.showRequestResult()

    def showRequestResult(self):
        status_code = self.mapLabel.getStatusCode()
        if status_code == 404:
            QMessageBox.information(self, "Search Result",
                                    "Nothing not found!\nPlease, specify the address")
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

    def mousePressEvent(self, event):
        focused_widget = QApplication.focusWidget()
        if focused_widget:
            focused_widget.clearFocus()
        QMainWindow.mousePressEvent(self, event)

    def clickAddress(self, event):
        label = self.mapLabel
        if not label or not label.toponym:
            return
        pos = event.localPos()
        x, y = pos.x(), pos.y()
        delta_long = 0.00001072883606 * 512 * 2 ** (label.MAX_SCALE - label.scale
                                                    ) / label.size().width() * (
                             x - label.size().width() / 2)
        delta_lat = 0.00000536441803 * 512 * 2 ** (label.MAX_SCALE - label.scale
                                                   ) / label.size().height() * (
                            label.size().height() / 2 - y)
        if event.button() == Qt.LeftButton:
            new_toponym = label.api_interaction.get_geocode(", ".join(map(str, (
                label.map_center[0] + delta_long,
                label.map_center[1] + delta_lat))), rspn=1)
            if new_toponym is None:
                return
            label.result_code = 200
            label.toponym = new_toponym
            label.object_label = True
            self.showRequestResult()
            label.updateView()
        elif event.button() == Qt.RightButton:
            new_toponym = label.api_interaction.get_geocode(", ".join(map(str, (
                label.map_center[0] + delta_long,
                label.map_center[1] + delta_lat))), rspn=1)
            if not new_toponym:
                return
            if lonlat_distance(new_toponym.getCoordinates(), (
                label.map_center[0] + delta_long,
                label.map_center[1] + delta_lat)) > 50:
                return
            organisation = label.api_interaction.get_organisation((
                label.map_center[0] + delta_long,
                label.map_center[1] + delta_lat,
            ), new_toponym.getAddress(), rspn=1, type="biz", spn="{},{}".format(
                1 / (111000 * abs(cos(label.map_center[1] + delta_lat))) * 50,
                str(1 / 111000 * 50)))
            if organisation is None:
                return
            organisation.postal_code = new_toponym.getPostalCode()
            label.result_code = 200
            label.toponym = organisation
            label.object_label = True
            self.showRequestResult()
            label.updateView()

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
