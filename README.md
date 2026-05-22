# Progetto di Data Intensive Application and Big Data

![Logo del Progetto](img/architetturaDIABD.jpg)

---

## Descrizione generale

Questo progetto implementa un'architettura completa per l'acquisizione, l'elaborazione, l'archiviazione e la visualizzazione di dati in tempo reale. Il sistema è progettato per ricevere dati grezzi da sensori (tramite UDP), instradarli attraverso un cluster Apache Kafka ad alta disponibilità, salvarli su MongoDB tramite Kafka Connect e infine visualizzarli su dashboard interattive con Grafana e un'interfaccia web personalizzata in Flask.

---

## Architettura e componenti

Il sistema è interamente containerizzato e si divide nei seguenti macro-blocchi logici:

### 1. Mock sensori:
Il punto di partenza dell'architettura consiste nella simulazione e generazione dei dati IoT, progettati per essere iniettati nel framework Apache Kafka. Ogni payload generato dai sensori presenta una struttura JSON leggera:

* sensor_id (String): Identificativo univoco del singolo dispositivo (es. TEMP, VIB).
* type (String): Tipologia di grandezza fisica rilevata (es. temperatura, vibrazione, umidità).
* value (Float): Valore numerico della telemetria, comprensivo di fluttuazioni e simulazione di anomalie casuali.
* location (String): L'impianto in cui il sensore è fisicamente installato (es. impianto_1, impianto_2).
* timestamp (String/ISO 8601): Data e ora esatta dell'acquisizione del dato.

Il campo location definisce l'instradamento dei dati all'interno del framework, determinando dinamicamente il topic di destinazione del messaggio. Questo garantisce la separazione logica e fisica dei flussi di dati tra impianti differenti.

### 2. Ingestion dei dati (sensori)

*   **Sensor gateway (`sensor-gateway`)**: Un'applicazione custom che espone la porta `8081 (UDP)` per ricevere i dati grezzi. Una volta ricevuto il datagramma UDP grezzo, il compito del Gateway si articola in due fasi fondamentali:

* Estrazione della chiave di routing: Viene letto il campo location per determinare il topic.
* Pubblicazione su Kafka: Il payload viene serializzato nuovamente ed emesso nel cluster Kafka tramite il modulo Producer della libreria confluent_kafka.

### 3. Streaming e messaggistica (Apache Kafka in modalità KRaft)
Il progetto utilizza Kafka senza ZooKeeper (modalità KRaft) garantendo un'architettura scalabile tramite 5 nodi:
*   **Controller Node**: 1 nodo (`controller`) dedicato esclusivamente alla gestione del quorum.
*   **Mixed Nodes**: 2 nodi (`broker1`, `broker2`) che fungono sia da broker per i dati che da controller.
*   **Broker Nodes**: 2 nodi (`broker3`, `broker4`) dedicati esclusivamente allo storage e allo smistamento dei messaggi.

### 4. Integrazione e storage (Kafka Connect & MongoDB)
*   **Kafka Connect (`connect`)**: Servizio configurato per trasferire automaticamente i dati dai topic Kafka verso altre destinazioni (in questo caso specifico, MongoDB).
*   **MongoDB (`mongodb`)**: Database NoSQL utilizzato come storage persistente a valle della pipeline.

### 5. Visualizzazione e frontend (Grafana & Flask)
*   **Grafana (`grafana`)**: Piattaforma di observability pre-configurata con plugin specifici (Infinity, Kafka datasource) per visualizzare metriche e dati in tempo reale. Le dashboard e le sorgenti dati vengono fornite automaticamente (provisioning).
*   **Flask App (`flask`)**: Applicazione web personalizzata che funge da frontend e API per interagire con i dati aggregati, interfacciandosi con MongoDB e Grafana.

---

## Prerequisiti

Per eseguire questo progetto, assicurati di utilizzare il sistema operativo richiesto e di avere installato i software necessari sulla tua macchina.

### Requisiti di Sistema
*   **Sistema Operativo:** Ubuntu (consigliata versione 22.04 LTS o superiore)

### Software richiesti
*   [Docker Engine](https://docs.docker.com/engine/install/)
*   [Docker Compose](https://docs.docker.com/compose/install/)
*   [Python 3.x](https://www.python.org/downloads/) (consigliata la versione 3.12 o superiore)
---

## Come avviare il progetto

1. Clona questo repository:
   ```bash
   git clone https://github.com/giox1965/progetto-kafka-esame-BigDataIntensiveApplications.git
   cd progetto-kafka-esame-BigDataIntensiveApplications
2. Assegna i permessi di esecuzione:
   ```
   chmod +x start.sh
   chmod +x stop.sh
   ```
3. Esegui il sistema:
   ```
   bash start.sh
   ```
4. Accedi al sistema da http://localhost:5000
5. Arresta il sistema:
   ```
   bash stop.sh
   ```

---

## Realizzazione del progetto

### 1. Configurazione del cluster Kafka (KRaft Mode)

La topologia del cluster è definita all'interno del file `docker-compose.yml` ed è composta da 5 nodi distribuiti strategicamente per garantire alta affidabilità e tolleranza ai guasti. Le configurazioni chiave si basano su variabili d'ambiente specifiche per ogni container:

#### Suddivisione dei ruoli (`KAFKA_PROCESS_ROLES`)
In un'architettura KRaft, i nodi possono assumere il ruolo di *broker* (gestione dei dati), *controller* (gestione dei metadati e del cluster) o entrambi. Nel nostro progetto i ruoli sono così distribuiti:

*   **Nodo controller dedicato (`controller`):** 
    *   `KAFKA_PROCESS_ROLES=controller`
    *   `KAFKA_NODE_ID=1`
    *   Questo nodo non memorizza i dati dei sensori, ma si occupa esclusivamente di mantenere il consenso e gestire lo stato del cluster, riducendo il carico di I/O.
*   **Nodi misti (`broker1`, `broker2`):**
    *   `KAFKA_PROCESS_ROLES=broker,controller`
    *   `KAFKA_NODE_ID=2` e `3`
    *   Questi due nodi gestiscono sia il salvataggio dei messaggi sia le operazioni di controllo, partecipando attivamente alle elezioni del quorum insieme al nodo controller puro.
*   **Nodi broker puri (`broker3`, `broker4`):**
    *   `KAFKA_PROCESS_ROLES=broker`
    *   `KAFKA_NODE_ID=4` e `5`
    *   Questi container sono dedicati esclusivamente allo storage e alla distribuzione dei messaggi sui topic.

#### Il quorum e il cluster ID
Per far comunicare correttamente i nodi e garantire che condividano lo stesso stato, sono state configurate due variabili fondamentali su **tutti** i container Kafka:

*   `KAFKA_CLUSTER_ID`: Impostato su una stringa univoca (`"xtzWWN4bTjitpL3kfd9s5g"`). Assicura che tutti e 5 i nodi si riconoscano come appartenenti alla stessa rete logica.
*   `KAFKA_CONTROLLER_QUORUM_VOTERS`: Definisce quali nodi hanno diritto di voto per l'elezione del leader del cluster. Nel nostro caso, è impostato su `1@controller:9093,2@broker1:9093,3@broker2:9093`. In questo modo, il quorum è composto da 3 nodi, permettendo al cluster di continuare a funzionare anche se uno dei nodi votanti dovesse fallire.

#### Rete e listeners
La comunicazione di rete è separata logicamente:
*   I metadati del controller viaggiano sulla porta `9093` tramite i `KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER`.
*   I dati applicativi (i messaggi dei sensori) vengono scambiati tra i broker e verso i client sulla porta `9091` tramite l'interfaccia `INTERNAL`. I nodi broker puri espongono solo quest'ultima, in quanto non partecipano al traffico di controllo.

#### Replicazione
Per garantire un alta disponibilità dei dati e tolleranza ai guasti i topic vengono replicati con un fattore di replicazione `KAFKA_DEFAULT_REPLICATION_FACTOR: 3`.

### 2. Archiviazione dati ed interfaccia

Per garantire la persistenza a lungo termine dei dati provenienti dai sensori, il progetto utilizza **MongoDB**, un database NoSQL orientato ai documenti, ideale per memorizzare le strutture JSON flessibili.

#### MongoDB (`mongodb`)
Questo container esegue l'istanza principale del database, e rappresenta la destinazione finale (Sink) della nostra pipeline di streaming.
*   **Sicurezza ed autenticazione:** Il database viene inizializzato al primo avvio con le credenziali di root definite dalle variabili d'ambiente (`MONGO_INITDB_ROOT_USERNAME=admin` e `MONGO_INITDB_ROOT_PASSWORD=password`). 
*   **Integrazione con Kafka:** I dati non vengono scritti direttamente in MongoDB dall'applicazione dei sensori, ma vengono riversati automaticamente dal servizio **Kafka Connect**, che legge dal topic e inserisce i documenti nel database nella collezione associata al topic.

### 3. Automazione e configurazione di Kafka Connect

Per trasferire i dati in tempo reale dal cluster Kafka a MongoDB, il progetto sfrutta **Kafka Connect**. Invece di configurare manualmente il connettore ad ogni avvio, è stata implementata una soluzione completamente automatizzata tramite un'immagine Docker personalizzata.

#### Build personalizzata e script di avvio (`entrypoint.sh`)
Il servizio `connect` è basato sull'immagine ufficiale Confluent, ma è stato esteso tramite un `Dockerfile` dedicato per eseguire due operazioni fondamentali:
1.  **Installazione del plugin:** Scarica e installa automaticamente il plugin ufficiale `mongodb/kafka-connect-mongodb` tramite `confluent-hub`.
2.  **Auto-provisioning (entrypoint.sh):** Lo script di avvio fa partire il worker di Kafka Connect in background e rimane in ascolto (tramite polling) finché l'API REST non risponde con un codice `200 OK`. A quel punto, inietta automaticamente la configurazione del connettore tramite una chiamata `curl`.

#### Dettaglio della Configurazione
La chiamata REST configura un connettore denominato `mongo-sink-telemetria` con le seguenti proprietà chiave:

*   **Flusso dei dati:**
    *   `connector.class`: Specifica l'utilizzo del `MongoSinkConnector` per scrivere dati verso MongoDB.
    *   `topics`: Indica al connettore da quale topic Kafka deve leggere i messaggi in arrivo.
*   **Destinazione MongoDB:**
    *   `connection.uri`: `mongodb://admin:password@mongodb:27017` URI di connessione con le credenziali definite nel container del database.
    *   `database`: `iot_database` Nome del database di destinazione, creato automaticamente se non esiste.

    Configurando in questa modalità il connettore, per ogni topic registrato in Kafka verrà creata una specifica collezione in MongoDB.
 
### 4. Frontend e API REST (Flask)

Per rendere i dati archiviati facilmente accessibili agli utenti e integrabili in interfacce personalizzate, il progetto include un'applicazione backend leggera scritta in Python utilizzando il micro-framework **Flask**. Questo servizio agisce da strato intermedio (middleware) tra il database MongoDB e il frontend.

L'applicazione si connette all'istanza interna di MongoDB tramite la libreria `pymongo` ed espone una serie di endpoint RESTful utili per l'esplorazione e la visualizzazione dei dati:

#### Endpoint Esposti

*   **`GET /`**
    Restituisce la pagina web principale (`index.html` servito dalla cartella templates) che agisce da dashboard utente.
*   **`GET /api/<impianto_id>/<sensor_id>/mean`**
    Recupera tutti i dati di un sensore in un impianto, suddivide i record in intervalli di 5 minuti e restituisce le medie dei valori in ogni intervallo.
*   **`GET /api/query_personalizzata `**
    Esegue una query personalizzata nel DB e restituisce il risultato.
*   **`GET /api/impianti `**
    Restituisce gli impianti (collezioni) presenti nel DB.
*   **`GET /api/<impianto_id>/sensori`**
    Restituisce i sensori presenti nell'impianto selezionato.

L'applicazione è configurata per l'esecuzione in background dal `docker-compose` ed è esposta sull'host locale alla porta **5000** (`http://localhost:5000`).

### 5. Visualizzazione e monitoraggio (Grafana)

La presentazione dei dati è affidata a **Grafana**, una piattaforma leader per la creazione di dashboard interattive. 

Invece di richiedere all'utente di configurare manualmente le sorgenti dati e creare i grafici al primo avvio, il progetto utilizza il meccanismo di **Provisioning** di Grafana. Tramite file di configurazione YAML, l'istanza parte già perfettamente integrata con il resto dell'infrastruttura.

#### Origini dati preconfigurate (Datasources)
All'avvio, Grafana carica automaticamente due datasource essenziali, abilitati grazie all'installazione di plugin specifici definiti nel `docker-compose.yml`:

1.  **Flask API (Infinity Datasource):** 
    *   **Plugin:** `yesoreyeram-infinity-datasource`
    *   **Scopo:** Permette a Grafana di interrogare direttamente gli endpoint REST esposti dal nostro backend Flask.
2.  **Kafka Cluster (Kafka Datasource):**
    *   **Plugin:** `hamedkarbasi93-kafka-datasource`
    *   **Scopo:** Stabilisce una connessione diretta con i nodi del cluster Kafka (`broker1`...`broker4` sulla porta `9091`). Questo permette di monitorare lo stream di messaggi in tempo reale direttamente dai topic, bypassando completamente il database.

#### Caricamento automatico delle dashboard
Oltre alle sorgenti dati, anche i cruscotti grafici vengono forniti dinamicamente:
*   **Provider delle Dashboard:** Un file YAML indica a Grafana di scansionare la directory `/var/lib/grafana/dashboards` (montata come volume dal progetto locale).

![Logo del Progetto](img/architetturaDettaglioDIABD.jpg)