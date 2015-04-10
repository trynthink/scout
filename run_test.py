#!/usr/bin/env python3

""" Tests for running the engine """

# Import code to be tested
import run

# Import needed packages
import unittest
import numpy


class TestMeasureInit(unittest.TestCase):
    """ Ensure that measure attributes are correctly initiated """

    # Sample measure for use in testing attributes
    sample_measure = {"name": "sample measure 1",
                      "end_use": ["heating", "cooling"],
                      "fuel_type": "electricity (grid)",
                      "technology_type": "supply",
                      "technology": ['boiler (electric)',
                                     'ASHP', 'GSHP', 'room AC'],
                      "bldg_type": "single family home",
                      "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}

    def test_attributes(self):
        # Create an instance of the object using sample_measure
        measure_instance = run.Measure(**self.sample_measure)
        # Put object attributes into a dict
        attribute_dict = measure_instance.__dict__
        # Loop through sample measure keys and compare key values
        # to those from the "attribute_dict"
        for key in self.sample_measure.keys():
            self.assertEqual(attribute_dict[key],
                             self.sample_measure[key])
        # Check to see that sample measure is correctly identified
        # as inactive
        self.assertEqual(measure_instance.active, 0)


class FindMasterMicrosegmentTest(unittest.TestCase):
    """ Test the operation of the find_master_microsegment function to
    verify measure microsegment-related attribute inputs yield expected master
    microsegment output """

    # Sample input dict of microsegment stock/energy info. to reference in
    # generating master microsegments for a measure
    sample_msegin = {
        'AIA_CZ1': {
            'single family home': {
                'square footage': {"2009": 100, "2010": 200},
                'electricity (grid)': {
                    'heating': {'demand': {'windows conduction': {
                                           'stock': 'NA',
                                           'energy': {"2009": 0, "2010": 0}},
                                           'windows solar': {
                                           'stock': 'NA',
                                           'energy': {"2009": 1, "2010": 1}}},
                                'supply': {'boiler (electric)': {
                                           'stock': {"2009": 2, "2010": 2},
                                           'energy': {"2009": 2, "2010": 2}},
                                           'ASHP': {
                                           'stock': {"2009": 3, "2010": 3},
                                           'energy': {"2009": 3, "2010": 3}},
                                           'GSHP': {
                                           'stock': {"2009": 4, "2010": 4},
                                           'energy': {"2009": 4, "2010": 4}}}},
                    'secondary heating': {'demand': {'windows conduction': {
                                                     'stock': 'NA',
                                                     'energy': {"2009": 5,
                                                                "2010": 5}},
                                                     'windows solar': {
                                                     'stock': 'NA',
                                                     'energy': {"2009": 6,
                                                                "2010": 6}}},
                                          'supply': {'non-specific': 7}},
                    'cooling': {'demand': {'windows conduction': {
                                           'stock': 'NA',
                                           'energy': {"2009": 5, "2010": 5}},
                                           'windows solar': {
                                           'stock': 'NA',
                                           'energy': {"2009": 6, "2010": 6}}},
                                'supply': {'central AC': {
                                           'stock': {"2009": 7, "2010": 7},
                                           'energy': {"2009": 7, "2010": 7}},
                                           'room AC': {
                                           'stock': {"2009": 8, "2010": 8},
                                           'energy': {"2009": 8, "2010": 8}},
                                           'ASHP': {
                                           'stock': {"2009": 9, "2010": 9},
                                           'energy': {"2009": 9, "2010": 9}},
                                           'GSHP': {
                                           'stock': {"2009": 10, "2010": 10},
                                           'energy': {"2009": 10,
                                                      "2010": 10}}}},
                    'lighting': {'linear fluorescent': {
                                 'stock': {"2009": 11, "2010": 11},
                                 'energy': {"2009": 11, "2010": 11}},
                                 'general service': {
                                 'stock': {"2009": 12, "2010": 12},
                                 'energy': {"2009": 12, "2010": 12}},
                                 'reflector': {
                                 'stock': {"2009": 13, "2010": 13},
                                 'energy': {"2009": 13, "2010": 13}},
                                 'external': {
                                 'stock': {"2009": 14, "2010": 14},
                                 'energy': {"2009": 14, "2010": 14}}}},
                    'natural gas': {'water heating': {
                                    'stock': {"2009": 15, "2010": 15},
                                    'energy': {"2009": 15, "2010": 15}}}},
            'multi family home': {
                'square footage': {"2009": 300, "2010": 400},
                'electricity (grid)': {
                    'heating': {'demand': {'windows conduction': {
                                           'stock': 'NA',
                                           'energy': {"2009": 0, "2010": 0}},
                                           'windows solar': {
                                           'stock': 'NA',
                                           'energy': {"2009": 1, "2010": 1}}},
                                'supply': {'boiler (electric)': {
                                           'stock': {"2009": 2, "2010": 2},
                                           'energy': {"2009": 2, "2010": 2}},
                                           'ASHP': {
                                           'stock': {"2009": 3, "2010": 3},
                                           'energy': {"2009": 3, "2010": 3}},
                                           'GSHP': {
                                           'stock': {"2009": 4, "2010": 4}}}},
                    'lighting': {'linear fluorescent': {
                                 'stock': {"2009": 11, "2010": 11},
                                 'energy': {"2009": 11, "2010": 11}},
                                 'general service': {
                                 'stock': {"2009": 12, "2010": 12},
                                 'energy': {"2009": 12, "2010": 12}},
                                 'reflector': {
                                 'stock': {"2009": 13, "2010": 13},
                                 'energy': {"2009": 13, "2010": 13}},
                                 'external': {
                                 'stock': {"2009": 14, "2010": 14},
                                 'energy': {"2009": 14, "2010": 14}}}}}},
        'AIA_CZ2': {
            'single family home': {
                'square footage': {"2009": 500, "2010": 600},
                'electricity (grid)': {
                    'heating': {'demand': {'windows conduction': {
                                           'stock': 'NA',
                                           'energy': {"2009": 0, "2010": 0}},
                                           'windows solar': {
                                           'stock': 'NA',
                                           'energy': {"2009": 1, "2010": 1}}},
                                'supply': {'boiler (electric)': {
                                           'stock': {"2009": 2, "2010": 2},
                                           'energy': {"2009": 2, "2010": 2}},
                                           'ASHP': {
                                           'stock': {"2009": 3, "2010": 3},
                                           'energy': {"2009": 3, "2010": 3}},
                                           'GSHP': {
                                           'stock': {"2009": 4, "2010": 4},
                                           'energy': {"2009": 4, "2010": 4}}}},
                    'secondary heating': {'demand': {'windows conduction': {
                                                     'stock': 'NA',
                                                     'energy': {"2009": 5,
                                                                "2010": 5}},
                                                     'windows solar': {
                                                     'stock': 'NA',
                                                     'energy': {"2009": 6,
                                                                "2010": 6}}},
                                          'supply': {'non-specific': 7}},
                    'cooling': {'demand': {'windows conduction': {
                                           'stock': 'NA',
                                           'energy': {"2009": 5, "2010": 5}},
                                           'windows solar': {
                                           'stock': 'NA',
                                           'energy': {"2009": 6, "2010": 6}}},
                                'supply': {'central AC': {
                                           'stock': {"2009": 7, "2010": 7},
                                           'energy': {"2009": 7, "2010": 7}},
                                           'room AC': {
                                           'stock': {"2009": 8, "2010": 8},
                                           'energy': {"2009": 8, "2010": 8}},
                                           'ASHP': {
                                           'stock': {"2009": 9, "2010": 9},
                                           'energy': {"2009": 9, "2010": 9}},
                                           'GSHP': {
                                           'stock': {"2009": 10, "2010": 10},
                                           'energy': {"2009": 10,
                                                      "2010": 10}}}},
                    'lighting': {'linear fluorescent': {
                                 'stock': {"2009": 11, "2010": 11},
                                 'energy': {"2009": 11, "2010": 11}},
                                 'general service': {
                                 'stock': {"2009": 12, "2010": 12},
                                 'energy': {"2009": 12, "2010": 12}},
                                 'reflector': {
                                 'stock': {"2009": 13, "2010": 13},
                                 'energy': {"2009": 13, "2010": 13}},
                                 'external': {
                                 'stock': {"2009": 14, "2010": 14},
                                 'energy': {"2009": 14, "2010": 14}}}},
                    'natural gas': {'water heating': {
                                    'stock': {"2009": 15, "2010": 15},
                                    'energy': {"2009": 15, "2010": 15}}}},
            'multi family home': {
                'square footage': {"2009": 700, "2010": 800},
                'electricity (grid)': {
                    'heating': {'demand': {'windows conduction': {
                                           'stock': 'NA',
                                           'energy': {"2009": 0, "2010": 0}},
                                           'windows solar': {
                                           'stock': 'NA',
                                           'energy': {"2009": 1, "2010": 1}}},
                                'supply': {'boiler (electric)': {
                                           'stock': {"2009": 2, "2010": 2},
                                           'energy': {"2009": 2, "2010": 2}},
                                           'ASHP': {
                                           'stock': {"2009": 3, "2010": 3},
                                           'energy': {"2009": 3, "2010": 3}},
                                           'GSHP': {
                                           'stock': {"2009": 4, "2010": 4}}}},
                    'lighting': {'linear fluorescent': {
                                 'stock': {"2009": 11, "2010": 11},
                                 'energy': {"2009": 11, "2010": 11}},
                                 'general service': {
                                 'stock': {"2009": 12, "2010": 12},
                                 'energy': {"2009": 12, "2010": 12}},
                                 'reflector': {
                                 'stock': {"2009": 13, "2010": 13},
                                 'energy': {"2009": 13, "2010": 13}},
                                 'external': {
                                 'stock': {"2009": 14, "2010": 14},
                                 'energy': {"2009": 14, "2010": 14}}}}}},
        'AIA_CZ4': {
            'multi family home': {
                'square footage': {"2009": 900, "2010": 1000},
                'electricity (grid)': {
                    'lighting': {'linear fluorescent': {
                                 'stock': {"2009": 11, "2010": 11},
                                 'energy': {"2009": 11, "2010": 11}},
                                 'general service': {
                                 'stock': {"2009": 12, "2010": 12},
                                 'energy': {"2009": 12, "2010": 12}},
                                 'reflector': {
                                 'stock': {"2009": 13, "2010": 13},
                                 'energy': {"2009": 13, "2010": 13}},
                                 'external': {
                                 'stock': {"2009": 14, "2010": 14},
                                 'energy': {"2009": 14, "2010": 14}}}}}}}

    # List of measures with attribute combinations that should all be found in
    # the key chains of the "sample_msegin" dict above
    ok_measures = [{"name": "sample measure 1",
                    "end_use": ["heating", "cooling"],
                    "fuel_type": "electricity (grid)",
                    "technology_type": "supply",
                    "technology": ['boiler (electric)',
                                   'ASHP', 'GSHP', 'room AC'],
                    "bldg_type": "single family home",
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                   {"name": "sample measure 2",
                    "end_use": "water heating",
                    "fuel_type": "natural gas",
                    "technology_type": "supply",
                    "technology": None,
                    "bldg_type": "single family home",
                    "climate_zone": "AIA_CZ1"},
                   {"name": "sample measure 3",
                    "end_use": "lighting",
                    "fuel_type": "electricity (grid)",
                    "technology_type": "supply",
                    "technology": ["linear fluorescent",
                                   "general service",
                                   "external"],
                    "bldg_type": ["single family home",
                                  "multi family home"],
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                   {"name": "sample measure 4",
                    "end_use": "heating",
                    "fuel_type": "electricity (grid)",
                    "technology_type": "demand",
                    "technology": ["windows conduction",
                                   "windows solar"],
                    "bldg_type": ["single family home",
                                  "multi family home"],
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                   {"name": "sample measure 5",
                    "end_use": "heating",
                    "fuel_type": "electricity (grid)",
                    "technology_type": "demand",
                    "technology": "windows solar",
                    "bldg_type": "single family home",
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                   {"name": "sample measure 6",
                    "end_use": ["heating", "secondary heating", "cooling"],
                    "fuel_type": "electricity (grid)",
                    "technology_type": "demand",
                    "technology": ["windows conduction", "windows solar"],
                    "bldg_type": "single family home",
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}]

    # List of measures with attribute combinations that should match some of
    # the key chains in the "sample_msegin" dict above (i.e., AIA_CZ1 ->
    # single family home -> electricity (grid) -> cooling -> GSHP is
    # a valid chain, AIA_CZ1 -> single family home -> electricity (grid) ->
    # cooling -> linear fluorescent is not).
    partial_measures = [{"name": "partial measure 1",
                         "end_use": "cooling",
                         "fuel_type": "electricity (grid)",
                         "technology_type": "supply",
                         "technology": ['boiler (electric)', 'ASHP'],
                         "bldg_type": "single family home",
                         "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                        {"name": "partial measure 2",
                         "end_use": ["heating", "cooling"],
                         "fuel_type": "electricity (grid)",
                         "technology_type": "supply",
                         "technology": ["linear fluorescent",
                                        "general service",
                                        "external", 'GSHP', 'ASHP'],
                         "bldg_type": "single family home",
                         "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}]

    # List of measures with attribute combinations that should not match any
    # of the key chains in the "sample_msegin" dict above
    blank_measures = [{"name": "blank measure 1",
                       "end_use": "cooling",
                       "fuel_type": "electricity (grid)",
                       "technology_type": "supply",
                       "technology": 'boiler (electric)',
                       "bldg_type": "single family home",
                       "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                      {"name": "blank measure 2",
                       "end_use": ["heating", "cooling"],
                       "fuel_type": "electricity (grid)",
                       "technology_type": "supply",
                       "technology": ["linear fluorescent",
                                      "general service",
                                      "external"],
                       "bldg_type": "single family home",
                       "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                      {"name": "blank measure 3",
                       "end_use": "lighting",
                       "fuel_type": "natural gas",
                       "technology_type": "supply",
                       "technology": ["linear fluorescent",
                                      "general service",
                                      "external"],
                       "bldg_type": "single family home",
                       "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                      {"name": "blank measure 4",
                       "end_use": "lighting",
                       "fuel_type": "solar",
                       "technology_type": "supply",
                       "technology": ["linear fluorescent",
                                      "general service",
                                      "external"],
                       "bldg_type": "single family home",
                       "climate_zone": "AIA_CZ1"}]

    # Master microsegments that should be generated by "ok_measures"
    # above using the "sample_msegin" dict
    ok_out = [{"stock": {"2009": 72, "2010": 72},
               "energy": {"2009": 72, "2010": 72}},
              {"stock": {"2009": 15, "2010": 15},
               "energy": {"2009": 15, "2010": 15}},
              {"stock": {"2009": 148, "2010": 148},
               "energy": {"2009": 148, "2010": 148}},
              {"stock": {"2009": 1600, "2010": 2000},
               "energy": {"2009": 4, "2010": 4}},
              {"stock": {"2009": 600, "2010": 800},
               "energy": {"2009": 2, "2010": 2}},
              {"stock": {"2009": 600, "2010": 800},
               "energy": {"2009": 46, "2010": 46}}]

    # Master microsegments that should be generated by "partial_measures"
    # above using the "sample_msegin" dict
    partial_out = [{"stock": {"2009": 18, "2010": 18},
                    "energy": {"2009": 18, "2010": 18}},
                   {"stock": {"2009": 52, "2010": 52},
                    "energy": {"2009": 52, "2010": 52}}]

    # Master microsegments that should be generated by "blank_measures"
    # above using the "sample_msegin" dict
    blank_out = list(numpy.repeat({"stock": None,
                                   "energy": None}, len(blank_measures)))

    # Test for correct output from "ok_measures" input
    def test_mseg_ok(self):
        for idx, measure in enumerate(self.ok_measures):
            # Create an instance of the object based on ok measure info
            measure_instance = run.Measure(**measure)
            # Assert output dict is correct
            self.assertEqual(measure_instance.find_master_microsegment(
                             self.sample_msegin),
                             self.ok_out[idx])

    # Test for correct output from "partial_measures" input
    def test_mseg_partial(self):
        for idx, measure in enumerate(self.partial_measures):
            # Create an instance of the object based on partial measure info
            measure_instance = run.Measure(**measure)
            # Assert output dict is correct
            self.assertEqual(measure_instance.find_master_microsegment(
                             self.sample_msegin),
                             self.partial_out[idx])

    # Test for correct output from "blank_measures" input
    def test_mseg_blank(self):
        for idx, measure in enumerate(self.blank_measures):
            # Create an instance of the object based on blank measure info
            measure_instance = run.Measure(**measure)
            # Assert output dict is correct
            self.assertEqual(measure_instance.find_master_microsegment(
                             self.sample_msegin),
                             self.blank_out[idx])


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == '__main__':
    main()
