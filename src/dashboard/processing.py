import pandas as pd
import os

def load_and_clean_data(filename: str = "data/raw/rappi_scrape.csv"):
    """
    Loads raw scrape data and performs basic cleaning.
    """
    if not os.path.exists(filename):
        # Return an empty dataframe with expected columns if file doesn't exist
        return pd.DataFrame(columns=["timestamp", "restaurant_name", "delivery_fee", "eta"])
    
    df = pd.read_csv(filename)
    
    # Simple cleaning logic
    # Convert "$10" -> 10.0
    if "delivery_fee" in df.columns:
        df["delivery_fee_clean"] = df["delivery_fee"].str.replace(r'[^0-9.]', '', regex=True).astype(float, errors='ignore')
    
    # Convert "20 min" -> 20
    if "eta" in df.columns:
        df["eta_clean"] = df["eta"].str.replace(r'[^0-9.]', '', regex=True).astype(float, errors='ignore')
        
    return df
