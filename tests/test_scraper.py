import os
import pandas as pd
from src.scraper.rappi import save_to_csv

def test_save_to_csv(tmp_path):
    # Setup
    test_data = {
        "timestamp": "2026-04-17T12:00:00",
        "url": "https://test.com",
        "restaurant_name": "Test Restaurant",
        "delivery_fee": "$10",
        "eta": "20 min"
    }
    test_file = tmp_path / "test_scrape.csv"
    
    # Act
    save_to_csv(test_data, filename=str(test_file))
    
    # Assert
    assert os.path.exists(test_file)
    df = pd.read_csv(test_file)
    assert len(df) == 1
    assert df.iloc[0]["restaurant_name"] == "Test Restaurant"
