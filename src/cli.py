import typer
import asyncio
from typing import List, Optional
import os
import time
import json
import pandas as pd
import random
from src.scraper.rappi import scrape_rappi_by_address, save_to_json as save_rappi, get_available_products
from src.scraper.uber_eats import scrape_uber_eats_by_address, save_to_json as save_uber
from src.scraper.chedraui import scrape_chedraui_by_address, save_to_json as save_chedraui
from src.dashboard.app import app as dashboard_app

app = typer.Typer(help="Delivery Competitive Intelligence CLI")

def clear_data():
    """Removes existing raw data files."""
    for f in ["data/raw/rappi_products.json", "data/raw/uber_products.json", "data/raw/chedraui_products.json"]:
        if os.path.exists(f):
            os.remove(f)
            typer.echo(f"Cleared {f}")

@app.command()
def clean():
    """Clears all scraped data to start fresh."""
    clear_data()

@app.command()
def benchmark(
    vendor: str = typer.Option("all", "--vendor", "-v", help="rappi, uber, or all"),
    restaurant: str = typer.Option("McDonald's", "--restaurant", "-r"),
    headless: bool = typer.Option(True, "--headless/--no-headless"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l"),
    renew: bool = typer.Option(False, "--renew/--no-renew"),
    timestamp: bool = typer.Option(False, "--timestamp/--no-timestamp", help="Append timestamp to filename"),
):
    """Benchmark for RESTAURANTS (McDonald's)."""
    if renew:
        clear_data()

    run_id = datetime.now().strftime("%Y%m%d_%H%M") if timestamp else None
    
    address_file = "data/raw/resolved_addresses.csv"
    if not os.path.exists(address_file):
        address_file = "data/raw/addresses.csv"

    df = pd.read_csv(address_file)
    if limit:
        df = df.head(limit)

    current_time_mexico = pd.Timestamp.now(tz='America/Mexico_City')
    if current_time_mexico.hour < 12:
        products = ["McTrío Desayuno Deluxe", "Café Americano grande", "Desayuno para 2"]
    else:
        products = ["Coca-Cola mediana", "Big Mac", "McTrío Hamb con Queso"]

    vendors = ["rappi", "uber"] if vendor == "all" else [vendor]
    
    for v in vendors:
        typer.echo(f"--- {v.upper()} Restaurant Benchmark ---")
        filename = f"data/raw/{v}_products_{run_id}.json" if run_id else None
        
        for i, row in df.iterrows():
            addr, lat, lng = row["original_address"], row.get("lat"), row.get("lng")
            parts = [p.strip() for p in addr.split(',')]
            municipality = parts[1] if len(parts) > 1 else "Unknown"
            city = parts[2] if len(parts) > 2 else "Unknown"
            
            try:
                if v == "rappi":
                    data = asyncio.run(scrape_rappi_by_address(addr, restaurant, products, headless=headless, lat=lat, lng=lng, city=city, municipality=municipality))
                    save_rappi(data, filename=filename)
                elif v == "uber":
                    data = asyncio.run(scrape_uber_eats_by_address(addr, restaurant, products, headless=headless, lat=lat, lng=lng, city=city, municipality=municipality))
                    save_uber(data, filename=filename)
                time.sleep(random.uniform(5, 10))
            except Exception as e:
                typer.echo(f"  Error: {e}")

@app.command()
def benchmark_retail(
    vendor: str = typer.Option("all", "--vendor", "-v", help="rappi, uber, chedraui, or all"),
    headless: bool = typer.Option(True, "--headless/--no-headless"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l"),
    renew: bool = typer.Option(False, "--renew/--no-renew"),
    timestamp: bool = typer.Option(False, "--timestamp/--no-timestamp", help="Append timestamp to filename"),
):
    """Benchmark for RETAIL products (Chedraui) across all three vendors."""
    if renew:
        for f in ["data/raw/rappi_products.json", "data/raw/uber_products.json", "data/raw/chedraui_products.json"]:
            if os.path.exists(f): os.remove(f)

    run_id = datetime.now().strftime("%Y%m%d_%H%M") if timestamp else None

    address_file = "data/raw/resolved_addresses.csv"
    if not os.path.exists(address_file):
        address_file = "data/raw/addresses.csv"

    df = pd.read_csv(address_file)
    if limit: df = df.head(limit)

    products = ["Coca-Cola Original 600 ml", "Leche Alpura Entera 1 L", "Papas Sabritas Sal 42 g"]

    vendors = ["rappi", "uber", "chedraui"] if vendor == "all" else [vendor]
    
    for v in vendors:
        typer.echo(f"--- {v.upper()} Retail Benchmark (Chedraui) ---")
        filename = f"data/raw/{v}_products_{run_id}.json" if run_id else None

        for i, row in df.iterrows():
            addr, lat, lng = row["original_address"], row.get("lat"), row.get("lng")
            parts = [p.strip() for p in addr.split(',')]
            mun, city = (parts[1] if len(parts) > 1 else "N/A"), (parts[2] if len(parts) > 2 else "N/A")
            
            try:
                if v == "rappi":
                    data = asyncio.run(scrape_rappi_by_address(addr, "Chedraui", products, headless=headless, lat=lat, lng=lng, city=city, municipality=mun))
                    save_rappi(data, filename=filename)
                elif v == "uber":
                    data = asyncio.run(scrape_uber_eats_by_address(addr, "Chedraui", products, headless=headless, lat=lat, lng=lng, city=city, municipality=mun))
                    save_uber(data, filename=filename)
                elif v == "chedraui":
                    data = asyncio.run(scrape_chedraui_by_address(addr, products, headless=headless, lat=lat, lng=lng, city=city, municipality=mun))
                    save_chedraui(data, filename=filename)
                time.sleep(random.uniform(5, 10))
            except Exception as e:
                typer.echo(f"  Error: {e}")

@app.command()
def dashboard():
    """Launches the Plotly Dash dashboard."""
    typer.echo("Launching dashboard on port 8051...")
    dashboard_app.run(debug=True, port=8051)

if __name__ == "__main__":
    app()
