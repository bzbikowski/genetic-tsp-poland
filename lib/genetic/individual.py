import random


class Individual:
    def __init__(self, genotype=None):
        if genotype is not None:
            # validate
            self.genotype = genotype
        else:
            self.genotype = []
        self.roulette_value = 0
        self.distance = 0

    def __radd__(self, other):
        return other + self.distance

    def __add__(self, other):
        return self.distance + other

    def __gt__(self, other):
        return self.distance > other.distance

    def generate_values(self, range_number):
        self.genotype = random.sample(range(range_number), k=range_number)

    def update_distance(self, max_dist):
        self.distance *= -1
        self.distance += max_dist + 100

    def calculate_roullete_part(self, sum_distance):
        return self.distance / sum_distance

    def set_roullete_part(self, part):
        self.roulette_value = part

    def insert_mutation(self):
        city_pos = random.randrange(0, 18)
        new_pos = random.randrange(0, 17)
        city = self.genotype.pop(city_pos)
        self.genotype.insert(new_pos, city)

    def calculate_distance(self, d_matrix):
        city_pop = -1
        starting_point = -1
        first_city = True
        for city in self.genotype:
            if first_city:
                starting_point = city
                first_city = False
            elif not first_city and self.distance == 0:
                self.distance += d_matrix[starting_point, city]
            else:
                self.distance += d_matrix[city_pop, city]
            city_pop = city
        self.distance += d_matrix[city_pop, starting_point]