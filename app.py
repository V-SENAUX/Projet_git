import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px

# Charger les données CSV avec des noms de colonnes personnalisés
# Par exemple : 'timestamp', 'bitcoin', 'ethereum', 'binance_coin', 'solana'
df = pd.read_csv('bitcoin_data_mult.csv', sep=';', header=None, names=['timestamp', 'bitcoin', 'ethereum', 'binance_coin', 'solana'])

# Vérifie les colonnes
print(df.columns)  # Affiche les noms des colonnes pour vérifier

# Convertir la colonne 'timestamp' en format datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')

# Remplacer les virgules par des points dans les colonnes numériques
for col in df.columns[1:]:  # Exclude the 'timestamp' column
    df[col] = df[col].str.replace('\u202f', '').str.replace(',', '.').astype(float)

# Créer une application Dash
app = dash.Dash(__name__)

# Créer un graphique de séries temporelles
fig = px.line(df, x='timestamp', y=df.columns[1:], title='Crypto Prices Over Time')

# Définir le layout du Dashboard
app.layout = html.Div([
    html.H1("Cryptocurrency Prices Dashboard"),
    html.Div([
        dcc.Graph(figure=fig)
    ]),
    html.Div([
        html.H3("Scraped Data Table"),
        html.Table([
            html.Thead(
                html.Tr([html.Th(col) for col in df.columns])
            ),
            html.Tbody([
                html.Tr([html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(len(df))
            ])
        ])
    ])
])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
