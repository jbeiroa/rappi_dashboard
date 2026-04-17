import typer
import asyncio
from typing import List, Optional
import os
import time
from src.scraper.rappi import scrape_rappi_by_address, save_to_json
from src.dashboard.app import app as dashboard_app

app = typer.Typer(help="Rappi Competitive Intelligence CLI")

@app.command()
def scrape_rappi(
    address: str = typer.Option("Calle Polanco, Polanco V Sección 11560 Miguel Hidalgo, Ciudad de México", "--address", "-a", help="The address to set on Rappi"),
    restaurant: str = typer.Option("Mc Donald's", "--restaurant", "-r", help="The restaurant to search for"),
    products: Optional[List[str]] = typer.Option(
        ["Big Mac + Coca", "Coca-Cola Zero mediana", "McTrío Hamb con Queso"], 
        "--product", "-p", 
        help="Products to scrape prices for"
    ),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Whether to run the browser in headless mode"),
):
    """
    Scrapes Rappi for a specific restaurant and products at a given address.
    Saves results to a structured JSON file.
    """
    typer.echo(f"Starting Rappi scraper...")
    typer.echo(f"Address: {address}")
    typer.echo(f"Restaurant: {restaurant}")
    typer.echo(f"Products: {', '.join(products)}")
    
    data = asyncio.run(scrape_rappi_by_address(address, restaurant, products, headless=headless))
    save_to_json(data)
    
    typer.echo("Scraping completed successfully.")

@app.command()
def scrape_all_addresses(
    addresses_file: str = typer.Option("data/raw/addresses.csv", "--file", "-f", help="CSV file with addresses"),
    restaurant: str = typer.Option("Mc Donald's", "--restaurant", "-r", help="The restaurant to search for"),
    products: Optional[List[str]] = typer.Option(
        ["Big Mac + Coca", "Coca-Cola Zero mediana", "McTrío Hamb con Queso"], 
        "--product", "-p", 
        help="Products to scrape prices for"
    ),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Whether to run the browser in headless mode"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit the number of addresses to scrape"),
):
    """
    Iterates through all addresses in the CSV and scrapes the restaurant benchmark.
    Saves results to a structured JSON file.
    """
    import pandas as pd
    if not os.path.exists(addresses_file):
        typer.echo(f"Error: {addresses_file} not found.")
        raise typer.Exit()
    
    df = pd.read_csv(addresses_file)
    address_list = df["address"].tolist()
    
    if limit:
        address_list = address_list[:limit]
        
    typer.echo(f"Starting benchmark for {len(address_list)} addresses...")
    
    for i, address in enumerate(address_list):
        typer.echo(f"[{i+1}/{len(address_list)}] Scraping: {address}")
        try:
            data = asyncio.run(scrape_rappi_by_address(address, restaurant, products, headless=headless))
            save_to_json(data)
            # Adaptive delay to avoid detection
            import random
            time_to_wait = random.uniform(5, 15)
            typer.echo(f"Success. Waiting {time_to_wait:.1f}s...")
            time.sleep(time_to_wait)
        except Exception as e:
            typer.echo(f"Failed scraping {address}: {e}")
            continue
    
    typer.echo("Full benchmark completed.")

@app.command()
def dashboard():
    """
    Launches the Plotly Dash dashboard.
    """
    typer.echo("Launching dashboard...")
    dashboard_app.run_server(debug=True)

if __name__ == "__main__":
    app()
