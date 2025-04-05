#!/bin/bash
cd /home/ubuntu/Projet_git
source ../myenv/bin/activate
python generate_report.py >> report.log 2>&1
