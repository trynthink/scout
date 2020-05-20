-- 20 April 2020

CREATE SCHEMA IF NOT EXISTS ${schema};

-- ---------------------------------------------------------------------------
-- Table `ecm`
--
-- For the purpose of the tests, the following fields should be populated
-- for use by ecm_prep.py and run.py: id, name, definition
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${schema}.ecm
(
    id             integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name           varchar(255) UNIQUE NOT NULL,
    definition     jsonb               NOT NULL,
    energy_use     numeric,
    co2_emissions  numeric,
    operating_cost numeric,
    is_default     boolean,
    is_silence     boolean,
    control_status varchar(45)         NOT NULL,
    type           varchar(45)         NOT NULL,
    status         varchar(45)         NOT NULL,
    comments       varchar(512),
    created_by     integer,
    created_at     timestamptz,
    updated_by     integer,
    updated_at     timestamptz,
    run_at         timestamptz,
    finished_at    timestamptz
);

-- ---------------------------------------------------------------------------
-- Table `ecm_data`
--
-- All of these fields should be populated for testing purposes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${schema}.ecm_data
(
    id                 integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    ecm_id             integer     NOT NULL
        references ${schema}.ecm (id),
    energy_calc_method varchar(70) NOT NULL,
    uncomp_data        jsonb       NOT NULL,
    comp_data          jsonb       NOT NULL,
    constraint ${schema}_ecm_data_ecm_id_energy_calc_method_uniq UNIQUE (ecm_id, energy_calc_method)
);

-- ---------------------------------------------------------------------------
-- Table `analysis`
--
-- For the purpose of developing the tests, the only fields that should be
-- populated by run.py are: ecm_id, ecm_results, energy_calc_method
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${schema}.analysis
(
    id                 integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name               varchar(255) NOT NULL,
    is_default         boolean,
    control_status     varchar(45)  NOT NULL,
    status             varchar(45)  NOT NULL,
    comments           varchar(512),
    ecm_results        jsonb,
    energy_calc_method varchar(70)  NOT NULL,
    created_by         integer,
    created_at         timestamptz,
    updated_by         integer,
    updated_at         timestamptz,
    run_at             timestamptz,
    finished_at        timestamptz
);

-- ---------------------------------------------------------------------------
-- Table `analysis_ecms`
--
-- Maintains the many-to-one mapping of ecms associated with an analysis
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${schema}.analysis_ecms
(
    id                 integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    analysis_id        integer      NOT NULL
        references ${schema}.analysis (id),
    ecm_id             integer      NOT NULL
        references ${schema}.ecm (id),
    constraint ${schema}_analysis_ecms_analysis_id_ecm_id_uniq UNIQUE (analysis_id, ecm_id)
);

-- ---------------------------------------------------------------------------
-- View `ecm_data_view`
--
-- This view is for convenience to join the ecm name with the ecm_data table
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW ${schema}.ecm_data_view AS
SELECT ecm_id, name, energy_calc_method, uncomp_data, comp_data
FROM scout_db.ecm_data,
     scout_db.ecm
WHERE ecm_id = ecm.id;

-- ---------------------------------------------------------------------------
-- View `analysis_view`
--
-- This view is for convenience to join the ecm_ids with the analysis table
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW ${schema}.analysis_view AS
SELECT analysis.*, coalesce(ecm_ids, '[]'::jsonb) as ecm_ids
FROM scout_db.analysis
         LEFT JOIN (SELECT analysis_id, ('[' || string_agg(ecm_id::text, ',' ORDER BY ecm_id) || ']')::jsonb as ecm_ids
                    FROM scout_db.analysis_ecms
                    GROUP BY analysis_id) as aggregation ON aggregation.analysis_id = analysis.id;
