#!/bin/bash
cd "$(dirname "$0")"

# Vérification et installation des dépendances système (demandera le mot de passe sudo si nécessaire)
if ! dpkg -s libxcb-cursor0 >/dev/null 2>&1; then
    echo "Installation de la dépendance système libxcb-cursor0 requise par PyQt6 (X11)..."
    sudo apt-get update
    sudo apt-get install -y libxcb-cursor0
fi

if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

LIVECHAT_DEBUG=1 python -m livechat_desktop
