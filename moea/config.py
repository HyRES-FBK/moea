from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

ENERGYPLAN_DIR = PROJ_ROOT / "EnergyPLAN"
ENERGYPLAN_EXE = ENERGYPLAN_DIR / "EnergyPLAN.exe"
ENERGYPLAN_DATA = ENERGYPLAN_DIR / "energyPLAN Data"
ENERGYPLAN_SPOOL = ENERGYPLAN_DIR / "spool"
ENERGYPLAN_RESULTS = ENERGYPLAN_SPOOL / "results"
ENERGYPLAN_COSTS_DIR = ENERGYPLAN_DATA / "Costs"
ENERGYPLAN_DATA_DIR = ENERGYPLAN_DATA / "Data"
ENERGYPLAN_DISTRIBUTIONS_DIR = ENERGYPLAN_DATA / "Distributions"

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
