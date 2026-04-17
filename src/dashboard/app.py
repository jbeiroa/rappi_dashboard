from dash import Dash, html, dcc, Input, Output
import plotly.express as px
from src.dashboard.processing import load_and_clean_data

app = Dash(__name__)

# Use Spanish labels as per GEMINI.md
app.layout = html.Div([
    html.H1("Dashboard de Inteligencia Competitiva - Rappi", style={'textAlign': 'center'}),
    
    html.Div([
        html.P("Este tablero muestra las métricas recolectadas de Rappi en México."),
    ], style={'padding': '20px'}),

    dcc.Interval(
        id='interval-component',
        interval=10*1000, # in milliseconds (10 seconds)
        n_intervals=0
    ),

    html.Div([
        dcc.Graph(id='delivery-fee-graph'),
        dcc.Graph(id='eta-graph'),
    ], style={'display': 'flex', 'flex-direction': 'column'})
])

@app.callback(
    [Output('delivery-fee-graph', 'figure'),
     Output('eta-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    df = load_and_clean_data()
    
    if df.empty:
        # Placeholder figures if no data exists
        fig_fee = px.bar(title="Esperando datos de Costo de Envío...")
        fig_eta = px.bar(title="Esperando datos de Tiempo de Entrega (ETA)...")
    else:
        fig_fee = px.bar(
            df, 
            x="restaurant_name", 
            y="delivery_fee_clean", 
            title="Costo de Envío por Restaurante",
            labels={"restaurant_name": "Restaurante", "delivery_fee_clean": "Costo de Envío ($)"}
        )
        
        fig_eta = px.bar(
            df, 
            x="restaurant_name", 
            y="eta_clean", 
            title="Tiempo Estimado de Entrega (ETA)",
            labels={"restaurant_name": "Restaurante", "eta_clean": "Minutos"}
        )
        
    return fig_fee, fig_eta

if __name__ == '__main__':
    app.run_server(debug=True)
