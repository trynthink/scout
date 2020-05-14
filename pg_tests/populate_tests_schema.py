#!/usr/bin/env python3
from dateutil.parser import parse
from string import Template
from os import walk
import gzip
import json
import pickle
import psycopg2
import sys
sys.path.append('../')
from common import db, tzinfos


schema = db['schema'] + '_tests'

conn = psycopg2.connect(
    user=db['user'],
    password=db['password'],
    host=db['host'],
    port=db['port'],
    database=db['name'])
cursor = conn.cursor()

# Destroy and recreate schema
cursor.execute('DROP SCHEMA IF EXISTS ' + schema + ' CASCADE')
conn.commit()
ddl_template = Template(open('../DDL.sql', 'r').read())
ddl = ddl_template.substitute({'schema': schema})

cursor.execute(ddl)

# Populate ecm table
ecm_definitions = []
for (root, dirs, files) in walk('../ecm_definitions'):
    for file in files:
        if file.endswith('.json') and file != 'package_ecms.json':
            ecm_definitions.append(file)
    break

for ecm in ecm_definitions:
    with open('../ecm_definitions/' + ecm) as file:
        definition = json.load(file)

    name = definition['name']
    added_at = parse(definition['_added_by']['timestamp'], tzinfos=tzinfos).strftime('%Y-%m-%d %H:%M:%S %z')

    updated_at = None
    if isinstance(definition['_updated_by'], list) and definition['_updated_by'][-1]['timestamp'] is not None:
        updated_at = parse(definition['_updated_by'][-1]['timestamp'], tzinfos=tzinfos).strftime('%Y-%m-%d %H:%M:%S %z')
    elif isinstance(definition['_updated_by'], dict) and definition['_updated_by']['timestamp'] is not None:
        updated_at = parse(definition['_updated_by']['timestamp'], tzinfos=tzinfos).strftime('%Y-%m-%d %H:%M:%S %z')

    print('Inserting ecm: ' + name)
    cursor.execute('INSERT INTO ' + schema + '.ecm '
                   '(name, definition, created_at, updated_at, control_status, type, status) '
                   'VALUES (%s, %s, %s, %s, \'\', \'\', \'\')',
                   (name, json.dumps(definition), added_at, updated_at))

conn.commit()

# Create dict of ecm ids
ecm_ids = {}
cursor.execute('SELECT name, id FROM ' + schema + '.ecm')
rows = cursor.fetchall()
for row in rows:
    ecm_ids[row[0]] = row[1]

# Populate ecm_data table
competition_results = []
for (root, dirs, files) in walk('../supporting_data/ecm_competition_data'):
    for file in files:
        if file.endswith('.pkl.gz'):
            competition_results.append(file)
    break

with open('../supporting_data/ecm_prep.json') as file:
    all_uncomp_data = json.load(file)

for result in competition_results:
    with gzip.open('../supporting_data/ecm_competition_data/' + result, 'rb') as file:
        comp_data = pickle.load(file)

    name = result[:-7]
    uncomp_data = list(filter(lambda record: record['name'] == name, all_uncomp_data))[0]

    print('Inserting data: ' + name)
    if name in ecm_ids:
        ecm_id = ecm_ids[name]
        cursor.execute('INSERT INTO ' + schema + '.ecm_data '
                       '(ecm_id, energy_calc_method, uncomp_data, comp_data) '
                       'VALUES (%s, \'\', %s, %s)', (ecm_id, json.dumps(uncomp_data), json.dumps(comp_data)))
    else:
        raise Exception('ECM "' + name + '" not found in ecm table')

conn.commit()

# Populate analysis table
with open('../results/ecm_results.json') as file:
    results = json.load(file)

for name, ecm_result in results.items():
    print('Inserting analysis: ' + name)
    if name in ecm_ids:
        ecm_id = ecm_ids[name]
        cursor.execute('INSERT INTO ' + schema + '.analysis '
                       '(ecm_id, ecm_results, control_status, status) '
                       'VALUES (%s, %s, \'\', \'\')', (ecm_id, json.dumps(ecm_result)))
    else:
        raise Exception('ECM "' + name + '" not found in ecm table')

conn.commit()
cursor.close()
conn.close()
