import sys

sys.path.append('..')
from PyQt5.QtCore import QSize, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QLabel, QLineEdit, QFileDialog, \
    QComboBox, QCheckBox, QMessageBox, QProgressBar
from PyQt5.QtGui import QPixmap
from Scripts.mc_analysis_simple import bangladesh_analysis

class MainLCOEWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.bangladesh = None
        self.parameters = None
        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(1500, 800))
        self.setStyleSheet("background-color: white")
        self.click_bangladesh()

        home = QLabel(self)
        home.resize(500, 200)
        home.move(500, 100)
        home.setText("Suncable & UNSW LCOE Model")
        home.setWordWrap(True)
        home.setStyleSheet("font-size: 42pt; color: #152053")
        home.setAlignment(Qt.AlignCenter)

        self.sc_logo = QLabel(self)
        self.pixmap = QPixmap('../Scripts/suncable_logo.png')
        smaller_pixmap = self.pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.sc_logo.resize(150, 150)
        self.sc_logo.setPixmap(smaller_pixmap)
        self.sc_logo.move(580, 300)

        self.unsw_logo = QLabel(self)
        self.unsw_pm = QPixmap('../Scripts/crest.jpg')
        unsw_smaller_pixmap = self.unsw_pm.scaled(150, 150, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.unsw_logo.resize(150, 150)
        self.unsw_logo.setPixmap(unsw_smaller_pixmap)
        self.unsw_logo.move(750, 300)

    def click_bangladesh(self):
        b_button = QPushButton('Create Bangladesh Project', self)
        b_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        b_button.resize(200, 50)
        b_button.move(650, 580)
        b_button.clicked.connect(self.clicked_bangladesh)
        self.close()

    def clicked_bangladesh(self):
        self.bangladesh = BangladeshWindow()
        self.bangladesh.show()
        self.close()


class BangladeshWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.param_labels()
        self.param_boxes()
        self.create_bangladesh()
        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(1500, 800))
        self.setStyleSheet("background-color: white")

        self.sc_logo = QLabel(self)
        self.pixmap = QPixmap('../Scripts/suncable_logo.png')
        smaller_pixmap = self.pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.sc_logo.resize(60, 60)
        self.sc_logo.setPixmap(smaller_pixmap)
        self.sc_logo.move(1350, 110)

        self.unsw_logo = QLabel(self)
        self.unsw_pm = QPixmap('../Scripts/crest.jpg')
        unsw_smaller_pixmap = self.unsw_pm.scaled(50, 50, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.unsw_logo.resize(80, 80)
        self.unsw_logo.setPixmap(unsw_smaller_pixmap)
        self.unsw_logo.move(1420, 100)

    def param_labels(self):
        title_params = QLabel(self)
        title_params.resize(400, 50)
        title_params.move(550, 120)
        title_params.setText("Parameters")
        title_params.setStyleSheet("font-size: 42pt; color: #152053")
        title_params.setAlignment(Qt.AlignCenter)

        name_label = QLabel(self)
        name_label.resize(200, 50)
        name_label.move(350, 200)
        name_label.setText("Name")
        name_label.setStyleSheet("font-size: 12pt; color: #152053")
        name_label.setAlignment(Qt.AlignCenter)

        latitude_label = QLabel(self)
        latitude_label.resize(200, 50)
        latitude_label.move(550, 200)
        latitude_label.setText("Latitude")
        latitude_label.setStyleSheet("font-size: 12pt; color: #152053")
        latitude_label.setAlignment(Qt.AlignCenter)

        longitude_label = QLabel(self)
        longitude_label.resize(200, 50)
        longitude_label.move(750, 200)
        longitude_label.setText("Longitude")
        longitude_label.setStyleSheet("font-size: 12pt; color: #152053")
        longitude_label.setAlignment(Qt.AlignCenter)

        drate_label = QLabel(self)
        drate_label.resize(200, 50)
        drate_label.move(950, 200)
        drate_label.setText("Discount Rate")
        drate_label.setStyleSheet("font-size: 12pt; color: #152053")
        drate_label.setAlignment(Qt.AlignCenter)

        altitude_label = QLabel(self)
        altitude_label.resize(200, 50)
        altitude_label.move(350, 300)
        altitude_label.setText("Altitude")
        altitude_label.setStyleSheet("font-size: 12pt; color: #152053")
        altitude_label.setAlignment(Qt.AlignCenter)

        site_area_label = QLabel(self)
        site_area_label.resize(200, 50)
        site_area_label.move(550, 300)
        site_area_label.setText("Site Area")
        site_area_label.setStyleSheet("font-size: 12pt; color: #152053")
        site_area_label.setAlignment(Qt.AlignCenter)

        distance_substation_label = QLabel(self)
        distance_substation_label.resize(200, 50)
        distance_substation_label.move(750, 300)
        distance_substation_label.setText("Distance to Substation")
        distance_substation_label.setStyleSheet("font-size: 12pt; color: #152053")
        distance_substation_label.setAlignment(Qt.AlignCenter)

        distance_road_label = QLabel(self)
        distance_road_label.resize(200, 50)
        distance_road_label.move(950, 300)
        distance_road_label.setText("Distance to Road")
        distance_road_label.setStyleSheet("font-size: 12pt; color: #152053")
        distance_road_label.setAlignment(Qt.AlignCenter)

        mwh_rating_label = QLabel(self)
        mwh_rating_label.resize(200, 50)
        mwh_rating_label.move(350, 400)
        mwh_rating_label.setText("MWH Rating")
        mwh_rating_label.setStyleSheet("font-size: 12pt; color: #152053")
        mwh_rating_label.setAlignment(Qt.AlignCenter)

        flood_risk_label = QLabel(self)
        flood_risk_label.resize(200, 50)
        flood_risk_label.move(550, 400)
        flood_risk_label.setText("Flood Risk")
        flood_risk_label.setStyleSheet("font-size: 12pt; color: #152053")
        flood_risk_label.setAlignment(Qt.AlignCenter)

        num_iterations_label = QLabel(self)
        num_iterations_label.resize(200, 50)
        num_iterations_label.move(750, 400)
        num_iterations_label.setText("Number of Iterations")
        num_iterations_label.setStyleSheet("font-size: 12pt; color: #152053")
        num_iterations_label.setAlignment(Qt.AlignCenter)

        timezone_label = QLabel(self)
        timezone_label.resize(200, 50)
        timezone_label.move(950, 400)
        timezone_label.setText("Time Zone")
        timezone_label.setStyleSheet("font-size: 12pt; color: #152053")
        timezone_label.setAlignment(Qt.AlignCenter)

    def param_boxes(self):
        self.name_box = QLineEdit(self)
        self.name_box.resize(100, 25)
        self.name_box.move(400, 250)
        self.name_box.setStyleSheet("color: black; border: 1px solid black;")
        self.name_box.setAlignment(Qt.AlignCenter)

        self.latitude_box = QLineEdit(self)
        self.latitude_box.resize(100, 25)
        self.latitude_box.move(600, 250)
        self.latitude_box.setStyleSheet("color: black; border: 1px solid black;")
        self.latitude_box.setAlignment(Qt.AlignCenter)

        self.longitude_box = QLineEdit(self)
        self.longitude_box.resize(100, 25)
        self.longitude_box.move(800, 250)
        self.longitude_box.setStyleSheet("color: black; border: 1px solid black;")
        self.longitude_box.setAlignment(Qt.AlignCenter)

        self.drate_box = QLineEdit(self)
        self.drate_box.resize(100, 25)
        self.drate_box.move(1000, 250)
        self.drate_box.setStyleSheet("color: black; border: 1px solid black;")
        self.drate_box.setAlignment(Qt.AlignCenter)

        self.altitude_box = QLineEdit(self)
        self.altitude_box.resize(100, 25)
        self.altitude_box.move(400, 350)
        self.altitude_box.setStyleSheet("color: black; border: 1px solid black;")
        self.altitude_box.setAlignment(Qt.AlignCenter)

        self.site_area_box = QLineEdit(self)
        self.site_area_box.resize(100, 25)
        self.site_area_box.move(600, 350)
        self.site_area_box.setStyleSheet("color: black; border: 1px solid black;")
        self.site_area_box.setAlignment(Qt.AlignCenter)

        self.distance_substation_box = QLineEdit(self)
        self.distance_substation_box.resize(100, 25)
        self.distance_substation_box.move(800, 350)
        self.distance_substation_box.setStyleSheet("color: black; border: 1px solid black;")
        self.distance_substation_box.setAlignment(Qt.AlignCenter)

        self.distance_road_box = QLineEdit(self)
        self.distance_road_box.resize(100, 25)
        self.distance_road_box.move(1000, 350)
        self.distance_road_box.setStyleSheet("color: black; border: 1px solid black;")
        self.distance_road_box.setAlignment(Qt.AlignCenter)

        self.mwh_rating_box = QLineEdit(self)
        self.mwh_rating_box.resize(100, 25)
        self.mwh_rating_box.move(400, 450)
        self.mwh_rating_box.setStyleSheet("color: black; border: 1px solid black;")
        self.mwh_rating_box.setAlignment(Qt.AlignCenter)

        self.flood_risk_box = QComboBox(self)
        self.flood_risk_box.addItems(["None", "Low", "Medium", "High"])
        self.flood_risk_box.resize(100, 25)
        self.flood_risk_box.move(600, 450)
        self.flood_risk_box.setStyleSheet("color: black; border: 1px solid black;")

        self.num_iterations_box = QComboBox(self)
        self.num_iterations_box.addItems(["100", "500", "2000"])
        self.num_iterations_box.resize(100, 25)
        self.num_iterations_box.move(800, 450)
        self.num_iterations_box.setStyleSheet("color: black; border: 1px solid black;")

        self.timezone_box = QComboBox(self)
        self.timezone_box.addItems(["UTC"])
        self.timezone_box.resize(100, 25)
        self.timezone_box.move(1000, 450)
        self.timezone_box.setStyleSheet("color: black; border: 1px solid black;")

    def create_bangladesh(self):
        c_button = QPushButton('Create Project', self)
        c_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        c_button.resize(200, 50)
        c_button.move(650, 700)
        c_button.clicked.connect(self.click_create_project)

    def click_create_project(self):
        name = self.name_box.text()
        latitude = self.latitude_box.text()
        longitude = self.longitude_box.text()
        drate = self.drate_box.text()
        altitude = self.altitude_box.text()
        site_area = self.site_area_box.text()
        mwh_rating = self.mwh_rating_box.text()
        distance_substation = self.distance_substation_box.text()
        distance_road = self.distance_road_box.text()
        flood_risk = self.flood_risk_box.currentText()
        num_iterations = self.num_iterations_box.currentText()
        time_zone = self.timezone_box.currentText()

        inputs = [name, latitude, longitude, drate, altitude, site_area, mwh_rating, time_zone, distance_substation,
                  distance_road, flood_risk, num_iterations]
        bangladesh_analysis(inputs)

app = QApplication(sys.argv)
window = MainLCOEWindow()
window.show()
app.exec()
