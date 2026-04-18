import pandas as pd
import os
import json

def load_and_clean_data():
    """
    Loads raw scrape data from JSON files and returns a unified DataFrame.
    """
    files = {
        "Rappi": "data/raw/rappi_products.json",
        "Uber Eats": "data/raw/uber_products.json",
        "Chedraui": "data/raw/chedraui_products.json"
    }
    
    all_data = []
    
    for app_name, filepath in files.items():
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    for item in data:
                        if 'app_name' not in item: item['app_name'] = app_name
                    all_data.extend(data)
                except:
                    pass
    
    if not all_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_data)
    
    # Cleaning
    if "delivery_fee" in df.columns:
        df["delivery_fee_clean"] = pd.to_numeric(df["delivery_fee"], errors='coerce').fillna(0.0)
    
    if "eta" in df.columns:
        df["eta_clean"] = pd.to_numeric(df["eta"], errors='coerce').fillna(0.0)

    if "final_price" in df.columns:
        df["final_price_clean"] = pd.to_numeric(df["final_price"], errors='coerce')
    
    # Categorize products
    # If target product has retail keywords OR store name is Chedraui, mark as Retail
    retail_keywords = ["coca-cola", "leche", "sabritas", "papas", "agua"]
    
    def get_category(row):
        target = str(row.get("target_product", "")).lower()
        store = str(row.get("store_name", "")).lower()
        if any(k in target for k in retail_keywords) or "chedraui" in store:
            return "Retail"
        return "Restaurante"

    df["category"] = df.apply(get_category, axis=1)
        
    return df
