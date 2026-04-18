from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.processing import load_and_clean_data

# Rappi Brand Palette
RAPPI_MAIN = "#f6553f"
RAPPI_DARK = "#c81c20"
RAPPI_TEXT_LIGHT = "#fa3d22"
RAPPI_BG_ACCENT = "#d2bca5"
RAPPI_ACCENT_MUTED = "#a46484"

app = Dash(__name__, title="CI Dashboard - Rappi vs Competencia", suppress_callback_exceptions=True)

# Custom CSS for cards and layout
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; margin: 0; }
            .kpi-card {
                background-color: white; border-radius: 10px; padding: 20px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;
                border-top: 5px solid ''' + RAPPI_MAIN + ''';
            }
            .kpi-title { font-size: 0.9rem; color: #6c757d; text-transform: uppercase; letter-spacing: 1px; }
            .kpi-value { font-size: 1.8rem; font-weight: bold; color: ''' + RAPPI_DARK + '''; margin: 10px 0; }
            .filter-container { background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .header-bar { background-color: ''' + RAPPI_MAIN + '''; color: white; padding: 20px; text-align: center; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div([
    html.Div([
        html.H1("Competitive Intelligence Dashboard", style={'margin': '0'}),
        html.P("Benchmarking: Rappi vs Uber Eats vs Chedraui Direct", style={'opacity': '0.9'})
    ], className="header-bar"),

    html.Div([
        dcc.Tabs(id="tabs-main", value='tab-global', children=[
            dcc.Tab(label='Panorama General (Nacional)', value='tab-global', 
                    selected_style={'borderTop': f'3px solid {RAPPI_MAIN}', 'fontWeight': 'bold'}),
            dcc.Tab(label='Análisis Detallado (Local)', value='tab-local',
                    selected_style={'borderTop': f'3px solid {RAPPI_MAIN}', 'fontWeight': 'bold'}),
        ], style={'marginBottom': '20px'}),

        html.Div(id='tabs-content')
    ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '0 20px'})
])

def get_kpi_row(df_filtered):
    if df_filtered.empty:
        return html.Div("No hay datos disponibles.")
    
    platforms = df_filtered["app_name"].unique()
    kpis = []
    
    for platform in ["Rappi", "Uber Eats", "Chedraui"]:
        if platform not in platforms: continue
        
        pdf = df_filtered[df_filtered["app_name"] == platform]
        avg_price = pdf["total_price"].mean()
        avg_eta = pdf["eta_clean"].mean()
        promo_rate = (pdf["is_promoted"].sum() / len(pdf)) * 100
        
        kpis.append(html.Div([
            html.Div([
                html.Div(platform, style={'fontSize': '1.2rem', 'fontWeight': 'bold', 'color': RAPPI_MAIN}),
                html.Hr(style={'margin': '10px 0'}),
                html.Div("Precio Total Promedio", className="kpi-title"),
                html.Div(f"${avg_price:,.2f}", className="kpi-value"),
                html.Div("ETA Promedio", className="kpi-title"),
                html.Div(f"{avg_eta:.0f} min", className="kpi-value"),
                html.Div("% con Promoción", className="kpi-title"),
                html.Div(f"{promo_rate:.1f}%", className="kpi-value", style={'fontSize': '1.4rem'}),
            ], className="kpi-card")
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '3%'}))
        
    return html.Div(kpis, style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '30px'})

@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs-main', 'value')]
)
def render_tab_content(tab):
    df = load_and_clean_data()
    if df.empty:
        return html.Div([html.H3("Esperando datos de los scrapers...")], style={'textAlign': 'center', 'padding': '100px'})

    if tab == 'tab-global':
        return render_global_view(df)
    else:
        return render_local_view(df)

def render_global_view(df):
    # 1. Price Positioning (Boxplot)
    fig_price = px.box(
        df, x="target_product", y="final_price_clean", color="app_name",
        title="Posicionamiento de Precios por Producto (Nacional)",
        labels={"target_product": "Producto", "final_price_clean": "Precio ($)", "app_name": "Plataforma"},
        color_discrete_map={"Rappi": RAPPI_MAIN, "Uber Eats": RAPPI_ACCENT_MUTED, "Chedraui": RAPPI_BG_ACCENT}
    )
    fig_price.update_layout(plot_bgcolor='white', paper_bgcolor='white')

    # 2. Operational Advantage (ETA Histogram)
    fig_eta = px.histogram(
        df[df["app_name"] != "Chedraui"], # Chedraui eta is 0/NA usually
        x="eta_clean", color="app_name", barmode="overlay",
        title="Tiempos de Entrega (ETA): Rappi vs Uber",
        labels={"eta_clean": "Minutos", "app_name": "Plataforma"},
        color_discrete_map={"Rappi": RAPPI_MAIN, "Uber Eats": RAPPI_ACCENT_MUTED}
    )
    fig_eta.update_traces(opacity=0.75)

    # 3. Geographic Variability
    geo_df = df.groupby(["city", "app_name"])["total_price"].mean().reset_index()
    fig_geo = px.bar(
        geo_df, x="city", y="total_price", color="app_name", barmode="group",
        title="Variabilidad por Ciudad (Precio Total Promedio)",
        color_discrete_map={"Rappi": RAPPI_MAIN, "Uber Eats": RAPPI_ACCENT_MUTED, "Chedraui": RAPPI_BG_ACCENT}
    )

    return html.Div([
        html.H3("Resumen Nacional", style={'textAlign': 'center', 'color': RAPPI_DARK}),
        get_kpi_row(df),
        html.Div([
            dcc.Graph(figure=fig_price),
        ], className="filter-container"),
        html.Div([
            html.Div([dcc.Graph(figure=fig_eta)], style={'width': '48%', 'display': 'inline-block'}),
            html.Div([dcc.Graph(figure=fig_geo)], style={'width': '48%', 'display': 'inline-block', 'float': 'right'}),
        ], style={'marginBottom': '50px'})
    ])

def render_local_view(df):
    cities = sorted(df["city"].unique())
    categories = sorted(df["category"].unique())
    
    return html.Div([
        html.Div([
            html.Div([
                html.Label("Categoría", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='dropdown-cat', options=categories, value=categories[0], clearable=False),
            ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
            
            html.Div([
                html.Label("Ciudad", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='dropdown-city', options=cities, value=cities[0], clearable=False),
            ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
            
            html.Div([
                html.Label("Municipio / Alcaldía", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='dropdown-mun', clearable=True, placeholder="Todos los municipios"),
            ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        ], className="filter-container"),

        html.Div(id='local-kpis'),
        
        html.Div([
            html.Div([dcc.Graph(id='graph-local-price')], style={'width': '48%', 'display': 'inline-block'}),
            html.Div([dcc.Graph(id='graph-local-fees')], style={'width': '48%', 'display': 'inline-block', 'float': 'right'}),
        ]),
        
        html.Div([
            dcc.Graph(id='graph-local-promo'),
        ], style={'marginTop': '20px'})
    ])

@app.callback(
    [Output('dropdown-mun', 'options'),
     Output('dropdown-mun', 'value')],
    [Input('dropdown-city', 'value')]
)
def update_mun_dropdown(selected_city):
    df = load_and_clean_data()
    muns = sorted(df[df["city"] == selected_city]["municipality"].unique())
    return muns, None

@app.callback(
    [Output('local-kpis', 'children'),
     Output('graph-local-price', 'figure'),
     Output('graph-local-fees', 'figure'),
     Output('graph-local-promo', 'figure')],
    [Input('dropdown-cat', 'value'),
     Input('dropdown-city', 'value'),
     Input('dropdown-mun', 'value')]
)
def update_local_graphs(cat, city, mun):
    df = load_and_clean_data()
    dff = df[(df["category"] == cat) & (df["city"] == city)]
    if mun:
        dff = dff[dff["municipality"] == mun]
    
    if dff.empty:
        placeholder = px.scatter(title="No hay datos para esta selección")
        return html.Div("Sin datos"), placeholder, placeholder, placeholder

    # KPI Row
    kpi_row = get_kpi_row(dff)

    # 1. Local Price Comparison
    fig_price = px.box(
        dff, x="target_product", y="total_price", color="app_name",
        title=f"Precio Total en {city} ({mun if mun else 'Todos'})",
        color_discrete_map={"Rappi": RAPPI_MAIN, "Uber Eats": RAPPI_ACCENT_MUTED, "Chedraui": RAPPI_BG_ACCENT}
    )
    
    # 2. Fee Structure (Stacked Bar)
    fee_df = dff.groupby("app_name")[["final_price_clean", "delivery_fee_clean"]].mean().reset_index()
    fig_fees = go.Figure(data=[
        go.Bar(name='Precio Producto', x=fee_df['app_name'], y=fee_df['final_price_clean'], marker_color=RAPPI_ACCENT_MUTED),
        go.Bar(name='Costo Envío', x=fee_df['app_name'], y=fee_df['delivery_fee_clean'], marker_color=RAPPI_MAIN)
    ])
    fig_fees.update_layout(barmode='stack', title="Estructura de Costos: Producto vs Envío")

    # 3. Promo Strategy
    promo_df = dff.groupby("app_name").agg(
        avg_discount=('discount_pct', 'mean'),
        promo_count=('is_promoted', 'sum'),
        total_items=('scraped_product_name', 'count')
    ).reset_index()
    promo_df["promo_freq"] = (promo_df["promo_count"] / promo_df["total_items"]) * 100
    
    fig_promo = px.scatter(
        promo_df, x="promo_freq", y="avg_discount", size="total_items", color="app_name",
        title="Estrategia Promocional: Frecuencia vs Intensidad",
        labels={"promo_freq": "% de productos con oferta", "avg_discount": "Descuento Promedio (%)"},
        color_discrete_map={"Rappi": RAPPI_MAIN, "Uber Eats": RAPPI_ACCENT_MUTED, "Chedraui": RAPPI_BG_ACCENT}
    )

    return kpi_row, fig_price, fig_fees, fig_promo

if __name__ == '__main__':
    app.run(debug=True, port=8051)
