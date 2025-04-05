import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Charger les données
df = pd.read_csv("bitcoin_data_mult.csv", sep=";", header=None,
                 names=["timestamp", "bitcoin", "ethereum", "binance_coin", "solana", "cardano", "chainlink"])
df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")

# Remplacer les virgules et convertir en float
for col in df.columns[1:]:
    df[col] = df[col].astype(str).str.replace('\u202f', '').str.replace(',', '.').astype(float)

# Filtrer sur les dernières 24h
now = datetime.now()
df_last24h = df[df["timestamp"] > (now - pd.Timedelta(hours=24))]

# Statistiques
stats = df_last24h.describe()

# Sauvegarder le résumé en texte
with open("daily_report.txt", "w") as f:
    f.write(f"Rapport du {now.strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write("Statistiques descriptives (dernières 24h):\n")
    f.write(stats.to_string())
    f.write("\n\n")

# Générer un graphique
plt.figure(figsize=(12, 6))
for coin in df.columns[1:]:
    plt.plot(df_last24h["timestamp"], df_last24h[coin], label=coin)
plt.legend()
plt.title("Évolution des prix sur 24h")
plt.xlabel("Heure")
plt.ylabel("Prix en USD")
plt.grid(True)
plt.tight_layout()
plt.savefig("daily_price_chart.png")
