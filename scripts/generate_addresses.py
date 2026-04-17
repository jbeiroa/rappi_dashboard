import re
import pandas as pd
import os

def generate_addresses(input_file="docs/scraper_research.md", output_file="data/raw/addresses.csv"):
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract table rows
    # Pattern: | # | Alcaldía / Municipio | Colonia / Zona | NSE | ... |
    # We want clusters 1, 2, 3, 4
    rows = re.findall(r'\| \d+ \| ([^|]+) \| ([^|]+) \| ([^|]+) \|', content)
    
    addresses = []
    for row in rows:
        municipio = row[0].strip()
        colonia = row[1].strip()
        # Full address: Colonia, Municipio, CDMX (or correct state)
        # Note: scraper_research.md identifies clusters by state
        # I'll add a simplified state mapping
        state = "Ciudad de México"
        if municipio in ["Monterrey", "San Pedro Garza García", "Guadalupe", "Apodaca", "Santa Catarina", "San Nicolás de los Garza"]:
            state = "Nuevo León"
        elif municipio in ["Guadalajara", "Zapopan", "Tlajomulco de Zúñiga"]:
            state = "Jalisco"
        elif municipio in ["Querétaro", "San Pedro Cholula", "Puebla"]:
            # Actually Querétaro is a city/state, Puebla is a city/state
            if municipio == "Querétaro": state = "Querétaro"
            else: state = "Puebla"
            
        full_address = f"{colonia}, {municipio}, {state}"
        addresses.append(full_address)
    
    df = pd.DataFrame(addresses, columns=["address"])
    os.makedirs("data/raw", exist_ok=True)
    df.to_csv(output_file, index=False)
    print(f"Generated {len(addresses)} addresses in {output_file}")

if __name__ == "__main__":
    generate_addresses()
