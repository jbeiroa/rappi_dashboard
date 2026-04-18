# Dashboard de Inteligencia Competitiva para Rappi

Este proyecto es una evaluación técnica para Rappi, enfocada en la construcción de un sistema de inteligencia competitiva resiliente y automatizado para el mercado de delivery en México. Cuenta con scrapers especializados para **Rappi**, **Uber Eats** y **Chedraui**, utilizando Playwright, y un dashboard en Plotly Dash para visualizar métricas clave de rendimiento.

## 🚀 Descripción General

El sistema está diseñado para navegar las complejidades del ecosistema de delivery en México. Prioriza la resiliencia técnica, la precisión de la geolocalización y la generación de insights estratégicos accionables, permitiendo comparativas tanto en el sector de restaurantes (ej. McDonald's) como en retail (ej. Supermercados).

### Capacidades Actuales
- **Scraping Multi-Vendor (Playwright + Stealth):** Extracción de alta fidelidad desde las interfaces web de Rappi, Uber Eats y Chedraui, manejando contenido dinámico y redirecciones complejas.
- **Geolocalización Precisa:** Resolución automática de 50 direcciones estratégicas a coordenadas exactas (lat/lng) y Códigos Postales, asegurando comparativas precisas por zona.
- **Pipeline de Datos Automatizado:** Extracción de datos a JSON versionados por fecha y hora, con limpieza y categorización automatizada usando `pandas`.
- **Automatización CI/CD:** Flujo de GitHub Actions configurado para ejecutar los benchmarks automáticamente dos veces por semana y subir los resultados a Google Drive de forma segura.
- **Dashboard Interactivo:** Aplicación en Plotly Dash con un diseño de doble pestaña (Nacional y Local) que visualiza posicionamiento de precios, ventajas de tiempos de entrega (ETA), estructura de fees y estrategias promocionales.

## 🛠 Instalación

Este proyecto utiliza `uv` para la gestión de dependencias.

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

### 1. Scrapear una Dirección Específica
Para probar un scraper en una dirección particular:

```bash
PYTHONPATH=. uv run python -m src.cli scrape --vendor uber --address "Polanco, Miguel Hidalgo" --restaurant "McDonald's"
```

### 2. Ejecutar Benchmarks Completos
Los benchmarks procesan el listado de direcciones resueltas para recopilar datos a escala nacional.

```bash
# Benchmark de Restaurantes (Rappi y Uber Eats)
PYTHONPATH=. uv run python -m src.cli benchmark --vendor all --timestamp --no-headless

# Benchmark de Retail (Rappi, Uber Eats y Chedraui)
PYTHONPATH=. uv run python -m src.cli benchmark-retail --vendor all --timestamp
```

### 3. Lanzar el Dashboard
Para visualizar los datos (asegúrate de tener archivos JSON en `data/raw/`):

```bash
PYTHONPATH=. uv run python -m src.cli dashboard
```
El dashboard estará disponible en `http://127.0.0.1:8051/`.

### 4. Ejecutar Pruebas
```bash
PYTHONPATH=. uv run pytest tests/
```

## 🗺️ Estructura del Proyecto

- `src/`: Código fuente principal.
  - `scraper/`: Lógica de automatización para Rappi, Uber Eats y Chedraui.
  - `dashboard/`: Aplicación Dash y lógica de procesamiento de métricas.
- `scripts/`: Scripts de soporte para resolución de direcciones y carga a la nube.
- `tests/`: Suite de pruebas automatizadas.
- `data/`: Almacenamiento local para datasets (ignorado por git para evitar archivos pesados).
- `docs/`: Reportes de investigación y documentación de metodologías.
- `.github/workflows/`: Automatizaciones de ejecución programada.

---
*Nota: El desarrollo técnico se realiza en inglés para mantener estándares de ingeniería, pero la interfaz del Dashboard y la documentación principal se presentan en español para alinearse con los requerimientos de negocio regionales.*
