import copy
import os
import time

import maps
from map_loader import MapLoader
from maps import Map
from maps import GWMap
from maps import SoilMap
from maps import LandUseMap
from maps import ParcelMap
from maps import ElevationMap
from maps import DetailedLandUseMap
from maps import RunoffCoMap
from maps import AdvancedLandUseMap


map_loader = MapLoader()


class SuitableAreaBasedOnGW:
    def get_suitable_areas(self, GW_ascii_map_name, user_limit):
        self.gw_map = map_loader.load_map(GWMap, GW_ascii_map_name)
        self.output = Map()
        self.output.set_config(self.gw_map.map)
        # self.output.no_data_value = 0
        for i in range(len(self.gw_map.map.matrix)):
            self.output.matrix.append([])
            for pixel in self.gw_map.map.matrix[i]:
                if pixel == self.gw_map.map.no_data_value:
                    self.output.matrix[i].append(self.output.no_data_value)
                elif pixel > user_limit:
                    self.output.matrix[i].append(0)
                else:
                    self.output.matrix[i].append(1)
        return self.output


class SuitableSoilArea:
    def get_suitable_areas(self, soil_ascii_map_name, land_use_ascii_map_name, user_soil_number):
        self.soil_map = map_loader.load_map(SoilMap, soil_ascii_map_name)
        self.land_use_map = map_loader.load_map(LandUseMap, land_use_ascii_map_name)
        self.output = Map()
        self.output.set_config(self.soil_map.map)
        for i in range(len(self.soil_map.map.matrix)):
            self.output.matrix.append([])
            for j in range(len(self.soil_map.map.matrix[i])):
                if self.soil_map.map.matrix[i][j] == self.soil_map.map.no_data_value:
                    self.output.matrix[i].append(self.output.no_data_value)
                elif self.soil_map.map.matrix[i][j] != user_soil_number:
                    self.output.matrix[i].append(0)
                elif self.land_use_map.map.matrix[i][j] == LandUseMap.VALUES.URBON_AND_BUILT_UP or \
                        self.land_use_map.map.matrix[i][j] == LandUseMap.VALUES.WATER_BODIES:
                    self.output.matrix[i].append(0)
                else:
                    self.output.matrix[i].append(1)
        return self.output


class FindingRiperianZone:
    def __init__(self):
        self.land_use_map = LandUseMap()
        self.pixel_distance = 0
        self.output= Map()
        self.land_use_tuple = Map()

    def get_riperian_zone(self, land_use_ascii_map_name, user_distance):
        self.land_use_map = map_loader.load_map(LandUseMap, land_use_ascii_map_name)
        self.pixel_distance = user_distance / self.land_use_map.map.cell_size
        if int(self.pixel_distance) != self.pixel_distance:
            self.pixel_distance = int(self.pixel_distance) + 1
        self.pixel_distance = int(self.pixel_distance)
        self.output = Map()
        self.output.set_config(self.land_use_map.map)
        self.build_basic_output_2()
        landuse_map = self.land_use_map.map
        # t0 = time.time()
        for i in range(len(landuse_map.matrix)):
            for j in range(len(landuse_map.matrix[i])):
                if landuse_map.matrix[i][j] != landuse_map.no_data_value:
                    self.output.matrix[i][j] = 0
        for i in range(len(landuse_map.matrix)):
            for j in range(len(landuse_map.matrix[i])):
                if landuse_map.matrix[i][j] == LandUseMap.VALUES.WATER_BODIES:
                    self.highlight_nearby_pixels(i, j)
        return self.output

    def build_basic_output_matrix(self):
        self.output.matrix = [[self.output.no_data_value]*self.output.n_cols]*self.output.n_rows

    def highlight_nearby_pixels(self, i, j):
        landuse_map = self.land_use_map.map
        for x in range(i - self.pixel_distance, i + self.pixel_distance):
            for y in range(j - self.pixel_distance, j + self.pixel_distance):
                if landuse_map.matrix[x][y] != LandUseMap.VALUES.WATER_BODIES and \
                    landuse_map.matrix[x][y] != LandUseMap.VALUES.URBON_AND_BUILT_UP and \
                        landuse_map.matrix[x][y] != landuse_map.no_data_value:
                    self.output.matrix[x][y] = 1

    def get_riperian_zone2(self, land_use_ascii_map_name, user_distance):
        self.land_use_map = map_loader.load_map(LandUseMap, land_use_ascii_map_name)
        self.pixel_distance = user_distance / self.land_use_map.map.cell_size
        if int(self.pixel_distance) != self.pixel_distance:
            self.pixel_distance = int(self.pixel_distance) + 1
        self.pixel_distance = int(self.pixel_distance)
        self.output = Map()
        self.output.set_config(self.land_use_map.map)
        self.build_basic_output_matrix()
        landuse_map = self.land_use_map.map
        # t0 = time.time()
        for i in range(len(landuse_map.matrix)):
            for j in range(len(landuse_map.matrix[i])):
                if landuse_map.matrix[i][j] == landuse_map.no_data_value:
                    continue
                elif landuse_map.matrix[i][j] == LandUseMap.VALUES.WATER_BODIES or \
                    landuse_map.matrix[i][j] == LandUseMap.VALUES.URBON_AND_BUILT_UP:
                    self.output.matrix[i][j] = 0
                elif self.pixel_has_water_next_to_it(i, j):
                    self.output.matrix[i][j] = 1
                else:
                    self.output.matrix[i][j] = 0
        return self.output

    def build_basic_output_2(self):
        for i in range(len(self.land_use_map.map.matrix)):
            self.output.matrix.append([])
            for j in range(len(self.land_use_map.map.matrix[i])):
                self.output.matrix[i].append(self.output.no_data_value)

    def pixel_has_water_next_to_it(self, i, j):
        landuse_map = self.land_use_map.map
        for x in range(i - self.pixel_distance, i + self.pixel_distance):
            for y in range(j - self.pixel_distance, j + self.pixel_distance):
                if x == i and y == j:
                    continue
                if landuse_map.matrix[x][y] == LandUseMap.VALUES.WATER_BODIES:
                    return True
        return False


class RoofAreaCalculator:
    def __init__(self):
        self.land_use_map = LandUseMap()
        self.parcel_map = ParcelMap()
        self.output = {}
        self.roof_pixels = {}

    def get_roof_areas(self, land_use_ascii_map_name, parcel_ascii_map_name):
        self.init_maps(land_use_ascii_map_name, parcel_ascii_map_name)
        for i in range(len(self.parcel_map.map.matrix)):
            for j in range(len(self.parcel_map.map.matrix[i])):
                if self.coordination_is_roof(i, j):
                    self.increase_roof_pixels(i, j)
        for key in self.roof_pixels.keys():
            self.output[key] = self.roof_pixels[key] * self.parcel_map.map.cell_size
        return self.output

    def init_maps(self, land_use_ascii_map_name, parcel_ascii_map_name):
        self.land_use_map = map_loader.load_map(LandUseMap, land_use_ascii_map_name)
        self.parcel_map = map_loader.load_map(ParcelMap, parcel_ascii_map_name)
        self.output = {}
        self.roof_pixels = {}

    def coordination_is_roof(self, i, j):\
        return self.parcel_map.map.matrix[i][j] != self.parcel_map.map.no_data_value

    def increase_roof_pixels(self, i, j):
        roof_number = self.parcel_map.map.matrix[i][j]
        num_of_pixels = self.roof_pixels.get(roof_number, 0)
        self.roof_pixels[roof_number] = num_of_pixels + 1

    def build_map_for_output(self, file_name):
        file = open('maps/' + file_name, 'w+')
        str_data = ""
        str_data += self.parcel_map.map.get_config_string()
        str_data += str(self.output)
        file.write(str_data)


class FlatRoofFinder:
    def __init__(self):
        self.max_flat_roof_number = 0
        self.flat_roofs = Map()
        self.output = Map()
        self.land_use_map = LandUseMap()
        self.parcel_map = ParcelMap()
        self.dem_map = ElevationMap()
        self.minimum_valuable_area = 10
        self.maximum_possible_slope = 10
        self.roof_number_to_roofs = {}

    def get_flat_roofs_by_slope_map(self, land_use_ascii_map_name, parcel_ascii_map_name, slope_dot_map_name):
        pass

    def get_flat_roofs_by_elevation_map(self, land_use_ascii_map_name,
                                        parcel_ascii_map_name,
                                        dem_ascii_map_name,
                                        minimum_valuable_area,
                                        maximum_possible_slope):
        # t1 = time.time()
        self.init_variables_by_elevation_map(land_use_ascii_map_name,
                                             parcel_ascii_map_name,
                                             dem_ascii_map_name,
                                             minimum_valuable_area,
                                             maximum_possible_slope)
        # print('init:', time.time() - t1)
        # t2 = time.time()
        self.build_flat_roofs_map()
        # print('build:', time.time() - t2)
        # t3 = time.time()
        self.calculate_valuable_flat_roofs_by_area()
        # print('calculate:', time.time() - t3)
        return self.output

    def init_variables_by_elevation_map(self, land_use_ascii_map_name,
                                        parcel_ascii_map_name,
                                        dem_ascii_map_name,
                                        minimum_valuable_area,
                                        maximum_possible_slope):
        self.max_flat_roof_number = 0

        self.land_use_map = map_loader.load_map(LandUseMap, land_use_ascii_map_name)
        self.parcel_map= map_loader.load_map(ParcelMap, parcel_ascii_map_name)
        self.dem_map = map_loader.load_map(ElevationMap, dem_ascii_map_name)

        self.flat_roofs = Map()
        self.output = Map()
        self.flat_roofs.set_config(self.land_use_map.map)
        self.output.set_config(self.flat_roofs)
        for i in range(len(self.land_use_map.map.matrix)):
            self.flat_roofs.matrix.append([])
            self.output.matrix.append([])
            for j in range(len(self.land_use_map.map.matrix[i])):
                self.flat_roofs.matrix[i].append(self.flat_roofs.no_data_value)
                self.output.matrix[i].append(self.output.no_data_value)

        self.minimum_valuable_area = minimum_valuable_area
        self.maximum_possible_slope = maximum_possible_slope

        self.roof_number_to_roofs = {}

    def build_flat_roofs_map(self):
        landuse = self.land_use_map.map
        parcel = self.parcel_map.map
        for i in range(len(self.flat_roofs.matrix)):
            for j in range(len(self.flat_roofs.matrix[i])):
                if landuse.matrix[i][j] != LandUseMap.VALUES.URBON_AND_BUILT_UP or \
                        parcel.matrix[i][j] == parcel.no_data_value:
                    # if landuse.matrix[i][j] == LandUseMap.VALUES.URBON_AND_BUILT_UP or \
                    #         parcel.matrix[i][j] != parcel.no_data_value:
                    continue
                # pixel[i][j] is a roof
                # print('roof:)')
                # print('i:', i, 'j:', j)
                if self.flat_roofs.matrix[i][j] == self.flat_roofs.no_data_value:
                    # print('i am girvin:D')
                    self.set_new_number_for_roof(i, j)
                # else:
                #     print(self.flat_roofs.matrix[i][j])
                for x in range(i - 1, i + 2):
                    for y in range(j - 1, j + 2):
                        # try:
                        #     print('x:', x, 'y:', y)
                        # except:
                        #     print('x o y out of index:D')
                        if x == i and y == j:
                            # print('khodam:D')
                            continue
                        if x < 0 or y < 0 or x >= self.flat_roofs.n_rows or y >= self.flat_roofs.n_cols:
                            # print('roof on gooshe:D')
                            continue
                        # now pixel[x][y] exist!
                        if landuse.matrix[x][y] != LandUseMap.VALUES.URBON_AND_BUILT_UP or \
                                parcel.matrix[x][y] == parcel.no_data_value:
                            # print('edge roof:D')
                            continue
                        # now pixel[x][y] is a roof
                        if not self.pixels_are_in_the_same_range(i, j, x, y):
                            # print('near roof not in same range')
                            continue
                        # now pixel[i][j] and pixel[x][y] are next to each other and are flat
                        if self.flat_roofs.matrix[x][y] == self.flat_roofs.matrix[i][j]:
                            # print('all the same chib:D')
                            continue
                        if self.flat_roofs.matrix[x][y] == self.flat_roofs.no_data_value:
                            # print('new near girvin roof:D')
                            self.set_new_pixel_with_new_range(x, y, i, j)
                        else:
                            # print('chib roof:D')
                            self.set_all_pixels_in_new_range_with_ones_in_old_range(i, j, x, y)
                # os.system('pause')

    def set_new_number_for_roof(self, i, j):
        self.max_flat_roof_number += 1
        self.roof_number_to_roofs[self.max_flat_roof_number] = []
        self.roof_number_to_roofs[self.max_flat_roof_number].append({'x': i, 'y': j})
        self.flat_roofs.matrix[i][j] = self.max_flat_roof_number

    def pixels_are_in_the_same_range(self, i, j, x, y):
        if abs(self.dem_map.map.matrix[i][j] - self.dem_map.map.matrix[x][y]) < self.maximum_possible_slope:
            return True
        return False

    def set_new_pixel_with_new_range(self, x, y, i, j):
        # print('old girvin:', self.flat_roofs.matrix[x][y])
        self.flat_roofs.matrix[x][y] = self.flat_roofs.matrix[i][j]
        # print('new chib:D:', self.flat_roofs.matrix[x][y])
        # print('old roof:', self.roof_number_to_roofs[self.flat_roofs.matrix[x][y]])
        self.roof_number_to_roofs[self.flat_roofs.matrix[x][y]].append({'x': x, 'y': y})
        # print('new roof:', self.roof_number_to_roofs[self.flat_roofs.matrix[x][y]])

    def set_all_pixels_in_new_range_with_ones_in_old_range(self, i, j, x, y):
        roof_number_that_should_be_deleted = self.flat_roofs.matrix[i][j]
        # print('deleted roof number:', roof_number_that_should_be_deleted)
        main_roof_number = self.flat_roofs.matrix[x][y]
        # print('main roof number:', main_roof_number)
        roofs_that_should_go_to_main_roof_number = self.roof_number_to_roofs[roof_number_that_should_be_deleted]
        # print('ed up roofs:', roofs_that_shoud_go_to_main_roof_number)
        # print('main roofs before:', self.roof_number_to_roofs[main_roof_number])
        for roof in roofs_that_should_go_to_main_roof_number:
            self.flat_roofs.matrix[roof['x']][roof['y']] = main_roof_number
            self.roof_number_to_roofs[main_roof_number].append(roof)
        # print('main roofs after:', self.roof_number_to_roofs[main_roof_number])
        self.roof_number_to_roofs[roof_number_that_should_be_deleted] = []
        # print('ed up number:', self.roof_number_to_roofs[roof_number_that_should_be_deleted])

    def calculate_valuable_flat_roofs_by_area(self):
        minimum_pixels_to_be_useful = self.minimum_valuable_area / (self.output.cell_size ** 2)
        # print('num:', minimum_pixels_to_be_useful)
        # t = 0
        # i = 0
        # for key in self.roof_number_to_roofs:
        #     # print(len(self.roof_number_to_roofs[key]))
        #     if len(self.roof_number_to_roofs[key]) > 0:
        #         # print('t yes')
        #         t += 1
        #     if len(self.roof_number_to_roofs[key]) >= minimum_pixels_to_be_useful:
        #         # print('i yes')
        #         i += 1
        # print('t:', t)
        # print('i:', i)
        tmp_number_to_roof = copy.deepcopy(self.roof_number_to_roofs)
        for key in self.roof_number_to_roofs:
            # print('flat roof number', key, ':')
            # print(self.roof_number_to_roofs[key])
            # print('len is:', len(self.roof_number_to_roofs[key]))
            if len(self.roof_number_to_roofs[key]) < minimum_pixels_to_be_useful:
                del tmp_number_to_roof[key]  # not so sure about it!
                continue
            # flat roof size is good
            # print(key, 'added:)')
            for roof in self.roof_number_to_roofs[key]:
                # print('before output number i:', roof['x'], 'j:', roof['y'], 'was: ', self.output.matrix[roof['x']][roof['y']])
                self.output.matrix[roof['x']][roof['y']] = key
                # print('now output number i:', roof['x'], 'j:', roof['y'], 'is: ', self.output.matrix[roof['x']][roof['y']])
            # os.system('pause')
        self.roof_number_to_roofs = tmp_number_to_roof


class RoadFinder :
    def __init__(self):
        self.detailed_landuse_map = DetailedLandUseMap()
        self.output = Map()

    def get_detailed_landuse_map(self, detailed_landuse_map_ascii):
        self.detailed_landuse_map = map_loader.load_map(DetailedLandUseMap, detailed_landuse_map_ascii)
        detailed_landuse_map = self.detailed_landuse_map.map
        self.build_basic_output()
        for i in range(len(detailed_landuse_map.matrix)):
            for j in range(len(detailed_landuse_map.matrix[i])):
                if detailed_landuse_map.matrix[i][j] == detailed_landuse_map.no_data_value:
                    continue
                if detailed_landuse_map.mطططططططatrix[i][j] == DetailedLandUseMap.VALUES.Asphalt:
                    self.output.matrix[i][j] = 1
                else:
                    self.output.matrix[i][j] = 0
        return self.output

    def build_basic_output(self):
        for i in range(len(self.detailed_landuse_map.map.matrix)):
            self.output.matrix.append([])
            for j in range(len(self.detailed_landuse_map.map.matrix[i])):
                self.output.matrix[i].append(self.output.no_data_value)


class RunoffCoefficient:
    def __init__(self):
        self.runoff_coefficient_map = RunoffCoMap()
        self.output = Map()

    def get_runoff_coefficient_map(self, runoff_coefficient_map_ascii, user_limit):
        self.runoff_coefficient_map = map_loader.load_map(RunoffCoefficient, runoff_coefficient_map_ascii)
        runoff_coefficient_map = self.runoff_coefficient_map.map
        self.build_basic_output()
        for i in range(len(runoff_coefficient_map.matrix)):
            for j in range(len(runoff_coefficient_map.matrix[i])):
                if runoff_coefficient_map.matrix[i][j] == runoff_coefficient_map.no_data_value:
                    if runoff_coefficient_map.matrix[i][j] >= user_limit:
                        self.output.matrix[i][j] = 1
                    else:
                        self.output.matrix[i][j] = 0
        return self.output

    def build_basic_output(self):
        for i in range(len(self.runoff_coefficient_map.map.matrix)):
            self.output.matrix.append([])
            for j in range(len(self.runoff_coefficient_map.map.matrix[i])):
                self.output.matrix[i].append(self.output.no_data_value)


class RainGardenFinder:
    def __init__(self):
        self.list_of_acceptable_land_use_parts = [
            LandUseMap.VALUES.URBON_AND_BUILT_UP,
            LandUseMap.VALUES.WATER_BODIES
        ]

        self.max_rain_garden_id = 0
        self.rain_gardens = Map()
        self.output = Map()
        self.land_use_map = LandUseMap()
        self.minimum_valuable_area = 10
        self.rain_garden_ids_to_pixels = {}

    def get_rain_gardens(self, land_use_ascii_map_name, minimum_valuable_area):
        # t1 = time.time()
        self.init_variables(land_use_ascii_map_name, minimum_valuable_area)
        # print('init:', time.time() - t1)
        # t2 = time.time()
        self.build_rain_garden_map()
        # print('build:', time.time() - t2)
        # t3 = time.time()
        self.calculate_valuable_rain_gardens_by_area()
        # print('calculate:', time.time() - t3)
        return self.output

    def init_variables(self, land_use_ascii_map_name, minimum_valuable_area):
        self.max_rain_garden_id = 0

        self.land_use_map = map_loader.load_map(LandUseMap, land_use_ascii_map_name)
        self.rain_gardens = Map()
        self.output = Map()
        self.rain_gardens.set_config(self.land_use_map.map)
        self.output.set_config(self.rain_gardens)
        for i in range(len(self.land_use_map.map.matrix)):
            self.rain_gardens.matrix.append([])
            self.output.matrix.append([])
            for j in range(len(self.land_use_map.map.matrix[i])):
                self.rain_gardens.matrix[i].append(self.rain_gardens.no_data_value)
                self.output.matrix[i].append(self.output.no_data_value)

        self.minimum_valuable_area = minimum_valuable_area

        self.rain_garden_ids_to_pixels = {}

    def build_rain_garden_map(self):
        landuse = self.land_use_map.map
        for i in range(len(self.rain_gardens.matrix)):
            for j in range(len(self.rain_gardens.matrix[i])):
                if landuse.matrix[i][j] == landuse.no_data_value:
                    continue
                if landuse.matrix[i][j] not in self.list_of_acceptable_land_use_parts:
                    self.rain_gardens.matrix[i][j] = 0
                    continue
                # pixel[i][j] is a roof
                # print('roof:)')
                # print('i:', i, 'j:', j)
                if self.rain_gardens.matrix[i][j] == self.rain_gardens.no_data_value:
                    # print('i am girvin:D')
                    self.set_new_id_for_garden(i, j)
                # else:
                #     print(self.flat_roofs.matrix[i][j])
                for x in range(i - 1, i + 2):
                    for y in range(j - 1, j + 2):
                        # try:
                        #     print('x:', x, 'y:', y)
                        # except:
                        #     print('x o y out of index:D')
                        if x == i and y == j:
                            # print('khodam:D')
                            continue
                        if x < 0 or y < 0 or x >= self.rain_gardens.n_rows or y >= self.rain_gardens.n_cols:
                            # print('roof on gooshe:D')
                            continue
                        # now pixel[x][y] exist!
                        if landuse.matrix[x][y] not in self.list_of_acceptable_land_use_parts:
                            # print('edge roof:D')
                            continue
                        # now pixel[x][y] is a rain garden
                        if self.rain_gardens.matrix[x][y] == self.rain_gardens.matrix[i][j]:
                            # print('all the same chib:D')
                            continue
                        if self.rain_gardens.matrix[x][y] == self.rain_gardens.no_data_value:
                            # print('new near girvin roof:D')
                            self.set_new_pixel_with_new_range(x, y, i, j)
                        else:
                            # print('chib roof:D')
                            self.set_all_pixels_in_new_range_with_ones_in_old_range(i, j, x, y)
                # os.system('pause')

    def set_new_id_for_garden(self, i, j):
        self.max_rain_garden_id += 1
        self.rain_gardens.matrix[i][j] = self.max_rain_garden_id
        self.rain_garden_ids_to_pixels[self.max_rain_garden_id] = []
        self.rain_garden_ids_to_pixels[self.max_rain_garden_id].append({'x': i, 'y': j})

    def set_new_pixel_with_new_range(self, x, y, i, j):
        # print('old girvin:', self.flat_roofs.matrix[x][y])
        self.rain_gardens.matrix[x][y] = self.rain_gardens.matrix[i][j]
        # print('new chib:D:', self.flat_roofs.matrix[x][y])
        # print('old roof:', self.roof_number_to_roofs[self.flat_roofs.matrix[x][y]])
        self.rain_garden_ids_to_pixels[self.rain_gardens.matrix[x][y]].append({'x': x, 'y': y})
        # print('new roof:', self.roof_number_to_roofs[self.flat_roofs.matrix[x][y]])

    def set_all_pixels_in_new_range_with_ones_in_old_range(self, i, j, x, y):
        rain_garden_number_that_should_be_deleted = self.rain_gardens.matrix[i][j]
        # print('deleted roof number:', roof_number_that_should_be_deleted)
        main_rain_garden_number = self.rain_gardens.matrix[x][y]
        # print('main roof number:', main_roof_number)
        rain_gardens_that_should_go_to_main_rain_garden_id = \
            self.rain_garden_ids_to_pixels[rain_garden_number_that_should_be_deleted]
        # print('ed up roofs:', roofs_that_shoud_go_to_main_roof_number)
        # print('main roofs before:', self.roof_number_to_roofs[main_roof_number])
        for rain_garden in rain_gardens_that_should_go_to_main_rain_garden_id:
            self.rain_gardens.matrix[rain_garden['x']][rain_garden['y']] = main_rain_garden_number
            self.rain_garden_ids_to_pixels[main_rain_garden_number].append(rain_garden)
        # print('main roofs after:', self.roof_number_to_roofs[main_roof_number])
        self.rain_garden_ids_to_pixels[rain_garden_number_that_should_be_deleted] = []
        # print('ed up number:', self.roof_number_to_roofs[roof_number_that_should_be_deleted])

    def calculate_valuable_rain_gardens_by_area(self):
        minimum_pixels_to_be_useful = self.minimum_valuable_area / (self.output.cell_size ** 2)
        # print('num:', minimum_pixels_to_be_useful)
        # t = 0
        # i = 0
        # for key in self.roof_number_to_roofs:
        #     # print(len(self.roof_number_to_roofs[key]))
        #     if len(self.roof_number_to_roofs[key]) > 0:
        #         # print('t yes')
        #         t += 1
        #     if len(self.roof_number_to_roofs[key]) >= minimum_pixels_to_be_useful:
        #         # print('i yes')
        #         i += 1
        # print('t:', t)
        # print('i:', i)
        tmp_ids_to_pixels = copy.deepcopy(self.rain_garden_ids_to_pixels)
        for key in self.rain_garden_ids_to_pixels:
            # print('flat roof number', key, ':')
            # print(self.roof_number_to_roofs[key])
            # print('len is:', len(self.roof_number_to_roofs[key]))
            if len(self.rain_garden_ids_to_pixels[key]) < minimum_pixels_to_be_useful:
                del tmp_ids_to_pixels[key]    # not so sure about it!
                continue
            # flat roof size is good
            # print(key, 'added:)')
            for rain_garden in self.rain_garden_ids_to_pixels[key]:
                # print('before output number i:', roof['x'], 'j:', roof['y'], 'was: ', self.output.matrix[roof['x']][roof['y']])
                self.output.matrix[rain_garden['x']][rain_garden['y']] = key
                # print('now output number i:', roof['x'], 'j:', roof['y'], 'is: ', self.output.matrix[roof['x']][roof['y']])
            # os.system('pause')
        self.rain_garden_ids_to_pixels = tmp_ids_to_pixels


class UserMergeForAlgorithms:
    def __init__(self):
        self.user_limit_on_max_maps_per_percent = 0
        self.priority_list = None
        self.num_of_pixels_of_priority = None
        self.priority_index = 0
        self.priority_item = None
        self.basic_landuse_map = None
        self.taha_map = None
        self.my_map = None
        self.parcel_map = None
        self.dem_map = None
        self.priority_maps = None

    def init(self, priority_list, basic_landuse_map, taha_map,
             basic_landuse_ascii_map_name_for_rain_garden_and_flat_roof, minimum_rain_garden_valuable_area,
             parcel_ascii_map_name_for_flat_roof, dem_ascii_map_name_for_flat_roof, minimum_flat_roof_valuable_area,
             maximum_possible_slope_for_flat_roof,
             user_limit_on_max_maps_per_percent):
        #   raingarden
        self.basic_landuse_ascii_map_name_for_rain_garden_and_flat_roof = basic_landuse_ascii_map_name_for_rain_garden_and_flat_roof
        self.minimum_rain_garden_valuable_area = minimum_rain_garden_valuable_area

        #   flat roof
        self.parcel_ascii_map_name_for_flat_roof = parcel_ascii_map_name_for_flat_roof
        self.dem_ascii_map_name_for_flat_roof = dem_ascii_map_name_for_flat_roof
        self.minimum_flat_roof_valuable_area = minimum_flat_roof_valuable_area
        self.maximum_possible_slope_for_flat_roof = maximum_possible_slope_for_flat_roof

        self.user_limit_on_max_maps_per_percent = user_limit_on_max_maps_per_percent
        self.priority_list = priority_list
        self.num_of_pixels_of_priority = {}
        self.priority_maps = {}
        for priority_name in priority_list:
            self.num_of_pixels_of_priority[priority_name] = 0
            self.priority_maps[priority_name] = {'maps': {}, 'final': None}
        matrix = taha_map.map.matrix
        for i in range(len(matrix)):
            for j in range(len(matrix)):
                data = int(matrix[i][j])
                if data in priority_list:
                    self.num_of_pixels_of_priority[data] += 1
        print('final pixel nums:', self.num_of_pixels_of_priority)
            # priority maps:{
            #     priority item: {
            #     'final': Map(),
            #     'maps': {
            #         5:[Map1, Map2, ...],
            #         10:[Map1, Map2, ...],
            #         ...,
            #         100:[Map1]
            #     }
            # }
            # }
        self.basic_landuse_map = basic_landuse_map
        self.taha_map = taha_map
        self.my_map = taha_map

        ### old final maps, new basic maps
        self.basic_map_for_me = self.basic_landuse_map.map.matrix

    def get_priorities(self, priority_list, basic_landuse_map, taha_map,
                       basic_landuse_ascii_map_name_for_rain_garden_and_flat_roof, minimum_rain_garden_valuable_area,
                       parcel_ascii_map_name_for_flat_roof, dem_ascii_map_name_for_flat_roof, minimum_flat_roof_valuable_area, maximum_possible_slope_for_flat_roof,
                       user_limit_on_max_maps_per_percent):    # main method
        print('first. priority list:', priority_list)
        self.init(priority_list, basic_landuse_map, taha_map,
                  basic_landuse_ascii_map_name_for_rain_garden_and_flat_roof, minimum_rain_garden_valuable_area,
                  parcel_ascii_map_name_for_flat_roof, dem_ascii_map_name_for_flat_roof, minimum_flat_roof_valuable_area, maximum_possible_slope_for_flat_roof,
                  user_limit_on_max_maps_per_percent)
        print('after basic init')
        self.print()
        for priority_index in range(len(priority_list)):
            print('on priority index:', priority_index)
            self.priority_index = priority_index
            self.priority_item = priority_list[priority_index]
            print('on priority item:', self.priority_item)
            self.build_maps_for_priority_item()
        return self.priority_maps

    def print(self):
        print('****************inside print***************')
        print('priority list:', self.priority_list)
        print('priority maps:', self.priority_maps)
            # priority maps:{
            #     priority item: {
            #     'final': Map(),
            #     'maps': {
            #         5:[Map1, Map2, ...],
            #         10:[Map1, Map2, ...],
            #         ...,
            #         100:[Map1]
            #     }
            # }
            # }

    def build_maps_for_priority_item(self):
        step = 5
        maps_for_priority = {'maps': {}, 'final': None}
        print('start:')
        if self.priority_item == AdvancedLandUseMap.VALUES.GREEN_ROOF:
            print('green roof')
            method_to_call_for_priority_item = self.build_green_roof_maps_for_priority_item_with_percentage
        elif self.priority_item == AdvancedLandUseMap.VALUES.RAIN_GARDEN:
            print('rain garden')
            method_to_call_for_priority_item = self.build_rain_garden_maps_for_priority_item_with_percentage
        else:
            print('continuous')
            method_to_call_for_priority_item = self.build_continuous_maps_for_priority_item_with_percentage
        all_priority_pixels = self.num_of_pixels_of_priority[self.priority_item]
        for i in range(1, int(100 / step) + 1):
            print('i:', i)
            percent = step * i
            print('%:', percent)
            num_of_pixels = int(all_priority_pixels * (percent/100))
            print('alllll of pixels:', all_priority_pixels)
            print('num of pixels:', num_of_pixels)
            maps = [[]]
            maps = method_to_call_for_priority_item(num_of_pixels)
            print('maps len:', len(maps))
            maps_for_priority['maps'][percent] = maps
            if percent == 100:
                maps_for_priority['final'] = maps[0]  # should not be empty!!
                self.basic_map_for_me = maps_for_priority['final']
            # print('maps for priority:', maps_for_priority)
        self.priority_maps[self.priority_item] = maps_for_priority
        print('final priority maps:', len(self.priority_maps[self.priority_item]))

    def build_green_roof_maps_for_priority_item_with_percentage(self, max_num_of_pixels):
        new_maps = []
        print('green roof2')
        my_flat_roof_finder = FlatRoofFinder()
        flat_roof_output = my_flat_roof_finder.get_flat_roofs_by_elevation_map(
            self.basic_landuse_ascii_map_name_for_rain_garden_and_flat_roof,
            self.parcel_ascii_map_name_for_flat_roof,
            self.dem_ascii_map_name_for_flat_roof,
            self.minimum_flat_roof_valuable_area,
            self.maximum_possible_slope_for_flat_roof)
        flat_roof_ids_to_pixels = my_flat_roof_finder.roof_number_to_roofs
        cp_flat_roof_ids_to_pixels = copy.deepcopy(flat_roof_ids_to_pixels)
        for map_no in range(self.user_limit_on_max_maps_per_percent):

            smallest = 100000000
            for i in cp_flat_roof_ids_to_pixels:
                if len(cp_flat_roof_ids_to_pixels[i]) < smallest:
                    smallest = len(cp_flat_roof_ids_to_pixels[i])
                    print('small:', smallest)
            print('final smallest:', smallest)
            if smallest > max_num_of_pixels:
                break

            new_map_to_append = copy.deepcopy(self.basic_map_for_me)    ##########################
            if not cp_flat_roof_ids_to_pixels:
                break
            max_no = max_num_of_pixels
            new_map_pixels = {}
            tmp_rain_garden_ids_to_pixels = copy.deepcopy(cp_flat_roof_ids_to_pixels)
            flag = False
            for rain_id in cp_flat_roof_ids_to_pixels:
                num_of_rain_pixels = len(cp_flat_roof_ids_to_pixels[rain_id])
                if num_of_rain_pixels > max_no:
                    continue
                max_no -= num_of_rain_pixels
                new_map_pixels[rain_id] = cp_flat_roof_ids_to_pixels[rain_id]
                for pixel in new_map_pixels[rain_id]:
                    new_map_to_append[pixel['x']][pixel['y']] = AdvancedLandUseMap.VALUES.RAIN_GARDEN
                # print('map111:', new_map_pixels[rain_id])
                del tmp_rain_garden_ids_to_pixels[rain_id]
                flag = True
                print('deleted the bech', len(tmp_rain_garden_ids_to_pixels), len(cp_flat_roof_ids_to_pixels))
                # print('map222:', new_map_pixels[rain_id])
            cp_flat_roof_ids_to_pixels = tmp_rain_garden_ids_to_pixels

            # print('smallest cp:', len(cp_flat_roof_ids_to_pixels))
            # print('new_map to append:', new_map_to_append)
            if flag:
                print('appended!')
                new_maps.append(new_map_to_append)
            print('new map appended!', len(new_maps))
        return new_maps

    def build_rain_garden_maps_for_priority_item_with_percentage(self, max_num_of_pixels):
        new_maps = []
        print('rain garden2')
        my_rain_garden_finder = RainGardenFinder()
        rain_garden_output = my_rain_garden_finder.get_rain_gardens(
            self.basic_landuse_ascii_map_name_for_rain_garden_and_flat_roof,
            self.minimum_rain_garden_valuable_area)
        rain_garden_ids_to_pixels = my_rain_garden_finder.rain_garden_ids_to_pixels
        cp_rain_garden_ids_to_pixels = copy.deepcopy(rain_garden_ids_to_pixels)
        for map_no in range(self.user_limit_on_max_maps_per_percent):

            smallest = 100000000
            for i in cp_rain_garden_ids_to_pixels:
                if len(cp_rain_garden_ids_to_pixels[i]) < smallest:
                    smallest = len(cp_rain_garden_ids_to_pixels[i])
                    print('small:', smallest)
            print('final smallest:', smallest)
            if smallest > max_num_of_pixels:
                break

            new_map_to_append = copy.deepcopy(self.basic_map_for_me)    #############################
            if not cp_rain_garden_ids_to_pixels:
                break
            max_no = max_num_of_pixels
            new_map_pixels = {}
            tmp_rain_garden_ids_to_pixels = copy.deepcopy(cp_rain_garden_ids_to_pixels)
            flag = False
            for rain_id in cp_rain_garden_ids_to_pixels:
                num_of_rain_pixels = len(cp_rain_garden_ids_to_pixels[rain_id])
                if num_of_rain_pixels > max_no:
                    continue
                max_no -= num_of_rain_pixels
                new_map_pixels[rain_id] = cp_rain_garden_ids_to_pixels[rain_id]
                for pixel in new_map_pixels[rain_id]:
                    new_map_to_append[pixel['x']][pixel['y']] = AdvancedLandUseMap.VALUES.RAIN_GARDEN
                # print('map111:', new_map_pixels[rain_id])
                del tmp_rain_garden_ids_to_pixels[rain_id]
                flag = True
                print('deleted the bech', len(tmp_rain_garden_ids_to_pixels), len(cp_rain_garden_ids_to_pixels))
                # print('map222:', new_map_pixels[rain_id])
            cp_rain_garden_ids_to_pixels = tmp_rain_garden_ids_to_pixels


            # print('smallest cp:', len(cp_rain_garden_ids_to_pixels))
            # print('new_map to append:', new_map_to_append)
            if flag:
                print('appended!')
                new_maps.append(new_map_to_append)
            print('new map appended!', len(new_maps))
        return new_maps


    # def build_continuous_maps_for_priority_item(self):
    #     step = 5
    #     maps_for_priority = {'maps': {}, 'final': None}
    #     print('start:')
    #     for i in range(1, int(100/step) + 1):
    #         print('i:', i)
    #         percent = step * i
    #         print('%:', percent)
    #         maps = [[]]
    #         # maps = self.build_maps_for_priority_item_with_percentage(percent)
    #         print('maps len:', len(maps))
    #         maps_for_priority['maps'][percent] = maps
    #         if percent == 100:
    #             maps_for_priority['final'] = maps[0]    # should not be empty!!
    #         print('maps for priority:', maps_for_priority)
    #     self.priority_maps[self.priority_item] = maps_for_priority
    #     print('final priority maps:', self.priority_maps)

    def build_continuous_maps_for_priority_item_with_percentage(self, num_of_pixels):
        print('continuous2')
        maps = []
        priority_item = self.priority_item
        print('priority item:', priority_item)
        main_map = copy.deepcopy(self.my_map.map)
        matrix = main_map.matrix
        for map_no in range(self.user_limit_on_max_maps_per_percent):
            new_map_to_append = copy.deepcopy(self.basic_map_for_me)    ###############################
            seen_pixels = 0
            for i in range(len(matrix)):
                # print('i:', i)
                # print('seen pixels:', seen_pixels)
                # print('num of pixels:', num_of_pixels)
                # print('seen pixels > num of pixels:', seen_pixels > num_of_pixels)
                if seen_pixels > num_of_pixels:
                    # print('seen pixels > num_of_pixels111:', seen_pixels)
                    break
                col = matrix[i]
                for j in range(len(col)):
                    # print('j:', j)
                    if seen_pixels > num_of_pixels:
                        # print('seen pixels > num_of_pixels222:', seen_pixels)
                        break
                    it = matrix[i][j]
                    # print('matrix[i][j]:', matrix[i][j])
                    if it == priority_item:
                        matrix[i][j] = main_map.no_data_value
                        # print('it = priority item = ', it)
                        # print('i:', i, ', j:', j)
                        seen_pixels += 1
                        # print('seen_pixels:', seen_pixels)
                        new_map_to_append[i][j] = it
                        # main_map.matrix[i][j] = self.basic_landuse_map.map.matrix[i][j]
            else:
                # print('seen pixels > num_of_pixels333:', seen_pixels)
                maps.append({'map': new_map_to_append, 'num_of_pixels:': seen_pixels})
                # print('maps len111:', len(maps))
                break
            maps.append({'map': new_map_to_append, 'num_of_pixels:': seen_pixels})
            print('maps len222:', len(maps))
        return maps


class UserMergeForAlgorithmsTest:
    def test_get_priorities(self):
        basic_landuse_map = map_loader.load_map(LandUseMap, "landuse.asc")
        taha_map = map_loader.load_map(DetailedLandUseMap, "landuse.asc")
        parcel_map = map_loader.load_map(ParcelMap, 'roofs30.asc')
        dem_map = map_loader.load_map(ElevationMap, 'elevation.asc')

        print('taha map:', taha_map.map.get_config_string())
        print('landuse map:', basic_landuse_map.map.get_config_string())
        a = UserMergeForAlgorithms().get_priorities(
            [5], basic_landuse_map, taha_map,
            "landuse.asc", 10,
            "roof30true.asc", "elevation.asc", 10, 5,
            30)
UserMergeForAlgorithmsTest().test_get_priorities()
