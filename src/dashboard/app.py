from dash import Dash, html, dcc, Input, Output
import plotly.express as px
from src.dashboard.processing import load_and_clean_data

app = Dash(__name__, title="Benchmark Delivery MX")

app.layout = html.Div([
    html.H1("Inteligencia Competitiva: Multi-Vendor Mexico", style={'textAlign': 'center', 'color': '#2C3E50'}),
    
    html.Div([
        html.P("Comparación de precios en Restaurantes y Retail (Rappi vs Uber vs Chedraui)."),
    ], style={'padding': '10px', 'textAlign': 'center'}),

    dcc.Interval(
        id='interval-component',
        interval=15*1000,
        n_intervals=0
    ),

    dcc.Tabs(id="tabs-example-graph", value='tab-restaurante', children=[
        dcc.Tab(label='Restaurantes (McDonald\'s)', value='tab-restaurante'),
        dcc.Tab(label='Retail (Supermercado)', value='tab-retail'),
    ]),
    
    html.Div(id='tabs-content-example-graph')
], style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'})

@app.callback(
    Output('tabs-content-example-graph', 'children'),
    [Input('tabs-example-graph', 'value'),
     Input('interval-component', 'n_intervals')]
)
def render_content(tab, n):
    df = load_and_clean_data()
    
    if df.empty:
        return html.Div([html.H3("Esperando datos...")], style={'textAlign': 'center', 'padding': '50px'})

    if tab == 'tab-restaurante':
        dff = df[df["category"] == "Restaurante"]
        title = "Comparación de Precios: McDonald's"
    else:
        dff = df[df["category"] == "Retail"]
        title = "Comparación de Precios: Retail / Súper"

    if dff.empty:
        return html.Div([html.H3(f"No hay datos para {tab} todavía.")], style={'textAlign': 'center', 'padding': '50px'})

    # 1. Price Comparison
    fig_price = px.box(
        dff, 
        x="target_product", 
        y="final_price_clean", 
        color="app_name",
        title=title,
        labels={"target_product": "Producto", "final_price_clean": "Precio ($)", "app_name": "Plataforma"},
        points="all"
    )
    fig_price.update_layout(boxmode='group')

    # 2. Delivery Fee (Overall)
    fig_fee = px.violin(
        dff, 
        y="delivery_fee_clean", 
        x="app_name", 
        color="app_name",
        box=True, 
        points="all",
        title="Distribución de Costos de Envío",
        labels={"app_name": "Plataforma", "delivery_fee_clean": "Costo de Envío ($)"}
    )
    
    # 3. ETA (Overall)
    fig_eta = px.histogram(
        dff, 
        x="eta_clean", 
        color="app_name", 
        barmode="overlay",
        title="Distribución de Tiempos de Entrega (ETA)",
        labels={"eta_clean": "Minutos", "app_name": "Plataforma"}
    )
    fig_eta.update_traces(opacity=0.75)

    return html.Div([
        dcc.Graph(figure=fig_price),
        html.Div([
            dcc.Graph(figure=fig_fee, style={'width': '50%', 'display': 'inline-block'}),
            dcc.Graph(figure=fig_eta, style={'width': '50%', 'display': 'inline-block'}),
        ])
    ])

if __name__ == '__main__':
    app.run_server(debug=True)
