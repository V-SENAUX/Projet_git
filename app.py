import sys
print(sys.executable)

import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import numpy as np
from dash.dependencies import Input, Output

# === Fonctions utiles ===

# Maximum Drawdown
def max_drawdown(series):
    cumulative = series.cummax()
    drawdown = (series - cumulative) / cumulative
    return drawdown.min()

# RSI (Relative Strength Index)
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Charger et préparer les données depuis le CSV
def load_data():
    df = pd.read_csv('/home/ubuntu/Projet_git/bitcoin_data_mult.csv', sep=';', header=0, names=['timestamp', 'bitcoin', 'ethereum', 'binance_coin', 'solana'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')
    for col in df.columns[1:]:
        df[col] = df[col].astype(str).str.replace('\u202f', '').str.replace(',', '.').astype(float)
    return df

# === Application Dash ===
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Cryptocurrency Dashboard", style={'textAlign': 'center'}),

    dcc.Interval(
        id='interval-component',
        interval=60 * 1000,  # actualisation automatique toutes les 60 secondes
        n_intervals=0
    ),

    dcc.Graph(id='price-graph'),

    html.H2("Choisir les cryptos à afficher dans le tableau"),
    dcc.Checklist(
        id='crypto-selector',
        options=[{'label': col, 'value': col} for col in ['bitcoin', 'ethereum', 'binance_coin', 'solana']],
        value=['bitcoin', 'ethereum', 'binance_coin', 'solana'],
        inline=True
    ),

    html.Div(id='data-table'),

    html.Div(id='indicators'),

    html.Div(id='correlation-graph'),

    html.Div(id='moving-avg-graph'),

    html.Div(id='rsi-tabs')
])

# === Callbacks ===

@app.callback(
    Output('price-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_price_graph(n):
    df = load_data()
    return px.line(df, x='timestamp', y=df.columns[1:], title='Crypto Prices Over Time')


@app.callback(
    Output('data-table', 'children'),
    [Input('crypto-selector', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_table(selected_cryptos, n):
    df = load_data()
    table_df = df[['timestamp'] + selected_cryptos]
    return html.Table([
        html.Thead(html.Tr([html.Th(col) for col in table_df.columns])),
        html.Tbody([
            html.Tr([html.Td(table_df.iloc[i][col]) for col in table_df.columns])
            for i in range(min(len(table_df), 20))
        ])
    ])


@app.callback(
    Output('indicators', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_indicators(n):
    df = load_data()

    volatility = df[df.columns[1:]].pct_change(fill_method=None).std() * 100
    mdd = {crypto: max_drawdown(df[crypto]) * 100 for crypto in df.columns[1:]}
    rsi_data = {crypto: compute_rsi(df[crypto]) for crypto in df.columns[1:]}

    return html.Div([
        html.H2("Volatilité (%)"),
        html.Ul([html.Li(f"{crypto}: {vol:.2f}%") for crypto, vol in volatility.items()]),

        html.H2("Maximum Drawdown (MDD)"),
        html.Ul([html.Li(f"{crypto}: {val:.2f}%") for crypto, val in mdd.items()]),

        html.H2("RSI (dernière valeur)"),
        html.Ul([html.Li(f"{crypto}: {rsi_data[crypto].iloc[-1]:.2f}") for crypto in df.columns[1:]])
    ])


@app.callback(
    Output('correlation-graph', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_correlation(n):
    df = load_data()
    correlation = df[df.columns[1:]].corr()
    return html.Div([
        html.H2("Corrélation entre cryptos"),
        dcc.Graph(
            figure=px.imshow(correlation, text_auto=True, title="Correlation Matrix")
        )
    ])


@app.callback(
    Output('moving-avg-graph', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_moving_avg(n):
    df = load_data()
    moving_avg = df[df.columns[1:]].rolling(window=7).mean()
    moving_avg['timestamp'] = df['timestamp']
    return html.Div([
        html.H2("Moyenne Mobile (7 points)"),
        dcc.Graph(
            figure=px.line(moving_avg, x='timestamp', y=df.columns[1:], title="Moving Averages")
        )
    ])


@app.callback(
    Output('rsi-tabs', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_rsi_graph(n):
    df = load_data()
    rsi_data = {crypto: compute_rsi(df[crypto]) for crypto in df.columns[1:]}
    return html.Div([
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
