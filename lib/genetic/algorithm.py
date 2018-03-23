from lib.genetic.individual import Individual
import random


class Evolutionary:
    def __init__(self, distance_array):
        self.data_array = distance_array

    def start_algorithm(self, pop_lenght, max_gen, cross_chance, mutation_chance):
        current_gen = max_gen
        population = self.create_population(pop_lenght)
        glob_value = 99999999999999
        min_values = []
        glob_genotype = None
        while current_gen >= 0:
            if current_gen % 10 == 0:
                print("Genetation -> {}".format(current_gen))
            ###### SELECTION ######
            loc_value, loc_genotype = self.find_minimum(population)
            if loc_value < glob_value:
                glob_value = loc_value
                glob_genotype = loc_genotype
            min_values.append(glob_value)
            maximum_dist = self.find_maxiumum(population)
            for ind in population:
                ind.update_distance(maximum_dist)
            all_dist = sum(population)
            population.sort()
            roullete_sum = 0
            for ind in population:
                part = ind.calculate_roullete_part(all_dist)
                roullete_sum += part
                ind.set_roullete_part(roullete_sum)
            parents = []
            for _ in range(pop_lenght):
                random_number = random.random()
                for i in range(len(population) - 1):
                    if i == 0 and 0 <= random_number <= population[i].roulette_value:
                        parents.append(population[i])
                        break
                    elif population[i-1].roulette_value < random_number <= population[i].roulette_value:
                        parents.append(population[i])
                        break
                    elif i == pop_lenght - 1 and population[i].roulette_value <= random_number <= 1:
                        parents.append(population[i])
                        break
            ##### CROSSOVER ######
            childs = self.OX_crossover(parents, cross_chance)
            ##### MUTATION #####
            for child in childs:
                if random.random() < mutation_chance:
                    child.insert_mutation()
                child.calculate_distance(self.data_array)
            population = childs
            current_gen -= 1
        return glob_value, min_values, glob_genotype

    def create_population(self, lenght):
        population = []
        for _ in range(lenght):
            ind = Individual()
            ind.generate_values(len(self.data_array))
            ind.calculate_distance(self.data_array)
            population.append(ind)
        return population

    def find_maxiumum(self, population):
        maximum = -1
        for ind in population:
            if ind.distance > maximum:
                maximum = ind.distance
        return maximum

    def find_minimum(self, population):
        minimum = 9999999999
        genotype = None
        for ind in population:
            if ind.distance < minimum:
                minimum = ind.distance
                genotype = ind.genotype
        return minimum, genotype

    def OX_crossover(self, parents, cross_chance):
        childs = []
        random.shuffle(parents)
        while len(parents) > 1:
            p1 = parents.pop(0)
            p2 = parents.pop(0)
            if cross_chance < random.random():
                childs.append(Individual(p1.genotype))
                childs.append(Individual(p2.genotype))
            else:
                while True:
                    c1 = random.randrange(0, len(self.data_array))
                    c2 = random.randrange(0, len(self.data_array))
                    if not c1 == c2:
                        if c1 > c2:
                            c1, c2 = c2, c1
                        break
                lenght = len(p1.genotype) - c2
                ch1_genotype = p1.genotype[c1:c2]
                ch2_genotype = p2.genotype[c1:c2]

                p1_seq = p1.genotype[c2:] + p1.genotype[:c2]
                p2_seq = p2.genotype[c2:] + p2.genotype[:c2]

                p1_ffe = [i for i in p2_seq if i not in ch1_genotype]
                p2_ffe = [i for i in p1_seq if i not in ch2_genotype]

                for _ in range(lenght):
                    ch1_genotype.append(p1_ffe.pop(0))
                index = 0
                while len(p1_ffe) > 0:
                    ch1_genotype.insert(index, p1_ffe.pop(0))
                    index += 1

                for _ in range(lenght):
                    ch2_genotype.append(p2_ffe.pop(0))
                index = 0
                while len(p2_ffe) > 0:
                    ch2_genotype.insert(index, p2_ffe.pop(0))
                    index += 1

                childs.append(Individual(ch1_genotype))
                childs.append(Individual(ch2_genotype))
        return childs

