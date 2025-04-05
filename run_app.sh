#!/bin/bash

cd /home/ubuntu/Projet_git

# Kill le processus précédent
pkill -f "python3 app.py"

# Relancer
nohup python3 app.py > dash.log 2>&1 &
