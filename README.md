# Dashboard de Inteligencia Competitiva para Rappi

Este proyecto es una evaluación técnica para Rappi, enfocada en la construcción de un sistema de inteligencia competitiva resiliente y automatizado para el mercado de delivery en México. Actualmente cuenta con un scraper especializado para Rappi utilizando Playwright y un dashboard en Plotly Dash para visualizar métricas clave de rendimiento.

## 🚀 Descripción General

El sistema está diseñado para navegar las complejidades del ecosistema de delivery en México (Rappi, Uber Eats, DiDi Food). Prioriza la resiliencia técnica, la precisión de la geolocalización y la generación de insights estratégicos accionables.

### Capacidades Actuales
- **Scraper con Playwright:** Extracción de alta fidelidad desde la interfaz web de Rappi, manejando contenido dinámico y SPAs.
- **CLI Personalizada:** Interfaz de línea de comandos unificada construida con `typer` para la gestión de scrapers y el dashboard.
- **Pipeline de Datos Automatizado:** Extracción de datos crudos a CSV con limpieza y normalización automatizada usando `pandas`.
- **Dashboard Interactivo:** Aplicación en Plotly Dash (en español) que visualiza Tarifas de Envío y ETAs a través de diferentes benchmarks de restaurantes.
- **Stack de Python Moderno:** Gestionado íntegramente con `uv` para una gestión de dependencias extremadamente rápida y reproducible.

## 🛠 Instalación

Este proyecto utiliza `uv`. Asegúrate de tenerlo instalado, luego ejecuta:

```bash
# Clonar el repositorio
git clone https://github.com/jbeiroa/rappi_dashboard.git
cd rappi_dashboard

# Sincronizar dependencias y crear entorno virtual
uv sync

# Instalar los navegadores de Playwright
uv run playwright install chromium
```

## 📖 Uso

Todas las operaciones se gestionan a través de la herramienta `src/cli.py`.

### 1. Scrapear un Restaurante
Para probar el scraper en una URL específica de un restaurante en Rappi:

```bash
# Ejecutar en modo headless (predeterminado)
PYTHONPATH=. uv run python -m src.cli scrape-rappi "https://www.rappi.com.mx/restaurantes/..."

# Ejecutar con el navegador visible (para inspección)
PYTHONPATH=. uv run python -m src.cli scrape-rappi "https://www.rappi.com.mx/restaurantes/..." --no-headless
```

### 2. Lanzar el Dashboard
Para visualizar los datos de inteligencia competitiva:

```bash
PYTHONPATH=. uv run python -m src.cli dashboard
```
El dashboard estará disponible en `http://127.0.0.1:8050/`.

### 3. Ejecutar Pruebas
```bash
PYTHONPATH=. uv run pytest
```

## 🗺️ Estructura del Proyecto

- `src/`: Código fuente principal.
  - `scraper/`: Lógica de automatización y extracción con Playwright.
  - `dashboard/`: Aplicación Dash y procesamiento de datos.
- `notebooks/`: Análisis exploratorio de datos (EDA) e investigación.
- `scripts/`: Scripts de utilidad ad-hoc.
- `tests/`: Suite de pruebas con Pytest.
- `data/`: Almacenamiento local para datasets `raw` y `processed` (ignorado por git).
- `docs/`: Instrucciones de la asignación y documentación de investigación.

## 📝 TODO / Próximos Pasos

- [ ] **Soporte Multi-Vendor:** Implementar scrapers para Uber Eats y DiDi Food.
- [ ] **Escalamiento Geográfico:** Automatizar el scraping en las 50 ubicaciones estratégicas identificadas en `docs/scraper_research.md`.
- [ ] **Evasión Avanzada:** Integrar rotación de proxies residenciales y plugins de sigilo (stealth).
- [ ] **Product Matching:** Implementar algoritmos de coincidencia difusa (fuzzy matching) para comparar productos idénticos en diferentes plataformas.
- [ ] **Despliegue:** Contenerizar la aplicación para despliegue en la nube (AWS/GCP).

---
*Nota: El desarrollo se realiza en inglés, pero la interfaz del Dashboard y la documentación principal (README) se presentan en español para alinearse con los requerimientos regionales.*
