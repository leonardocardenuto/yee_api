#!/bin/bash

# Este script ativa o ambiente virtual e inicia a API Yee

# Ativar o ambiente virtual
cd /home/ec2-user/yee_app
source .venv/bin/activate


# Executar o script Python
python3 wsgi.py

