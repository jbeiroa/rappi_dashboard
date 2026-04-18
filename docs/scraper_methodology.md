# Metodología de Desarrollo de Scrapers

Este documento detalla el enfoque técnico, los retos superados y las soluciones implementadas durante el desarrollo de los scrapers para el sistema de Inteligencia Competitiva.

## 🎯 Objetivo
Extraer con precisión precios (original, final, descuento), tarifas de envío y tiempos de entrega (ETA) para productos benchmark en 50 ubicaciones estratégicas de México.

## ✅ Rappi: Resiliencia y Flexibilidad
- **Bypass de Búsqueda:** Se optó por navegar directamente a la URL de búsqueda (`/busqueda?query=...`) para evitar la inestabilidad de los inputs dinámicos en la UI.
- **Lógica de Escape de Hubs:** Rappi suele redirigir a "hubs" de marca. El scraper detecta esto y selecciona automáticamente el primer enlace con ID numérico para llegar al menú real.
- **Fuzzy Matching:** El uso de `rapidfuzz` permite mapear nombres de productos (ej. "Big Mac") incluso con variaciones regionales o caracteres especiales.

## ✅ Uber Eats: Extracción Basada en Contenido
- **Reto de Selectores Dinámicos:** Uber Eats utiliza nombres de clases CSS altamente ofuscados y cambiantes.
- **Solución:** Se implementó una lógica de extracción basada en la inspección total del `body` usando expresiones regulares (Regex) para identificar ETAs y costos de envío (buscando patrones como "MXN", "$" y "min").
- **Coincidencia Difusa:** Se aplica un umbral de coincidencia del 80% para asegurar que el benchmark compare productos equivalentes.

## ✅ Chedraui (Retail): Geocodificación y CPs
- **Validación de Ubicación:** A diferencia de los agregadores, Chedraui requiere un Código Postal (CP) para mostrar inventario y precios reales.
- **Extracción de CPs:** Se mejoró el script `resolve_addresses.py` para capturar el CP directamente desde los resultados de Google Maps durante la fase de resolución de direcciones.
- **Navegación VTEX:** Se adaptaron los selectores para manejar la arquitectura SPA de la plataforma Chedraui, asegurando la carga completa de las tarjetas de producto.

## ❌ Lo que no funcionó (DiDi Food)
- **Bloqueo por Login:** DiDi Food requiere obligatoriamente una cuenta vinculada a un número telefónico mexicano para acceder a menús y precios. Sin un dispositivo físico local, el acceso automatizado fue inviable. Esta investigación está documentada en `docs/didi_investigation.md`.

## 🛠 Automatización y Versionado
- **Timestamps:** Cada ejecución genera archivos únicos (`rappi_products_20260418_1200.json`) permitiendo análisis históricos de precios sin sobrescribir datos previos.
- **CI/CD con GitHub Actions:** Se configuró un flujo de trabajo que ejecuta los benchmarks automáticamente (Lunes y Viernes) y carga los archivos JSON a una carpeta segura de Google Drive utilizando una Service Account.

## 🔑 Insumos Clave del Usuario
- **Paleta de Colores Rappi:** Aseguró que el dashboard final sea visualmente coherente con la marca (#f6553f).
- **XPath de Uber:** La precisión de un XPath específico para métricas permitió resolver inconsistencias iniciales en la extracción de Uber Eats.
- **Horarios de Menú:** La lógica distingue automáticamente entre el menú de Desayuno (antes de las 12 PM) y el de Comida/Cena basándose en la hora local de CDMX.
