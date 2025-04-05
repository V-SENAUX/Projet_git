#!/bin/bash

# Active l'environnement virtuel
source /home/ubuntu/Projet_git/venv/bin/activate

# Aller dans le dossier du projet (important pour que le chemin du CSV soit bon)
cd /home/ubuntu/Projet_git

# Exécuter le script de scraping
./scrape_mult.sh
