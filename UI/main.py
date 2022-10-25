import sys
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QLabel, QLineEdit


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

        dc_box = QLineEdit(self)
        dc_box.resize(100, 50)
        dc_box.move(200, 150)
        dc_box.setStyleSheet("color: black")
        dc_box.setAlignment(Qt.AlignCenter)

        nzones_box = QLineEdit(self)
        nzones_box.resize(100, 50)
        nzones_box.move(200, 200)
        nzones_box.setStyleSheet("color: black")
        nzones_box.setAlignment(Qt.AlignCenter)

        zarea_box = QLineEdit(self)
        zarea_box.resize(100, 50)
        zarea_box.move(200, 250)
        zarea_box.setStyleSheet("color: black")
        zarea_box.setAlignment(Qt.AlignCenter)

        tmodel_box = QLineEdit(self)
        tmodel_box.resize(100, 50)
        tmodel_box.move(200, 300)
        tmodel_box.setStyleSheet("color: black")
        tmodel_box.setAlignment(Qt.AlignCenter)

        elimit_box = QLineEdit(self)
        elimit_box.resize(100, 50)
        elimit_box.move(600, 150)
        elimit_box.setStyleSheet("color: black")
        elimit_box.setAlignment(Qt.AlignCenter)

        scapacity_box = QLineEdit(self)
        scapacity_box.resize(100, 50)
        scapacity_box.move(600, 200)
        scapacity_box.setStyleSheet("color: black")
        scapacity_box.setAlignment(Qt.AlignCenter)

        sprice_box = QLineEdit(self)
        sprice_box.resize(100, 50)
        sprice_box.move(600, 250)
        sprice_box.setStyleSheet("color: black")
        sprice_box.setAlignment(Qt.AlignCenter)

        drate_box = QLineEdit(self)
        drate_box.resize(100, 50)
        drate_box.move(600, 300)
        drate_box.setStyleSheet("color: black")
        drate_box.setAlignment(Qt.AlignCenter)

    def create_project(self):
        h_button = QPushButton('Home', self)
        h_button.setStyleSheet("color: white")
        h_button.setStyleSheet("background-color: #152053")
        h_button.resize(400, 100)
        h_button.move(0, 0)
        h_button.clicked.connect(self.clicked_home)

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

    def clicked_create(self):
        return

class OptimiseWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UNSW LCOE Model")
        self.setFixedSize(QSize(2000, 1000))
        self.setStyleSheet("background-color: white")
        self.optimise_nav_bar()

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

    def montecarlo_nav_bar(self):
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

    def graph_nav_bar(self):
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
window = ParametersWindow()
window.show()

app.exec()
