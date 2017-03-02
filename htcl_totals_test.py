#!/usr/bin/env python3

""" Tests for running the htcl_totals.py routine """

# Import code to be tested
import htcl_totals

# Import needed packages
import unittest
import itertools


class CommonMethods(object):
    """Define common methods for use in all tests below."""

    def dict_check(self, dict1, dict2):
        """Check the equality of two dicts.

        Args:
            dict1 (dict): First dictionary to be compared
            dict2 (dict): Second dictionary to be compared

        Raises:
            AssertionError: If dictionaries are not equal.
        """
        # zip() and zip_longest() produce tuples for the items
        # identified, where in the case of a dict, the first item
        # in the tuple is the key and the second item is the value;
        # in the case where the dicts are not of identical size,
        # zip_longest() will use the fill value created below as a
        # substitute in the dict that has missing content; this
        # value is given as a tuple to be of comparable structure
        # to the normal output from zip_longest()
        fill_val = ('substituted entry', 5.2)

        # In this structure, k and k2 are the keys that correspond to
        # the dicts or unitary values that are found in i and i1,
        # respectively, at the current level of the recursive
        # exploration of dict1 and dict1, respectively
        for (k, i), (k2, i2) in itertools.zip_longest(sorted(dict1.items()),
                                                      sorted(dict2.items()),
                                                      fillvalue=fill_val):
            # Confirm that at the current location in the dict structure,
            # the keys are equal; this should fail if one of the dicts
            # is empty, is missing section(s), or has different key names
            self.assertEqual(k, k2)

            # If the recursion has not yet reached the terminal/leaf node
            if isinstance(i, dict):
                # Test that the dicts from the current keys are equal
                self.assertCountEqual(i, i2)
                # Continue to recursively traverse the dict
                self.dict_check(i, i2)
            else:
                # At the terminal/leaf node, formatted as a point value
                self.assertAlmostEqual(i, i2, places=2)


class SumHtClEnergyTest(unittest.TestCase, CommonMethods):
    """Test operation of 'sum_htcl_energy' function.

    Verify that function properly sums all heating and cooling energy for
    a given climate zone, building type, and structure type combination,
    converting from site to source energy in the process.

    Attributes:
        aeo_years (list): Modeling time horizon.
        ss_conv (dict): Site-source conversion factors.
        ok_msegs_in (dict): Sample stock/energy data to use in developing sums.
        ok_out (dict): Sum totals that should be yielded by function given
            valid sample inputs.
    """

    @classmethod
    def setUpClass(cls):
        """Define objects/variables for use across all class functions."""
        cls.aeo_years = ["2009", "2010"]
        cls.ss_conv = {
            "electricity": {"2009": 3, "2010": 4},
            "natural gas": {"2009": 1, "2010": 1},
            "distillate": {"2009": 1, "2010": 1},
            "other fuel": {"2009": 1, "2010": 1}}
        cls.ok_msegs_in = {
            "AIA_CZ1": {
                "single family home": {
                    "new homes": {"2009": 1, "2010": 1},
                    "total homes": {"2009": 10, "2010": 10},
                    "total square footage": {"2009": 100, "2010": 100},
                    "electricity": {
                        "lighting": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}},
                        "heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "secondary heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "cooling": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "water heating": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}}},
                    "natural gas": {
                        "heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "secondary heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "water heating": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}}}},
                "assembly": {
                    "new square footage": {"2009": 1, "2010": 1},
                    "total square footage": {"2009": 5, "2010": 5},
                    "electricity": {
                        "lighting": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}},
                        "heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "cooling": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "refrigeration": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}}
                    },
                    "distillate": {
                        "heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "water heating": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}}}}},
            "AIA_CZ2": {
                "single family home": {
                    "new homes": {"2009": 1, "2010": 1},
                    "total homes": {"2009": 100, "2010": 100},
                    "total square footage": {"2009": 1000, "2010": 1000},
                    "electricity": {
                        "lighting": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}},
                        "heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "secondary heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "cooling": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "water heating": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}}},
                    "natural gas": {
                        "heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "secondary heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "water heating": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}}}},
                "assembly": {
                    "new square footage": {"2009": 1, "2010": 1},
                    "total square footage": {"2009": 10, "2010": 10},
                    "electricity": {
                        "lighting": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}},
                        "heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "cooling": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "refrigeration": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}}
                    },
                    "distillate": {
                        "heating": {
                            "supply": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}},
                            "demand": {
                                "tech 1": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}},
                                "tech 2": {
                                    "stock": {"2009": 1, "2010": 1},
                                    "energy": {"2009": 1, "2010": 1}}}},
                        "water heating": {
                            "tech 1": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}},
                            "tech 2": {
                                "stock": {"2009": 1, "2010": 1},
                                "energy": {"2009": 1, "2010": 1}}}}}}}
        cls.ok_out = {
            "AIA_CZ1": {
                "single family home": {
                    "new": {"2009": 2.2, "2010": 5.6},
                    "existing": {"2009": 19.8, "2010": 22.4}
                },
                "assembly": {
                    "new": {"2009": 2.8, "2010": 7.2},
                    "existing": {"2009": 11.2, "2010": 10.8}
                }},
            "AIA_CZ2": {
                "single family home": {
                    "new": {"2009": 0.22, "2010": 0.56},
                    "existing": {"2009": 21.78, "2010": 27.44}
                },
                "assembly": {
                    "new": {"2009": 1.4, "2010": 3.6},
                    "existing": {"2009": 12.6, "2010": 14.4}
                }}}

    def test_ok(self):
        """Test for correct function output given valid inputs."""
        self.dict_check(
            htcl_totals.sum_htcl_energy(
                self.ok_msegs_in, self.aeo_years, self.ss_conv),
            self.ok_out)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    """Trigger default behavior of running all test fixtures in the file."""
    unittest.main()

if __name__ == "__main__":
    main()
