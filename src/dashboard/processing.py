import pandas as pd
import os
import json
import glob

def load_and_clean_data():
    """
    Loads raw scrape data from JSON files and returns a unified DataFrame.
    Supports timestamped and non-timestamped files.
    """
    all_data = []
    
    file_patterns = {
        "Rappi": "data/raw/rappi_products*.json",
        "Uber Eats": "data/raw/uber_products*.json",
        "Chedraui": "data/raw/chedraui_products*.json"
    }
    
    for app_name, pattern in file_patterns.items():
        files = glob.glob(pattern)
        for filepath in files:
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
    
    # Check if 'scraped_product_name' exists
    if "scraped_product_name" not in df.columns:
        df["scraped_product_name"] = "Not Found"
        
    # Exclude Not Found to avoid skewing price numbers
    df = df[df["scraped_product_name"] != "Not Found"].copy()
    
    if df.empty:
        return df

    # Cleaning and numeric conversion
    df["delivery_fee_clean"] = pd.to_numeric(df.get("delivery_fee"), errors='coerce').fillna(0.0)
    df["eta_clean"] = pd.to_numeric(df.get("eta"), errors='coerce').fillna(0.0)
    df["final_price_clean"] = pd.to_numeric(df.get("final_price"), errors='coerce').fillna(0.0)
    df["original_price_clean"] = pd.to_numeric(df.get("original_price"), errors='coerce').fillna(df["final_price_clean"])
    df["discount_amount_clean"] = pd.to_numeric(df.get("discount_amount"), errors='coerce').fillna(0.0)
    
    df["city"] = df.get("city", "Unknown").fillna("Unknown")
    df["municipality"] = df.get("municipality", "Unknown").fillna("Unknown")
    
    # Filter out 0 prices to avoid bad data
    df = df[df["final_price_clean"] > 0].copy()
    
    # Derived metrics
    df["total_price"] = df["final_price_clean"] + df["delivery_fee_clean"]
    df["is_promoted"] = df["discount_amount_clean"] > 0
    df["discount_pct"] = (df["discount_amount_clean"] / df["original_price_clean"].replace(0, 1)) * 100
    
    # Categorize products
    retail_keywords = ["coca-cola", "leche", "sabritas", "papas", "agua"]
    def get_category(row):
        target = str(row.get("target_product", "")).lower()
        store = str(row.get("store_name", "")).lower()
        if any(k in target for k in retail_keywords) or "chedraui" in store:
            return "Retail"
        return "Restaurante"

    df["category"] = df.apply(get_category, axis=1)
        
    return df
