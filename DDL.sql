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
    comments       varchar(512)        NULL,
    created_by     integer             NULL,
    created_at     timestamptz,
    updated_by     integer             NULL,
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
    ecm_id             integer      NOT NULL
        references ${schema}.ecm (id),
    is_default         boolean,
    control_status     varchar(45)  NOT NULL,
    status             varchar(45)  NOT NULL,
    comments           varchar(512) NULL,
    ecm_results        jsonb,
    energy_calc_method varchar(70)  NULL,
    created_by         integer,
    created_at         timestamptz,
    updated_by         integer,
    updated_at         timestamptz,
    run_at             timestamptz,
    finished_at        timestamptz,
    constraint ${schema}_analysis_ecm_id_energy_calc_method_uniq UNIQUE (ecm_id, energy_calc_method)
);
