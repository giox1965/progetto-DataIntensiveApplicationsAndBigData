#!/bin/bash

SCRIPT_PYTHON="mock_sensors.py"

echo "=== 1. Arresto del progetto Docker Compose ==="

if command -v docker &> /dev/null; then
    echo "Esecuzione di sudo docker compose down..."
    sudo docker compose down
else
    echo "Docker non trovato o non installato, salto questo passaggio."
fi

echo "=== 2. Arresto dello script $SCRIPT_PYTHON ==="

PID_SCRIPT=$(pgrep -f "$SCRIPT_PYTHON")

if [ -n "$PID_SCRIPT" ]; then
    echo "Trovato processo $SCRIPT_PYTHON con PID: $PID_SCRIPT"
    echo "Arresto del processo in corso..."
    
    kill $PID_SCRIPT
    
    sleep 1
    if pgrep -f "$SCRIPT_PYTHON" &> /dev/null; then
        echo "Il processo non si è chiuso, forzatura con SIGKILL..."
        kill -9 $PID_SCRIPT
    fi
    echo "Script Python arrestato con successo."
else
    echo "Nessuna istanza di $SCRIPT_PYTHON trovata in esecuzione."
fi

echo "=== Sistema arrestato con successo! ==="