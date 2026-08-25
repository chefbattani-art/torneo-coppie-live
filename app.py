import streamlit as st
from streamlit_autorefresh import st_autorefresh
from core.torneo import nuovo_stato, crea_torneo
from core.gestione_partite import assegna_tavoli, registra_risultato
from core.classifiche import classifiche
from core.fasi_finali import prepara_fasce, crea_primo_turno, avanza_fascia
from utils.storage import carica, salva
from utils.importazione import importa_coppie
from utils.pdf import genera_pdf
from ui.styles import CSS
from ui.components import header, match_card, metric_card

st.set_page_config(page_title="Torneo Coppie Fisse LIVE", page_icon="🏆", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st_autorefresh(interval=5000, key="refresh")

if "state" not in st.session_state:
    st.session_state.state = carica() or nuovo_stato()
state = st.session_state.state

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<div class='brand'>⚽<br><b>TORNEO</b><br><span>COPPIE FISSE</span><br><strong>LIVE</strong></div>", unsafe_allow_html=True)
    page = st.radio(
        "MENU",
        ["⚡ Live", "🏆 Gironi & Classifiche", "🗓️ Calendario", "🥇 Fasi Finali", "📊 Statistiche", "🔐 Admin"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    if state.get("coppia_selezionata"):
        st.markdown(f"<div class='your-team'>👥 LA TUA COPPIA<br><b>{state['coppia_selezionata']}</b></div>", unsafe_allow_html=True)
    st.caption("Aggiornamento automatico ogni 5 secondi")

# --- SETUP ---
if state["fase"] == "setup":
    header("⚔️", "SETUP TORNEO", "CONFIGURAZIONE INIZIALE")
    st.markdown("<div class='hero'>🏆 <b>TORNEO COPPIE FISSE LIVE</b><br><small>Imposta il torneo e poi avvia la fase a gironi.</small></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        testo = st.text_area("Coppie partecipanti", height=220, placeholder="Mario Rossi / Luigi Bianchi\nPaolo Verdi / Marco Neri\n...")
        ng = st.number_input("Numero gironi", 1, 16, 2)
        nt = st.number_input("Biliardini disponibili", 1, 30, 2)
    with c2:
        st.markdown("### 📥 Importazione")
        st.info("Puoi incollare direttamente un elenco copiato da WhatsApp. Numeri ed emoji vengono ignorati.")
        if st.button("🚀 CREA TORNEO", use_container_width=True):
            coppie = importa_coppie(testo)
            if len(coppie) < 2:
                st.error("Inserisci almeno 2 coppie.")
            elif ng > len(coppie):
                st.error("I gironi non possono essere più numerosi delle coppie.")
            else:
                st.session_state.state = crea_torneo(coppie, int(ng), int(nt))
                salva(st.session_state.state)
                st.rerun()
    st.stop()

# assegna automaticamente i tavoli a ogni refresh
assegna_tavoli(state)

# --- LIVE ---
if page == "⚡ Live":
    header("⚔️", f"TORNEO N° {state.get('numero_torneo',1)}", "FASE A GIRONI", live=True)
    live = [m for ms in state["partite"].values() for m in ms if m["in_corso"]]
    queue = [m for ms in state["partite"].values() for m in ms if not m["giocata"] and not m["in_corso"]]

    st.markdown("### 🏆 PARTITE NEI BILIARDINI")
    if not live:
        st.info("Nessuna partita in corso. Il prossimo match verrà assegnato automaticamente.")
    for m in live:
        match_card(m, state)

    st.markdown("### 🕒 IN CODA")
    if queue:
        for i, m in enumerate(queue[:8], 1):
            st.markdown(f"<div class='queue'><span>CODA #{i}</span><b>{m['casa']}</b> ⚡ VS ⚡ <b>{m['ospite']}</b></div>", unsafe_allow_html=True)
    else:
        st.success("Coda vuota.")

    st.markdown("### 📊 CLASSIFICA GENERALE")
    cls = classifiche(state)
    for g, rows in cls.items():
        with st.expander(f"GIRONE {g}", expanded=True):
            st.dataframe(rows, use_container_width=True, hide_index=True)

# --- GIRONI ---
elif page == "🏆 Gironi & Classifiche":
    header("🏆", "GIRONI", "CLASSIFICHE LIVE")
    cls = classifiche(state)
    for g, rows in cls.items():
        st.markdown(f"<div class='section-title'>🏆 GIRONE {g}</div>", unsafe_allow_html=True)
        st.dataframe(rows, use_container_width=True, hide_index=True)
    if st.button("🥇 CHIUDI GIRONI E CREA FASCE", use_container_width=True):
        prepara_fasce(state)
        crea_primo_turno(state, "A")
        crea_primo_turno(state, "B")
        salva(state)
        st.rerun()

# --- CALENDARIO ---
elif page == "🗓️ Calendario":
    header("🗓️", "CALENDARIO", "PARTITE")
    for g, matches in state["partite"].items():
        st.markdown(f"### GIRONE {g}")
        for m in matches:
            status = "🟢 LIVE" if m["in_corso"] else ("✅ GIOCATA" if m["giocata"] else "⏳ CODA")
            score = f"{m['gol_casa']} - {m['gol_ospite']}" if m["giocata"] else "—"
            st.markdown(f"<div class='calendar-row'><b>{m['id']}</b> {m['casa']} <strong>VS</strong> {m['ospite']} <span>{score} · {status} · Tavolo {m.get('tavolo') or '—'}</span></div>", unsafe_allow_html=True)

# --- FINALI ---
elif page == "🥇 Fasi Finali":
    header("🥇", "FASI FINALI", "TABELLONI")
    for fascia in ["A", "B"]:
        st.markdown(f"<div class='section-title'>🏆 FASCIA {fascia}</div>", unsafe_allow_html=True)
        matches = state["finali"].get(fascia, [])
        if not matches:
            st.info("Tabellone non ancora generato.")
            continue
        for m in matches:
            match_card(m, state, final=True)
        if all(m["giocata"] for m in matches):
            if st.button(f"➡️ AVANZA FASCIA {fascia}", key=f"advance-{fascia}", use_container_width=True):
                avanza_fascia(state, fascia)
                salva(state)
                st.rerun()

    if state.get("podio"):
        st.markdown("<div class='podium'>🏆<br><b>PODIO FINALE</b><br><span>🥇 1°</span> &nbsp; <span>🥈 2°</span> &nbsp; <span>🥉 3°</span> &nbsp; <span>4°</span></div>", unsafe_allow_html=True)

# --- STATS ---
elif page == "📊 Statistiche":
    header("📊", "STATISTICHE", "TORNEO")
    cls = classifiche(state)
    total = sum(len(x) for x in state["partite"].values())
    done = sum(m["giocata"] for ms in state["partite"].values() for m in ms)
    a,b,c = st.columns(3)
    metric_card(a, "PARTITE", total, "calendario")
    metric_card(b, "GIOCATE", done, "live")
    metric_card(c, "COMPLETAMENTO", f"{(done/total*100):.0f}%" if total else "0%", "torneo")

# --- ADMIN ---
elif page == "🔐 Admin":
    header("🔐", "PANNELLO ADMIN", "CONTROLLO TORNEO")
    pin = st.text_input("PIN amministratore", type="password")
    if pin != state.get("admin_pin", "1234"):
        st.warning("Inserisci il PIN per accedere.")
    else:
        st.success("Admin autorizzato.")
        for tavolo in range(1, state["numero_tavoli"] + 1):
            if st.button(f"🔓 LIBERA BILIARDINO {tavolo}", key=f"free-{tavolo}"):
                for ms in state["partite"].values():
                    for m in ms:
                        if m.get("tavolo") == tavolo:
                            m["in_corso"] = False
                            m["tavolo"] = None
                salva(state)
                st.rerun()
        st.download_button("📄 ESPORTA PDF", genera_pdf(state), "torneo.pdf", "application/pdf", use_container_width=True)
        if st.button("⚠️ RESET TORNEO", use_container_width=True):
            st.session_state.state = nuovo_stato()
            salva(st.session_state.state)
            st.rerun()

salva(state)
