#!/bin/bash

# Avvia Kafka Connect in background
/etc/confluent/docker/run &

echo "Waiting for Kafka Connect to start..."
# Aspetta finché l'API di Connect non risponde (codice 200)
while [ $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8083/) -ne 200 ]; do 
  sleep 5
done

echo "Kafka Connect is UP! Loading MongoDB connector..."

curl -X PUT http://localhost:8083/connectors/mongo-sink-telemetria/config \
     -H "Content-Type: application/json" \
     -d '{
     "connector.class": "com.mongodb.kafka.connect.MongoSinkConnector",
     "tasks.max": "1",
     "topics": "impianto_1,impianto_2,impianto_3,impianto_4,impianto_5",
     "connection.uri": "mongodb://admin:password@mongodb:27017",
     "database": "iot_database",
     "key.converter": "org.apache.kafka.connect.storage.StringConverter",
     "value.converter": "org.apache.kafka.connect.json.JsonConverter",
     "value.converter.schemas.enable": "false",
     "errors.tolerance": "all",
     "errors.log.enable": "true",
     "errors.log.include.messages": "true"
   }'

wait