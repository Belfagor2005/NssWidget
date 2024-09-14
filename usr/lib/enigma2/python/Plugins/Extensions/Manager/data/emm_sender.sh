#!/bin/bash
# # mod by lululla 24/08/2024
# # Aggiornato il $(date +"%d/%m/%Y")

set -e  # # Interrompe l'esecuzione in caso di errori

# # Funzione per la pulizia
cleanup() { rm -f /tmp/*.tmp /tmp/*.html; }

# # Assicura la pulizia anche in caso di interruzione dello script
trap cleanup EXIT

# # Costanti
ATR_183E='3F FF 95 00 FF 91 81 71 FE 47 00 54 49 47 45 52 36 30 31 20 52 65 76 4D 38 37 14'
atr_string='aHR0cHM6Ly9wYXN0ZWJpbi5jb20vcmF3L0I5N0hDOGll'

echo "Trova il file di configurazione di Oscam"
OSCAM_VERSION=$(find /tmp/ -name oscam.version | sed -n 1p)
OSCAM_CONFIG_DIR=$(grep -ir "ConfigDir" "$OSCAM_VERSION" | awk -F ":      " '{ print $2 }')
OSCAM_CONF="${OSCAM_CONFIG_DIR}/oscam.conf"

emm_file=$(echo "$atr_string" | base64 -d)

echo "Estrai le informazioni di configurazione"
OSCAM_USER=$(grep -ir "httpuser" "$OSCAM_CONF" | awk -F "=" '{ print $2 }' | sed 's/^[ \t]*//')
OSCAM_PASSWD=$(grep -ir "httppwd" "$OSCAM_CONF" | awk -F "=" '{ print $2 }' | sed 's/^[ \t]*//')
OSCAM_HTTPPORT=$(grep -ir "httpport" "$OSCAM_CONF" | awk -F "=" '{ print $2 }' | sed 's/^[ \t]*//')
OSCAM_PORT=$(echo "$OSCAM_HTTPPORT" | sed -e 's|+||g')

echo "Ottieni la lista dei lettori attivi"
curl -s --user "${OSCAM_USER}:${OSCAM_PASSWD}" --anyauth -k "http://127.0.0.1:${OSCAM_PORT}/status.html" |
    grep "Restart Reader" |
    sed -e 's|<TD CLASS="statuscol1"><A HREF="status.html?action=restart&amp;label=||g' |
    sed 's/^[ \t]*//' |
    awk -F "\"" '{ print $1 }' > /tmp/active_readers.tmp

# # Scarica il file EMM
if ! curl -s -o /tmp/emm.txt "$emm_file"; then
    echo "Errore nel download del file EMM. Uscita."
    exit 1
fi

echo "Processa ogni lettore attivo"
while IFS= read -r label; do
    curl -s --user "${OSCAM_USER}:${OSCAM_PASSWD}" --anyauth -k "http://127.0.0.1:${OSCAM_PORT}/entitlements.html?label=${label}" > "/tmp/${label}_entitlements.html"

    atr=$(grep -o '<TD COLSPAN="4">.*</TD>' "/tmp/${label}_entitlements.html" | sed 's|<TD COLSPAN="4">||;s|</TD>||' | sed 's/.$//g')

    if [ "$ATR_183E" == "$atr" ]; then
        echo "Invio nuovi EMM alla carta $label"
        emm=$(cat /tmp/emm.txt)
        curl -s -k --user "${OSCAM_USER}:${OSCAM_PASSWD}" --anyauth "http://127.0.0.1:${OSCAM_PORT}/emm_running.html?label=${label}&emmcaid=183E&ep=${emm}&action=Launch" > /dev/null
        echo "Invio EMM completato."
    fi
echo "Aggiornamento EMM completato."
done < /tmp/active_readers.tmp

exit 0


