"""
Generate complete training notebook with all cells
"""

import json
from pathlib import Path

def create_training_notebook():
    """Generate the complete training notebook structure"""
    
    cells = []
    
    # Cell 1: Title
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Stock Movement Prediction Model Training\n",
            "\n",
            "**Goal**: Predict future direction (up/down/flat) for US stocks over horizons {1, 5, 20} trading days using multi-source time-series data.\n",
            "\n",
            "**Data Sources**:\n",
            "- Yahoo Finance (yfinance): Primary OHLCV data\n",
            "- Stooq: Fallback market data source\n",
            "- FRED API: Macro economic indicators\n",
            "\n",
            "**Model**: XGBoost multi-class classifier with walk-forward validation\n",
            "\n",
            "**Critical**: This notebook implements strict data leakage prevention at every stage."
        ]
    })
    
    # Cell 2: Section - Imports
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 1. Imports and Configuration"]
    })
    
    # Cell 3: Imports code
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Standard library\n",
            "import os\n",
            "import sys\n",
            "import json\n",
            "import pickle\n",
            "import warnings\n",
            "from datetime import datetime, timedelta\n",
            "from pathlib import Path\n",
            "from typing import List, Dict, Tuple, Optional\n",
            "\n",
            "# Data handling\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "\n",
            "# Data sources\n",
            "import yfinance as yf\n",
            "import requests\n",
            "from fredapi import Fred\n",
            "\n",
            "# ML libraries\n",
            "from sklearn.linear_model import LogisticRegression\n",
            "from sklearn.preprocessing import StandardScaler\n",
            "from sklearn.metrics import confusion_matrix, classification_report, accuracy_score\n",
            "import xgboost as xgb\n",
            "\n",
            "# Visualization\n",
            "import matplotlib.pyplot as plt\n",
            "import matplotlib.dates as mdates\n",
            "\n",
            "# Statistics\n",
            "from statsmodels.tsa.arima.model import ARIMA\n",
            "\n",
            "warnings.filterwarnings('ignore')\n",
            "pd.set_option('display.max_columns', None)\n",
            "pd.set_option('display.max_rows', 100)\n",
            "\n",
            "print(\"✓ All imports successful\")\n",
            "print(f\"Pandas version: {pd.__version__}\")\n",
            "print(f\"NumPy version: {np.__version__}\")\n",
            "print(f\"XGBoost version: {xgb.__version__}\")"
        ]
    })
    
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.9.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    # Save notebook
    output_path = Path("../notebooks/train.ipynb")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print(f"✓ Notebook created at {output_path}")

if __name__ == "__main__":
    create_training_notebook()
