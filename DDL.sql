CREATE SCHEMA IF NOT EXISTS ${schema};

-- ---------------------------------------------------------------------------
-- Table `ecm`
--
-- For the purpose of the tests, the following fields should be populated
-- for use by ecm_prep.py and run.py: id, name, definition
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${schema}.ecm
(
    id              integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name            varchar(255) UNIQUE NOT NULL,
    definition      jsonb               NOT NULL,
    load_shape_file varchar(150),
    is_package      boolean             NOT NULL,
    is_tsv          boolean,
    climate_zone    varchar(255)[],
    building_class  varchar(255)[],
    end_use         varchar(255)[],
    energy_use      numeric,
    co2_emissions   numeric,
    operating_cost  numeric,
    is_default      boolean,
    is_silence      boolean,
    control_status  varchar(45)         NOT NULL,
    type            varchar(45)         NOT NULL,
    status          varchar(45)         NOT NULL,
    comments        text,
    created_by      integer,
    created_at      timestamptz,
    updated_by      integer,
    updated_at      timestamptz,
    run_at          timestamptz,
    finished_at     timestamptz,
    send_for_review boolean
);

-- ---------------------------------------------------------------------------
-- Table `ecm_data`
--
-- All of these fields should be populated for testing purposes
-- ---------------------------------------------------------------------------
DO
$$
    BEGIN
        IF NOT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'tsv_perspectives') THEN
            CREATE TYPE ${schema}.tsv_perspectives AS ENUM ('','summer_peak', 'summer_off_peak', 'winter_peak', 'winter_off_peak');
        END IF;
        IF NOT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'calc_methods') THEN
            CREATE TYPE ${schema}.calc_methods AS ENUM ('site', 'captured', 'fossil_equivalent');
        END IF;
    END
$$;


CREATE TABLE IF NOT EXISTS ${schema}.ecm_data
(
    id                 integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    ecm_id             integer                NOT NULL
        REFERENCES ${schema}.ecm (id),
    energy_calc_method ${schema}.calc_methods NOT NULL,
    tsv_view           ${schema}.tsv_perspectives,
    uncomp_data        jsonb                  NOT NULL,
    comp_data          jsonb                  NOT NULL,
    CONSTRAINT ${schema}_ecm_data_ecm_id_tsv_view_energy_calc_method_uniq UNIQUE (ecm_id, tsv_view, energy_calc_method)
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
    comments           text,
    energy_calc_method ${schema}.calc_methods,
    has_tsv            boolean DEFAULT FALSE,
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
    id          integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    analysis_id integer NOT NULL
        REFERENCES ${schema}.analysis (id),
    ecm_id      integer NOT NULL
        REFERENCES ${schema}.ecm (id),
    CONSTRAINT ${schema}_analysis_ecms_analysis_id_ecm_id_uniq UNIQUE (analysis_id, ecm_id)
);

-- ---------------------------------------------------------------------------
-- Table `analysis_data`
--
-- Maintains the many-to-one mapping of json data with an analysis
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ${schema}.analysis_data
(
    id          integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    analysis_id integer NOT NULL
        REFERENCES ${schema}.analysis (id),
    tsv_view    ${schema}.tsv_perspectives,
    ecm_results jsonb,
    season      varchar(512),
    CONSTRAINT ${schema}_analysis_data_analysis_id_tsv_view_uniq UNIQUE (analysis_id, tsv_view)
);

-- ---------------------------------------------------------------------------
-- View `ecm_data_view`
--
-- This view is for convenience to join the ecm name with the ecm_data table
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW ${schema}.ecm_data_view AS
SELECT ecm_id, name, energy_calc_method, tsv_view, uncomp_data, comp_data
FROM ${schema}.ecm_data,
     ${schema}.ecm
WHERE ecm_id = ecm.id;

-- ---------------------------------------------------------------------------
-- View `analysis_view`
--
-- This view is for convenience to join the ecm_ids with the analysis table
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW ${schema}.analysis_view AS
SELECT analysis.*, data.season, data.ecm_results, COALESCE(ecm_ids, '[]'::jsonb) AS ecm_ids
FROM ${schema}.analysis
         LEFT JOIN (SELECT analysis_id, ('[' || STRING_AGG(ecm_id::text, ',' ORDER BY ecm_id) || ']')::jsonb AS ecm_ids
                    FROM ${schema}.analysis_ecms
                    GROUP BY analysis_id) AS aggregation ON aggregation.analysis_id = analysis.id
         LEFT JOIN (SELECT analysis_id, season, ecm_results
                    FROM ${schema}.analysis_data) AS data ON data.analysis_id = analysis.id;
