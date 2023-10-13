from pathlib import Path


class FilePaths:
    # Package data:
    _root_dir = Path(__file__).resolve().parents[0]  # package install dir
    SUPPORTING_DATA = _root_dir / "supporting_data"
    THERMAL_LOADS = SUPPORTING_DATA / "thermal_loads_data"
    CONVERT_DATA = SUPPORTING_DATA / "convert_data"
    STOCK_ENERGY = SUPPORTING_DATA / "stock_energy_tech_data"
    TSV_DATA = SUPPORTING_DATA / "tsv_data"

    # Non-package data:
    _parent_dir = Path.cwd()  # parent dir of repo
    ECM_DEF = _parent_dir / "ecm_definitions"
    INPUTS = _parent_dir / "inputs"
    RESULTS = _parent_dir / "results"
    INT_FILES = _parent_dir / "int_files"
    METADATA_PATH = INPUTS / "metadata.json"
