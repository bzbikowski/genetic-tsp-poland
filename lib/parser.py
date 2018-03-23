import os
import sys
from PyQt5.QtCore import QUrl, QJsonDocument, QTimer, QThread
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from lib.distance_matrix import Distance_matrix
import numpy as np
import codecs
import time
import math


class Service_request(QThread):
    def __init__(self, api_key, parent):
        super().__init__(parent)
        self.parent = parent
        self._validate_api_key(api_key)
        self._busy = False
        self.redirect_fun = None
        self.addicional_args = []
        self.cluster_i_index = 0
        self.cluster_j_index = 0
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self._finished_getting_reply)

    def get_request(self, request):
        self.manager.get(request)

    def read_cities_from_file(self, path):
        cities = []
        rpath = "./" + path
        with codecs.open(rpath, "r", "utf-8") as file:
            lines = file.readlines()
            for line, city in enumerate(lines):
                if line == len(lines) - 1:
                    cities.append(city.split("/n")[0])
                else:
                    cities.append(city.split("/n")[0][:-1])
        return cities

    def get_cities_position(self, path):
        def make_request(cities):
            url_text = url_header + "&address=" + cities[self.geo_city_index] + "&key=" + self.key
            if self.geo_city_index == len(cities) - 1:
                self.addicional_args.append([True])
            else:
                self.addicional_args.append([False])
            url = QUrl(url_text)
            nr = QNetworkRequest()
            nr.setUrl(url)
            self.redirect_fun = self._geocoding
            self._busy = True
            self.get_request(nr)
            self.geo_city_index += 1
            if self.geo_city_index == len(cities):
                self.timer.stop()

        url_header = "https://maps.googleapis.com/maps/api/geocode/json?language=pl"
        cities = self.read_cities_from_file(path)
        while self._busy:
            pass
        if os.path.exists("./data/tmp_geo.txt"):
            self.geo_array = np.loadtxt("./data/tmp_geo.txt")
            if len(self.geo_array) == len(cities):
                self.parent.ready_geocoding_array()
            else:
                print("Lenght of array in file 'tmp_geo.txt' and cities in loaded data doesn't match.")
        else:
            self.geo_array = []
            self.geo_city_index = 0
            make_request(cities)
            self.timer = QTimer()
            self.timer.setInterval(1000)
            self.timer.timeout.connect(lambda: make_request(cities))
            self.timer.start()

    def get_distance_matrix(self, path):
        def make_request(cit):
            org_cities = "|".join(cit[self.cluster_i_index])
            dest_cities = "|".join(cit[self.cluster_j_index])
            if self.cluster_i_index == len(cit) - 1 and self.cluster_j_index == len(cit) - 1:
                self.addicional_args.append([self.cluster_i_index, self.cluster_j_index, True])
            else:
                self.addicional_args.append([self.cluster_i_index, self.cluster_j_index, False])
            url_text = url_header + "&origins=" + org_cities + "&destinations=" + dest_cities + "&key=" + self.key
            url = QUrl(url_text)
            nr = QNetworkRequest()
            nr.setUrl(url)
            self.redirect_fun = self._distance_matrix
            self._busy = True
            self.get_request(nr)
            self.cluster_j_index += 1
            if self.cluster_j_index == len(cit):
                self.cluster_j_index = 0
                self.cluster_i_index += 1
            if self.cluster_i_index == len(cit):
                self.timer.stop()
                self.cluster_i_index = 0
                self.cluster_j_index = 0
        cities = self.read_cities_from_file(path)
        url_header = "https://maps.googleapis.com/maps/api/distancematrix/json?language=pl"
        while self._busy:
            pass
        if os.path.exists("./data/tmp_dist.txt"):
            self.dist_array = np.loadtxt("./data/tmp_dist.txt")
            if len(self.dist_array) == len(cities):
                self.parent.ready_distance_array()
            else:
                print("Lenght of array in file 'tmp_dist.txt' and cities in loaded data doesn't match.")
        else:
            clusters = [[] for _ in range(math.ceil(len(cities) / 10))]
            cluster_index = 0
            for i, city in enumerate(cities):
                if i > 0 and i % 10 == 0:
                    cluster_index += 1
                clusters[cluster_index].append(city)
            self.dist_array = np.zeros((len(cities), len(cities)))
            self.cluster_i_index = 0
            self.cluster_j_index = 0
            self.timer = QTimer()
            make_request(clusters)
            self.timer = QTimer()
            self.timer.setInterval(5000)
            self.timer.timeout.connect(lambda: make_request(clusters))
            self.timer.start()

    def _finished_getting_reply(self, reply):
        error = reply.error()
        if error == QNetworkReply.NoError:
            bytes_string = reply.readAll()
            document = QJsonDocument().fromJson(bytes_string)
            args = self.addicional_args.pop(len(self.addicional_args)-1)
            if not document.isNull():
                self.redirect_fun(document, args)
                self._busy = False
            else:
                print("error")
        else:
            print("Error occured: ", error)
            print(reply.errorString())

    def _distance_matrix(self, document, args):
        cluster = (args[0], args[1])
        final = args[2]
        print(document["status"].toString())
        for i, row in enumerate(document["rows"].toArray()):
            for j, element in enumerate(row["elements"].toArray()):
                tmp = element["distance"]["value"].toInt()
                self.dist_array[cluster[0]*10+i][cluster[1]*10+j] = tmp
        if final:
            self.dist_array /= 1000
            np.savetxt("./data/tmp_dist.txt", self.dist_array)
            self.parent.ready_distance_array()

    def _geocoding(self, document, args):
        end = args[0]
        print(document["status"].toString())
        for i, result in enumerate(document["results"].toArray()):
            print(result["formatted_address"].toString())
            geo = result["geometry"]
            loc = geo["location"]
            self.geo_array.append((loc["lat"].toDouble(), loc["lng"].toDouble()))
        if end:
            np.savetxt("./data/tmp_geo.txt", self.geo_array)
            self.parent.ready_geocoding_array()

    def _validate_api_key(self, api_key):
        self.key = api_key

    def get_path_beetween_cities(self, city1, city2):
        url_header = "https://maps.googleapis.com/maps/api/directions/json?language=pl"
        url_text = url_header + "&origin=" + city1 + "&destination=" + city2 + "&key=" + self.key
        url = QUrl(url_text)
        nr = QNetworkRequest()
        nr.setUrl(url)
        self.dir_points = []
        self.addicional_args.append([None])
        self.redirect_fun = self._directions
        self._busy = True
        self.get_request(nr)
        pass

    def _directions(self, document, args):
        print(document["status"].toString())
        for i, route in enumerate(document["routes"].toArray()):
            print(f"Route nr {i}")
            for j, path in enumerate(route["legs"].toArray()):
                print(f"Path nr {j}")
                for k, step in enumerate(path["steps"].toArray()):
                    print(f"Step nr {k}")
                    start_loc = step["start_location"]
                    lat_start_loc = start_loc["lat"].toDouble()
                    lng_start_loc = start_loc["lng"].toDouble()
                    self.dir_points.append([lat_start_loc, lng_start_loc])
        self.parent.ready_direction_array()