import typer
import asyncio
from src.scraper.rappi import scrape_rappi_restaurant, save_to_csv
from src.dashboard.app import app as dashboard_app

app = typer.Typer(help="Rappi Competitive Intelligence CLI")

@app.command()
def scrape_rappi(
    url: str = typer.Argument(..., help="The URL of the Rappi restaurant to scrape"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Whether to run the browser in headless mode"),
):
    """
    Scrapes a Rappi restaurant and saves the results to a CSV.
    """
    typer.echo(f"Starting Rappi scraper for: {url}")
    data = asyncio.run(scrape_rappi_restaurant(url, headless=headless))
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
