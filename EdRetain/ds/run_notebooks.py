import subprocess
import sys
from pathlib import Path
from loguru import logger

NOTEBOOKS = [
    "RFM_KPI.ipynb",
    "churn_probability.ipynb", 
    "kmeans.ipynb",
    "survival_analysis.ipynb",
    "CLV.ipynb",
    "Campaign Analysis.ipynb",
]

def run_notebook(notebook_path):
    """Execute single notebook"""
    notebook_name = Path(notebook_path).name
    logger.info(f"Running: {notebook_name}")
    
    cmd = [
        "jupyter", "nbconvert",
        "--to", "notebook",
        "--execute", 
        "--inplace",
        notebook_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logger.info(f"SUCCESS: {notebook_name}")
            return True
        else:
            logger.error(f"FAILED: {notebook_name}")
            logger.error(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"TIMEOUT: {notebook_name} (5 min)")
        return False

def main():
    logger.info("AUTO-EXECUTING JUPYTER NOTEBOOKS")
    logger.info("=" * 50)
    
    success_count = 0
    existing_notebooks = [n for n in NOTEBOOKS if Path(n).exists()]
    
    for notebook in NOTEBOOKS:
        if Path(notebook).exists():
            if run_notebook(notebook):
                success_count += 1
        else:
            logger.warning(f"SKIPPED (not found): {notebook}")
    
    logger.info("=" * 50)
    logger.info(f"COMPLETE: {success_count}/{len(existing_notebooks)}")
    
    return 0 if success_count == len(existing_notebooks) else 1

if __name__ == "__main__":
    sys.exit(main())
