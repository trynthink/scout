#!/usr/bin/env python3
import gzip
import json
import pickle
import sys
from os import walk
from string import Template

import psycopg2
from dateutil.parser import parse

sys.path.append("../")
from common import db, tzinfos  # noqa: E402

schema = db["schema"] + "_tests"

conn = psycopg2.connect(
    user=db["user"], password=db["password"], host=db["host"], port=db["port"], database=db["name"],
)
cursor = conn.cursor()

# Destroy and recreate schema
cursor.execute("DROP SCHEMA IF EXISTS " + schema + " CASCADE")
conn.commit()
ddl_template = Template(open("../DDL.sql", "r").read())
ddl = ddl_template.substitute({"schema": schema})

cursor.execute(ddl)

# Populate ecm table
ecm_definitions = []
for (root, dirs, files) in walk("../ecm_definitions"):
    for file in files:
        if file.endswith(".json") and file != "package_ecms.json":
            ecm_definitions.append(file)
    break

for ecm in ecm_definitions:
    with open("../ecm_definitions/" + ecm) as file:
        definition = json.load(file)

    name = definition["name"]
    added_at = parse(definition["_added_by"]["timestamp"], tzinfos=tzinfos).strftime(
        "%Y-%m-%d %H:%M:%S %z"
    )

    updated_at = None
    if (
        isinstance(definition["_updated_by"], list)
        and definition["_updated_by"][-1]["timestamp"] is not None
    ):
        updated_at = parse(definition["_updated_by"][-1]["timestamp"], tzinfos=tzinfos).strftime(
            "%Y-%m-%d %H:%M:%S %z"
        )
    elif (
        isinstance(definition["_updated_by"], dict)
        and definition["_updated_by"]["timestamp"] is not None
    ):
        updated_at = parse(definition["_updated_by"]["timestamp"], tzinfos=tzinfos).strftime(
            "%Y-%m-%d %H:%M:%S %z"
        )

    print("Inserting ecm: " + name)
    cursor.execute(
        "INSERT INTO " + schema + ".ecm "
        "(name, definition, created_at, updated_at, control_status, type, status) "
        "VALUES (%s, %s, %s, %s, '', '', '')",
        (name, json.dumps(definition), added_at, updated_at),
    )

conn.commit()

# Create dict of ecm ids
ecm_ids = {}
cursor.execute("SELECT name, id FROM " + schema + ".ecm")
rows = cursor.fetchall()
for row in rows:
    ecm_ids[row[0]] = row[1]

# Populate ecm_data table
competition_results = []
for (root, dirs, files) in walk("../supporting_data/ecm_competition_data"):
    for file in files:
        if file.endswith(".pkl.gz"):
            competition_results.append(file)
    break

with open("../supporting_data/ecm_prep.json") as file:
    all_uncomp_data = json.load(file)

for result in competition_results:
    with gzip.open("../supporting_data/ecm_competition_data/" + result, "rb") as file:
        comp_data = pickle.load(file)

    name = result[:-7]
    uncomp_data = list(filter(lambda record: record["name"] == name, all_uncomp_data))[0]

    print("Inserting data: " + name)
    if name in ecm_ids:
        ecm_id = ecm_ids[name]
        cursor.execute(
            "INSERT INTO " + schema + ".ecm_data "
            "(ecm_id, energy_calc_method, uncomp_data, comp_data) "
            "VALUES (%s, '', %s, %s)",
            (ecm_id, json.dumps(uncomp_data), json.dumps(comp_data)),
        )
    else:
        raise Exception('ECM "' + name + '" not found in ecm table')

conn.commit()

# Populate analysis table with ecms 1 and 3
ecm_results = {}
with open("../results/ecm_results.json") as file:
    all_results = json.load(file)

# Add ecm 1
name = ecm_definitions[0][:-5]
ecm_results[name] = all_results[name]

# Add ecm 3
name = ecm_definitions[1][:-5]
ecm_results[name] = all_results[name]

print("Inserting analysis")
cursor.execute(
    "INSERT INTO " + schema + ".analysis "
    "(name, energy_calc_method, ecm_results, control_status, status) "
    "VALUES (%s, '', %s, '', '')",
    ("My Analysis", json.dumps(ecm_results)),
)

# Add foreign key constraints for ecms
cursor.execute(
    "INSERT INTO " + schema + ".analysis_ecms "
    "(analysis_id, ecm_id) "
    "VALUES (%s, %s), (%s, %s)",
    (1, 1, 1, 3),
)

conn.commit()
cursor.close()
conn.close()
