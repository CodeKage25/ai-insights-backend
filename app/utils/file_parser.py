import pandas as pd
import numpy as np
from typing import List, Any, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FileParseError(Exception):
    pass

def parse_file(filepath: str, max_rows: int = 5) -> Tuple[List[List[Any]], pd.DataFrame]:
    """
    Parse CSV/Excel file and return preview data + full DataFrame for analysis
    
    Returns:
        Tuple of (preview_data, full_dataframe)
    """
    try:
        path = Path(filepath)
        if not path.exists():
            raise FileParseError(f"File not found: {filepath}")
        
        # 
        if path.suffix.lower() == '.csv':
            # Read full dataset for analysis
            df_full = pd.read_csv(filepath)
            # Read limited rows for preview
            df_preview = pd.read_csv(filepath, nrows=max_rows)
        elif path.suffix.lower() in ['.xls', '.xlsx']:
            df_full = pd.read_excel(filepath, engine='openpyxl')
            df_preview = pd.read_excel(filepath, nrows=max_rows, engine='openpyxl')
        else:
            raise FileParseError(f"Unsupported file type: {path.suffix}")
        
        # Convert preview to list format
        preview_data = []
        
        # Add headers
        headers = df_preview.columns.tolist()
        preview_data.append(headers)
        
        # Add data rows, handling NaN values
        for _, row in df_preview.iterrows():
            row_data = []
            for value in row:
                if pd.isna(value):
                    row_data.append(None)
                elif isinstance(value, (np.integer, np.floating)):
                    row_data.append(float(value) if isinstance(value, np.floating) else int(value))
                else:
                    row_data.append(str(value))
            preview_data.append(row_data)
        
        logger.info(f"Successfully parsed file: {filepath} ({len(df_full)} rows, {len(df_full.columns)} columns)")
        return preview_data, df_full
        
    except Exception as e:
        logger.error(f"Error parsing file {filepath}: {str(e)}")
        raise FileParseError(f"Failed to parse file: {str(e)}")
