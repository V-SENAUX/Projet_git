import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import numpy as np

# Charger les données CSV
df = pd.read_csv('bitcoin_data_mult.csv', sep=';', header=None, names=['timestamp', 'bitcoin', 'ethereum', 'binance_coin', 'solana'])

# Conversion du timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')

# Nettoyage des données (virgules et espaces)
for col in df.columns[1:]:
    df[col] = df[col].astype(str).str.replace('\u202f', '').str.replace(',', '.').astype(float)

# === Calculs des indicateurs ===

# Volatilité (écart-type)
volatility = df[df.columns[1:]].pct_change(fill_method=None).std() * 100

# Moyenne mobile (7 points)
moving_avg = df[df.columns[1:]].rolling(window=7).mean()

# Corrélation
correlation = df[df.columns[1:]].corr()

# Maximum Drawdown
def max_drawdown(series):
    cumulative = series.cummax()
    drawdown = (series - cumulative) / cumulative
    return drawdown.min()

mdd = {crypto: max_drawdown(df[crypto]) * 100 for crypto in df.columns[1:]}

# RSI (Relative Strength Index)
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

rsi_data = {crypto: compute_rsi(df[crypto]) for crypto in df.columns[1:]}

# === Application Dash ===
app = dash.Dash(__name__)

app.layout = html.Div([ 
    html.H1("Cryptocurrency Dashboard", style={'textAlign': 'center'}),

    # Graphique principal
    dcc.Graph(
        id='price-graph',
        figure=px.line(df, x='timestamp', y=df.columns[1:], title='Crypto Prices Over Time')
    ),

    html.H2("Choisir les cryptos à afficher dans le tableau"),
    dcc.Checklist(
        id='crypto-selector',
        options=[{'label': col, 'value': col} for col in df.columns[1:]],
        value=df.columns[1:].tolist(),
        inline=True
    ),

    html.Div(id='data-table'),

    html.H2("Volatilité (%)"),
    html.Ul([html.Li(f"{crypto}: {vol:.2f}%") for crypto, vol in volatility.items()]),

    html.H2("Maximum Drawdown (MDD)"),
    html.Ul([html.Li(f"{crypto}: {val:.2f}%") for crypto, val in mdd.items()]),

    html.H2("RSI (dernière valeur)"),
    html.Ul([html.Li(f"{crypto}: {rsi_data[crypto].iloc[-1]:.2f}") for crypto in df.columns[1:]]),

    html.H2("Corrélation entre cryptos"),
    dcc.Graph(
        figure=px.imshow(correlation, text_auto=True, title="Correlation Matrix")
    ),

    html.H2("Moyenne Mobile (7 points)"),
    dcc.Graph(
        figure=px.line(moving_avg.assign(timestamp=df['timestamp']), x='timestamp', y=moving_avg.columns,
                       title="Moving Averages")
    ),

    html.H2("RSI par crypto"),
    dcc.Tabs([ 
        dcc.Tab(label=crypto, children=[ 
            dcc.Graph( 
                figure=go.Figure( 
                    data=[go.Scatter(x=df['timestamp'], y=rsi_data[crypto], mode='lines', name='RSI')], 
                    layout=go.Layout(title=f"RSI - {crypto}", yaxis=dict(range=[0, 100])) 
                ) 
            ) 
        ]) for crypto in df.columns[1:] 
    ])
])

# === Callback pour tableau interactif ===
from dash.dependencies import Input, Output

@app.callback(
    Output('data-table', 'children'),
    Input('crypto-selector', 'value')
)
def update_table(selected_cryptos):
    # Sélectionner uniquement les colonnes souhaitées
    table_df = df[['timestamp'] + selected_cryptos]
    return html.Table([
        html.Thead(html.Tr([html.Th(col) for col in table_df.columns])),
        html.Tbody([
            html.Tr([html.Td(table_df.iloc[i][col]) for col in table_df.columns])
            for i in range(min(len(table_df), 20))  # Affiche les 20 dernières lignes
        ])
    ])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
