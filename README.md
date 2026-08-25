# Torneo Coppie Fisse LIVE

App Streamlit mobile-first in stile Dark / Gaming / Neon.

## Regole già impostate

- PIN Admin: `0000`
- Il giocatore deve obbligatoriamente selezionare il proprio nome.
- Ogni giocatore vede la propria area personale.
- La partita LIVE della propria coppia viene mostrata in alto.
- Il giocatore può inserire il risultato solo della propria partita LIVE.
- Il punteggio si seleziona con pulsanti da 0 a 7, senza tastiera.
- Vittoria con scarto >= 2: 3 punti.
- Vittoria con scarto di 1: 2 punti al vincitore e 1 al perdente.
- Pareggio: 2 punti a testa.
- Classifica: punti, scontri diretti, differenza reti, gol fatti.
- Fascia A: prime 4 posizioni di ogni girone.
- Fascia B: posizioni successive.
- Fasi finali con avanzamento.
- Regola LIVE fissa: **chi perde resta al tavolo**.
- La prossima coppia in coda entra contro chi è rimasto al tavolo.
- Aggiornamento automatico ogni 5 secondi.

## Avvio

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Nota

Questa versione usa lo stato di Streamlit. Per un torneo reale con molti telefoni collegati contemporaneamente, il passo successivo consigliato è collegare un database centrale (es. Supabase/PostgreSQL), così tutti i dispositivi condividono lo stesso stato in modo affidabile.


## WhatsApp / avvisi di turno

Il giocatore inserisce obbligatoriamente il numero WhatsApp insieme al nome.

La logica prevista è:
1. quando la coppia è a una partita dal turno, viene preparato l'avviso "PREPARATI";
2. quando viene assegnato il tavolo, viene preparato l'avviso "È IL VOSTRO TURNO" con numero del biliardino e avversario.

**Nota:** per l'invio effettivo dei messaggi WhatsApp è necessario collegare una WhatsApp Business Platform/API. Questa versione salva già il numero e prepara gli eventi di notifica, ma non invia messaggi tramite un account WhatsApp personale.
