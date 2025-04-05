#!/bin/bash
cd /home/ubuntu/Projet_git
nohup ./run_app.sh > dash.log 2>&1 &
echo "Dashboard lancé sur le port 8050."
