import sys
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
    if len(series) < period:  # Vérifie si le nombre de données est suffisant pour calculer le RSI
        return pd.Series([np.nan] * len(series))  # Retourne NaN si pas assez de données
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Charger et préparer les données depuis le CSV
def load_data():
    df = pd.read_csv('/home/ubuntu/Projet_git/bitcoin_data_mult.csv', sep=';', header=0, names=['timestamp', 'bitcoin', 'ethereum', 'binance_coin', 'solana'])
    # Convertir l'heure en heure locale (UTC+2, heure de Paris)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S') + pd.Timedelta(hours=2)
    
    # Nettoyage des données
    for col in df.columns[1:]:
        df[col] = df[col].astype(str).str.replace('\u202f', '').str.replace(',', '.').astype(float)
    # Remplir les valeurs manquantes avec la dernière valeur disponible
    df = df.fillna(method='ffill')

    return df

# Calculer les indicateurs du rapport quotidien
def daily_report(df):
    # Sélectionner uniquement les données du jour (en se basant sur la date)
    today = df[df['timestamp'].dt.date == pd.to_datetime("today").date()]
    
    if len(today) == 0:
        return {}
    
    open_price = today.iloc[0]  # Premier prix de la journée
    close_price = today.iloc[-1]  # Dernier prix de la journée
    
    daily_volatility = today.iloc[:, 1:].pct_change().std().mean() * 100  # Volatilité quotidienne moyenne
    evolution = (close_price[1:] - open_price[1:]) / open_price[1:] * 100  # Evolution en % de la journée

    return {
        "open_price": open_price[1:].to_dict(),
        "close_price": close_price[1:].to_dict(),
        "daily_volatility": daily_volatility,
        "evolution": evolution.to_dict(),
    }


# === Application Dash ===
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Cryptocurrency Dashboard", style={'textAlign': 'center'}),

    dcc.Interval(
        id='interval-component',
        interval=60 * 1000,  # actualisation automatique toutes les 60 secondes
        n_intervals=0
    ),

    html.Div(id='price-graph'),

    # Déplacer la section "Choisir les cryptos" à la fin
    html.Div(id='indicators'),
    html.Div(id='correlation-graph'),
    html.Div(id='moving-avg-graph'),
    html.Div(id='rsi-tabs'),
    html.Div(id='daily-report'),
])

# === Callbacks ===

@app.callback(
    Output('price-graph', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_price_graph(n):
    df = load_data()

    graphs = []
    for crypto in df.columns[1:]:
        last_value = df[crypto].dropna().iloc[-1]
        graphs.append(
            html.Div([
                html.H3(f"Prix de {crypto} - Dernier : {last_value:,.2f} USD"),
                dcc.Graph(
                    figure=go.Figure(
                        data=[go.Scatter(x=df['timestamp'], y=df[crypto], mode='lines', name=crypto)],
                        layout=go.Layout(
                            title=f"Prix de {crypto}",
                            xaxis=dict(title='Timestamp'),
                            yaxis=dict(title='Price (USD)')
                        )
                    )
                )
            ])
        )

    return graphs


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
    # Calculer la moyenne mobile par crypto
    moving_avg_data = {crypto: df[crypto].rolling(window=7).mean() for crypto in df.columns[1:]}  # Moyenne mobile par crypto
    
    return html.Div([
        html.H2("Moyenne Mobile (7 points) par crypto"),
        dcc.Tabs([
            dcc.Tab(label=crypto, children=[
                dcc.Graph(
                    figure=go.Figure(
                        data=[go.Scatter(x=df['timestamp'], y=moving_avg_data[crypto], mode='lines', name=f"Moving Average - {crypto}")],
                        layout=go.Layout(title=f"Moving Average (7) - {crypto}")
                    )
                )
            ]) for crypto in df.columns[1:]
        ])
    ])


@app.callback(
    Output('rsi-tabs', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_rsi_graph(n):
    df = load_data()

    rsi_data = {crypto: compute_rsi(df[crypto]) for crypto in df.columns[1:]}

    fig = go.Figure()

    for crypto in df.columns[1:]:
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=rsi_data[crypto],
            mode='lines', name=f'RSI - {crypto}'
        ))

    fig.update_layout(
        title="RSI pour toutes les cryptos",
        xaxis=dict(title='Timestamp'),
        yaxis=dict(title='RSI', range=[0, 100]),
        showlegend=True
    )

    return html.Div([
        dcc.Graph(figure=fig)
    ])


@app.callback(
    Output('daily-report', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_daily_report(n):
    df = load_data()
    report = daily_report(df)
    
    # Mettre à jour seulement à 20h
    current_hour = pd.to_datetime("now").hour
    if current_hour == 20:
        return html.Div([
            html.H2("Daily Report (Mis à jour à 20h)"),
            html.Ul([
                html.Li(f"Volatilité quotidienne: {report['daily_volatility']:.2f}%")
            ]),
            html.H3("Prix d'ouverture:"),
            html.Ul([
                html.Li(f"{crypto}: {price:.2f}") for crypto, price in report["open_price"].items()
            ]),
            html.H3("Prix de clôture:"),
            html.Ul([
                html.Li(f"{crypto}: {price:.2f}") for crypto, price in report["close_price"].items()
            ]),
            html.H3("Évolution de la journée:"),
            html.Ul([
                html.Li(f"{crypto}: {evol:.2f}%") for crypto, evol in report["evolution"].items()
            ]),
        ])
    else:
        return html.Div([html.H2("Le rapport quotidien sera mis à jour à 20h.")])



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
