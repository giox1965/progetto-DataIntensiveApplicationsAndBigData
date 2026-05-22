#!/bin/bash

VENV_DIR=".venv"
SCRIPT_PYTHON="mock_sensors.py"

echo "=== 1. Controllo e configurazione Ambiente Virtuale ==="

if ! command -v python3 &> /dev/null; then
    echo "Errore: Python3 non è installato su questo sistema."
    exit 1
fi

echo "=== 2. Avvio dello script mock_sensors.py ==="

if [ -f "$SCRIPT_PYTHON" ]; then
    echo "Avvio di $SCRIPT_PYTHON in background..."
    python3 "$SCRIPT_PYTHON" > mock_sensors.log 2>&1 &
    
    PID_SCRIPT=$!
    echo "Script avviato con successo (PID: $PID_SCRIPT). I log sono in 'mock_sensors.log'."
else
    echo "Errore: file $SCRIPT_PYTHON non trovato!"
    deactivate
    exit 1
fi

deactivate

echo "=== 3. Avvio del progetto Docker Compose ==="

if ! command -v docker &> /dev/null; then
    echo "Errore: Docker non sembra essere installato."
    exit 1
fi

echo "Esecuzione di sudo docker compose up --build -d..."
sudo docker compose up --build -d

echo "=== Procedura completata! ==="