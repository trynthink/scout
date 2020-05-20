#!/usr/bin/env python3
import json
import re
import sys
import unittest
from os import walk

import psycopg2

sys.path.append("../")
from common import db  # noqa: E402


class PostgreSQLTest(unittest.TestCase):
    """Test connectivity and queries against the test schema"""

    conn = None
    cursor = None
    schema = None

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        cls.is_snake_case = re.compile("^[a-z]+(?:_[a-z]+)*$").match

    @classmethod
    def tearDownClass(cls):
        if cls.cursor is not None:
            cls.cursor.close()
        if cls.conn is not None:
            cls.conn.close()

    def test_0_environment(self):
        """Check environment variables"""
        self.assertIsNotNone(db["host"])
        self.assertGreater(len(db["host"]), 0)
        self.assertIsNotNone(db["name"])
        self.assertTrue(self.is_snake_case(db["name"]))
        self.assertIsNotNone(db["schema"])
        self.assertTrue(self.is_snake_case(db["schema"]))
        self.assertIsNotNone(db["user"])
        self.assertGreater(len(db["user"]), 0)
        self.assertIsNotNone(db["password"])
        self.assertGreater(len(db["password"]), 0)
        self.assertGreater(db["port"], 1023)

        PostgreSQLTest.schema = db["schema"] + "_tests"

    def test_1_connection(self):
        """Ensure PostgreSQL connection"""
        try:
            PostgreSQLTest.conn = psycopg2.connect(
                user=db["user"],
                password=db["password"],
                host=db["host"],
                port=db["port"],
                database=db["name"],
            )
        except psycopg2.Error as e:
            print("Unable to connect")
            print(e.pgerror)
            print(e.diag.message_detail)
            sys.exit(1)
        else:
            PostgreSQLTest.cursor = PostgreSQLTest.conn.cursor()

    def test_populated_ecms(self):
        """Ensure that the ecms table is populated and the row count matches the filesystem"""
        ecm_files = []
        ecm_names = []
        for (root, dirs, files) in walk("../ecm_definitions"):
            for file in files:
                if file.endswith(".json") and file != "package_ecms.json":
                    ecm_files.append(file)
            break

        self.assertGreater(len(ecm_files), 0)

        for filename in ecm_files:
            with open("../ecm_definitions/" + filename) as file:
                definition = json.load(file)
                ecm_names.append(definition["name"])

        unique_names = set(ecm_names)
        self.assertEqual(len(unique_names), len(ecm_files))

        query = "SELECT name, definition FROM " + self.schema + ".ecm"
        self.cursor.execute(query)
        response = self.cursor.fetchall()
        self.assertEqual(len(unique_names), len(response))

        for row in response:
            # Make sure name in database matches a file in the directory
            self.assertIn(row[0], unique_names)
            # Make sure the definition is non-empty
            self.assertGreater(len(row[1]), 0)

    def test_populated_ecm_data(self):
        """Ensure that the ecm_data table is populated and that all rows have populated uncomp and
        comp values"""
        query = "SELECT count(*) FROM " + self.schema + ".ecm_data"
        self.cursor.execute(query)
        response = self.cursor.fetchone()
        self.assertGreater(response[0], 0)

        # Make sure none of the uncomp/comp fields are empty dicts
        query = (
            "SELECT count(*) FROM "
            + self.schema
            + ".ecm_data WHERE uncomp_data <> '{}' AND comp_data <> '{}'"
        )
        self.cursor.execute(query)
        response = self.cursor.fetchone()
        self.assertGreater(response[0], 0)

    def test_ecm_data_view(self):
        # Check that the view is working as expected to add a name field
        query = "SELECT name FROM " + self.schema + ".ecm_data_view"
        self.cursor.execute(query)
        response = self.cursor.fetchone()
        self.assertGreater(len(response[0]), 0)

    def test_populated_analysis(self):
        """Ensure that the analysis table is populated and that all rows have populated
        ecm_results"""
        query = "SELECT count(*) FROM " + self.schema + ".analysis"
        self.cursor.execute(query)
        response = self.cursor.fetchone()
        self.assertGreater(response[0], 0)

        # Make sure none of the ecm_results fields are empty dicts
        query = "SELECT count(*) FROM " + self.schema + ".analysis WHERE ecm_results <> '{}'"
        self.cursor.execute(query)
        response = self.cursor.fetchone()
        self.assertGreater(response[0], 0)

        # Make sure the analysis has associated ecms
        query = "SELECT id FROM " + self.schema + ".analysis"
        self.cursor.execute(query)
        analysis_id = self.cursor.fetchone()[0]
        query = (
            "SELECT count(*) FROM "
            + self.schema
            + ".analysis_ecms WHERE analysis_id = %s" % analysis_id
        )
        self.cursor.execute(query)
        response = self.cursor.fetchone()
        self.assertGreater(response[0], 0)

    def test_analysis_view(self):
        # Check that the view is working as expected to create an ecm_ids jsonb field
        query = "SELECT ecm_ids FROM " + self.schema + ".analysis_view"
        self.cursor.execute(query)
        response = self.cursor.fetchone()
        self.assertGreater(len(response[0]), 0)


if __name__ == "__main__":
    unittest.main()
