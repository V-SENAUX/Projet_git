#!/bin/bash

# URL de la page à scrapper
URL="https://www.zonebourse.com/cours/cryptomonnaie/BITCOIN-BTC-USD-45553945/"

# Télécharger le contenu de la page
content=$(curl -s "$URL")

# Extraire le prix du bitcoin à partir du fichier téléchargé
price=$(echo "$content" | grep -oP 'data-id="45553945" data-type="Cryptoquotes" data-field="last" data-round="2"  >\s*\K[^<]+' | head -n 1)

# Récupérer l'heure actuelle
time=$(date '+%Y-%m-%d %H:%M:%S')

# Créer un fichier CSV s'il n'existe pas
if [ ! -f bitcoin_data.csv ]; then
    echo "timestamp,price" > bitcoin_data.csv
fi

# Sauvegarder les données
echo "$time,$price" >> bitcoin_data.csv

# Afficher le résultat
echo "Scraped at $time: $price USD"
