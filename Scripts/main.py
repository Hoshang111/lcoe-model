import re
import sys
import time

sys.path.append('..')
from PyQt5.QtCore import QSize, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QLabel, QLineEdit, QFileDialog, QComboBox, \
    QCheckBox, QMessageBox, QProgressBar
from PyQt5.QtGui import QPixmap
from mc_opt import run
from mc_analysis import run_mc
from Functions.graphing_functions import calculate_variance_diff
from db import add_params, add_scenario

this_module = sys.modules[__name__]
this_module.file = 'no file loaded'
this_module.scenarios = 1
this_module.num_iterations = ""


def set_file(filename):
    this_module.file = filename


class Optimiser(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        run(this_module.file)


class OptExternal(QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)

    def run(self):
        count = 0
        while count < 101:
            count += 1
            time.sleep(2.27)
            self.countChanged.emit(count)


class Montecarlo(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        run_mc(this_module.num_iterations)


class MonteExternal(QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)

    def run(self):
        count = 0
        while count < 101:
            count += 1
            time.sleep(0.93)
            self.countChanged.emit(count)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(1500, 800))
        self.setStyleSheet("background-color: white")
        self.click_start()
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

    def click_start(self):
        s_button = QPushButton('Projects', self)
        s_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        s_button.resize(200, 50)
        s_button.move(650, 500)
        s_button.clicked.connect(self.create_or_load)

    def create_or_load(self):
        self.clw = CreateLoadWindow()
        self.clw.show()
        self.close()

    def click_bangladesh(self):
        b_button = QPushButton('Create Bangladesh Project', self)
        b_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        b_button.resize(200, 50)
        b_button.move(650, 580)
        b_button.clicked.connect(self.clicked_bangladesh)
        self.close()

    def clicked_parameters(self):
        self.parameters = ParametersWindow()
        self.parameters.show()
        self.close()

    def clicked_bangladesh(self):
        self.bangladesh = BangladeshWindow()
        self.bangladesh.show()
        self.close()


class BangladeshWindow(QWidget):
    def __init__(self):
        super().__init__()

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

        title_params = QLabel(self)
        title_params.resize(500, 100)
        title_params.move(500, 120)
        title_params.setText("Bangladesh Project")
        title_params.setStyleSheet("font-size: 42pt; color: #152053")
        title_params.setAlignment(Qt.AlignCenter)


class CreateLoadWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Project Status")
        self.setFixedSize(QSize(400, 400))
        self.setStyleSheet("background-color: white")
        self.new_project()
        self.load_project()

        n_label = QLabel(self)
        n_label.setText("Would you like to create or load a project?")
        n_label.setWordWrap(True)
        n_label.setStyleSheet("font-size: 15pt; color: #152053")
        n_label.move(50, 100)

    def new_project(self):
        n_button = QPushButton('New Project', self)
        n_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        n_button.resize(100, 50)
        n_button.move(100, 300)
        n_button.clicked.connect(self.clicked_parameters)

    def load_project(self):
        l_button = QPushButton('Load Project', self)
        l_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        l_button.resize(100, 50)
        l_button.move(250, 300)
        l_button.clicked.connect(self.click_load_project)

    def click_load_project(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*)", options=options)
        set_file(filename)
        self.optimise = OptimiseWindow()
        self.optimise.show()
        self.close()

    def clicked_parameters(self):
        self.parameters = ParametersWindow()
        self.parameters.show()
        self.close()


class ParametersWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(1500, 800))
        self.setStyleSheet("background-color: white")
        self.parameters_nav_bar()
        self.param_labels()
        self.param_boxes()
        self.create_project()

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

        dc_label = QLabel(self)
        dc_label.resize(200, 50)
        dc_label.move(550, 200)
        dc_label.setText("DC Total")
        dc_label.setStyleSheet("font-size: 12pt; color: #152053")
        dc_label.setAlignment(Qt.AlignCenter)

        nzones_label = QLabel(self)
        nzones_label.resize(200, 50)
        nzones_label.move(550, 300)
        nzones_label.setText("Number of Zones")
        nzones_label.setStyleSheet("font-size: 12pt; color: #152053")
        nzones_label.setAlignment(Qt.AlignCenter)

        zarea_label = QLabel(self)
        zarea_label.resize(200, 50)
        zarea_label.move(550, 400)
        zarea_label.setText("Zone Area")
        zarea_label.setStyleSheet("font-size: 12pt; color: #152053")
        zarea_label.setAlignment(Qt.AlignCenter)

        tmodel_label = QLabel(self)
        tmodel_label.resize(200, 50)
        tmodel_label.move(550, 500)
        tmodel_label.setText("Temperature Model")
        tmodel_label.setStyleSheet("font-size: 12pt; color: #152053")
        tmodel_label.setAlignment(Qt.AlignCenter)

        numracks_label = QLabel(self)
        numracks_label.resize(200, 50)
        numracks_label.move(550, 600)
        numracks_label.setText("Number of Racks")
        numracks_label.setStyleSheet("font-size: 12pt; color: #152053")
        numracks_label.setAlignment(Qt.AlignCenter)

        elimit_label = QLabel(self)
        elimit_label.resize(200, 50)
        elimit_label.move(750, 200)
        elimit_label.setText("Export Limit")
        elimit_label.setStyleSheet("font-size: 12pt; color: #152053")
        elimit_label.setAlignment(Qt.AlignCenter)

        scapacity_label = QLabel(self)
        scapacity_label.resize(200, 50)
        scapacity_label.move(750, 300)
        scapacity_label.setText("Storage Capacity")
        scapacity_label.setStyleSheet("font-size: 12pt; color: #152053")
        scapacity_label.setAlignment(Qt.AlignCenter)

        sprice_label = QLabel(self)
        sprice_label.resize(200, 50)
        sprice_label.move(750, 400)
        sprice_label.setText("Scheduled Price")
        sprice_label.setStyleSheet("font-size: 12pt; color: #152053")
        sprice_label.setAlignment(Qt.AlignCenter)

        drate_label = QLabel(self)
        drate_label.resize(200, 50)
        drate_label.move(750, 500)
        drate_label.setText("Discount Rate")
        drate_label.setStyleSheet("font-size: 12pt; color: #152053")
        drate_label.setAlignment(Qt.AlignCenter)

        rackratio_label = QLabel(self)
        rackratio_label.resize(200, 50)
        rackratio_label.move(750, 600)
        rackratio_label.setText("Rack Interval Ratio")
        rackratio_label.setStyleSheet("font-size: 12pt; color: #152053")
        rackratio_label.setAlignment(Qt.AlignCenter)

    def param_boxes(self):
        self.dc_box = QLineEdit(self)
        self.dc_box.resize(100, 25)
        self.dc_box.move(600, 250)
        self.dc_box.setStyleSheet("color: black; border: 1px solid black;")
        self.dc_box.setAlignment(Qt.AlignCenter)

        self.nzones_box = QLineEdit(self)
        self.nzones_box.resize(100, 25)
        self.nzones_box.move(600, 350)
        self.nzones_box.setStyleSheet("color: black; border: 1px solid black;")
        self.nzones_box.setAlignment(Qt.AlignCenter)

        self.zarea_box = QLineEdit(self)
        self.zarea_box.resize(100, 25)
        self.zarea_box.move(600, 450)
        self.zarea_box.setStyleSheet("color: black; border: 1px solid black;")
        self.zarea_box.setAlignment(Qt.AlignCenter)

        self.tmodel_box = QComboBox(self)
        self.tmodel_box.addItems(["PVSyst", "SAPM"])
        self.tmodel_box.resize(100, 25)
        self.tmodel_box.move(600, 550)
        self.tmodel_box.setStyleSheet("color: black")

        self.numracks_box = QLineEdit(self)
        self.numracks_box.resize(100, 25)
        self.numracks_box.move(600, 650)
        self.numracks_box.setStyleSheet("color: black; border: 1px solid black;")
        self.numracks_box.setAlignment(Qt.AlignCenter)

        self.elimit_box = QLineEdit(self)
        self.elimit_box.resize(100, 25)
        self.elimit_box.move(800, 250)
        self.elimit_box.setStyleSheet("color: black; border: 1px solid black;")
        self.elimit_box.setAlignment(Qt.AlignCenter)

        self.scapacity_box = QLineEdit(self)
        self.scapacity_box.resize(100, 25)
        self.scapacity_box.move(800, 350)
        self.scapacity_box.setStyleSheet("color: black; border: 1px solid black;")
        self.scapacity_box.setAlignment(Qt.AlignCenter)

        self.sprice_box = QLineEdit(self)
        self.sprice_box.resize(100, 25)
        self.sprice_box.move(800, 450)
        self.sprice_box.setStyleSheet("color: black; border: 1px solid black;")
        self.sprice_box.setAlignment(Qt.AlignCenter)

        self.drate_box = QLineEdit(self)
        self.drate_box.resize(100, 25)
        self.drate_box.move(800, 550)
        self.drate_box.setStyleSheet("color: black; border: 1px solid black;")
        self.drate_box.setAlignment(Qt.AlignCenter)

        self.rackratio_box = QLineEdit(self)
        self.rackratio_box.resize(100, 25)
        self.rackratio_box.move(800, 650)
        self.rackratio_box.setStyleSheet("color: black; border: 1px solid black;")
        self.rackratio_box.setAlignment(Qt.AlignCenter)

    def create_project(self):
        c_button = QPushButton('Create Project', self)
        c_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        c_button.resize(200, 50)
        c_button.move(650, 700)
        c_button.clicked.connect(self.click_create_project)

    def parameters_nav_bar(self):
        h_button = QPushButton('Home', self)
        h_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        h_button.resize(300, 100)
        h_button.move(0, 0)
        h_button.clicked.connect(self.clicked_home)

        parameters_label = QLabel(self)
        parameters_label.resize(300, 100)
        parameters_label.move(300, 0)
        parameters_label.setText("Parameters")
        parameters_label.setStyleSheet("background-color: white; color: #152053; font-size: 10pt")
        parameters_label.setAlignment(Qt.AlignCenter)

        o_button = QPushButton('Optimise', self)
        o_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        o_button.resize(300, 100)
        o_button.move(600, 0)
        o_button.clicked.connect(self.clicked_optimise)

        m_button = QPushButton('Montecarlo', self)
        m_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        m_button.resize(300, 100)
        m_button.move(900, 0)
        m_button.clicked.connect(self.clicked_montecarlo)

        g_button = QPushButton('Graphs', self)
        g_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        g_button.resize(300, 100)
        g_button.move(1200, 0)
        g_button.clicked.connect(self.clicked_graphs)

    def clicked_home(self):
        self.home = MainWindow()
        self.home.show()
        self.close()

    def clicked_optimise(self):
        self.optimise = OptimiseWindow()
        self.optimise.show()
        self.close()

    def clicked_montecarlo(self):
        self.montecarlo = MontecarloWindow()
        self.montecarlo.show()
        self.close()

    def clicked_graphs(self):
        self.graphs = GraphWindow()
        self.graphs.show()
        self.close()

    def click_create_project(self):
        dc_total = self.dc_box.text()
        num_zones = self.nzones_box.text()
        zone_area = self.zarea_box.text()
        temp_model = self.tmodel_box.currentText()
        export_limit = self.elimit_box.text()
        storage_capacity = self.scapacity_box.text()
        scheduled_price = self.sprice_box.text()
        discount_rate = self.drate_box.text()
        num_racks = self.numracks_box.text()
        rack_interval_ratio = self.rackratio_box.text()

        if dc_total == "" or num_zones == "" or zone_area == "" or temp_model == "" or export_limit == "" or \
                storage_capacity == "" or scheduled_price == "" or discount_rate == "" or num_racks == "" \
                or rack_interval_ratio == "":
            msg = QMessageBox()
            msg.setWindowTitle("Invalid Inputs")
            msg.setText("Some input fields were left blank!")
            msg.exec()
        else:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "", "All Files (*);",
                                                      options=options)
            add_params(fileName, dc_total, num_zones, zone_area, temp_model, export_limit, storage_capacity,
                       scheduled_price
                       , discount_rate, num_racks, rack_interval_ratio)
            set_file(fileName)
            self.optimise = OptimiseWindow()
            self.optimise.show()
            self.close()


class OptimiseWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(1500, 800))
        self.setStyleSheet("background-color: white")
        self.optimise_nav_bar()
        self.opt_labels()
        self.optimise_project()
        self.add_scenario()

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

        opt = QLabel(self)
        opt.resize(400, 90)
        opt.move(550, 120)
        opt.setText("Optimiser")
        opt.setStyleSheet("font-size: 42pt; color: #152053")
        opt.setAlignment(Qt.AlignCenter)

    def opt_labels(self):
        split_file = re.split("/", this_module.file)
        i = 0
        for reg in split_file:
            i += 1
        file = split_file[i - 1]
        stuff_in_string = "Loaded Project: %s" % file

        loaded_file = QLabel(self)
        loaded_file.setText(stuff_in_string)
        loaded_file.setStyleSheet("color: #152053; font-size: 20pt")
        loaded_file.resize(400, 50)
        loaded_file.move(50, 200)

        year_label = QLabel(self)
        year_label.resize(200, 50)
        year_label.move(650, 200)
        year_label.setText("Year")
        year_label.setStyleSheet("color: #152053; font-size: 15pt")
        year_label.setAlignment(Qt.AlignCenter)

        moutech_label = QLabel(self)
        moutech_label.resize(200, 50)
        moutech_label.move(650, 300)
        moutech_label.setText("Mounting Technology")
        moutech_label.setStyleSheet("color: #152053; font-size: 15pt")
        moutech_label.setAlignment(Qt.AlignCenter)

        modtech_label = QLabel(self)
        modtech_label.resize(200, 50)
        modtech_label.move(650, 400)
        modtech_label.setText("Module Technology")
        modtech_label.setStyleSheet("color: #152053; font-size: 15pt")
        modtech_label.setAlignment(Qt.AlignCenter)

        self.year = QComboBox(self)
        self.year.addItems(["2024", "2026", "2028"])
        self.year.resize(100, 25)
        self.year.move(700, 250)
        self.year.setStyleSheet("color: black")

        self.m_tech = QComboBox(self)
        self.m_tech.addItems(["SAT", "MAV", "Fixed"])
        self.m_tech.resize(100, 25)
        self.m_tech.move(700, 350)
        self.m_tech.setStyleSheet("color: black")

        self.mod_tech = QComboBox(self)
        self.mod_tech.addItems(["PERC", "TOPCON", "HJT"])
        self.mod_tech.resize(100, 25)
        self.mod_tech.move(700, 450)
        self.mod_tech.setStyleSheet("color: black")

        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 200, 25)
        self.pbar.move(660, 650)
        self.pbar.hide()

    def add_scenario(self):
        self.as_button = QPushButton('Add Scenario', self)
        self.as_button.setStyleSheet("background-color: #152053; color:white; font-size: 10pt")
        self.as_button.resize(200, 50)
        self.as_button.move(650, 500)
        self.as_button.clicked.connect(self.add_scen)

    def add_scen(self):
        scenario = "%s_%s_%s" % (self.m_tech.currentText(), self.mod_tech.currentText(), self.year.currentText())
        add_scenario(this_module.file, scenario, this_module.scenarios)
        this_module.scenarios += 1
        msg = QMessageBox()
        msg.setWindowTitle("Scenario Added!")
        msg_text = "Scenario: %s was added" % scenario
        msg.setText(msg_text)
        msg.exec()

    def optimise_project(self):
        self.o_button = QPushButton('Optimise', self)
        self.o_button.setStyleSheet("background-color: #152053; color:white; font-size: 10pt")
        self.o_button.resize(200, 50)
        self.o_button.move(650, 575)
        self.o_button.clicked.connect(self.opt_inputs)

    def opt_inputs(self):
        self.optimiser = Optimiser()
        self.optimiser.finished.connect(self.clicked_montecarlo)
        self.optimiser.start()
        self.pbar.show()
        self.calc = OptExternal()
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()
        msg = QMessageBox()
        msg.setWindowTitle("Optimiser is running!")
        msg.setText("Optimiser is currently running, do not close tabs.")
        msg.exec()

    def onCountChanged(self, value):
        self.pbar.setValue(value)

    def optimise_nav_bar(self):
        h_button = QPushButton('Home', self)
        h_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        h_button.resize(300, 100)
        h_button.move(0, 0)
        h_button.clicked.connect(self.clicked_home)

        p_button = QPushButton('Parameters', self)
        p_button.setStyleSheet("color: white")
        p_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        p_button.resize(300, 100)
        p_button.move(300, 0)
        p_button.clicked.connect(self.clicked_parameters)

        optimise_label = QLabel(self)
        optimise_label.resize(300, 100)
        optimise_label.move(600, 0)
        optimise_label.setText("Optimise")
        optimise_label.setStyleSheet("background-color: white; color: #152053; font-size: 10pt")
        optimise_label.setAlignment(Qt.AlignCenter)

        m_button = QPushButton('Montecarlo', self)
        m_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        m_button.resize(300, 100)
        m_button.move(900, 0)
        m_button.clicked.connect(self.clicked_montecarlo)

        g_button = QPushButton('Graphs', self)
        g_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        g_button.resize(300, 100)
        g_button.move(1200, 0)
        g_button.clicked.connect(self.clicked_graphs)

    def clicked_home(self):
        self.home = MainWindow()
        self.home.show()
        self.close()

    def clicked_parameters(self):
        self.parameters = ParametersWindow()
        self.parameters.show()
        self.close()

    def clicked_montecarlo(self):
        self.montecarlo = MontecarloWindow()
        self.montecarlo.show()
        self.close()

    def clicked_graphs(self):
        self.graphs = GraphWindow()
        self.graphs.show()
        self.close()


class MontecarloWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(1500, 800))
        self.setStyleSheet("background-color: white")
        self.montecarlo_nav_bar()
        self.run_montecarlo()
        self.monte_labels()

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

        montec = QLabel(self)
        montec.resize(500, 90)
        montec.move(500, 120)
        montec.setText("Montecarlo Analysis")
        montec.setStyleSheet("font-size: 42pt; color: #152053")
        montec.setAlignment(Qt.AlignCenter)

    def monte_labels(self):
        split_file = re.split("/", this_module.file)
        i = 0
        for reg in split_file:
            i += 1
        file = split_file[i - 1]
        stuff_in_string = "Loaded Project: %s" % file

        loaded_file = QLabel(self)
        loaded_file.setText(stuff_in_string)
        loaded_file.setStyleSheet("color: #152053; font-size: 20pt")
        loaded_file.resize(400, 50)
        loaded_file.move(50, 200)

        numit_label = QLabel(self)
        numit_label.resize(200, 50)
        numit_label.move(650, 250)
        numit_label.setText("Number of Iterations")
        numit_label.setStyleSheet("color: #152053; font-size: 15pt")
        numit_label.setAlignment(Qt.AlignCenter)

        self.mbar = QProgressBar(self)
        self.mbar.setGeometry(30, 40, 200, 25)
        self.mbar.move(660, 650)
        self.mbar.hide()

        self.iter_box = QLineEdit(self)
        self.iter_box.resize(100, 25)
        self.iter_box.move(700, 300)
        self.iter_box.setStyleSheet("color: black; border: 1px solid black;")
        self.iter_box.setAlignment(Qt.AlignCenter)

    def run_montecarlo(self):
        self.o_button = QPushButton('Run Analysis', self)
        self.o_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        self.o_button.resize(200, 50)
        self.o_button.move(650, 400)
        self.o_button.clicked.connect(self.mc_inputs)

    def mc_inputs(self):
        if self.iter_box.text() == "":
            msg = QMessageBox()
            msg.setWindowTitle("Specify Number of Iterations")
            msg.setText("Please fill the number of iterations you want")
            msg.exec()
        else:
            this_module.num_iterations = self.iter_box.text()
            self.montecarlo = Montecarlo()
            self.montecarlo.finished.connect(self.clicked_graphs)
            self.montecarlo.start()
            self.mbar.show()
            self.calc = MonteExternal()
            self.calc.countChanged.connect(self.onCountChanged)
            self.calc.start()
            msg = QMessageBox()
            msg.setWindowTitle("Montecarlo Analysis is running!")
            msg.setText("Analysis is currently running, do not close tabs.")
            msg.exec()

    def onCountChanged(self, value):
        self.mbar.setValue(value)

    def montecarlo_nav_bar(self):
        h_button = QPushButton('Home', self)
        h_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        h_button.resize(300, 100)
        h_button.move(0, 0)
        h_button.clicked.connect(self.clicked_home)

        p_button = QPushButton('Parameters', self)
        p_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        p_button.resize(300, 100)
        p_button.move(300, 0)
        p_button.clicked.connect(self.clicked_parameters)

        o_button = QPushButton('Optimise', self)
        o_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        o_button.resize(300, 100)
        o_button.move(600, 0)
        o_button.clicked.connect(self.clicked_optimise)

        montecarlo_label = QLabel(self)
        montecarlo_label.resize(300, 100)
        montecarlo_label.move(900, 0)
        montecarlo_label.setText("Montecarlo")
        montecarlo_label.setStyleSheet("background-color: white; color: #152053; font-size: 10pt")
        montecarlo_label.setAlignment(Qt.AlignCenter)

        g_button = QPushButton('Graphs', self)
        g_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        g_button.resize(300, 100)
        g_button.move(1200, 0)
        g_button.clicked.connect(self.clicked_graphs)

    def clicked_home(self):
        self.home = MainWindow()
        self.home.show()
        self.close()

    def clicked_parameters(self):
        self.parameters = ParametersWindow()
        self.parameters.show()
        self.close()

    def clicked_optimise(self):
        self.optimise = OptimiseWindow()
        self.optimise.show()
        self.close()

    def clicked_graphs(self):
        self.graphs = GraphWindow()
        self.graphs.show()
        self.close()


class GraphWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(1500, 800))
        self.setStyleSheet("background-color: white")
        self.graph_nav_bar()
        self.graph_labels()
        self.graph_buttons()

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

        grapht = QLabel(self)
        grapht.resize(500, 90)
        grapht.move(500, 120)
        grapht.setText("Graphs")
        grapht.setStyleSheet("font-size: 42pt; color: #152053")
        grapht.setAlignment(Qt.AlignCenter)

    def graph_labels(self):
        split_file = re.split("/", this_module.file)
        i = 0
        for reg in split_file:
            i += 1
        file = split_file[i - 1]
        stuff_in_string = "Loaded Project: %s" % file

        loaded_file = QLabel(self)
        loaded_file.setText(stuff_in_string)
        loaded_file.setStyleSheet("color: #152053; font-size: 20pt")
        loaded_file.resize(400, 50)
        loaded_file.move(50, 200)

        vary_label = QLabel(self)
        vary_label.resize(200, 75)
        vary_label.move(650, 200)
        vary_label.setText("Parameters to vary")
        vary_label.setStyleSheet("color: #152053; font-size: 15pt")
        vary_label.setAlignment(Qt.AlignCenter)

        self.weather_check = QCheckBox("Weather", self)
        self.weather_check.resize(120, 50)
        self.weather_check.move(600, 260)
        self.weather_check.setStyleSheet("color: black")

        self.losses_check = QCheckBox("Losses", self)
        self.losses_check.resize(120, 50)
        self.losses_check.move(720, 260)
        self.losses_check.setStyleSheet("color: black")

        self.costs_check = QCheckBox("Costs", self)
        self.costs_check.resize(120, 50)
        self.costs_check.move(840, 260)
        self.costs_check.setStyleSheet("color: black")

        interest_label = QLabel(self)
        interest_label.resize(200, 50)
        interest_label.move(650, 325)
        interest_label.setText("Parameter of interest")
        interest_label.setStyleSheet("color: #152053; font-size: 15pt")
        interest_label.setAlignment(Qt.AlignCenter)

        gtoc_label = QLabel(self)
        gtoc_label.resize(200, 50)
        gtoc_label.move(650, 460)
        gtoc_label.setText("Graphs to Create")
        gtoc_label.setStyleSheet("color: #152053; font-size: 15pt")
        gtoc_label.setAlignment(Qt.AlignCenter)

        self.metric = QComboBox(self)
        self.metric.addItems(["NPV", "LCOE", "Cost", "Yield"])
        self.metric.resize(100, 50)
        self.metric.move(705, 375)
        self.metric.setStyleSheet("color: black")

    def graph_buttons(self):
        self.calc_var = QCheckBox("Calculate Variance", self)
        self.calc_var.resize(120, 50)
        self.calc_var.move(630, 500)
        self.calc_var.setStyleSheet("color: black")

        self.create_his = QCheckBox("Create Histogram", self)
        self.create_his.resize(120, 50)
        self.create_his.move(750, 500)
        self.create_his.setStyleSheet("color: black")

        self.create_scatter = QCheckBox("Calculate Scatter", self)
        self.create_scatter.resize(120, 50)
        self.create_scatter.move(630, 550)
        self.create_scatter.setStyleSheet("color: black")
        self.create_scatter.setEnabled(False)

        self.create_reg = QCheckBox("Create Regression", self)
        self.create_reg.resize(120, 50)
        self.create_reg.move(750, 550)
        self.create_reg.setStyleSheet("color: black")
        self.create_reg.setEnabled(False)

        self.o_button = QPushButton('Run', self)
        self.o_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        self.o_button.resize(200, 50)
        self.o_button.move(650, 650)
        self.o_button.clicked.connect(self.graph_inputs)

    def graph_inputs(self):
        weather_var = self.weather_check.isChecked
        losses_var = self.losses_check.isChecked
        costs_var = self.costs_check.isChecked
        output_metric = self.metric.currentText()
        if self.calc_var.isChecked:
            self.create_reg.setEnabled(True)
            self.create_scatter.setEnabled(True)
            parameter_list, input_parameter, output_parameter = calculate_variance_diff('SAT_PERCa_2028',
                                                                                        'MAV_PERCa_2028'
                                                                                        , weather_var, costs_var,
                                                                                        losses_var, output_metric)
        msg = QMessageBox()
        msg.setWindowTitle("Graphs Successfully Produced!")
        msg.setText("Please check the Output Figures for your Graphs.")
        msg.exec()
        # if self.create_his.isChecked:
        #     run_histogram(scenarios, losses_var, weather_var, costs_var, output_metric)
        #
        # if self.create_scatter.isChecked:
        #     run_1d_scatter('SAT_PERCa_2028', 'MAV_PERCa_2028', parameter_list, input_parameter, output_parameter,
        #                    weather_var, costs_var,losses_var, output_metric)

    def graph_nav_bar(self):
        h_button = QPushButton('Home', self)
        h_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        h_button.resize(300, 100)
        h_button.move(0, 0)
        h_button.clicked.connect(self.clicked_home)

        p_button = QPushButton('Parameters', self)
        p_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        p_button.resize(300, 100)
        p_button.move(300, 0)
        p_button.clicked.connect(self.clicked_parameters)

        o_button = QPushButton('Optimise', self)
        o_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        o_button.resize(300, 100)
        o_button.move(600, 0)
        o_button.clicked.connect(self.clicked_optimise)

        o_button = QPushButton('Montecarlo', self)
        o_button.setStyleSheet("background-color: #152053; color: white; font-size: 10pt")
        o_button.resize(300, 100)
        o_button.move(900, 0)
        o_button.clicked.connect(self.clicked_montecarlo)

        graph_label = QLabel(self)
        graph_label.resize(300, 100)
        graph_label.move(1200, 0)
        graph_label.setText("Graphs")
        graph_label.setAlignment(Qt.AlignCenter)
        graph_label.setStyleSheet("background-color: white; color: #152053; font-size: 10pt")

    def clicked_home(self):
        self.home = MainWindow()
        self.home.show()
        self.close()

    def clicked_parameters(self):
        self.parameters = ParametersWindow()
        self.parameters.show()
        self.close()

    def clicked_optimise(self):
        self.optimise = OptimiseWindow()
        self.optimise.show()
        self.close()

    def clicked_montecarlo(self):
        self.montecarlo = MontecarloWindow()
        self.montecarlo.show()
        self.close()

    def clicked_graphs(self):
        self.graphs = GraphWindow()
        self.graphs.show()
        self.close()


app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()
