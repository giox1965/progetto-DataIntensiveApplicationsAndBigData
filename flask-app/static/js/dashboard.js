const selectImpianto = document.getElementById('selectImpianto');
const txtQuery = document.getElementById('txtQuery');
const txtRisultato = document.getElementById('txtRisultato');
const btnInviaQuery = document.getElementById('btnInviaQuery');
const errorContainer = document.getElementById('errorContainer');

if (txtQuery.value.trim() === "") {
    txtQuery.value = JSON.stringify({
    "filtro": { "type": "temperature" },
    "ordinamento": "timestamp",
    "direzione": -1,
    "limite": 5
    }, null, 2);
}

btnInviaQuery.addEventListener('click', () => {
    errorContainer.textContent = ""; 
    txtRisultato.value = "Esecuzione in corso... attendere.";

    let querySintassi;
    try {
        querySintassi = JSON.parse(txtQuery.value);
    } catch (e) {
        errorContainer.textContent = "Errore di sintassi JSON: Controlla le virgole, le parentesi e le virgolette.";
        txtRisultato.value = "";
        return;
    }

    querySintassi.impianto = selectImpianto.value;

    fetch('/api/query_personalizzata', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(querySintassi)
    })
    .then(response => {
        if (!response.ok && response.status !== 400) {
            throw new Error(`Errore HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            errorContainer.textContent = data.error;
            txtRisultato.value = "";
        } else {
            txtRisultato.value = JSON.stringify(data, null, 2);
        }
    })
    .catch(err => {
        errorContainer.textContent = "Impossibile connettersi al server Flask. Controlla che sia in esecuzione.";
        txtRisultato.value = "";
        console.error(err);
    });
});