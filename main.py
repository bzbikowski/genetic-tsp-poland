from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import sys
import os
import matplotlib.pyplot as plt
import gmplot.gmplot as gmplot
from lib.parser import Service_request
from lib.genetic.algorithm import Evolutionary


class MainFrame(QMainWindow):
    """This class implements main window for my Gui application"""
    def __init__(self):
        super(MainFrame, self).__init__()
        key = os.environ["API_KEY"]  # enter here yours key from Google Cloud Platform
        self.web_engine = None
        self.distance_array = None
        self.geocoding_array = None
        self.direction_array = None
        self.solver = None
        self.setup_gui()
        self.client = Service_request(api_key=key, parent=self)
        self.client.get_cities_position("data/cities.txt")
        self.client.get_distance_matrix("data/cities.txt")
        self.solve_shortest_path()
        # self.client.get_path_beetween_cities("Gdańsk", "Bydgoszcz")

    def setup_gui(self):
        """Create container for HTML file with map"""
        self.web_engine = QWebEngineView()
        self.setCentralWidget(self.web_engine)
        self.show()

    def ready_distance_array(self):
        self.distance_array = self.client.dist_array

    def ready_geocoding_array(self):
        self.geocoding_array = self.client.geo_array

    def ready_direction_array(self):
        self.direction_array = self.client.dir_points
        gmap = gmplot.GoogleMapPlotter(52.29661, 19.45500, 5)
        lat, lng = zip(*self.direction_array)
        gmap.plot(lat, lng)
        gmap.draw("dirs.html")

    def solve_shortest_path(self):
        self.solver = Evolutionary(self.distance_array)
        glob_min, min_values, glob_path = self.solver.start_algorithm(200, 1500, cross_chance=0.8, mutation_chance=0.08)
        print("The shortest path: {} km.".format(glob_min))
        self.plot_result(min_values, glob_path)

    def plot_result(self, min_values, glob_path):
        plt.plot(range(1501), min_values)
        plt.show()
        gmap = gmplot.GoogleMapPlotter(52.29661, 19.45500, 5)
        sorted_array = []
        for number in glob_path:
            sorted_array.append(self.geocoding_array[number])
        sorted_array.append(self.geocoding_array[glob_path[0]])
        lat, lng = zip(*sorted_array)
        gmap.plot(lat, lng)
        gmap.draw("map.html")
        self.web_engine.load(QUrl().fromLocalFile(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'map.html')))


if __name__ == "__main__":
    _app = QApplication(sys.argv)
    App = MainFrame()
    sys.exit(_app.exec_())
