#!/bin/bash

cd /home/ubuntu/Projet_git

# Relancer
nohup python3 app.py > dash.log 2>&1 &
