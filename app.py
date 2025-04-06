import sys
import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import numpy as np
from dash.dependencies import Input, Output
import os
import datetime
import json

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

def generate_report_for_day(df, day, is_today=True):
    # Déterminer la date de début et de fin de la journée
    day_start = datetime.datetime(day.year, day.month, day.day)
    day_end = day_start + datetime.timedelta(days=1)

    # Filtrer les données pour cette journée
    df_day = df[(df['timestamp'] >= day_start) & (df['timestamp'] < day_end)]

    # Initialiser les variables
    open_prices = df_day.iloc[0, 1:]
    current_prices = df_day.iloc[-1, 1:] if not df_day.empty else None
    volatility = df_day[df_day.columns[1:]].pct_change().std() * 100 if not df_day.empty else None
    report = f"Rapport du {day.strftime('%Y-%m-%d')}\n\n"

    for crypto in df_day.columns[1:]:
        report += f"{crypto}:\n"
        
        # Pour aujourd'hui, on affiche le prix actuel et l'évolution actuelle
        if is_today:
            if current_prices is not None:
                returns = ((current_prices - open_prices) / open_prices * 100)
                report += f"  - Prix d'ouverture: {open_prices[crypto]:.2f} USD\n"
                report += f"  - Prix actuel: {current_prices[crypto]:.2f} USD\n"
                report += f"  - Évolution actuelle: {returns[crypto]:.2f} %\n"
            else:
                report += f"  - Prix actuel: Pas encore disponible\n"
                report += f"  - Évolution actuelle: Pas encore disponible\n"
        # Pour hier, on affiche le prix de clôture et l'évolution
        else:
            close_price = df_day.iloc[-1][crypto] if not df_day.empty else None
            if close_price is not None:
                returns = ((close_price - open_prices[crypto]) / open_prices[crypto] * 100)
                report += f"  - Prix d'ouverture: {open_prices[crypto]:.2f} USD\n"
                report += f"  - Prix de clôture: {close_price:.2f} USD\n"
                report += f"  - Évolution: {returns:.2f} %\n"
            else:
                report += f"  - Prix de clôture: Pas encore disponible\n"
                report += f"  - Évolution: Pas encore disponible\n"
        
        report += f"  - Volatilité: {volatility[crypto]:.2f} %\n\n"

    return report


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
    html.Div(id='daily-report-section'),
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
    Output('daily-report-section', 'children'),
    Input('interval-component', 'n_intervals')
)
def display_daily_report(n):
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    yesterday = now - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    
    # Charger les données et générer les rapports
    df = load_data()  # Assure-toi que cette fonction charge correctement tes données
    today_report_content = generate_report_for_day(df, now, is_today=True)  # Rapport d'aujourd'hui
    yesterday_report_content = generate_report_for_day(df, yesterday, is_today=False)  # Rapport d'hier

    # Affichage des rapports sur la page
    return html.Div([
        html.H2(f"Rapport quotidien du {yesterday_str} (hier)"),
        html.Pre(yesterday_report_content),
        html.Hr(),  # Ligne de séparation entre les rapports
        html.H2(f"Rapport du {today_str} (aujourd'hui)"),
        html.Pre(today_report_content)
    ])



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
