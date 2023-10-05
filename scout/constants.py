from pathlib import Path


class FilePaths:
    _root_dir = Path(__file__).resolve().parents[1]
    INPUTS = _root_dir / "inputs"
    SUPPORTING_DATA = _root_dir / "supporting_data"
    THERMAL_LOADS = SUPPORTING_DATA / "thermal_loads_data"
    CONVERT_DATA = SUPPORTING_DATA / "convert_data"
    STOCK_ENERGY = SUPPORTING_DATA / "stock_energy_tech_data"
    TSV_DATA = SUPPORTING_DATA / "tsv_data"
    ECM_DEF = _root_dir / "ecm_definitions"
    METADATA_PATH = INPUTS / "metadata.json"
    RESULTS = Path.cwd() / "results"
