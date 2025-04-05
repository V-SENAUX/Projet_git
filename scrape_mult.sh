#!/bin/bash

# URL de la page à scrapper
URL1="https://www.zonebourse.com/cours/cryptomonnaie/BITCOIN-BTC-USD-45553945/"
URL2="https://www.zonebourse.com/cours/cryptomonnaie/ETHEREUM-ETH-USD-45554109/"
URL3="https://www.zonebourse.com/cours/cryptomonnaie/BINANCE-COIN-BNB-USD-133757270/"
URL4="https://www.zonebourse.com/cours/cryptomonnaie/SOLANA-SOL-USD-128433627/"

#Télécharger le contenu de chaque page
content1=$(curl -s "$URL1")
content2=$(curl -s "$URL2")
content3=$(curl -s "$URL3")
content4=$(curl -s "$URL4")

# Récupérer l'heure actuelle
time0=$(date '+%Y-%m-%d %H:%M:%S')

# Créer un fichier CSV s il n existe pas
if [ ! -f bitcoin_data_mult.csv ]; then
    echo "timestamp;bitcoin;ethereum;binance_coin;solana" > bitcoin_data_mult.csv
fi

price1=$(echo "$content1" | grep -oP 'data-id="45553945" data-type="Cryptoquotes" data-field="last" data-round="2"  >\s*\K[^<]+' | head -n 1)
price2=$(echo "$content2" | grep -oP 'data-id="45554109" data-type="Cryptoquotes" data-field="last" data-round="2"  >\s*\K[^<]+' | head -n 1)
price3=$(echo "$content3" | grep -oP 'data-id="133757270" data-type="Cryptoquotes" data-field="last" data-round="4"  >\s*\K[^<]+' | head -n 1)
price4=$(echo "$content4" | grep -oP 'data-id="128433627" data-type="Cryptoquotes" data-field="last" data-round="4"  >\s*\K[^<]+' | head -n 1)

# Sauvegarder les données
line="$time0;$price1;$price2;$price3;$price4"
echo "$line" >> bitcoin_data_mult.csv

# Afficher le résultat
echo "Scraped at $time0: ; Bitcoin: $price1 USD ; Etherum: $price2 USD ; Binance coin: $price3 USD ; Solana: $price4 USD"


