import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Charger les données
df = pd.read_csv("bitcoin_data_mult.csv", sep=";", header=None,
                 names=["timestamp", "bitcoin", "ethereum", "binance_coin", "solana"])
df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")

# Remplacer les virgules et convertir en float
for col in df.columns[1:]:
    df[col] = df[col].astype(str).str.replace('\u202f', '').str.replace(',', '.').astype(float)

# Filtrer sur les dernières 24h
now = datetime.now()
df_last24h = df[df["timestamp"] > (now - pd.Timedelta(hours=24))]

# Statistiques récapitulatives de la journée
daily_summary = df_last24h.describe()

# Sauvegarder les données résumées dans un fichier texte
with open("daily_report.txt", "w") as f:
    f.write(f"Rapport du {now.strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write("Résumé des données (dernières 24h):\n")
    f.write(daily_summary.to_string())
    f.write("\n\n")

# Générer un graphique pour chaque cryptomonnaie
for coin in ['bitcoin', 'ethereum', 'binance_coin', 'solana']:
    plt.figure(figsize=(12, 6))
    plt.plot(df_last24h["timestamp"], df_last24h[coin], label=coin, color='tab:blue')
    plt.title(f"Évolution des prix - {coin} (dernières 24h)")
    plt.xlabel("Heure")
    plt.ylabel(f"Prix en USD - {coin}")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{coin}_daily_chart.png")
    plt.close()

# Générer un graphique combiné pour toutes les cryptomonnaies
plt.figure(figsize=(12, 6))
for coin in ['bitcoin', 'ethereum', 'binance_coin', 'solana']:
    plt.plot(df_last24h["timestamp"], df_last24h[coin], label=coin)
plt.legend()
plt.title("Évolution des prix sur 24h")
plt.xlabel("Heure")
plt.ylabel("Prix en USD")
plt.grid(True)
plt.tight_layout()
plt.savefig("daily_price_combined_chart.png")
