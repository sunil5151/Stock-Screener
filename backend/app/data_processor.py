import pandas as pd
import numpy as np

class DataProcessor:
    """Handles data loading, validation, and preprocessing"""
    
    def __init__(self):
        self.df = None
        self.date_col = None
    
    def load_csv(self, file_path):
        """Load CSV file and return raw dataframe"""
        try:
            self.df = pd.read_csv(file_path)
            print(f"Loaded {len(self.df)} rows from {file_path}")
            return self.df
        except Exception as e:
            raise ValueError(f"Error loading CSV: {e}")
    
    def set_datetime_index(self):
        """Find datetime column and set it as index"""
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        
        # Try to find a suitable datetime column
        possible_cols = ['Timestamp', 'Date', 'Datetime', 'Time']
        
        for col in possible_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col])
                self.df.set_index(col, inplace=True)
                self.date_col = col
                print(f"Set '{col}' as datetime index")
                return True
        
        raise ValueError(
            "No suitable date column found. "
            "Rename your date column to 'Timestamp', 'Date', 'Datetime', or 'Time'."
        )
    
    def validate_ohlcv_columns(self):
        """Validate that required OHLCV columns exist"""
        if self.df is None:
            raise ValueError("No data loaded.")
        
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in self.df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        print("All OHLCV columns found ✓")
        return True
    
    def clean_data(self):
        """Keep only OHLCV columns and clean data"""
        if self.df is None:
            raise ValueError("No data loaded.")
        
        # Keep only required columns
        self.df = self.df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        
        # Remove any NaN values
        initial_rows = len(self.df)
        self.df.dropna(inplace=True)
        final_rows = len(self.df)
        
        if initial_rows != final_rows:
            print(f"Removed {initial_rows - final_rows} rows with NaN values")
        
        print(f"Data cleaned. Final shape: {self.df.shape}")
        return self.df
    
    def process_data(self, file_path):
        """Complete data processing pipeline"""
        self.load_csv(file_path)
        self.set_datetime_index()
        self.validate_ohlcv_columns()
        return self.clean_data()
    
    def get_data(self):
        """Return processed dataframe"""
        if self.df is None:
            raise ValueError("No data processed. Call process_data() first.")
        return self.df.copy()
    
    def get_data_info(self):
        """Return basic information about the dataset"""
        if self.df is None:
            return "No data loaded"
        
        return {
            'rows': len(self.df),
            'columns': list(self.df.columns),
            'date_range': f"{self.df.index.min()} to {self.df.index.max()}",
            'date_column': self.date_col
        }