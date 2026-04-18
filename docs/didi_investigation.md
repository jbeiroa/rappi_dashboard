# Investigación del Scraper de DiDi Food México

Este documento detalla los esfuerzos técnicos, las pruebas realizadas y las conclusiones sobre la viabilidad de extraer datos de DiDi Food México para este proyecto.

## 🔍 Intentos Realizados

1.  **Automatización de Navegador (Playwright + Stealth):**
    *   Se intentó navegar a la página principal (`didiglobal.com/food/mx/`) y a URLs directas de tiendas (ej. McDonald's Polanco) utilizando técnicas de evasión de detección de bots.
    *   **Resultado:** El sitio redirige automáticamente a un portal de inicio de sesión o a una "landing page" genérica que bloquea el acceso al menú y a los precios si no hay una sesión activa.

2.  **Acceso como Invitado (Guest Access):**
    *   Se probó forzar la entrada a través de la búsqueda y la selección de dirección manual en el navegador.
    *   **Resultado:** DiDi Food requiere obligatoriamente establecer una dirección y, en la mayoría de los flujos modernos de su web, solicita una validación de identidad (login) casi de inmediato para mostrar métricas operacionales reales (tarifas de envío y ETAs).

3.  **Análisis de API Pública (Developer Portal):**
    *   Se revisó la documentación oficial de la [OpenAPI de DiDi Food](https://developer.didi-food.com/es-MX/openapi).
    *   **Resultado:** Los endpoints están diseñados estrictamente para socios comerciales (merchants) y requieren un proceso de registro empresarial, aprobación de DiDi y credenciales de API vinculadas a una tienda real. No existe una API pública abierta para consulta de catálogos.

4.  **Ingeniería Inversa de Tráfico de Red:**
    *   Se inspeccionó el tráfico de red para identificar llamadas internas a microservicios de catálogo.
    *   **Resultado:** Las solicitudes están fuertemente protegidas por tokens de sesión dinámicos y firmas que se generan al autenticarse.

## ❌ Obstáculos Críticos (Blockers)

*   **Autenticación por SMS:** El inicio de sesión en DiDi Food requiere un número de teléfono mexicano para recibir un código de validación. Al no contar con un número local y físico, es imposible superar la barrera del login.
*   **Redirecciones Agresivas:** A diferencia de Rappi o Uber Eats, que permiten ver menús de forma limitada como invitado, DiDi Food ha "cerrado" su plataforma web significativamente en 2025-2026, priorizando el uso de la aplicación móvil.
*   **Geofencing Estricto:** La plataforma valida la consistencia entre la IP y la dirección solicitada, disparando retos de seguridad adicionales.

## 🏁 Conclusión

Actualmente, **DiDi Food México no es viable para scraping automatizado** bajo las condiciones de este proyecto debido a la dependencia absoluta de una cuenta autenticada con número telefónico mexicano. Se recomienda mover el enfoque hacia otros competidores con interfaces web más abiertas.
