import streamlit as st
import random
import re
import json
import os
import io
import time
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configurazione generale dell'Hub (deve essere la prima chiamata Streamlit)
st.set_page_config(
    page_title="Hub Tornei // By Battani", 
    page_icon="🏆", 
    layout="centered"
)

# --- STILE GRAFICO GLOBALE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@600;700&display=swap');

    .main { 
        background-color: #02040a; 
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(0, 243, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 50% 100%, rgba(212, 175, 55, 0.05) 0%, transparent 50%),
            linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
        font-family: 'Rajdhani', sans-serif;
        color: #f8fafc;
    }

    h1, h2, h3, h4, .stMarkdown {
        font-family: 'Orbitron', sans-serif !important;
    }

    .hero-title-container {
        text-align: center;
        padding: 20px 10px;
        margin-bottom: 20px;
    }
    .hero-main-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.8em;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 3px;
        background: linear-gradient(135deg, #00ff88 0%, #d4af37 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.4), 0 0 40px rgba(212, 175, 55, 0.3);
        margin-bottom: 5px;
    }
    .hero-subtitle {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.95em;
        font-weight: 700;
        color: #00f3ff;
        letter-spacing: 4px;
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
    }
    
    .pro-turn-banner {
        background: linear-gradient(135deg, #02151a, #04262b);
        border-left: 5px solid #00f3ff;
        border-right: 5px solid #d4af37;
        border-top: 1px solid rgba(0, 243, 255, 0.4);
        border-bottom: 1px solid rgba(212, 175, 55, 0.4);
        border-radius: 6px;
        padding: 16px;
        text-align: center;
        color: #00f3ff;
        font-family: 'Orbitron', sans-serif;
        font-size: 1.3em;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 4px;
        margin-bottom: 25px;
        box-shadow: 0 0 25px rgba(0, 243, 255, 0.25), inset 0 0 10px rgba(212, 175, 55, 0.1);
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
    }

    .pro-match-card {
        background: linear-gradient(160deg, #041014, #020608);
        border: 2px solid rgba(0, 243, 255, 0.5);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.8), 0 0 20px rgba(0, 243, 255, 0.15);
    }

    .match-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(212, 175, 55, 0.2);
        padding-bottom: 8px;
    }

    .biliardino-title {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        color: #d4af37;
        font-size: 1em;
        letter-spacing: 1.5px;
        text-shadow: 0 0 8px rgba(212, 175, 55, 0.4);
    }

    .turno-badge {
        background: #02151a;
        border: 1px solid #00f3ff;
        color: #00f3ff;
        padding: 3px 10px;
        border-radius: 4px;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.75em;
        font-weight: 700;
        letter-spacing: 1px;
        box-shadow: 0 0 8px rgba(0, 243, 255, 0.3);
    }

    .match-teams-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #041921;
        border: 1px solid rgba(0, 243, 255, 0.3);
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }

    .team-box {
        flex: 1;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.9em;
        font-weight: 700;
        color: #f8fafc;
        text-transform: uppercase;
    }

    .vs-badge {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        color: #d4af37;
        font-size: 1.1em;
        padding: 0 15px;
        text-shadow: 0 0 10px rgba(212, 175, 55, 0.6);
    }

    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #02202b, #043d52) !important;
        color: #ffffff !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        border: 1px solid #00f3ff !important;
        border-radius: 6px !important;
        padding: 10px 0px !important;
        font-size: 0.85em !important;
        letter-spacing: 1.0px !important;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.3);
        margin-top: 10px;
    }
    
    .pro-rank-container {
        background: #040c12;
        border: 1px solid rgba(0, 243, 255, 0.2);
        border-top: 3px solid #d4af37;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.5), 0 0 15px rgba(212, 175, 55, 0.1);
    }
    .pro-rank-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.1em;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12px;
        padding-bottom: 6px;
        border-bottom: 1px solid rgba(212, 175, 55, 0.3);
        color: #d4af37;
        text-shadow: 0 0 8px rgba(212, 175, 55, 0.4);
    }
    .pro-player-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #061721;
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 6px;
        font-size: 0.9em;
        border: 1px solid rgba(0, 243, 255, 0.15);
    }
    .pro-rank-name {
        font-family: 'Orbitron', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        color: #d4af37;
    }
    </style>
""", unsafe_allow_html=True)

# --- MENU DI SELEZIONE PRINCIPALE (SIDEBAR) ---
st.sidebar.title("🏆 HUB TORNEI // BATTANI")
tipo_torneo = st.sidebar.selectbox(
    "Scegli quale Torneo Avviare:",
    [
        "🏠 Home Hub",
        "⚽️ Torneo 1 (Inserisci nome)",
        "🎾 Torneo 2 (Inserisci nome)",
        "🔥 Torneo 3 (Baraonda a Vite)"
    ]
)

st.sidebar.markdown("---")

# =========================================================================
# 1. HOME HUB
# =========================================================================
if tipo_torneo == "🏠 Home Hub":
    st.markdown("""
        <div class="hero-title-container">
            <div class="hero-main-title">Piattaforma Unificata Tornei</div>
            <div class="hero-subtitle">Gestione Sportiva // By Battani</div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("### Benvenuto nell'Hub Centrale!")
        st.write("Da qui puoi gestire e selezionare comodamente il torneo desiderato tramite il menu laterale a sinistra.")
        st.info("💡 **Suggerimento:** Ciascun torneo mantiene le proprie impostazioni, classifiche e file di stato salvati separatamente in modo da non sovrapporre i dati.")

# =========================================================================
# 2. TORNEO 1 (Inserisci il codice del tuo primo script)
# =========================================================================
elif tipo_torneo == "⚽️ Torneo 1 (Inserisci nome)":
    st.markdown("""
        <div class="hero-title-container">
            <div class="hero-main-title">Torneo 1</div>
            <div class="hero-subtitle">By Battani</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.info("⚠️ Inserisci qui il codice del tuo **Torneo 1** adattando le chiavi dello `st.session_state` con il prefisso `t1_`.")
    
    # Esempio di struttura base per il Torneo 1:
    if "t1_iscritti" not in st.session_state:
        st.session_state.t1_iscritti = []
        
    squadra_t1 = st.text_input("Aggiungi partecipante/squadra al Torneo 1:", key="input_t1")
    if st.button("Registra in Torneo 1"):
        if squadra_t1:
            st.session_state.t1_iscritti.append(squadra_t1)
            st.success(f"Aggiunto: {squadra_t1}")
            
    st.write("Iscritti Torneo 1:", st.session_state.t1_iscritti)

# =========================================================================
# 3. TORNEO 2 (Inserisci il codice del tuo secondo script)
# =========================================================================
elif tipo_torneo == "🎾 Torneo 2 (Inserisci nome)":
    st.markdown("""
        <div class="hero-title-container">
            <div class="hero-main-title">Torneo 2</div>
            <div class="hero-subtitle">By Battani</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.info("⚠️ Inserisci qui il codice del tuo **Torneo 2** adattando le chiavi dello `st.session_state` con il prefisso `t2_`.")
    
    # Esempio di struttura base per il Torneo 2:
    if "t2_iscritti" not in st.session_state:
        st.session_state.t2_iscritti = []
        
    squadra_t2 = st.text_input("Aggiungi partecipante/squadra al Torneo 2:", key="input_t2")
    if st.button("Registra in Torneo 2"):
        if squadra_t2:
            st.session_state.t2_iscritti.append(squadra_t2)
            st.success(f"Aggiunto: {squadra_t2}")
            
    st.write("Iscritti Torneo 2:", st.session_state.t2_iscritti)

# =========================================================================
# 4. TORNEO 3 (Baraonda a Vite - Codice completo integrato)
# =========================================================================
elif tipo_torneo == "🔥 Torneo 3 (Baraonda a Vite)":
    
    # Gestione dello stato specifica per la Baraonda
    STATE_FILE_B = "torneo_baraonda_state.json"

    def salva_stato_baraonda():
        data = {
            "players": st.session_state.baraonda_players,
            "tournament_started": st.session_state.baraonda_tournament_started,
            "initial_lives": st.session_state.baraonda_initial_lives,
            "num_biliardini": st.session_state.baraonda_num_biliardini,
            "current_round_matches": st.session_state.baraonda_current_round_matches,
            "round_number": st.session_state.baraonda_round_number,
        }
        with open(STATE_FILE_B, "w") as f:
            json.dump(data, f)

    def carica_stato_baraonda():
        if os.path.exists(STATE_FILE_B):
            try:
                with open(STATE_FILE_B, "r") as f:
                    data = json.load(f)
                    st.session_state.baraonda_players = data.get("players", [])
                    st.session_state.baraonda_tournament_started = data.get("tournament_started", False)
                    st.session_state.baraonda_initial_lives = data.get("initial_lives", 5)
                    st.session_state.baraonda_num_biliardini = data.get("num_biliardini", 4)
                    st.session_state.baraonda_current_round_matches = data.get("current_round_matches", [])
                    st.session_state.baraonda_round_number = data.get("round_number", 0)
                    return True
            except:
                return False
        return False

    if "baraonda_initialized" not in st.session_state:
        st.session_state.baraonda_initialized = True
        if not carica_stato_baraonda():
            st.session_state.baraonda_players = []
            st.session_state.baraonda_tournament_started = False
            st.session_state.baraonda_initial_lives = 5
            st.session_state.baraonda_num_biliardini = 4
            st.session_state.baraonda_current_round_matches = []
            st.session_state.baraonda_round_number = 0

    if "baraonda_giocatore_selezionato" not in st.session_state:
        st.session_state.baraonda_giocatore_selezionato = None

    def genera_abbinamenti_baraonda():
        attivi = [p for p in st.session_state.baraonda_players if not p["eliminated"]]
        
        if st.session_state.baraonda_round_number == 1:
            atts = [p for p in attivi if p["role"] == "attaccante"]
            ports = [p for p in attivi if p["role"] == "portiere"]
            random.shuffle(atts)
            random.shuffle(ports)
            
            min_len = min(len(atts), len(ports))
            coppie = []
            for i in range(min_len):
                coppie.append({"att": atts[i], "port": ports[i]})
            random.shuffle(coppie)
        else:
            atts_w = [p for p in attivi if p["role"] == "attaccante" and p.get("last_result") == 'W']
            atts_l = [p for p in attivi if p["role"] == "attaccante" and p.get("last_result") != 'W']
            ports_w = [p for p in attivi if p["role"] == "portiere" and p.get("last_result") == 'W']
            ports_l = [p for p in attivi if p["role"] == "portiere" and p.get("last_result") != 'W']
            
            random.shuffle(atts_w)
            random.shuffle(atts_l)
            random.shuffle(ports_w)
            random.shuffle(ports_l)
            
            coppie = []
            while atts_w and ports_l:
                coppie.append({"att": atts_w.pop(0), "port": ports_l.pop(0)})
            while atts_l and ports_w:
                coppie.append({"att": atts_l.pop(0), "port": ports_w.pop(0)})
            while atts_w and ports_w:
                coppie.append({"att": atts_w.pop(0), "port": ports_w.pop(0)})
            while atts_l and ports_l:
                coppie.append({"att": atts_l.pop(0), "port": ports_l.pop(0)})
                
            random.shuffle(coppie)

        partite = []
        i = 0
        while i < len(coppie) - 1:
            partite.append({
                "teamA": (coppie[i]["att"], coppie[i]["port"]),
                "teamB": (coppie[i+1]["att"], coppie[i+1]["port"])
            })
            i += 2
            
        return {"partite": partite}

    # Security Admin Sidebar specifica per la Baraonda
    admin_code_b = st.sidebar.text_input("Codice Admin (Baraonda)", type="password", key="admin_b_pass")
    is_admin_b = (admin_code_b == "0000")

    # Titolo della pagina
    st.markdown("""
        <div class="hero-title-container">
            <div class="hero-main-title">Torneo Baraonda a Vite</div>
            <div class="hero-subtitle">Con Ruolo Live // By Battani</div>
        </div>
    """, unsafe_allow_html=True)

    nomi_giocatori_b = sorted(list(set([p["name"] for p in st.session_state.baraonda_players]))) if st.session_state.baraonda_players else []

    if st.session_state.baraonda_giocatore_selezionato is None:
        if nomi_giocatori_b:
            with st.container(border=True):
                st.markdown("### 👤 SELEZIONA UTENTE:")
                nome_scelto_b = st.selectbox("Iscritti:", nomi_giocatori_b, key="sel_user_b")
                if st.button("ACCEDI ALLA COMPETIZIONE", type="primary"):
                    st.session_state.baraonda_giocatore_selezionato = nome_scelto_b
                    st.rerun()
        else:
            st.warning("⚠️ Nessun partecipante caricato. Configura i dati dal pannello Admin sottostante.")
            
        if is_admin_b:
            with st.expander("⚙️ Pannello Configurazione & Gestione (Admin Baraonda)", expanded=True):
                st.session_state.baraonda_initial_lives = st.number_input("Vite iniziali", 1, 10, st.session_state.baraonda_initial_lives, key="b_ilives")
                st.session_state.baraonda_num_biliardini = st.number_input("Numero Biliardini", 1, 10, st.session_state.baraonda_num_biliardini, key="b_num_bil")
                lista_input_b = st.text_area("Incolla partecipanti (es: 1 ⚽️ Nome, 2 🥅 Nome):", height=80, key="b_in_text")
                if st.button("📥 Importa e Registra Giocatori", type="primary", key="b_imp_btn"):
                    for riga in lista_input_b.split("\n"):
                        riga_pulita = riga.strip()
                        if not riga_pulita: continue
                        role = "portiere" if "🥅" in riga_pulita else ("attaccante" if "⚽" in riga_pulita else None)
                        if role:
                            nome = re.sub(r'^\d+[\.\-\s]*', '', riga_pulita.replace("🥅", "").replace("⚽️", "").replace("⚽", "")).strip()
                            if nome and not any(p["name"].lower() == nome.lower() and p["role"] == role for p in st.session_state.baraonda_players):
                                st.session_state.baraonda_players.append({
                                    "id": len(st.session_state.baraonda_players)+1, 
                                    "name": nome, 
                                    "role": role, 
                                    "lives": st.session_state.baraonda_initial_lives, 
                                    "max_lives": st.session_state.baraonda_initial_lives, 
                                    "eliminated": False, 
                                    "last_result": None
                                })
                    salva_stato_baraonda()
                    st.rerun()
                if len(st.session_state.baraonda_players) >= 2 and not st.session_state.baraonda_tournament_started:
                    if st.button("🚀 Avvia Torneo", type="primary", key="b_start_btn"):
                        st.session_state.baraonda_tournament_started = True
                        st.session_state.baraonda_round_number = 1
                        st.session_state.baraonda_current_round_matches = genera_abbinamenti_baraonda()
                        salva_stato_baraonda()
                        st.rerun()
        st.stop()

    # Pannello di controllo utente loggato
    col_ub1, col_ub2 = st.columns([3, 1])
    with col_ub1:
        st.info(f"⚡ Operatore Connesso: **{st.session_state.baraonda_giocatore_selezionato.upper()}**")
    with col_ub2:
        if st.button("🔄 Logout", use_container_width=True, key="logout_b_btn"):
            st.session_state.baraonda_giocatore_selezionato = None
            st.rerun()

    st.markdown("---")

    if st.session_state.baraonda_tournament_started:
        data_turno_b = st.session_state.baraonda_current_round_matches
        
        if data_turno_b and not data_turno_b.get("partite"):
            st.session_state.baraonda_round_number += 1
            st.session_state.baraonda_current_round_matches = genera_abbinamenti_baraonda()
            salva_stato_baraonda()
            st.rerun()

        st.markdown(f"""<div class="pro-turn-banner">⚔️ TURNO DI GARA N° {st.session_state.baraonda_round_number}</div>""", unsafe_allow_html=True)

        partite_b = data_turno_b.get("partite", []) if data_turno_b else []
        if partite_b:
            num_bil_b = st.session_state.baraonda_num_biliardini
            partite_in_corso_b = partite_b[:num_bil_b]

            for idx_b, match_b in enumerate(partite_in_corso_b):
                tA_att, tA_port = match_b["teamA"]
                tB_att, tB_port = match_b["teamB"]
                biliardino_num_b = idx_b + 1

                st.markdown(f"""
                    <div class="pro-match-card">
                        <div class="match-header-row">
                            <span class="biliardino-title">🏟️ BILIARDINO {biliardino_num_b}</span>
                            <span class="turno-badge">TURNO {st.session_state.baraonda_round_number}</span>
                        </div>
                        <div class="match-teams-row">
                            <div class="team-box">🥅 {tA_port['name'].upper()} / ⚽️ {tA_att['name'].upper()}</div>
                            <div class="vs-badge">VS</div>
                            <div class="team-box">🥅 {tB_port['name'].upper()} / ⚽️ {tB_att['name'].upper()}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                nome_coppia_a_b = f"{tA_port['name'].upper()} & {tA_att['name'].upper()}"
                nome_coppia_b_b = f"{tB_port['name'].upper()} & {tB_att['name'].upper()}"

                cb1, cb2 = st.columns(2)
                with cb1:
                    if st.button(f"⚡ VITTORIA: {nome_coppia_a_b}", key=f"bwa_{st.session_state.baraonda_round_number}_{idx_b}", use_container_width=True):
                        perdenti_b = [tB_att, tB_port]
                        for v in [tA_att, tA_port]: v["last_result"] = 'W'
                        for per in perdenti_b:
                            per["last_result"] = 'L'
                            per["lives"] = max(0, per["lives"] - 1)
                            if per["lives"] == 0: per["eliminated"] = True

                        st.session_state.baraonda_current_round_matches["partite"].pop(idx_b)
                        salva_stato_baraonda()
                        st.rerun()

                with cb2:
                    if st.button(f"⚡ VITTORIA: {nome_coppia_b_b}", key=f"bwb_{st.session_state.baraonda_round_number}_{idx_b}", use_container_width=True):
                        perdenti_b = [tA_att, tA_port]
                        for v in [tB_att, tB_port]: v["last_result"] = 'W'
                        for per in perdenti_b:
                            per["last_result"] = 'L'
                            per["lives"] = max(0, per["lives"] - 1)
                            if per["lives"] == 0: per["eliminated"] = True

                        st.session_state.baraonda_current_round_matches["partite"].pop(idx_b)
                        salva_stato_baraonda()
                        st.rerun()

    st.markdown("---")

    if st.session_state.baraonda_players:
        st.markdown("### 📊 CLASSIFICHE IN TEMPO REALE")
        col_bc1, col_bc2 = st.columns(2)
        with col_bc1:
            st.markdown("""<div class="pro-rank-container"><div class="pro-rank-header">🥅 CLASSIFICA PORTIERI</div>""", unsafe_allow_html=True)
            for p in [x for x in st.session_state.baraonda_players if x["role"] == "portiere"]:
                if "max_lives" not in p:
                    p["max_lives"] = max(p["lives"], st.session_state.baraonda_initial_lives)
                pallini_str = ("🟢 " * p["lives"]) + ("🔴 " * (p["max_lives"] - p["lives"]))
                st.markdown(f"""<div class="pro-player-row"><span class="pro-rank-name">{p['name']}</span><span>{pallini_str}</span></div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with col_bc2:
            st.markdown("""<div class="pro-rank-container"><div class="pro-rank-header">⚽️ CLASSIFICA ATTACCANTI</div>""", unsafe_allow_html=True)
            for p in [x for x in st.session_state.baraonda_players if x["role"] == "attaccante"]:
                if "max_lives" not in p:
                    p["max_lives"] = max(p["lives"], st.session_state.baraonda_initial_lives)
                pallini_str = ("🟢 " * p["lives"]) + ("🔴 " * (p["max_lives"] - p["lives"]))
                st.markdown(f"""<div class="pro-player-row"><span class="pro-rank-name">{p['name']}</span><span>{pallini_str}</span></div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
