import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

FMU_PATH = os.getenv("DEFAULT_FMU_PATH", "models/fmus/PI_FOPDT.fmu")
FMU_NAME = Path(FMU_PATH).stem

SIM_PROMPT = """
You are an expert control engineer specializing in tuning and analyzing control systems through simulation experiments.
"""

# Alias for backward compatibility
SYS_PROMPT = f"""
# INSTRUCTIONS
{SIM_PROMPT}
"""
