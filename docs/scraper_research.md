# **Arquitectura de un Sistema de Inteligencia Competitiva de Alto Rendimiento para el Mercado de Delivery en México**

La industria del delivery y el quick commerce en México se encuentra en una fase de madurez caracterizada por una competencia feroz entre tres actores principales: Rappi, Uber Eats y DiDi Food.1 En este ecosistema, la capacidad de recolectar, procesar y analizar datos en tiempo real no es simplemente una ventaja operativa, sino una necesidad existencial para los equipos de Pricing, Operations y Strategy. El mercado mexicano presenta una complejidad geográfica y socioeconómica única, donde las variables críticas como el precio final, los tiempos de entrega y las tarifas de servicio fluctúan no solo por ciudad, sino por colonia y hora del día.1 La construcción de un sistema automatizado de Competitive Intelligence requiere una arquitectura técnica que sea, ante todo, resiliente ante los mecanismos de detección y capaz de escalar a través de una geografía vasta y diversa.3

## **1\. Opciones de Diseño de Arquitectura para el Scraper**

El diseño de un scraper moderno para plataformas de delivery debe enfrentarse a sitios web y aplicaciones móviles que utilizan Single Page Applications (SPA) y renderizado dinámico de JavaScript.5 A continuación, se presentan tres opciones arquitectónicas fundamentadas en las tendencias de ingeniería de datos de 2025-2026.

### **1.1 Opción A: Automatización de Navegador con Playwright (Recomendada)**

Playwright se ha consolidado como la herramienta de elección para el scraping de alta fidelidad en sitios que dependen fuertemente del lado del cliente.7 A diferencia de sus predecesores, Playwright permite una manipulación más profunda del navegador a través del protocolo Chrome DevTools (CDP), lo que facilita la interceptación de solicitudes de red y la emulación de geolocalización precisa.3

La implementación bajo esta arquitectura se basa en el uso de "Browser Contexts". Un solo proceso de navegador puede gestionar múltiples contextos, cada uno con sus propias cookies, almacenamiento local y coordenadas GPS, lo que permite simular usuarios en diferentes direcciones de Ciudad de México o Monterrey de forma simultánea sin el consumo excesivo de memoria que implicaría abrir múltiples instancias de Chrome.7

| Atributo | Playwright | Selenium | Scrapy |
| :---- | :---- | :---- | :---- |
| **Arquitectura** | Event-driven (CDP) | WebDriver Protocol | Asynchronous (Twisted) |
| **Velocidad** | Alta (optimización de contextos) | Media-Baja | Muy Alta (solo texto) |
| **Manejo de JS** | Nativo y robusto | Nativo | Limitado (requiere plugins) |
| **Anti-detección** | Excelente (Stealth plugins) | Moderado | Bajo (basado en headers) |
| **Uso de Recursos** | Medio-Alto | Muy Alto | Muy Bajo |

Fuente: 5

### **1.2 Opción B: Ingeniería Inversa de APIs Internas (Enfoque de Eficiencia)**

Este enfoque prescinde de la interfaz gráfica y se comunica directamente con los endpoints que alimentan la aplicación.11 Para plataformas como Uber Eats, esto implica interceptar llamadas GraphQL y solicitudes POST a endpoints como getFeedV1 o getCatalogPresentationV2.11 La ventaja crítica aquí es el rendimiento: se descargan bytes de datos estructurados en JSON en lugar de megabytes de imágenes y scripts de seguimiento.11

Para ejecutar esta opción, el sistema debe replicar fielmente los headers de autenticación, incluyendo el x-csrf-token y cookies específicas como uev2.loc, que encapsula la ubicación del usuario en una cadena codificada.12 Aunque es el método más rápido, es el más frágil, ya que cualquier cambio en la firma de la API interna puede romper el scraper instantáneamente.4

### **1.3 Opción C: Arquitectura Híbrida Modular**

La arquitectura más robusta para un proyecto de nivel profesional es una solución híbrida que utiliza Playwright para la navegación inicial, el manejo de sesiones y el bypass de retos (como CAPTCHAs), y luego extrae los tokens de sesión para realizar solicitudes directas a la API para el scraping de menús a gran escala.3 Este diseño separa la "Capa de Identidad" (gestión de autenticación y huellas digitales del navegador) de la "Capa de Extracción" (solicitudes de datos de alto volumen).8

## **2\. Dependencias Críticas y Stack Tecnológico**

La elección de dependencias debe priorizar la estabilidad, el manejo de asincronía y la facilidad de mantenimiento. Dado que el proyecto se centra en Python, el ecosistema estándar de 2025 ofrece herramientas potentes para cada etapa del pipeline.4

* **Extracción y Automatización**: playwright es la dependencia central para el manejo de navegadores.7 Se complementa con playwright-stealth para evadir la detección de automatización básica y undetected-playwright si las protecciones de Cloudflare son particularmente agresivas.3  
* **Procesamiento de Red**: httpx se prefiere sobre requests por su soporte nativo para asyncio y HTTP/2, lo cual es vital para simular el comportamiento de un navegador moderno y evitar ser bloqueado por huellas digitales de TLS obsoletas.3  
* **Análisis de Datos (Parsing)**: BeautifulSoup4 con el parser lxml sigue siendo la norma para extraer datos de fragmentos HTML complejos que no están disponibles vía API.5  
* **Estructuración y Validación**: pydantic es esencial para definir esquemas de datos para los precios, tarifas y tiempos de entrega, asegurando que cualquier anomalía (como un precio negativo o un campo nulo) sea capturada antes de llegar a la base de datos.14  
* **Gestión de Datos**: pandas para la normalización y limpieza inicial, y SQLAlchemy como ORM para la persistencia en una base de datos relacional como PostgreSQL.14  
* **Orquestación**: Apache Airflow o Prefect para programar las ejecuciones del scraper en diferentes ventanas horarias (desayuno, almuerzo, cena) y manejar reintentos automáticos en caso de fallos de red o bloqueos de IP.14

## **3\. Estrategias Avanzadas de Extracción y Evasión**

El scraping de Uber Eats y DiDi Food en 2025 no es una tarea trivial de "fetch and parse". Estas plataformas emplean sistemas de seguridad basados en comportamiento y reputación de IP que pueden identificar y bloquear un scraper en cuestión de minutos si no se implementan las estrategias adecuadas.3

### **3.1 Gestión de Proxies y Geolocalización Residencial**

El uso de proxies de centros de datos (Datacenter IPs) es inútil para este propósito, ya que la mayoría de los rangos de IP de proveedores de nube (AWS, GCP, Azure) están marcados como "no residenciales" y bloqueados por defecto.17 La arquitectura debe integrar una red de **Proxies Residenciales Rotativos** con geocodificación específica en México.3 Esto permite que cada solicitud parezca provenir de una conexión de hogar real en ciudades como Guadalajara o Puebla.3

Para maximizar la tasa de éxito contra los sistemas de protección más estrictos, se recomienda el uso de **Proxies Móviles (4G/5G)**. Debido a que las direcciones IP móviles son compartidas por miles de usuarios legítimos, las plataformas de delivery no pueden bloquearlas fácilmente sin afectar a clientes reales.3 La sincronización entre la IP del proxy y las coordenadas GPS emuladas en el navegador es crítica: si una IP de Monterrey intenta reportar una ubicación de Santa Fe (CDMX), el sistema de fraude de la plataforma detectará la inconsistencia y servirá una página de error o un CAPTCHA.3

### **3.2 Rotación de User-Agents y Fingerprinting**

El scraper debe rotar no solo las direcciones IP, sino también sus "huellas digitales" (Fingerprints). Esto incluye el User-Agent, pero también variables de hardware como la resolución de pantalla, la memoria disponible del sistema, las fuentes instaladas y los contextos de WebGL.3 El uso de herramientas que randomizan el TLS Handshake es también una práctica recomendada en 2026 para evitar que el servidor identifique el cliente como una librería de Python en lugar de un navegador real.3

## **4\. Geografía de la Inteligencia: Selección de 50 Direcciones en México**

Como profesional argentino que aborda el mercado mexicano, es fundamental comprender que México no es un mercado monolítico. Se divide en zonas con dinámicas de precios y comportamientos de consumo radicalmente distintos, definidos en gran medida por los Niveles Socioeconómicos (NSE) establecidos por la AMAI.19 Para este benchmarking, se han seleccionado 50 direcciones representativas que cubren el espectro de ingresos, desde el ultra-premium (A/B) hasta la clase media emergente (C/D+) en las cinco zonas metropolitanas más importantes del país.21

### **4.1 Conceptos Clave de la Geografía Mexicana para el Scraper**

En México, el término "Colonia" equivale a lo que en Argentina se conoce como "Barrio". Las "Alcaldías" (en CDMX) o "Municipios" (en el resto del país) son las divisiones administrativas mayores. Entender estas divisiones es vital porque las plataformas de delivery a menudo aplican recargos por "zona de alta demanda" o "distancia extendida" basándose en estos límites.1

### **4.2 Listado de 50 Direcciones para Benchmarking Competitivo**

A continuación, se detalla la selección de direcciones dividida por clústeres estratégicos. Estas ubicaciones han sido elegidas por su densidad de restaurantes, presencia de marcas de referencia (McDonald's, Starbucks, Farmacias del Ahorro) y su relevancia para la toma de decisiones de Rappi.1

#### **Clúster 1: Ciudad de México y Área Metropolitana (CDMX / Edomex)**

Esta zona es el epicentro del delivery en el país y donde la competencia en Service Fees es más agresiva.26

| \# | Alcaldía / Municipio | Colonia / Zona | NSE | Justificación Estratégica |
| :---- | :---- | :---- | :---- | :---- |
| 1 | Miguel Hidalgo | Polanco | A/B | Zona de mayor ticket promedio en México; benchmark de lujo.28 |
| 2 | Cuajimalpa | Santa Fe (Vasco de Quiroga) | A/B | Centro corporativo; alta demanda en horarios de oficina.28 |
| 3 | Cuauhtémoc | Roma Norte | C+ | Barrio hípster con alta densidad de Dark Kitchens.28 |
| 4 | Cuauhtémoc | Condesa | C+ | Zona turística y residencial de alta frecuencia de pedidos. |
| 5 | Benito Juárez | Del Valle Centro | C+ | Corazón de la clase media-alta con logística eficiente.26 |
| 6 | Benito Juárez | Narvarte | C | Alta densidad poblacional y competencia de fast food. |
| 7 | Álvaro Obregón | San Ángel | A/B | Zona residencial exclusiva con retos de acceso para repartidores. |
| 8 | Coyoacán | Del Carmen | C+ | Destino gastronómico tradicional; calles estrechas y tráfico alto.26 |
| 9 | Iztapalapa | Lomas de Estrella | D+ | Zona de expansión masiva; clave para volumen de pedidos.26 |
| 10 | Azcapotzalco | Clavería | C | Barrio tradicional en transformación industrial-residencial.26 |
| 11 | Huixquilucan (Edomex) | Interlomas | A/B | "Isla" de lujo con tiempos de entrega largos por geografía.21 |
| 12 | Naucalpan (Edomex) | Ciudad Satélite | C+ | El principal hub comercial del norte del área metropolitana.21 |
| 13 | Tlalnepantla (Edomex) | Arboledas | C | Zona residencial consolidada con fuerte presencia de retail.29 |
| 14 | Gustavo A. Madero | Lindavista | C+ | Cercanía a hospitales y centros educativos; flujo constante.26 |
| 15 | Venustiano Carranza | Jardín Balbuena | C | Zona de alta densidad habitacional en el oriente de la ciudad. |

#### **Clúster 2: Monterrey y Zona Metropolitana (Nuevo León)**

Monterrey es el mercado con mayor gasto per cápita en delivery de alimentos en México.30

| \# | Municipio | Colonia / Zona | NSE | Justificación Estratégica |
| :---- | :---- | :---- | :---- | :---- |
| 16 | San Pedro Garza García | Valle del Campestre | A/B | El municipio más rico de Latinoamérica; benchmark premium.32 |
| 17 | San Pedro Garza García | Valle Oriente | A/B | Hub de oficinas de lujo y centros comerciales exclusivos.32 |
| 18 | Monterrey | Colinas de San Jerónimo | C+ | Zona de topografía difícil (cerros); prueba de fuego para ETAs.35 |
| 19 | Monterrey | Cumbres 4to Sector | C+ | Zona de familias jóvenes con alto consumo de grocery/retail.31 |
| 20 | Monterrey | Mitras Centro | C | Cercanía al área médica de la UANL; pedidos frecuentes y rápidos.30 |
| 21 | Monterrey | Contry | C+ | Zona residencial del sur; benchmark para tarifas de distancia.31 |
| 22 | San Nicolás de los Garza | Anáhuac | C+ | El "Sillicon Valley" regio; usuarios tecnológicamente avanzados.31 |
| 23 | Monterrey | Tecnológico | C+ | Zona estudiantil (Tec de Monterrey); alta demanda nocturna.33 |
| 24 | San Pedro Garza García | Del Valle (Calzada) | A/B | Centro comercial y de servicios de alta gama.32 |
| 25 | Guadalupe | Lindavista | C+ | Importante clúster residencial en el oriente de la metrópoli.30 |
| 26 | Monterrey | Obispado | C+ | Mezcla de servicios de salud, oficinas y departamentos.29 |
| 27 | Apodaca | Las Cruces | C | Zona industrial y logística con crecimiento de quick commerce.34 |
| 28 | Santa Catarina | Valle Poniente | B | Zona residencial de lujo en la periferia montañosa. |
| 29 | Monterrey | Vista Hermosa | C+ | Zona residencial tradicional con alta lealtad a marcas. |
| 30 | Monterrey | San Jerónimo (Torres) | B | Alta densidad vertical; retos de entrega en departamentos. |

#### **Clúster 3: Guadalajara y Zapopan (Jalisco)**

Conocida como la ciudad de las "propinas generosas" y una cultura gastronómica local muy fuerte.39

| \# | Municipio | Colonia / Zona | NSE | Justificación Estratégica |
| :---- | :---- | :---- | :---- | :---- |
| 31 | Zapopan | Puerta de Hierro | A/B | Exclusividad total; torres de departamentos y malls de lujo.40 |
| 32 | Guadalajara | Providencia | A/B | Epicentro gastronómico de la ciudad; alta densidad de pedidos.41 |
| 33 | Guadalajara | Chapalita | C+ | Barrio tradicional con alta penetración de apps de delivery.42 |
| 34 | Zapopan | Valle Real | A/B | Fraccionamiento cerrado; clave para medir acceso de couriers. |
| 35 | Guadalajara | Americana | C+ | Zona de jóvenes profesionales y vida nocturna activa. |
| 36 | Zapopan | Arcos de Zapopan | C | Zona de clase media típica para medir el "mass market". |
| 37 | Guadalajara | Ladrón de Guevara | C+ | Cercanía a zonas financieras; pedidos de oficina constantes. |
| 38 | Zapopan | Ciudad del Sol | C+ | Hub de servicios y retail con fácil acceso vial.43 |
| 39 | Tlajomulco de Zúñiga | San Jorge | C | Zona de expansión suburbana con ticket promedio bajo.42 |
| 40 | Guadalajara | Santa Teresita | D+ | Barrio tradicional con fuerte competencia de comercio local. |

#### **Clúster 4: Mercados de Crecimiento (Querétaro / Puebla)**

Ciudades que reciben el éxodo de habitantes de CDMX, con perfiles de consumo muy similares pero logística más sencilla.21

| \# | Ciudad | Colonia / Zona | NSE | Justificación Estratégica |
| :---- | :---- | :---- | :---- | :---- |
| 41 | Querétaro | Juriquilla | A/B | Hub educativo y residencial de alto nivel fuera del centro.21 |
| 42 | Querétaro | Zibatá | C+ | Comunidad planeada con retos logísticos de "última milla".21 |
| 43 | Querétaro | Centro Histórico | C | Zona turística; benchmark para repartidores en bicicleta.21 |
| 44 | Querétaro | El Campanario | A/B | El fraccionamiento más exclusivo del estado.21 |
| 45 | Querétaro | Milenio III | C+ | Zona de alta densidad y conectividad rápida.21 |
| 46 | Puebla | Lomas de Angelópolis | A/B | Megadesarrollo privado; ciudad dentro de la ciudad.21 |
| 47 | Puebla | Angelópolis (Mall) | A/B | Hub comercial más moderno de la región sur de México.21 |
| 48 | San Pedro Cholula | Centro | C+ | Ciudad universitaria; alta demanda de pizza y snacks.21 |
| 49 | Puebla | La Paz | C+ | Zona residencial tradicional en una de las partes altas de la ciudad.21 |
| 50 | Puebla | Las Ánimas | C+ | Punto de convergencia comercial de clase media consolidada.21 |

## **5\. El Scraper: Lógica de Ejecución y Extracción de Métricas**

Para que el scraper cumpla con los requisitos del Caso Técnico de Rappi, la lógica de extracción debe ser granular. No basta con obtener el precio de una hamburguesa; se debe capturar la estructura de costos que el usuario ve en su pantalla antes de pagar.1

### **5.1 Definición de la Carga Útil (Payload) de Datos**

El sistema debe estar diseñado para recolectar, como mínimo, los siguientes campos en cada una de las 50 direcciones mencionadas:

* **Identificadores**: Nombre del restaurante, ID de la plataforma (Uber Eats/DiDi/Rappi), Dirección exacta y Coordenadas GPS utilizadas.44  
* **Métricas de Precio**: Precio base del producto (ej: Big Mac), Descuentos aplicados directamente al ítem, y Precio final unitario.1  
* **Métricas de Servicio**: Tarifa de envío (Delivery Fee), Tarifa de servicio (Service Fee), y Cargos adicionales por pedidos pequeños o alta demanda.1  
* **Métricas Operacionales**: Tiempo estimado de entrega (ETA), Disponibilidad del restaurante (Abierto/Cerrado/No disponible en la zona), y Promociones activas a nivel carrito (ej: "Envío gratis en compras de \+$200").1

### **5.2 Estructura del Código y Modularidad**

Un diseño profesional para este scraper en Python debería seguir un patrón de **Inyección de Dependencias** para facilitar la testing y la rotación de proveedores de proxies.17

1. **Modulo Client**: Encargado de la gestión de la sesión de Playwright o HTTPX, la rotación de proxies y la gestión de headers.3  
2. **Modulo Provider**: Clases abstractas para cada plataforma (UberEatsProvider, DidiFoodProvider). Cada una implementa su propia lógica de navegación o ingeniería inversa de API.47  
3. **Modulo Parser**: Lógica pura para extraer datos del JSON o HTML y convertirlos en objetos de Pydantic.14  
4. **Modulo Orchestrator**: El script principal que recibe el listado de 50 direcciones, las distribuye entre los workers y gestiona el guardado final en CSV/JSON.13

## **6\. Pipeline de Datos y Almacenamiento**

El volumen de datos generado por 50 direcciones, 3 competidores y múltiples productos de referencia puede escalar rápidamente. Un enfoque escalable debe considerar no solo la extracción, sino cómo esos datos se vuelven accionables para los analistas.14

### **6.1 Normalización y Limpieza de Datos**

Uno de los mayores desafíos es la inconsistencia en los nombres de los productos. McDonald's puede aparecer como "McDonald's (Polanco)" en una app y como "McDonals" en otra.6 La arquitectura debe incluir una capa de **Product Matching**. En una entrevista técnica para Rappi (un rol de AI Engineer), demostrar el uso de algoritmos de similitud de cadenas (como Levenshtein o Jaro-Winkler) o incluso un modelo de lenguaje ligero (LLM) para mapear productos de la competencia contra el catálogo propio de Rappi será un diferenciador crítico.1

### **6.2 Almacenamiento y Versionado**

Se recomienda almacenar los datos en tres niveles de madurez:

1. **Raw Layer (Bronze)**: JSONs crudos tal como se recibieron de la API. Esto permite auditar los datos y realizar capturas de pantalla de evidencia si el sitio cambia su estructura.1  
2. **Processed Layer (Silver)**: Datos limpios, sin duplicados y con tipos de datos correctos (precios como floats, fechas como ISO8601).14  
3. **Analytics Layer (Gold)**: Tablas optimizadas para el análisis competitivo, donde ya se han calculado métricas como el "Price Index" (Rappi vs Competencia) y el "ETA Delta".6

## **7\. Análisis de Insights Competitivos: ¿Qué buscar en los datos?**

El valor del scraper no reside en el código, sino en los hallazgos accionables. Siguiendo la rúbrica de evaluación (30% del peso en el informe), el sistema debe permitir identificar patrones estratégicos.1

* **Elasticidad de las Tarifas de Envío**: ¿Uber Eats reduce sus tarifas en zonas como Iztapalapa para ganar volumen, mientras las mantiene altas en Polanco?.1  
* **Guerra de Descuentos**: ¿DiDi Food está agresivamente subsidiando productos básicos (Coca-Cola, hamburguesas de entrada) para atraer nuevos usuarios al ecosistema?.1  
* **Ventaja en la Última Milla**: Comparar los tiempos de entrega. Si Rappi entrega un Combo McDonald's en 25 minutos en Monterrey mientras Uber tarda 35, hay una ventaja operacional que Pricing puede capitalizar con un Service Fee ligeramente superior.1  
* **Saturación de Verticales**: Analizar si la competencia tiene mayor disponibilidad en farmacias o retail en zonas específicas como Querétaro, lo que indicaría una brecha en la oferta de Rappi.1

## **8\. Consideraciones Éticas, Legales y de Seguridad**

Como se especifica en la consigna, el scraping debe ser ético.1 Esto implica:

* **Respeto al robots.txt**: No scrapear secciones prohibidas y mantener un Rate Limit razonable para no degradar el servicio de la competencia (negativa de servicio accidental).1  
* **Uso de User-Agents Transparentes**: En un entorno profesional, es buena práctica identificarse si el volumen es bajo, aunque en inteligencia competitiva esto a menudo lleva al bloqueo inmediato.1  
* **Cumplimiento de la LFPDPPP**: En México, la Ley Federal de Protección de Datos Personales en Posesión de los Particulares prohíbe scrapear datos personales. Dado que este proyecto solo busca precios y disponibilidad de negocios públicos, el riesgo legal es bajo, pero se debe documentar.44

## **9\. Conclusiones y Recomendaciones de Diseño**

Para un candidato a AI Engineer en Rappi, la solución ganadora no es el scraper que obtiene más filas, sino el que demuestra **Resiliencia Técnica** y **Visión Estratégica**.1

1. **Priorice la Calidad sobre la Cantidad**: Es preferible tener 20 direcciones perfectamente scrapeadas con todas las tarifas desglosadas que 50 direcciones con datos incompletos o erróneos.1  
2. **Diseñe para el Cambio**: Los selectores CSS y los endpoints de API cambian. Su arquitectura debe permitir actualizar la lógica de un competidor sin afectar al resto del sistema.13  
3. **Visualice para Decidir**: Los datos en un CSV son difíciles de digerir. Un pequeño dashboard en Streamlit que muestre un mapa de calor de los precios en CDMX impactará mucho más al equipo evaluador.1

Este diseño de arquitectura y la selección de direcciones proporcionan una base sólida para superar la entrevista técnica, demostrando un conocimiento profundo tanto del stack tecnológico de 2026 como de la realidad operativa del mercado mexicano.

#### **Fuentes citadas**

1. consigna.docx  
2. Canasta básica precio: cuánto cuesta la canasta básica en México \- Edenred México, acceso: abril 17, 2026, [https://www.edenred.mx/blog/canasta-basica-precio-cuanto-cuesta-la-canasta-basica-en-mexico](https://www.edenred.mx/blog/canasta-basica-precio-cuanto-cuesta-la-canasta-basica-en-mexico)  
3. The Ultimate Guide to Scalable Web Scraping in 2025: Tools, Proxies, and Automation Workflows \- DEV Community, acceso: abril 17, 2026, [https://dev.to/wisdomudo/the-ultimate-guide-to-scalable-web-scraping-in-2025-tools-proxies-and-automation-workflows-4j6l](https://dev.to/wisdomudo/the-ultimate-guide-to-scalable-web-scraping-in-2025-tools-proxies-and-automation-workflows-4j6l)  
4. Large-Scale Web Scraping: Your 2025 Guide to Building, Running, and Maintaining Powerful Data Extractors \- Hir Infotech, acceso: abril 17, 2026, [https://hirinfotech.com/large-scale-web-scraping-your-2025-guide-to-building-running-and-maintaining-powerful-data-extractors/](https://hirinfotech.com/large-scale-web-scraping-your-2025-guide-to-building-running-and-maintaining-powerful-data-extractors/)  
5. Scrapy vs Selenium: Which one to choose \- ScrapingBee, acceso: abril 17, 2026, [https://www.scrapingbee.com/blog/scrapy-vs-selenium/](https://www.scrapingbee.com/blog/scrapy-vs-selenium/)  
6. Leveraging Web Scraping DiDi Food Food Delivery Data, acceso: abril 17, 2026, [https://www.fooddatascrape.com/web-scraping-didi-food-delivery-data-intelligence.php](https://www.fooddatascrape.com/web-scraping-didi-food-delivery-data-intelligence.php)  
7. Playwright vs Selenium: The Ultimate Web Scraping Comparison, acceso: abril 17, 2026, [https://scrapegraphai.com/blog/playwright-vs-selenium](https://scrapegraphai.com/blog/playwright-vs-selenium)  
8. Top 10 web scraping tools in 2025: Complete developer guide \- Browserbase, acceso: abril 17, 2026, [https://www.browserbase.com/blog/best-web-scraping-tools](https://www.browserbase.com/blog/best-web-scraping-tools)  
9. Scrapy vs Playwright: Web Scraping Comparison Guide \- Bright Data, acceso: abril 17, 2026, [https://brightdata.com/blog/web-data/scrapy-vs-playwright](https://brightdata.com/blog/web-data/scrapy-vs-playwright)  
10. Python Scrapy VS Python Selenium Compared \- ScrapeOps, acceso: abril 17, 2026, [https://scrapeops.io/python-web-scraping-playbook/python-selenium-vs-python-scrapy/](https://scrapeops.io/python-web-scraping-playbook/python-selenium-vs-python-scrapy/)  
11. Digging Into Food Delivery With Chowline: Reverse Engineering ..., acceso: abril 17, 2026, [https://tgrcode.com/posts/digging\_into\_chowline](https://tgrcode.com/posts/digging_into_chowline)  
12. Uber Eats Scraping: Extract Store Listings and Menus | Scrape.do, acceso: abril 17, 2026, [https://scrape.do/blog/ubereats-scraping/](https://scrape.do/blog/ubereats-scraping/)  
13. Top 15 Python Projects to Build in 2025: From Beginner to Production \- Firecrawl, acceso: abril 17, 2026, [https://www.firecrawl.dev/blog/15-python-projects-2025](https://www.firecrawl.dev/blog/15-python-projects-2025)  
14. /python-scalable-data-pipelines-with-airflow-pandas-postgresql | Python in Plain English, acceso: abril 17, 2026, [https://python.plainenglish.io/building-scalable-data-pipelines-in-python-6e0ba17872fb](https://python.plainenglish.io/building-scalable-data-pipelines-in-python-6e0ba17872fb)  
15. Building an Automated Bitcoin Price ETL Pipeline with Airflow and PostgreSQL, acceso: abril 17, 2026, [https://dev.to/luxdevhq/building-an-automated-bitcoin-price-etl-pipeline-with-airflow-and-postgresql-1ok7](https://dev.to/luxdevhq/building-an-automated-bitcoin-price-etl-pipeline-with-airflow-and-postgresql-1ok7)  
16. Building a Modern Data Pipeline Architecture with Python, Kafka, Airflow, Teradata & Tableau | by Mahabir Mohapatra | Medium, acceso: abril 17, 2026, [https://mhmohapatra.medium.com/building-a-modern-data-pipeline-architecture-with-python-kafka-airflow-teradata-tableau-e8b02ef69648](https://mhmohapatra.medium.com/building-a-modern-data-pipeline-architecture-with-python-kafka-airflow-teradata-tableau-e8b02ef69648)  
17. Building a Production-Ready Scraping Infrastructure: Architecture Behind Scrape Creators, acceso: abril 17, 2026, [https://scrapecreators.com/blog/building-a-production-ready-scraping-infrastructure-architecture-behind-scrape-creators](https://scrapecreators.com/blog/building-a-production-ready-scraping-infrastructure-architecture-behind-scrape-creators)  
18. How to Build a Price Monitoring System with Python in 2026 (Complete Guide), acceso: abril 17, 2026, [https://dev.to/agenthustler/how-to-build-a-price-monitoring-system-with-python-in-2026-complete-guide-5d32](https://dev.to/agenthustler/how-to-build-a-price-monitoring-system-with-python-in-2026-complete-guide-5d32)  
19. Niveles Socioeconómicos | NORTH ALPHA \- MÉXICO, acceso: abril 17, 2026, [https://www.northalpha.com/productos/data/niveles-socioeconomicos/](https://www.northalpha.com/productos/data/niveles-socioeconomicos/)  
20. Clasificación de niveles socioeconómicos en México según la AMAI \- Fernando Gutiérrez, acceso: abril 17, 2026, [https://www.fergut.com/clasificacion-de-niveles-socioeconomicos-en-mexico-segun-la-amai/](https://www.fergut.com/clasificacion-de-niveles-socioeconomicos-en-mexico-segun-la-amai/)  
21. Mejores Ciudades para Vivir Cerca de CDMX 2026: Querétaro vs ..., acceso: abril 17, 2026, [https://grupocaisa.com/blog/mejores-cuidades-para-comprar-casa/](https://grupocaisa.com/blog/mejores-cuidades-para-comprar-casa/)  
22. Canasta básica en México: alimentos incluidos y supermercados más baratos según Profeco \- Debate, acceso: abril 17, 2026, [https://www.debate.com.mx/viral/canasta-basica-en-mexico-alimentos-incluidos-y-supermercados-mas-baratos-segun-profeco-20260110-0182.html](https://www.debate.com.mx/viral/canasta-basica-en-mexico-alimentos-incluidos-y-supermercados-mas-baratos-segun-profeco-20260110-0182.html)  
23. Estimaciones NSE 2020 y Regla AMAI 2022, acceso: abril 17, 2026, [https://www.amai.org/NSE/index.php?queVeo=NSE2020](https://www.amai.org/NSE/index.php?queVeo=NSE2020)  
24. Las 15 mejores plataformas de envío en México \- Cubbo, acceso: abril 17, 2026, [https://www.cubbo.com/posts/plataforma-envios-mexico](https://www.cubbo.com/posts/plataforma-envios-mexico)  
25. Mexico \- Distribution and Sales Channels \- International Trade Administration, acceso: abril 17, 2026, [https://www.trade.gov/country-commercial-guides/mexico-distribution-and-sales-channels](https://www.trade.gov/country-commercial-guides/mexico-distribution-and-sales-channels)  
26. Índice de Desarrollo Social (IDS) de la Ciudad de México, 2020\. \- Evalúa CDMX, acceso: abril 17, 2026, [https://www.evalua.cdmx.gob.mx/principales-atribuciones/medicion-del-indice-de-desarrollo-social-de-las-unidades-territoriales/medicion-del-indice-de-desarrollo-social-de-las-unidades-territoriales/mapas](https://www.evalua.cdmx.gob.mx/principales-atribuciones/medicion-del-indice-de-desarrollo-social-de-las-unidades-territoriales/medicion-del-indice-de-desarrollo-social-de-las-unidades-territoriales/mapas)  
27. Índice de Marginación (a nivel colonia) — https://dev-sieg.cdmx.gob ..., acceso: abril 17, 2026, [https://sieg.cdmx.gob.mx/layers/geonode%3Aim\_colonia](https://sieg.cdmx.gob.mx/layers/geonode%3Aim_colonia)  
28. These are the EXCLUSIVE AREAS of CDMX POLANCO SANTA FE 🏙️ and LA ROMA, acceso: abril 17, 2026, [https://www.youtube.com/watch?v=dKkW5iyshHY](https://www.youtube.com/watch?v=dKkW5iyshHY)  
29. Alquiler de oficinas en San Pedro Garza García | Coworking, Oficinas virtuales y salas de reuniones \- HQ, acceso: abril 17, 2026, [https://www.hq.com/es/mexico/nuevo-leon/san-pedro-garza-garcia](https://www.hq.com/es/mexico/nuevo-leon/san-pedro-garza-garcia)  
30. NIVELES SOCIOECONÓMICOS PARA AGEBS ... \- Amai.org, acceso: abril 17, 2026, [https://www.amai.org/NSE/mapas2022/MONTERREY\_URBANO\_AGEB.pdf](https://www.amai.org/NSE/mapas2022/MONTERREY_URBANO_AGEB.pdf)  
31. Cuales son las colonias de clase media en monterrey? \- Reddit, acceso: abril 17, 2026, [https://www.reddit.com/r/Monterrey/comments/1gxtfkg/cuales\_son\_las\_colonias\_de\_clase\_media\_en/](https://www.reddit.com/r/Monterrey/comments/1gxtfkg/cuales_son_las_colonias_de_clase_media_en/)  
32. Find Virtual Office Space & Addresses in San Pedro Garza Garcia, Mexico, acceso: abril 17, 2026, [https://www.davincivirtual.com/loc/mexico/san-pedro-garza-garcia-virtual-offices/](https://www.davincivirtual.com/loc/mexico/san-pedro-garza-garcia-virtual-offices/)  
33. Virtual Office Spaces in Monterrey (San Pedro), Mail Forwarding, Business Addresses, acceso: abril 17, 2026, [https://www.alliancevirtualoffices.com/virtual-office/mx/monterrey-san-pedro](https://www.alliancevirtualoffices.com/virtual-office/mx/monterrey-san-pedro)  
34. Coworking Space in San Pedro Garza García \- Regus, acceso: abril 17, 2026, [https://www.regus.com/en/mx/nuevo-leon/san-pedro-garza-garcia/coworking](https://www.regus.com/en/mx/nuevo-leon/san-pedro-garza-garcia/coworking)  
35. Las 8 mejores colonias para vivir en Monterrey \- Beleta, acceso: abril 17, 2026, [https://beleta.mx/blog/las-8-mejores-colonias-para-vivir-en-monterrey](https://beleta.mx/blog/las-8-mejores-colonias-para-vivir-en-monterrey)  
36. Food Delivery & Takeout in San Pedro Garza García THE BEST Restaurants in San Pedro Garza García | Uber Eats, acceso: abril 17, 2026, [https://www.ubereats.com/mx-en/city/san-pedro-garza-garc%C3%ADa-nl](https://www.ubereats.com/mx-en/city/san-pedro-garza-garc%C3%ADa-nl)  
37. Estudios sociodemográficos de las colonias de Monterrey \- MarketDataMexico, acceso: abril 17, 2026, [https://www.marketdatamexico.com/es/Municipio-Monterrey](https://www.marketdatamexico.com/es/Municipio-Monterrey)  
38. Virtual Office Spaces in San Pedro Garza Garcia, Mail Forwarding Service, Business Addresses, acceso: abril 17, 2026, [https://www.alliancevirtualoffices.com/virtual-office/mx/san-pedro-garza-garcia](https://www.alliancevirtualoffices.com/virtual-office/mx/san-pedro-garza-garcia)  
39. Conoce tu colonia, nueva plataforma de IIEG \- UDG TV, acceso: abril 17, 2026, [https://udgtv.com/noticias/conoce-tu-colonia-nueva-plataforma-de-iieg/44286](https://udgtv.com/noticias/conoce-tu-colonia-nueva-plataforma-de-iieg/44286)  
40. Inside one of the richest neighborhoods in Mexico | Puerta de Hierro Guadalajara \- YouTube, acceso: abril 17, 2026, [https://www.youtube.com/watch?v=blg6oENZUVE](https://www.youtube.com/watch?v=blg6oENZUVE)  
41. Providencia Guadalajara: Is It Worth Living Here? Complete Analysis 2025 \- YouTube, acceso: abril 17, 2026, [https://www.youtube.com/watch?v=QNt9TYFQ9kY](https://www.youtube.com/watch?v=QNt9TYFQ9kY)  
42. Guadalajara, Mexico \- Benchmark Electronics, acceso: abril 17, 2026, [https://www.bench.com/guadalajara-mexico](https://www.bench.com/guadalajara-mexico)  
43. El IIEG presenta la plataforma de Información Sociodemográfica por Colonia | Gobierno de Jalisco, acceso: abril 17, 2026, [https://jalisco.gob.mx/prensa/noticias/140064](https://jalisco.gob.mx/prensa/noticias/140064)  
44. DiDi Food Delivery API \- Extract DiDi Food Restaurant and Menu Data, acceso: abril 17, 2026, [https://www.realdataapi.com/didi-food-data-scraping.php](https://www.realdataapi.com/didi-food-data-scraping.php)  
45. DiDi Food Delivery Scraping API Services for Real-Time Data Collection, acceso: abril 17, 2026, [https://www.fooddatascrape.com/didi-food-data-api.php](https://www.fooddatascrape.com/didi-food-data-api.php)  
46. How to Architect a Large Python Application Without Creating Spaghetti Code, acceso: abril 17, 2026, [https://ramamtech.com/blog/large-python-app-architecture](https://ramamtech.com/blog/large-python-app-architecture)  
47. Architecture overview | Crawlee for Python · Fast, reliable Python web crawlers., acceso: abril 17, 2026, [https://crawlee.dev/python/docs/guides/architecture-overview](https://crawlee.dev/python/docs/guides/architecture-overview)  
48. Design Web Crawler | System Design \- GeeksforGeeks, acceso: abril 17, 2026, [https://www.geeksforgeeks.org/system-design/design-web-crawler-system-design/](https://www.geeksforgeeks.org/system-design/design-web-crawler-system-design/)  
49. Extract Food Categories & Menu Items from Didi Foods Mexico \- Food Data Scrape, acceso: abril 17, 2026, [https://www.fooddatascrape.com/extract-food-menu-categories-didi-foods-mexico.php](https://www.fooddatascrape.com/extract-food-menu-categories-didi-foods-mexico.php)  
50. Plotly: Interactive Data Visualization & Data Apps, acceso: abril 17, 2026, [https://plotly.com/](https://plotly.com/)  
51. Other Visualization Tools: Streamlit, Dash, and Bokeh for Dashboards & Reports ‍ \- DEV Community, acceso: abril 17, 2026, [https://dev.to/sebastianfuentesavalos/other-visualization-tools-streamlit-dash-and-bokeh-for-dashboards-reports-5cc9](https://dev.to/sebastianfuentesavalos/other-visualization-tools-streamlit-dash-and-bokeh-for-dashboards-reports-5cc9)  
52. What tech stack for dashboard? : r/learnpython \- Reddit, acceso: abril 17, 2026, [https://www.reddit.com/r/learnpython/comments/1s97f0x/what\_tech\_stack\_for\_dashboard/](https://www.reddit.com/r/learnpython/comments/1s97f0x/what_tech_stack_for_dashboard/)