#!/usr/bin/env python3

"""Extracted test data for Update Measures tests."""

sample_cpl_in_aia = {
            "AIA_CZ1": {
                "single family home": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "resistance heat": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "ASHP": {
                                    "performance": {
                                        "typical": {"2009": 3, "2010": 3},
                                        "best": {"2009": 3, "2010": 3},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {
                                            "new": {"2009": 6,
                                                    "2010": 6},
                                            "existing": {"2009": 3,
                                                         "2010": 3}},
                                        "best": {
                                            "new": {"2009": 6,
                                                    "2010": 6},
                                            "existing": {"2009": 3,
                                                         "2010": 3}},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 30, "2010": 30},
                                        "range": {"2009": 3, "2010": 3},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "GSHP": {
                                    "performance": {
                                        "typical": {"2009": 4, "2010": 4},
                                        "best": {"2009": 4, "2010": 4},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {
                                            "new": {"2009": 8,
                                                    "2010": 8},
                                            "existing": {"2009": 4,
                                                         "2010": 4}},
                                        "best": {
                                            "new": {"2009": 8,
                                                    "2010": 8},
                                            "existing": {"2009": 4,
                                                         "2010": 4}},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 40, "2010": 40},
                                        "range": {"2009": 4, "2010": 4},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {
                                            "new": {"2009": 8, "2010": 8},
                                            "existing": {
                                                "2009": 8, "2010": 8}
                                            },
                                        "best": {"2009": 8, "2010": 8},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 8, "2010": 8},
                                        "best": {"2009": 8, "2010": 8},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 80, "2010": 80},
                                        "range": {"2009": 8, "2010": 8},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 9, "2010": 9},
                                        "best": {"2009": 9, "2010": 9},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 9, "2010": 9},
                                        "best": {"2009": 9, "2010": 9},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 90, "2010": 90},
                                        "range": {"2009": 9, "2010": 9},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "central AC": {
                                    "performance": {
                                        "typical": {"2009": 10, "2010": 10},
                                        "best": {"2009": 10, "2010": 10},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 10, "2010": 10},
                                        "best": {"2009": 10, "2010": 10},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 100, "2010": 100},
                                        "range": {"2009": 10, "2010": 10},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "room AC": {
                                    "performance": {
                                        "typical": {"2009": 11, "2010": 11},
                                        "best": {"2009": 11, "2010": 11},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 11, "2010": 11},
                                        "best": {"2009": 11, "2010": 11},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 110, "2010": 110},
                                        "range": {"2009": 11, "2010": 11},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "ASHP": {
                                    "performance": {
                                        "typical": {"2009": 12, "2010": 12},
                                        "best": {"2009": 12, "2010": 12},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {
                                            "new": {"2009": 24,
                                                    "2010": 24},
                                            "existing": {"2009": 12,
                                                         "2010": 12}},
                                        "best": {
                                            "new": {"2009": 24,
                                                    "2010": 24},
                                            "existing": {"2009": 12,
                                                         "2010": 12}},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 120, "2010": 120},
                                        "range": {"2009": 12, "2010": 12},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "GSHP": {
                                    "performance": {
                                        "typical": {"2009": 13, "2010": 13},
                                        "best": {"2009": 13, "2010": 13},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {
                                            "new": {"2009": 26,
                                                    "2010": 26},
                                            "existing": {"2009": 13,
                                                         "2010": 13}},
                                        "best": {
                                            "new": {"2009": 26,
                                                    "2010": 26},
                                            "existing": {"2009": 13,
                                                         "2010": 13}},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 130, "2010": 130},
                                        "range": {"2009": 13, "2010": 13},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}}},
                    "natural gas": {
                        "water heating": {
                            "performance": {
                                "typical": {"2009": 18, "2010": 18},
                                "best": {"2009": 18, "2010": 18},
                                "units": "EF",
                                "source":
                                "EIA AEO"},
                            "installed cost": {
                                "before incentives": {
                                    "typical": {
                                                "new": {"2009": 18,
                                                        "2010": 18},
                                                "existing": {"2009": 18,
                                                             "2010": 18}},
                                    "best": {
                                        "new": {"2009": 18,
                                                "2010": 18},
                                        "existing": {"2009": 18,
                                                     "2010": 18}},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "incentives": {
                                    "by performance tier": {
                                        "2009": [
                                            [10, 0],
                                            [15, 0],
                                            [20, 3],
                                            [25, 9]],
                                        "2010": [
                                            [10, 0],
                                            [15, 0],
                                            [20, 3],
                                            [25, 9]]},
                                    "performance units": "EF"
                                }},
                            "lifetime": {
                                "average": {"2009": 180, "2010": 180},
                                "range": {"2009": 18, "2010": 18},
                                "units": "years",
                                "source": "EIA AEO"},
                            "consumer choice": {
                                "competed market share": {
                                    "source": "EIA AEO",
                                    "model type": "logistic regression",
                                    "parameters": {
                                        "b1": {"2009": "NA", "2010": "NA"},
                                        "b2": {"2009": "NA",
                                               "2010": "NA"}}},
                                "competed market": {
                                    "source": "COBAM",
                                    "model type": "bass diffusion",
                                    "parameters": {
                                        "p": "NA",
                                        "q": "NA"}}}}}}},
            "AIA_CZ2": {
                "single family home": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "resistance heat": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "ASHP": {
                                    "performance": {
                                        "typical": {"2009": 3, "2010": 3},
                                        "best": {"2009": 3, "2010": 3},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {
                                            "new": {"2009": 6,
                                                    "2010": 6},
                                            "existing": {"2009": 3,
                                                         "2010": 3}},
                                        "best": {
                                            "new": {"2009": 6,
                                                    "2010": 6},
                                            "existing": {"2009": 3,
                                                         "2010": 3}},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 30, "2010": 30},
                                        "range": {"2009": 3, "2010": 3},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "GSHP": {
                                    "performance": {
                                        "typical": {"2009": 4, "2010": 4},
                                        "best": {"2009": 4, "2010": 4},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {
                                            "new": {"2009": 4,
                                                    "2010": 4},
                                            "existing": {"2009": 2,
                                                         "2010": 2}},
                                        "best": {
                                            "new": {"2009": 4,
                                                    "2010": 4},
                                            "existing": {"2009": 2,
                                                         "2010": 2}},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 40, "2010": 40},
                                        "range": {"2009": 4, "2010": 4},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 8, "2010": 8},
                                        "best": {"2009": 8, "2010": 8},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 8, "2010": 8},
                                        "best": {"2009": 8, "2010": 8},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 80, "2010": 80},
                                        "range": {"2009": 8, "2010": 8},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 9, "2010": 9},
                                        "best": {"2009": 9, "2010": 9},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 9, "2010": 9},
                                        "best": {"2009": 9, "2010": 9},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 90, "2010": 90},
                                        "range": {"2009": 9, "2010": 9},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "central AC": {
                                    "performance": {
                                        "typical": {"2009": 10, "2010": 10},
                                        "best": {"2009": 10, "2010": 10},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 10, "2010": 10},
                                        "best": {"2009": 10, "2010": 10},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 100, "2010": 100},
                                        "range": {"2009": 10, "2010": 10},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "room AC": {
                                    "performance": {
                                        "typical": {"2009": 11, "2010": 11},
                                        "best": {"2009": 11, "2010": 11},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 11, "2010": 11},
                                        "best": {"2009": 11, "2010": 11},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 110, "2010": 110},
                                        "range": {"2009": 11, "2010": 11},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "ASHP": {
                                    "performance": {
                                        "typical": {"2009": 12, "2010": 12},
                                        "best": {"2009": 12, "2010": 12},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {
                                            "new": {"2009": 24,
                                                    "2010": 24},
                                            "existing": {"2009": 12,
                                                         "2010": 12}},
                                        "best": {
                                            "new": {"2009": 24,
                                                    "2010": 24},
                                            "existing": {"2009": 12,
                                                         "2010": 12}},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 120, "2010": 120},
                                        "range": {"2009": 12, "2010": 12},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "GSHP": {
                                    "performance": {
                                        "typical": {"2009": 13, "2010": 13},
                                        "best": {"2009": 13, "2010": 13},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {
                                            "new": {"2009": 26,
                                                    "2010": 26},
                                            "existing": {"2009": 13,
                                                         "2010": 13}},
                                        "best": {
                                            "new": {"2009": 26,
                                                    "2010": 26},
                                            "existing": {"2009": 13,
                                                         "2010": 13}},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 130, "2010": 130},
                                        "range": {"2009": 13, "2010": 13},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}}}}}}


sample_cpl_in_emm = {
            "FRCC": {
                "assembly": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "wall": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "roof": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "lighting gain": 0}},
                        "cooling": {
                            "demand": {
                                "wall": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "roof": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "lighting gain": 0}},
                        "lighting": {
                            "T5 F28": {
                                "performance": {
                                    "typical": {"2009": 14, "2010": 14},
                                    "best": {"2009": 14, "2010": 14},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 14, "2010": 14},
                                    "best": {"2009": 14, "2010": 14},
                                    "units": "2014$/ft^2 floor",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 140, "2010": 140},
                                    "range": {"2009": 14, "2010": 14},
                                    "units": "years",
                                    "source": "EIA AEO"},
                                "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                        "PCs": 0,
                        "MELs": {
                            "distribution transformers": 0
                        }
                    }
                },
                "single family home": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "wall": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "roof": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "cooling": {
                            "demand": {
                                "wall": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "roof": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}}
                    }
                }
            },
            "ERCT": {
                "assembly": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "wall": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "roof": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "lighting gain": 0}},
                        "cooling": {
                            "demand": {
                                "wall": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "roof": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "lighting gain": 0}},
                        "lighting": {
                            "T5 F28": {
                                "performance": {
                                    "typical": {"2009": 14, "2010": 14},
                                    "best": {"2009": 14, "2010": 14},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 14, "2010": 14},
                                    "best": {"2009": 14, "2010": 14},
                                    "units": "2014$/ft^2 floor",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 140, "2010": 140},
                                    "range": {"2009": 14, "2010": 14},
                                    "units": "years",
                                    "source": "EIA AEO"},
                                "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                        "PCs": 0,
                        "MELs": {
                            "distribution transformers": 0
                        }
                    }
                },
                "single family home": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "wall": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "roof": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "cooling": {
                            "demand": {
                                "wall": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "roof": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": "NA",
                                                       "2010": "NA"},
                                                "b2": {"2009": "NA",
                                                       "2010": "NA"}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}}
                    }
                }
            }
            }


ok_out_emm_features = [{
            "stock": {
                "total": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 11000000, "2010": 11000000}},
                "competed": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 11000000, "2010": 11000000}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 3.19, "2010": 3.2},
                    "efficient": {"2009": 2.870474322, "2010": 2.879472674}},
                "competed": {
                    "baseline": {"2009": 3.19, "2010": 3.2},
                    "efficient": {"2009": 2.870474322, "2010": 2.879472674}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 176.8610198, "2010": 175.2969732},
                    "efficient": {"2009": 159.0471025, "2010": 157.6405909}},
                "competed": {
                    "baseline": {"2009": 176.8610198, "2010": 175.2969732},
                    "efficient": {"2009": 159.0471025, "2010": 157.6405909}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}},
                    "competed": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 31.14282853, "2010": 29.41694822},
                        "efficient": {
                            "2009": 28.0237991, "2010": 26.47076987}},
                    "competed": {
                        "baseline": {"2009": 31.14282853, "2010": 29.41694822},
                        "efficient": {
                            "2009": 28.0237991, "2010": 26.47076987}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 5836.413654, "2010": 5784.800117},
                        "efficient": {
                            "2009": 5248.554381, "2010": 5202.139498}},
                    "competed": {
                        "baseline": {
                            "2009": 5836.413654, "2010": 5784.800117},
                        "efficient": {
                            "2009": 5248.554381, "2010": 5202.139498}}}},
            "lifetime": {"baseline": {"2009": 15, "2010": 15},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 11000000, "2010": 11000000}},
                "competed": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 11000000, "2010": 11000000}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 3.19, "2010": 3.2},
                    "efficient": {"2009": 1.592371609, "2010": 1.59736337}},
                "competed": {
                    "baseline": {"2009": 3.19, "2010": 3.2},
                    "efficient": {"2009": 1.592371609, "2010": 1.59736337}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 176.8610198, "2010": 175.2969732},
                    "efficient": {"2009": 87.79143306, "2010": 87.01506136}},
                "competed": {
                    "baseline": {"2009": 176.8610198, "2010": 175.2969732},
                    "efficient": {"2009": 87.79143306, "2010": 87.01506136}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}},
                    "competed": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 31.14282853, "2010": 29.41694822},
                        "efficient": {
                            "2009": 15.54976483, "2010": 14.68802445}},
                    "competed": {
                        "baseline": {"2009": 31.14282853, "2010": 29.41694822},
                        "efficient": {
                            "2009": 15.54976483, "2010": 14.68802445}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 5836.413654, "2010": 5784.800117},
                        "efficient": {
                            "2009": 2897.117291, "2010": 2871.497025}},
                    "competed": {
                        "baseline": {
                            "2009": 5836.413654, "2010": 5784.800117},
                        "efficient": {
                            "2009": 2897.117291, "2010": 2871.497025}}}},
            "lifetime": {"baseline": {"2009": 15, "2010": 15},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 11000000, "2010": 11000000}},
                "competed": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 11000000, "2010": 11000000}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 3.19, "2010": 3.2},
                    "efficient": {
                        "2009": 1.592371609 / 2, "2010": 1.59736337 / 2}},
                "competed": {
                    "baseline": {"2009": 3.19, "2010": 3.2},
                    "efficient": {
                        "2009": 1.592371609 / 2, "2010": 1.59736337 / 2}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 176.8610198, "2010": 175.2969732},
                    "efficient": {
                        "2009": 87.79143306 / 2, "2010": 87.01506136 / 2}},
                "competed": {
                    "baseline": {"2009": 176.8610198, "2010": 175.2969732},
                    "efficient": {
                        "2009": 87.79143306 / 2, "2010": 87.01506136 / 2}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}},
                    "competed": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 31.14282853, "2010": 29.41694822},
                        "efficient": {
                            "2009": 15.54976483 / 2, "2010": 14.68802445 / 2}},
                    "competed": {
                        "baseline": {"2009": 31.14282853, "2010": 29.41694822},
                        "efficient": {
                            "2009": 15.54976483 / 2,
                            "2010": 14.68802445 / 2}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 5836.413654, "2010": 5784.800117},
                        "efficient": {
                            "2009": 2897.117291 / 2, "2010": 2871.497025 / 2}},
                    "competed": {
                        "baseline": {
                            "2009": 5836.413654, "2010": 5784.800117},
                        "efficient": {
                            "2009": 2897.117291 / 2,
                            "2010": 2871.497025 / 2}}}},
            "lifetime": {"baseline": {"2009": 15, "2010": 15},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 11000000 * 1000/(11*1000000),
                            "2010": 11000000 * 1000/(11*1000000)},
                    "measure": {"2009": 11000000 * 1000/(11*1000000),
                                "2010": 11000000 * 1000/(11*1000000)}},
                "competed": {
                    "all": {"2009": 11000000 * 1000/(11*1000000),
                            "2010": 11000000 * 1000/(11*1000000)},
                    "measure": {"2009": 11000000 * 1000/(11*1000000),
                                "2010": 11000000 * 1000/(11*1000000)}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 3.19, "2010": 3.2},
                    "efficient": {
                        "2009": 1.592371609 / 2, "2010": 1.59736337 / 2}},
                "competed": {
                    "baseline": {"2009": 3.19, "2010": 3.2},
                    "efficient": {
                        "2009": 1.592371609 / 2, "2010": 1.59736337 / 2}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 176.8610198, "2010": 175.2969732},
                    "efficient": {
                        "2009": 87.79143306 / 2, "2010": 87.01506136 / 2}},
                "competed": {
                    "baseline": {"2009": 176.8610198, "2010": 175.2969732},
                    "efficient": {
                        "2009": 87.79143306 / 2, "2010": 87.01506136 / 2}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}},
                    "competed": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 31.14282853, "2010": 29.41694822},
                        "efficient": {
                            "2009": 15.54976483 / 2, "2010": 14.68802445 / 2}},
                    "competed": {
                        "baseline": {"2009": 31.14282853, "2010": 29.41694822},
                        "efficient": {
                            "2009": 15.54976483 / 2,
                            "2010": 14.68802445 / 2}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 5836.413654, "2010": 5784.800117},
                        "efficient": {
                            "2009": 2897.117291 / 2, "2010": 2871.497025 / 2}},
                    "competed": {
                        "baseline": {
                            "2009": 5836.413654, "2010": 5784.800117},
                        "efficient": {
                            "2009": 2897.117291 / 2,
                            "2010": 2871.497025 / 2}}}},
            "lifetime": {"baseline": {"2009": 15, "2010": 15},
                         "measure": 1}}]


sample_mseg_in_emm = {
            "FRCC": {
                "assembly": {
                    "total square footage": {"2009": 11, "2010": 11},
                    "new square footage": {"2009": 0, "2010": 0},
                    "electricity": {
                        "heating": {
                            "demand": {
                                "wall": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 0, "2010": 0}},
                                "roof": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 1, "2010": 1}},
                                "lighting gain": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": -7, "2010": -7}}}},
                        "cooling": {
                            "demand": {
                                "wall": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 5, "2010": 5}},
                                "roof": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 6, "2010": 6}},
                                "lighting gain": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 6, "2010": 6}}}},
                        "lighting": {
                            "T5 F28": {
                                "stock": "NA",
                                "energy": {
                                    "2009": 11, "2010": 11}}},
                        "PCs": {
                            "stock": "NA",
                            "energy": {"2009": 12, "2010": 12}},
                        "MELs": {
                            "distribution transformers": {
                                "stock": "NA",
                                "energy": {"2009": 24, "2010": 24}
                            }
                        }}},
                "single family home": {
                    "total square footage": {"2009": 11, "2010": 11},
                    "total homes": {"2009": 1000, "2010": 1000},
                    "new homes": {"2009": 0, "2010": 0},
                    "electricity": {
                        "heating": {
                            "demand": {
                                "wall": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 0, "2010": 0}},
                                "roof": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 1, "2010": 1}}}},
                        "cooling": {
                            "demand": {
                                "wall": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 5, "2010": 5}},
                                "roof": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 6, "2010": 6}}}}
                    }
                }
            },
            "ERCT": {
                "assembly": {
                    "total square footage": {"2009": 11, "2010": 11},
                    "new square footage": {"2009": 0, "2010": 0},
                    "electricity": {
                        "heating": {
                            "demand": {
                                "wall": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 0, "2010": 0}},
                                "roof": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 1, "2010": 1}},
                                "lighting gain": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": -7, "2010": -7}}}},
                        "cooling": {
                            "demand": {
                                "wall": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 5, "2010": 5}},
                                "roof": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 6, "2010": 6}},
                                "lighting gain": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 6, "2010": 6}}}},
                        "lighting": {
                            "T5 F28": {
                                "stock": "NA",
                                "energy": {
                                    "2009": 11, "2010": 11}}},
                        "PCs": {
                            "stock": "NA",
                            "energy": {"2009": 12, "2010": 12}},
                        "MELs": {
                            "distribution transformers": {
                                "stock": "NA",
                                "energy": {"2009": 24, "2010": 24}
                            }
                        }
                    }
                },
                "single family home": {
                    "total square footage": {"2009": 11, "2010": 11},
                    "total homes": {"2009": 1000, "2010": 1000},
                    "new homes": {"2009": 0, "2010": 0},
                    "electricity": {
                        "heating": {
                            "demand": {
                                "wall": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 0, "2010": 0}},
                                "roof": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 1, "2010": 1}}}},
                        "cooling": {
                            "demand": {
                                "wall": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 5, "2010": 5}},
                                "roof": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 6, "2010": 6}}}}
                    }
                }
            }}


ok_out_emm_metrics_mkts = [{
            "stock": {
                "total": {
                    "all": {"2009": 11000000 * 1000/(11*1000000),
                            "2010": 11000000 * 1000/(11*1000000)},
                    "measure": {"2009": 11000000 * 1000/(11*1000000),
                                "2010": 11000000 * 1000/(11*1000000)}},
                "competed": {
                    "all": {"2009": 11000000 * 1000/(11*1000000),
                            "2010": 11000000 * 1000/(11*1000000)},
                    "measure": {"2009": 11000000 * 1000/(11*1000000),
                                "2010": 11000000 * 1000/(11*1000000)}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 0.0004722848327,
                                 "2010": 0.0004737653494},
                    "efficient": {"2009": 0.0004722848327,
                                  "2010": 0.0004737653494}},
                "competed": {
                    "baseline": {"2009": 0.0004722848327,
                                 "2010": 0.0004737653494},
                    "efficient": {"2009": 0.0004722848327,
                                  "2010": 0.0004737653494}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 0.02664545748, "2010": 0.02640982197},
                    "efficient": {
                        "2009": 0.02664545748, "2010": 0.02640982197}},
                "competed": {
                    "baseline": {"2009": 0.02664545748, "2010": 0.02640982197},
                    "efficient": {
                        "2009": 0.02664545748, "2010": 0.02640982197}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}},
                    "competed": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}}},
                "energy": {
                    "total": {
                        "baseline": {
                            "2009": 0.005350888907, "2010": 0.005054352136},
                        "efficient": {
                            "2009": 0.005350888907, "2010": 0.005054352136}},
                    "competed": {
                        "baseline": {
                            "2009": 0.005350888907, "2010": 0.005054352136},
                        "efficient": {
                            "2009": 0.005350888907, "2010": 0.005054352136}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 0.8793000969, "2010": 0.871524125},
                        "efficient": {
                            "2009": 0.8793000969, "2010": 0.871524125}},
                    "competed": {
                        "baseline": {
                            "2009": 0.8793000969, "2010": 0.871524125},
                        "efficient": {
                            "2009": 0.8793000969, "2010": 0.871524125}}}},
            "lifetime": {"baseline": {"2009": 15, "2010": 15},
                         "measure": 1}},
            # Note: this measure tests sector-level savings shapes without
            # other TSV settings. Note that in such a case, the code will only
            # conduct hourly valuations on loads, not costs or emissions, thus
            # costs and emissions do not reflect TSV scaling factors
            {
            "stock": {
                "total": {
                    "all": {"2009": 11000000 * 1000/(11*1000000),
                            "2010": 11000000 * 1000/(11*1000000)},
                    "measure": {"2009": 11000000 * 1000/(11*1000000),
                                "2010": 11000000 * 1000/(11*1000000)}},
                "competed": {
                    "all": {"2009": 11000000 * 1000/(11*1000000),
                            "2010": 11000000 * 1000/(11*1000000)},
                    "measure": {"2009": 11000000 * 1000/(11*1000000),
                                "2010": 11000000 * 1000/(11*1000000)}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 3.19, "2010": 3.2},
                    "efficient": {"2009": 3.19 * 0.5, "2010": 3.2 * 0.5}},
                "competed": {
                    "baseline": {"2009": 3.19, "2010": 3.2},
                    "efficient": {"2009": 3.19 * 0.5, "2010": 3.2 * 0.5}}},
            "carbon": {
                "total": {
                    "baseline": {
                        "2009": 181.342,
                        "2010": 179.7383},
                    "efficient": {
                        "2009": 181.342 * 0.5,
                        "2010": 179.7383 * 0.5}},
                "competed": {
                    "baseline": {
                        "2009": 181.342,
                        "2010": 179.7383},
                    "efficient": {
                        "2009": 181.342 * 0.5,
                        "2010": 179.7383 * 0.5}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}},
                    "competed": {
                        "baseline": {"2009": 16500000, "2010": 16500000},
                        "efficient": {"2009": 16500000, "2010": 16500000}}},
                "energy": {
                    "total": {
                        "baseline": {
                            "2009": 28.9652,
                            "2010": 27.36},
                        "efficient": {
                            "2009": 28.9652 * 0.5,
                            "2010": 27.36 * 0.5}},
                    "competed": {
                        "baseline": {
                            "2009": 28.9652,
                            "2010": 32.37694687 / 1.183367941},
                        "efficient": {
                            "2009": 28.9652 * 0.5,
                            "2010": 27.36 * 0.5}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 5836.413654 / 0.9752898084,
                            "2010": 5784.800117 / 0.9752898084},
                        "efficient": {
                            "2009": (5836.413654 / 0.9752898084) * 0.5,
                            "2010": (5784.800117 / 0.9752898084) * 0.5}},
                    "competed": {
                        "baseline": {
                            "2009": 5836.413654 / 0.9752898084,
                            "2010": 5784.800117 / 0.9752898084},
                        "efficient": {
                            "2009": (5836.413654 / 0.9752898084) * 0.5,
                            "2010": (5784.800117 / 0.9752898084) * 0.5}}}},
            "lifetime": {"baseline": {"2009": 15, "2010": 15},
                         "measure": 1}}]


sample_mseg_in_aia = {
            "AIA_CZ1": {
                "single family home": {
                    "total square footage": {"2009": 100, "2010": 200},
                    "total homes": {"2009": 1000, "2010": 1000},
                    "new homes": {"2009": 100, "2010": 50},
                    "electricity": {
                      "heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 0, "2010": 0}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 1, "2010": 1}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {"2009": 10, "2010": 10}}},
                            "supply": {
                                "resistance heat": {
                                    "stock": {"2009": 2, "2010": 2},
                                    "energy": {"2009": 2, "2010": 2}},
                                "ASHP": {
                                    "stock": {"2009": 3, "2010": 3},
                                    "energy": {"2009": 3, "2010": 3}},
                                "GSHP": {
                                    "stock": {"2009": 4, "2010": 4},
                                    "energy": {"2009": 4, "2010": 4}}}},
                      "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 5, "2010": 5}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 6, "2010": 6}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {"2009": 10, "2010": 10}}},
                            "supply": {
                                "central AC": {
                                    "stock": {"2009": 7, "2010": 7},
                                    "energy": {"2009": 7, "2010": 7}},
                                "room AC": {
                                    "stock": {"2009": 8, "2010": 8},
                                    "energy": {"2009": 8, "2010": 8}},
                                "ASHP": {
                                    "stock": {"2009": 9, "2010": 9},
                                    "energy": {"2009": 9, "2010": 9}},
                                "GSHP": {
                                    "stock": {"2009": 10, "2010": 10},
                                    "energy": {"2009": 10, "2010": 10}}}}
                    },
                    "natural gas": {
                        "water heating": {
                            "stock": {"2009": 15, "2010": 15},
                            "energy": {"2009": 15, "2010": 15}}}}},
            "AIA_CZ2": {
                "single family home": {
                    "total square footage": {"2009": 500, "2010": 600},
                    "total homes": {"2009": 1000, "2010": 1000},
                    "new homes": {"2009": 100, "2010": 50},
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 0, "2010": 0}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 1, "2010": 1}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {"2009": 10, "2010": 10}}},
                            "supply": {
                                "resistance heat": {
                                    "stock": {"2009": 2, "2010": 2},
                                    "energy": {"2009": 2, "2010": 2}},
                                "ASHP": {
                                    "stock": {"2009": 3, "2010": 3},
                                    "energy": {"2009": 3, "2010": 3}},
                                "GSHP": {
                                    "stock": {"2009": 4, "2010": 4},
                                    "energy": {"2009": 4, "2010": 4}}}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 5, "2010": 5}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 6, "2010": 6}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {"2009": 10, "2010": 10}}},
                            "supply": {
                                "central AC": {
                                    "stock": {"2009": 7, "2010": 7},
                                    "energy": {"2009": 7, "2010": 7}},
                                "room AC": {
                                    "stock": {"2009": 8, "2010": 8},
                                    "energy": {"2009": 8, "2010": 8}},
                                "ASHP": {
                                    "stock": {"2009": 9, "2010": 9},
                                    "energy": {"2009": 9, "2010": 9}},
                                "GSHP": {
                                    "stock": {"2009": 10, "2010": 10},
                                    "energy": {"2009": 10, "2010": 10}}}}}}}}


def _convert_numpy_strings_to_python(obj):
    """Recursively convert numpy strings to Python strings in nested data structures.

    This fixes KeyError issues when looking up dictionary keys that are numpy.str_ objects
    with regular Python str objects.
    """
    import numpy as np

    if isinstance(obj, np.str_):
        return str(obj)
    elif isinstance(obj, dict):
        return {_convert_numpy_strings_to_python(k): _convert_numpy_strings_to_python(v)
                for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_convert_numpy_strings_to_python(item) for item in obj)
    else:
        return obj


# Apply conversion to all data structures to ensure numpy strings are converted
sample_cpl_in_aia = _convert_numpy_strings_to_python(sample_cpl_in_aia)
sample_cpl_in_emm = _convert_numpy_strings_to_python(sample_cpl_in_emm)
ok_out_emm_features = _convert_numpy_strings_to_python(ok_out_emm_features)
sample_mseg_in_emm = _convert_numpy_strings_to_python(sample_mseg_in_emm)
ok_out_emm_metrics_mkts = _convert_numpy_strings_to_python(ok_out_emm_metrics_mkts)
sample_mseg_in_aia = _convert_numpy_strings_to_python(sample_mseg_in_aia)
