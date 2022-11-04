import sys

sys.path.append('..')
from PyQt5.QtCore import QSize, Qt, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QLabel, QLineEdit, QFileDialog, QComboBox, \
    QCheckBox
from mc_opt import run
from mc_analysis import run_mc
from Functions.graphing_functions import calculate_variance_diff, load_analysis_dict

this_module = sys.modules[__name__]
this_module.file = 'no file loaded'
this_module.year = 2028
this_module.number_iter = 20


def set_file(filename):
    this_module.file = filename


def set_year(year):
    this_module.year = year


def set_iter(iter_n):
    this_module.number_iter = iter_n


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.parameters = None
        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(2000, 1000))
        self.setStyleSheet("background-color: white")
        self.home_nav_bar()

    def home_nav_bar(self):
        title_params = QLabel(self)
        title_params.resize(100, 50)
        title_params.move(100, 100)
        title_params.setText("Welcome to the UNSW LCOE Model!")
        title_params.setStyleSheet("color: black")
        title_params.setAlignment(Qt.AlignCenter)

        home_label = QLabel(self)
        home_label.resize(400, 100)
        home_label.move(0, 0)
        home_label.setText("Home")
        home_label.setAlignment(Qt.AlignCenter)
        home_label.setStyleSheet("color: black")
        home_label.setStyleSheet("background-color: white")

        p_button = QPushButton('Parameters', self)
        p_button.setStyleSheet("color: white")
        p_button.setStyleSheet("background-color: #152053")
        p_button.resize(400, 100)
        p_button.move(400, 0)
        p_button.clicked.connect(self.clicked_parameters)

        o_button = QPushButton('Optimise', self)
        o_button.setStyleSheet("color: white")
        o_button.setStyleSheet("background-color: #152053")
        o_button.resize(500, 100)
        o_button.move(800, 0)
        o_button.clicked.connect(self.clicked_optimise)

        m_button = QPushButton('Montecarlo', self)
        m_button.setStyleSheet("color: white")
        m_button.setStyleSheet("background-color: #152053")
        m_button.resize(500, 100)
        m_button.move(1200, 0)
        m_button.clicked.connect(self.clicked_montecarlo)

        g_button = QPushButton('Graphs', self)
        g_button.setStyleSheet("color: white")
        g_button.setStyleSheet("background-color: #152053")
        g_button.resize(500, 100)
        g_button.move(1600, 0)
        g_button.clicked.connect(self.clicked_graphs)

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


class ParametersWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(2000, 1000))
        self.setStyleSheet("background-color: white")
        self.parameters_nav_bar()
        self.param_labels()
        self.param_boxes()
        self.create_project()
        self.load_project()

    def param_labels(self):
        title_params = QLabel(self)
        title_params.resize(100, 50)
        title_params.move(100, 100)
        title_params.setText("Parameters")
        title_params.setStyleSheet("color: black")
        title_params.setAlignment(Qt.AlignCenter)

        dc_label = QLabel(self)
        dc_label.resize(100, 50)
        dc_label.move(100, 150)
        dc_label.setText("DC Total")
        dc_label.setStyleSheet("color: black")
        dc_label.setAlignment(Qt.AlignCenter)

        nzones_label = QLabel(self)
        nzones_label.resize(100, 50)
        nzones_label.move(100, 200)
        nzones_label.setText("Number of Zones")
        nzones_label.setStyleSheet("color: black")
        nzones_label.setAlignment(Qt.AlignCenter)

        zarea_label = QLabel(self)
        zarea_label.resize(100, 50)
        zarea_label.move(100, 250)
        zarea_label.setText("Zone Area")
        zarea_label.setStyleSheet("color: black")
        zarea_label.setAlignment(Qt.AlignCenter)

        tmodel_label = QLabel(self)
        tmodel_label.resize(100, 50)
        tmodel_label.move(100, 300)
        tmodel_label.setText("Temperature Model")
        tmodel_label.setStyleSheet("color: black")
        tmodel_label.setAlignment(Qt.AlignCenter)

        elimit_label = QLabel(self)
        elimit_label.resize(100, 50)
        elimit_label.move(500, 150)
        elimit_label.setText("Export Limit")
        elimit_label.setStyleSheet("color: black")
        elimit_label.setAlignment(Qt.AlignCenter)

        scapacity_label = QLabel(self)
        scapacity_label.resize(100, 50)
        scapacity_label.move(500, 200)
        scapacity_label.setText("Storage Capacity")
        scapacity_label.setStyleSheet("color: black")
        scapacity_label.setAlignment(Qt.AlignCenter)

        sprice_label = QLabel(self)
        sprice_label.resize(100, 50)
        sprice_label.move(500, 250)
        sprice_label.setText("Scheduled Price")
        sprice_label.setStyleSheet("color: black")
        sprice_label.setAlignment(Qt.AlignCenter)

        drate_label = QLabel(self)
        drate_label.resize(100, 50)
        drate_label.move(500, 300)
        drate_label.setText("Discount Rate")
        drate_label.setStyleSheet("color: black")
        drate_label.setAlignment(Qt.AlignCenter)

    def param_boxes(self):
        self.dc_box = QLineEdit(self)
        self.dc_box.resize(100, 50)
        self.dc_box.move(200, 150)
        self.dc_box.setStyleSheet("color: black")
        self.dc_box.setAlignment(Qt.AlignCenter)

        self.nzones_box = QLineEdit(self)
        self.nzones_box.resize(100, 50)
        self.nzones_box.move(200, 200)
        self.nzones_box.setStyleSheet("color: black")
        self.nzones_box.setAlignment(Qt.AlignCenter)

        self.zarea_box = QLineEdit(self)
        self.zarea_box.resize(100, 50)
        self.zarea_box.move(200, 250)
        self.zarea_box.setStyleSheet("color: black")
        self.zarea_box.setAlignment(Qt.AlignCenter)

        self.tmodel_box = QLineEdit(self)
        self.tmodel_box.resize(100, 50)
        self.tmodel_box.move(200, 300)
        self.tmodel_box.setStyleSheet("color: black")
        self.tmodel_box.setAlignment(Qt.AlignCenter)

        self.elimit_box = QLineEdit(self)
        self.elimit_box.resize(100, 50)
        self.elimit_box.move(600, 150)
        self.elimit_box.setStyleSheet("color: black")
        self.elimit_box.setAlignment(Qt.AlignCenter)

        self.scapacity_box = QLineEdit(self)
        self.scapacity_box.resize(100, 50)
        self.scapacity_box.move(600, 200)
        self.scapacity_box.setStyleSheet("color: black")
        self.scapacity_box.setAlignment(Qt.AlignCenter)

        self.sprice_box = QLineEdit(self)
        self.sprice_box.resize(100, 50)
        self.sprice_box.move(600, 250)
        self.sprice_box.setStyleSheet("color: black")
        self.sprice_box.setAlignment(Qt.AlignCenter)

        self.drate_box = QLineEdit(self)
        self.drate_box.resize(100, 50)
        self.drate_box.move(600, 300)
        self.drate_box.setStyleSheet("color: black")
        self.drate_box.setAlignment(Qt.AlignCenter)

    def create_project(self):
        c_button = QPushButton('Create Project', self)
        c_button.setStyleSheet("color: white")
        c_button.setStyleSheet("background-color: #152053")
        c_button.resize(200, 50)
        c_button.move(1700, 700)
        c_button.clicked.connect(self.click_create_project)

    def load_project(self):
        o_button = QPushButton('Load Project', self)
        o_button.setStyleSheet("color: white")
        o_button.setStyleSheet("background-color: #152053")
        o_button.resize(200, 50)
        o_button.move(1700, 600)
        o_button.clicked.connect(self.click_load_project)

    def parameters_nav_bar(self):
        h_button = QPushButton('Home', self)
        h_button.setStyleSheet("color: white")
        h_button.setStyleSheet("background-color: #152053")
        h_button.resize(400, 100)
        h_button.move(0, 0)
        h_button.clicked.connect(self.clicked_home)

        parameters_label = QLabel(self)
        parameters_label.resize(400, 100)
        parameters_label.move(400, 0)
        parameters_label.setText("Parameters")
        parameters_label.setStyleSheet("color: black")
        parameters_label.setStyleSheet("background-color: white")
        parameters_label.setAlignment(Qt.AlignCenter)

        o_button = QPushButton('Optimise', self)
        o_button.setStyleSheet("color: white")
        o_button.setStyleSheet("background-color: #152053")
        o_button.resize(500, 100)
        o_button.move(800, 0)
        o_button.clicked.connect(self.clicked_optimise)

        m_button = QPushButton('Montecarlo', self)
        m_button.setStyleSheet("color: white")
        m_button.setStyleSheet("background-color: #152053")
        m_button.resize(500, 100)
        m_button.move(1200, 0)
        m_button.clicked.connect(self.clicked_montecarlo)

        g_button = QPushButton('Graphs', self)
        g_button.setStyleSheet("color: white")
        g_button.setStyleSheet("background-color: #152053")
        g_button.resize(500, 100)
        g_button.move(1600, 0)
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
        temp_model = self.tmodel_box.text()
        export_limit = self.elimit_box.text()
        storage_capacity = self.scapacity_box.text()
        scheduled_price = self.sprice_box.text()
        discount_rate = self.drate_box.text()

    def click_load_project(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*.db)", options=options)
        set_file(filename)


class OptimiseWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(2000, 1000))
        self.setStyleSheet("background-color: white")
        self.optimise_nav_bar()
        self.opt_labels()
        self.optimise_project()

    def opt_labels(self):
        title_opt = QLabel(self)
        title_opt.resize(100, 50)
        title_opt.move(100, 100)
        title_opt.setText("Optimiser")
        title_opt.setStyleSheet("color: black")
        title_opt.setAlignment(Qt.AlignCenter)

        year_label = QLabel(self)
        year_label.resize(100, 50)
        year_label.move(100, 150)
        year_label.setText("Year")
        year_label.setStyleSheet("color: black")
        year_label.setAlignment(Qt.AlignCenter)

        moutech_label = QLabel(self)
        moutech_label.resize(120, 50)
        moutech_label.move(100, 250)
        moutech_label.setText("Mounting Technology")
        moutech_label.setStyleSheet("color: black")
        moutech_label.setAlignment(Qt.AlignCenter)

        modtech_label = QLabel(self)
        modtech_label.resize(120, 50)
        modtech_label.move(100, 350)
        modtech_label.setText("Module Technology")
        modtech_label.setStyleSheet("color: black")
        modtech_label.setAlignment(Qt.AlignCenter)

        numracks_label = QLabel(self)
        numracks_label.resize(120, 50)
        numracks_label.move(100, 450)
        numracks_label.setText("Number of Racks")
        numracks_label.setStyleSheet("color: black")
        numracks_label.setAlignment(Qt.AlignCenter)

        numracks_label = QLabel(self)
        numracks_label.resize(120, 50)
        numracks_label.move(100, 650)
        numracks_label.setText("Scenario 1")
        numracks_label.setStyleSheet("color: black")
        numracks_label.setAlignment(Qt.AlignCenter)

        scen1_label = QLabel(self)
        scen1_label.resize(200, 50)
        scen1_label.move(250, 650)
        scen1_label.setStyleSheet("background-color: grey")
        scen1_label.setAlignment(Qt.AlignCenter)

        self.year = QComboBox(self)
        self.year.addItems(["2024", "2026", "2028"])
        self.year.resize(100, 50)
        self.year.move(250, 150)
        self.year.setStyleSheet("color: black")

        self.m_tech = QComboBox(self)
        self.m_tech.addItems(["SAT", "MAV", "Fixed"])
        self.m_tech.resize(100, 50)
        self.m_tech.move(250, 250)
        self.m_tech.setStyleSheet("color: black")

        self.mod_tech = QComboBox(self)
        self.mod_tech.addItems(["PERC", "TOPCON", "HJT"])
        self.mod_tech.resize(100, 50)
        self.mod_tech.move(250, 350)
        self.mod_tech.setStyleSheet("color: black")

        self.numracks = QLineEdit(self)
        self.numracks.resize(100, 50)
        self.numracks.move(250, 450)
        self.numracks.setStyleSheet("color: black")
        self.numracks.setAlignment(Qt.AlignCenter)

    def optimise_project(self):
        self.o_button = QPushButton('Optimise', self)
        self.o_button.setStyleSheet("color: white")
        self.o_button.setStyleSheet("background-color: #152053")
        self.o_button.resize(200, 50)
        self.o_button.move(1700, 700)
        self.o_button.clicked.connect(self.opt_inputs)

    def opt_inputs(self):
        year, number_iter = run(this_module.file)
        set_year(year)
        set_iter(number_iter)

    def optimise_nav_bar(self):
        h_button = QPushButton('Home', self)
        h_button.setStyleSheet("color: white")
        h_button.setStyleSheet("background-color: #152053")
        h_button.resize(400, 100)
        h_button.move(0, 0)
        h_button.clicked.connect(self.clicked_home)

        p_button = QPushButton('Parameters', self)
        p_button.setStyleSheet("color: white")
        p_button.setStyleSheet("background-color: #152053")
        p_button.resize(400, 100)
        p_button.move(400, 0)
        p_button.clicked.connect(self.clicked_parameters)

        optimise_label = QLabel(self)
        optimise_label.resize(400, 100)
        optimise_label.move(800, 0)
        optimise_label.setText("Optimise")
        optimise_label.setStyleSheet("color: black")
        optimise_label.setStyleSheet("background-color: white")
        optimise_label.setAlignment(Qt.AlignCenter)

        m_button = QPushButton('Montecarlo', self)
        m_button.setStyleSheet("color: white")
        m_button.setStyleSheet("background-color: #152053")
        m_button.resize(500, 100)
        m_button.move(1200, 0)
        m_button.clicked.connect(self.clicked_montecarlo)

        g_button = QPushButton('Graphs', self)
        g_button.setStyleSheet("color: white")
        g_button.setStyleSheet("background-color: #152053")
        g_button.resize(500, 100)
        g_button.move(1600, 0)
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
        self.setFixedSize(QSize(2000, 1000))
        self.setStyleSheet("background-color: white")
        self.montecarlo_nav_bar()
        self.run_montecarlo()
        self.monte_labels()

    def monte_labels(self):
        year_label = QLabel(self)
        year_label.resize(100, 50)
        year_label.move(100, 150)
        year_label.setText("Number of Iterations")
        year_label.setStyleSheet("color: black")
        year_label.setAlignment(Qt.AlignCenter)

        moutech_label = QLabel(self)
        moutech_label.resize(100, 50)
        moutech_label.move(100, 200)
        moutech_label.setText("Input Project ID")
        moutech_label.setStyleSheet("color: black")
        moutech_label.setAlignment(Qt.AlignCenter)

        self.iter_box = QLineEdit(self)
        self.iter_box.resize(100, 50)
        self.iter_box.move(200, 150)
        self.iter_box.setStyleSheet("color: black")
        self.iter_box.setAlignment(Qt.AlignCenter)

    def run_montecarlo(self):
        self.o_button = QPushButton('Run', self)
        self.o_button.setStyleSheet("color: white")
        self.o_button.setStyleSheet("background-color: #152053")
        self.o_button.resize(200, 50)
        self.o_button.move(1700, 700)
        self.o_button.clicked.connect(self.mc_inputs)

    def mc_inputs(self):
        run_mc(this_module.year, this_module.number_iter)

    def montecarlo_nav_bar(self):
        title_monte = QLabel(self)
        title_monte.resize(100, 50)
        title_monte.move(100, 100)
        title_monte.setText("MonteCarlo Analysis")
        title_monte.setStyleSheet("color: black")
        title_monte.setAlignment(Qt.AlignCenter)

        h_button = QPushButton('Home', self)
        h_button.setStyleSheet("color: white")
        h_button.setStyleSheet("background-color: #152053")
        h_button.resize(400, 100)
        h_button.move(0, 0)
        h_button.clicked.connect(self.clicked_home)

        p_button = QPushButton('Parameters', self)
        p_button.setStyleSheet("color: white")
        p_button.setStyleSheet("background-color: #152053")
        p_button.resize(400, 100)
        p_button.move(400, 0)
        p_button.clicked.connect(self.clicked_parameters)

        o_button = QPushButton('Optimise', self)
        o_button.setStyleSheet("color: white")
        o_button.setStyleSheet("background-color: #152053")
        o_button.resize(500, 100)
        o_button.move(800, 0)
        o_button.clicked.connect(self.clicked_optimise)

        monte_label = QLabel(self)
        monte_label.resize(400, 100)
        monte_label.move(1200, 0)
        monte_label.setText("Montecarlo")
        monte_label.setStyleSheet("color: black")
        monte_label.setAlignment(Qt.AlignCenter)
        monte_label.setStyleSheet("background-color: white")

        g_button = QPushButton('Graphs', self)
        g_button.setStyleSheet("color: white")
        g_button.setStyleSheet("background-color: #152053")
        g_button.resize(500, 100)
        g_button.move(1600, 0)
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
        self.setFixedSize(QSize(2000, 1000))
        self.setStyleSheet("background-color: white")
        self.graph_nav_bar()
        self.graph_labels()
        self.graph_buttons()

    def graph_labels(self):
        vary_label = QLabel(self)
        vary_label.resize(100, 50)
        vary_label.move(100, 150)
        vary_label.setText("Parameter to vary")
        vary_label.setStyleSheet("color: black")
        vary_label.setAlignment(Qt.AlignCenter)

        interest_label = QLabel(self)
        interest_label.resize(125, 50)
        interest_label.move(100, 250)
        interest_label.setText("Parameter of interest")
        interest_label.setStyleSheet("color: black")
        interest_label.setAlignment(Qt.AlignCenter)

        self.weather_check = QCheckBox("Weather", self)
        self.weather_check.resize(120, 150)
        self.weather_check.move(250, 100)
        self.weather_check.setStyleSheet("color: black")

        self.losses_check = QCheckBox("Losses", self)
        self.losses_check.resize(120, 150)
        self.losses_check.move(350, 100)
        self.losses_check.setStyleSheet("color: black")

        self.costs_check = QCheckBox("Costs", self)
        self.costs_check.resize(120, 150)
        self.costs_check.move(450, 100)
        self.costs_check.setStyleSheet("color: black")

        self.metric = QComboBox(self)
        self.metric.addItems(["NPV", "LCOE", "Cost", "Yield"])
        self.metric.resize(100, 50)
        self.metric.move(250, 250)
        self.metric.setStyleSheet("color: black")

    def graph_buttons(self):
        self.create_his = QCheckBox("Create Histogram", self)
        self.create_his.resize(120, 150)
        self.create_his.move(1000, 200)
        self.create_his.setStyleSheet("color: black")

        self.create_reg = QCheckBox("Create Regression", self)
        self.create_reg.resize(120, 150)
        self.create_reg.move(1000, 300)
        self.create_reg.setStyleSheet("color: grey")
        self.create_reg.setEnabled(False)

        self.create_scatter = QCheckBox("Calculate Scatter", self)
        self.create_scatter.resize(120, 150)
        self.create_scatter.move(1000, 400)
        self.create_scatter.setStyleSheet("color: grey")
        self.create_scatter.setEnabled(False)

        self.o_button = QPushButton('Run', self)
        self.o_button.setStyleSheet("color: white")
        self.o_button.setStyleSheet("background-color: #152053")
        self.o_button.resize(200, 50)
        self.o_button.move(1700, 700)
        self.o_button.clicked.connect(self.graph_inputs)

        self.calc_var = QCheckBox("Calculate Variance", self)
        self.calc_var.resize(120, 150)
        self.calc_var.move(1000, 100)
        self.calc_var.setStyleSheet("color: black")

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

    def graph_nav_bar(self):
        title_graphs = QLabel(self)
        title_graphs.resize(100, 50)
        title_graphs.move(100, 100)
        title_graphs.setText("Graphs")
        title_graphs.setStyleSheet("color: black")
        title_graphs.setAlignment(Qt.AlignCenter)

        h_button = QPushButton('Home', self)
        h_button.setStyleSheet("color: white")
        h_button.setStyleSheet("background-color: #152053")
        h_button.resize(400, 100)
        h_button.move(0, 0)
        h_button.clicked.connect(self.clicked_home)

        p_button = QPushButton('Parameters', self)
        p_button.setStyleSheet("color: white")
        p_button.setStyleSheet("background-color: #152053")
        p_button.resize(400, 100)
        p_button.move(400, 0)
        p_button.clicked.connect(self.clicked_parameters)

        o_button = QPushButton('Optimise', self)
        o_button.setStyleSheet("color: white")
        o_button.setStyleSheet("background-color: #152053")
        o_button.resize(500, 100)
        o_button.move(800, 0)
        o_button.clicked.connect(self.clicked_optimise)

        m_button = QPushButton('Montecarlo', self)
        m_button.setStyleSheet("color: white")
        m_button.setStyleSheet("background-color: #152053")
        m_button.resize(500, 100)
        m_button.move(1200, 0)
        m_button.clicked.connect(self.clicked_montecarlo)

        graph_label = QLabel(self)
        graph_label.resize(400, 100)
        graph_label.move(1600, 0)
        graph_label.setText("Graphs")
        graph_label.setAlignment(Qt.AlignCenter)
        graph_label.setStyleSheet("color: black")
        graph_label.setStyleSheet("background-color: white")

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
