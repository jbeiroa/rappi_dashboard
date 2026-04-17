import typer
import asyncio
from typing import List, Optional
from src.scraper.rappi import scrape_rappi_by_address, save_to_csv
from src.dashboard.app import app as dashboard_app

app = typer.Typer(help="Rappi Competitive Intelligence CLI")

@app.command()
def scrape_rappi(
    address: str = typer.Option("Polanco, Miguel Hidalgo, CDMX", "--address", "-a", help="The address to set on Rappi"),
    restaurant: str = typer.Option("McDonald's", "--restaurant", "-r", help="The restaurant to search for"),
    products: Optional[List[str]] = typer.Option(
        ["Big Mac", "Combo Cuarto de Libra", "Coca-Cola 500ml"], 
        "--product", "-p", 
        help="Products to scrape prices for"
    ),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Whether to run the browser in headless mode"),
):
    """
    Scrapes Rappi for a specific restaurant and products at a given address.
    """
    typer.echo(f"Starting Rappi scraper...")
    typer.echo(f"Address: {address}")
    typer.echo(f"Restaurant: {restaurant}")
    typer.echo(f"Products: {', '.join(products)}")
    
    data = asyncio.run(scrape_rappi_by_address(address, restaurant, products, headless=headless))
    save_to_csv(data)
    
    typer.echo("Scraping completed successfully.")

@app.command()
def dashboard():
    """
    Launches the Plotly Dash dashboard.
    """
    typer.echo("Launching dashboard...")
    dashboard_app.run_server(debug=True)

if __name__ == "__main__":
    app()
