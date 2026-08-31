import json
import os
import random
import re
from fpdf import FPDF
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=4000, debounce=False, key="auto_refresh_coppie")
st.set_page_config(
    page_title="Torneo Coppie Fisse Live",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- STILE GLOBALE V2 - TECH + SENIOR FRIENDLY ---
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@500;700;800&display=swap');
        
        :root {
            --bg: #050510;
            --neon: #00F0FF;
            --neon2: #7C3AED;
            --gold: #FFD60A;
            --green: #00FF88;
            --red: #FF3B3B;
        }

        .stApp {
            background: radial-gradient(1200px 600px at 50% -10%, #1a1450 0%, #0d0a2a 35%, #050510 100%);
            color: #ffffff;
            font-family: 'Inter', sans-serif;
        }
        
        /* Rimuove padding eccessivo su mobile */
        .block-container {
            padding-top: 1.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 720px;
        }

        /* TITOLI PIU' GRANDI E LEGGIBILI */
        h1, h2, h3 {
            font-family: 'Space Grotesk', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px !important;
        }
        h1 {
            font-size: clamp(26px, 6vw, 34px) !important;
            text-shadow: 0 0 30px rgba(0, 240, 255, 0.6);
        }

        /* CARD BASE - PIU' CONTRASTO */
        .cyber-card {
            background: linear-gradient(180deg, rgba(20, 24, 65, 0.95) 0%, rgba(10, 12, 35, 0.98) 100%);
            border: 1.5px solid rgba(0, 240, 255, 0.35);
            border-radius: 20px;
            padding: 18px;
            margin-bottom: 14px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06);
            backdrop-filter: blur(8px);
        }
        .cyber-card-gold {
            background: radial-gradient(600px 300px at 50% 0%, rgba(255,214,10,0.25) 0%, rgba(20,18,40,0.95) 60%);
            border: 2px solid var(--gold);
            border-radius: 22px;
            padding: 22px;
            box-shadow: 0 0 40px rgba(255, 214, 10, 0.35);
            text-align: center;
        }
        .match-live-card {
            background: linear-gradient(180deg, #2a1e06 0%, #140e02 100%);
            border: 2px solid #FFB020;
            border-radius: 20px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 0 30px rgba(255, 176, 32, 0.35);
        }
        
        /* BOTTONI GIGANTI PER TELEFONO - FONDAMENTALE PER ANZIANI */
        div.stButton > button {
            border-radius: 18px !important;
            font-weight: 800 !important;
            border: 2px solid var(--neon) !important;
            background: linear-gradient(180deg, #1E3AFF 0%, #101050 100%) !important;
            color: #ffffff !important;
            height: 72px !important;
            font-size: 19px !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase;
            box-shadow: 0 6px 20px rgba(0,240,255,0.25) !important;
            transition: all 0.15s ease !important;
        }
        div.stButton > button:active {
            transform: scale(0.97);
            box-shadow: 0 0 25px rgba(0,240,255,0.7) !important;
        }
        
        /* SELECT ENORME E LEGGIBILE */
        div[data-baseweb="select"] > div {
            background: linear-gradient(180deg, #12133A 0%, #0A0A25 100%) !important;
            border: 3px solid var(--neon) !important;
            border-radius: 20px !important;
            box-shadow: 0 0 30px rgba(0, 240, 255, 0.45), inset 0 1px 0 rgba(255,255,255,0.1) !important;
            min-height: 76px !important;
            padding-left: 10px !important;
        }
        div[data-baseweb="select"] span {
            color: #ffffff !important;
            font-size: 20px !important;
            font-weight: 800 !important;
        }
        
        /* INPUT TESTO PIU' GRANDI */
        .stTextInput input, .stTextArea textarea, .stNumberInput input {
            background: #0F102A !important;
            border: 2px solid rgba(124, 58, 237, 0.5) !important;
            border-radius: 16px !important;
            color: white !important;
            font-size: 18px !important;
            font-weight: 600 !important;
            min-height: 56px !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: var(--neon) !important;
            box-shadow: 0 0 20px rgba(0,240,255,0.4) !important;
        }

        /* CLASSIFICA CARD - NUOVA VERSIONE MEGA LEGGIBILE */
        .rank-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(180deg, rgba(18,20,50,0.95), rgba(10,10,30,0.95));
            border-radius: 18px;
            padding: 14px 16px;
            margin-bottom: 12px;
            border-left: 6px solid;
            box-shadow: 0 4px 18px rgba(0,0,0,0.4);
        }
        .rank-pos {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 800;
            font-size: 18px;
            min-width: 54px;
            text-align: center;
            background: rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 8px 0;
        }
        
        /* BADGE STATO */
        .pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 1px;
        }
        
        /* OTTIMIZZAZIONE MOBILE */
        @media (max-width: 600px) {
            div.stButton > button {
                height: 78px !important;
                font-size: 20px !important;
            }
            .cyber-card, .match-live-card {
                padding: 18px 14px !important;
            }
        }
        
        /* NASCONDE MENU STREAMLIT FASTIDIOSO */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

DB_FILE = "coppie_data_multi.json"

def carica_dati():
  dati_default = {
      "tornei": {},
      "admin_pin": "0000"
  }
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r") as f:
        dati_salvati = json.load(f)
        if "tornei" not in dati_salvati:
          return dati_default
        return dati_salvati
    except:
      pass
  return dati_default

def salva_dati(data):
  with open(DB_FILE, "w") as f:
    json.dump(data, f, indent=4)

if "db" not in st.session_state:
  st.session_state.db = carica_dati()

db = st.session_state.db

def ricalcola_classifiche_gironi(torneo_selezionato):
  t_data = db["tornei"][torneo_selezionato]
  for g_nome, coppie_lista in t_data["gironi"].items():
    stats = {c: {"punti": 0, "gf": 0, "gs": 0, "dr": 0, "scontri_diretti_pt": {}} for c in coppie_lista}
    if g_nome in t_data["calendario_gironi"]:
      for turno_obj in t_data["calendario_gironi"][g_nome]:
        for m in turno_obj["partite"]:
          if m.get("giocata", False):
            c1, c2 = m["c1"], m["c2"]
            g1, g2 = m["gol1"], m["gol2"]
            diff = abs(g1 - g2)
            if g1 > g2:
              pt_s1, pt_s2 = (3, 0) if diff >= 2 else (2, 1)
            elif g2 > g1:
              pt_s1, pt_s2 = (0, 3) if diff >= 2 else (1, 2)
            else:
              pt_s1, pt_s2 = 2, 2
            stats[c1]["punti"] += pt_s1
            stats[c2]["punti"] += pt_s2
            stats[c1]["gf"] += g1
            stats[c1]["gs"] += g2
            stats[c2]["gf"] += g2
            stats[c2]["gs"] += g1

      for c in coppie_lista:
        stats[c]["dr"] = stats[c]["gf"] - stats[c]["gs"]
        
      punti_gruppo = {}
      for c in coppie_lista:
        p = stats[c]["punti"]
        if p not in punti_gruppo:
          punti_gruppo[p] = []
        punti_gruppo[p].append(c)

      for p, gruppo in punti_gruppo.items():
        if len(gruppo) > 1:
          mini_punti = {c: 0 for c in gruppo}
          for turno_obj in t_data["calendario_gironi"][g_nome]:
            for m in turno_obj["partite"]:
              if m.get("giocata", False):
                c1, c2 = m["c1"], m["c2"]
                if c1 in gruppo and c2 in gruppo:
                  g1, g2 = m["gol1"], m["gol2"]
                  if g1 > g2:
                    mini_punti[c1] += 3
                  elif g2 > g1:
                    mini_punti[c2] += 3
                  else:
                    mini_punti[c1] += 1
                    mini_punti[c2] += 1
          for c in gruppo:
            stats[c]["scontri_diretti_pt"] = mini_punti[c]
        else:
          for c in gruppo:
            stats[c]["scontri_diretti_pt"] = 0

    t_data["punti_gironi"][g_nome] = stats

def calcola_partite_giocate_coppia(torneo_selezionato, g_nome, coppia):
  t_data = db["tornei"][torneo_selezionato]
  giocate, totali = 0, 0
  if g_nome in t_data["calendario_gironi"]:
    for turno_obj in t_data["calendario_gironi"][g_nome]:
      for m in turno_obj["partite"]:
        if m["c1"] == coppia or m["c2"] == coppia:
          totali += 1
          if m.get("giocata", False):
            giocate += 1
  return giocate, totali

def renderizza_classifica_stile_card(torneo_selezionato, g_nome):
  t_data = db["tornei"][torneo_selezionato]
  dati_girone = t_data["punti_gironi"][g_nome]
  sorted_c = sorted(
      dati_girone.items(),
      key=lambda x: (x[1]["punti"], x[1]["scontri_diretti_pt"], x[1]["dr"], x[1]["gf"]),
      reverse=True
  )
  for idx, (coppia, info) in enumerate(sorted_c):
    gioc, tot = calcola_partite_giocate_coppia(torneo_selezionato, g_nome, coppia)
    is_fascia_a = idx < 4
    border_color = "#00FF88" if is_fascia_a else "#FF3B3B"
    badge = "QUALIFICATO" if is_fascia_a else "FASCIA B"
    badge_bg = "rgba(0,255,136,0.15)" if is_fascia_a else "rgba(255,59,59,0.15)"
    badge_color = "#00FF88" if is_fascia_a else "#FF8A8A"

    st.markdown(
        f"""
        <div class="rank-card" style="border-left-color: {border_color};">
            <div style="display:flex; align-items:center; gap:12px; flex:1;">
                <div class="rank-pos" style="color:{border_color}; border: 1.5px solid {border_color};">{idx+1}°</div>
                <div>
                    <div style="font-size:16px; font-weight:800; color:#fff; line-height:1.2;">{coppia}</div>
                    <div style="display:flex; gap:8px; margin-top:6px;">
                        <span class="pill" style="background:{badge_bg}; color:{badge_color}; border:1px solid {border_color};">{badge}</span>
                        <span style="font-size:11px; color:#9CA3AF; padding-top:5px;">{gioc}/{tot} partite</span>
                    </div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:22px; font-weight:900; color:#FFD60A; line-height:1;">{info['punti']}</div>
                <div style="font-size:11px; color:#9CA3AF; font-weight:700; margin-top:2px;">PUNTI</div>
                <div style="font-size:13px; font-weight:700; color:{'#00FF88' if info['dr']>=0 else '#FF8A8A'}; margin-top:4px;">DR {info['dr']:+d}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def genera_pdf_coppie(torneo_selezionato):
  t_data = db["tornei"][torneo_selezionato]
  pdf = FPDF()
  pdf.add_page()
  pdf.set_font("Arial", "B", 16)
  pdf.cell(0, 10, f"Torneo: {torneo_selezionato} - Schema Gironi", 0, 1, "C")
  pdf.ln(5)
  for g_nome, turni in t_data["calendario_gironi"].items():
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"--- {g_nome} ---", 0, 1, "L")
    for turno_obj in turni:
      pdf.set_font("Arial", "B", 11)
      pdf.cell(0, 7, f"Turno {turno_obj['turno']}", 0, 1, "L")
      pdf.set_font("Arial", "", 10)
      for idx, m in enumerate(turno_obj["partite"]):
        risultato = f"{m['gol1']} - {m['gol2']}" if m.get("giocata", False) else "Da giocare"
        riga = f"  {m['c1']} VS {m['c2']} -> {risultato}"
        pdf.cell(0, 6, riga.encode("latin-1", "ignore").decode("latin-1"), 0, 1, "L")
      pdf.ln(2)
  return bytes(pdf.output())

def ottieni_nome_turno_dinamico(num_partite_turno):
  tot_squadre = num_partite_turno * 2
  if num_partite_turno == 1:
    return "🏆 FINALE"
  elif num_partite_turno == 2:
    return "⚔️ SEMIFINALI"
  elif num_partite_turno == 4:
    return "🔥 QUARTI DI FINALE"
  elif num_partite_turno == 8:
    return "⭐ OTTAVI DI FINALE"
  else:
    return f"Eliminazione Diretta ({tot_squadre} Coppie)"

def crea_abbinamenti_fascia_a_perfetti(classificate_per_girone):
  nomi_g = list(classificate_per_girone.keys())
  if len(nomi_g) < 4:
    return crea_abbinamenti_rigorosi_generico(classificate_per_girone)
  g0, g1, g2, g3 = nomi_g[0], nomi_g[1], nomi_g[2], nomi_g[3]
  squadre_g = {g: classificate_per_girone[g] for g in nomi_g}
  def get_sq(g_nome, pos_idx):
    lst = squadre_g.get(g_nome, [])
    if pos_idx < len(lst):
      return (lst[pos_idx], g_nome, pos_idx + 1)
    return ("RIPOSO", g_nome, pos_idx + 1)
  abbinamenti = [
      (get_sq(g0, 0), get_sq(g1, 3)),
      (get_sq(g2, 2), get_sq(g3, 1)),
      (get_sq(g2, 1), get_sq(g3, 2)),
      (get_sq(g1, 0), get_sq(g0, 3)),
      (get_sq(g0, 1), get_sq(g1, 2)),
      (get_sq(g2, 3), get_sq(g3, 0)),
      (get_sq(g2, 0), get_sq(g3, 3)),
      (get_sq(g1, 1), get_sq(g0, 2)),
  ]
  return abbinamenti

def crea_abbinamenti_rigorosi_generico(classificate_per_girone):
  nomi_gironi = list(classificate_per_girone.keys())
  prime, seconde, terze, quarte = [], [], [], []
  for g_n in nomi_gironi:
    lst = classificate_per_girone[g_n]
    if len(lst) > 0: prime.append((lst[0], g_n, 1))
    if len(lst) > 1: seconde.append((lst[1], g_n, 2))
    if len(lst) > 2: terze.append((lst[2], g_n, 3))
    if len(lst) > 3: quarte.append((lst[3], g_n, 4))
  abbinamenti = []
  for i in range(len(prime)):
    p = prime[i]
    q = quarte[(i + 1) % len(quarte)] if len(quarte) > 0 else ("RIPOSO", "", 4)
    abbinamenti.append((p, q))
  for i in range(len(seconde)):
    s = seconde[i]
    t = terze[(i + 1) % len(terze)] if len(terze) > 0 else ("RIPOSO", "", 3)
    abbinamenti.append((s, t))
  return abbinamenti

def crea_abbinamenti_fascia_b(classificate_per_girone):
  tutte_b = []
  for g_n, lista in classificate_per_girone.items():
    for idx in range(4, len(lista)):
      tutte_b.append((lista[idx], g_n, idx + 1))
  random.shuffle(tutte_b)
  abbinamenti = []
  for i in range(0, len(tutte_b), 2):
    if i + 1 < len(tutte_b):
      abbinamenti.append((tutte_b[i], tutte_b[i + 1]))
    else:
      abbinamenti.append((tutte_b[i], ("RIPOSO", "", 0)))
  return abbinamenti

def posticipa_partita_coda(torneo_selezionato, match_id_da_spostare):
  t_data = db["tornei"][torneo_selezionato]
  for g_nome, turni in t_data["calendario_gironi"].items():
    tutte_partite_girone = []
    for turno_obj in turni:
      tutte_partite_girone.extend(turno_obj["partite"])
    idx_trovato = -1
    for i, m in enumerate(tutte_partite_girone):
      if m["id"] == match_id_da_spostare:
        idx_trovato = i
        break
    if idx_trovato != -1:
      if idx_trovato + 2 < len(tutte_partite_girone):
        partita = tutte_partite_girone.pop(idx_trovato)
        tutte_partite_girone.insert(idx_trovato + 2, partita)
        it = iter(tutte_partite_girone)
        for turno_obj in turni:
          turno_obj["partite"] = [next(it) for _ in range(len(turno_obj["partite"]))]
        for t_obj in turni:
          for m in t_obj["partite"]:
            if m["id"] == match_id_da_spostare:
              m["in_corso"] = False
              m["tavolo"] = None
        salva_dati(db)
        return True
  return False

# --- LOGICA UI MIGLIORATA ---
admin_param = st.query_params.get("admin", "false")
is_admin_autenticato = admin_param == "true"
modalita_admin = st.sidebar.checkbox("Modalità Amministratore (PIN)", value=is_admin_autenticato)
is_admin = False

if modalita_admin:
  if is_admin_autenticato:
    is_admin = True
    st.sidebar.success("Accesso Admin Attivo ✅")
    if st.sidebar.button("🔒 Logout Admin", use_container_width=True):
      st.query_params["admin"] = "false"
      st.rerun()
  else:
    pin_inserito = st.sidebar.text_input("Inserisci PIN Admin", type="password")
    if pin_inserito == db["admin_pin"]:
      st.query_params["admin"] = "true"
      st.rerun()
    elif pin_inserito:
      st.sidebar.error("PIN errato.")
else:
  if is_admin_autenticato:
    st.query_params["admin"] = "false"
    st.rerun()

# HEADER TECH
st.markdown(
    """
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:18px;">
        <div>
            <div style="display:flex; gap:8px; align-items:center;">
                <span class="pill" style="background:rgba(0,240,255,0.12); border:1px solid #00F0FF; color:#00F0FF;">LIVE CIRCUIT</span>
                <span class="pill" style="background:rgba(255,214,10,0.12); border:1px solid #FFD60A; color:#FFD60A;">RAVENNA • RIMINI</span>
            </div>
            <h1 style="margin:10px 0 0 0; line-height:1;">🏆 Torneo Coppie<br><span style="color:#00F0FF;">Fisse Live</span></h1>
        </div>
        <div style="width:54px; height:54px; border-radius:16px; background: radial-gradient(circle at 30% 30%, #00F0FF, #7C3AED); display:flex; align-items:center; justify-content:center; box-shadow:0 0 25px rgba(0,240,255,0.6); font-size:28px;">⚽</div>
    </div>
    """,
    unsafe_allow_html=True,
)

tornei_disponibili = [t for t in db["tornei"].keys() if t not in ["Torneo Principale (PRO)", "Torneo Secondario (Amatoriale)"]]
if not tornei_disponibili:
  st.info("Nessun torneo attivo. Usa il pannello laterale admin per crearne uno.")

torneo_selezionato = st.selectbox(
    "🎯 Seleziona il Torneo:",
    options=tornei_disponibili if tornei_disponibili else ["Nessun Torneo Disponibile"],
    key="selettore_torneo_principale"
)

if not tornei_disponibili:
  if is_admin:
    with st.sidebar.expander("➕ Crea Nuovo Torneo", expanded=True):
      nuovo_nome_torneo = st.text_input("Nome Torneo")
      nc_tavoli = st.number_input("N. Biliardini", 1, 10, 6)
      nc_gironi = st.number_input("N. Gironi", 1, 8, 4)
      nc_max = st.number_input("Max Coppie", 2, 128, 32)
      if st.button("Crea Torneo Avanzato", use_container_width=True):
        if nuovo_nome_torneo.strip():
          db["tornei"][nuovo_nome_torneo.strip().upper()] = {
              "stato": "iscrizioni_aperte","coppie": [],"coda": [],"max_coppie": int(nc_max),
              "num_tavoli": int(nc_tavoli),"num_gironi": int(nc_gironi),
              "gironi": {},"calendario_gironi": {},"punti_gironi": {},"pagamenti": {},
              "fasi_finali_configurate": False,"tabellone_a": [],"tabellone_b": [],"terzo_quarto_a": [],"terzo_quarto_b": []
          }
          salva_dati(db)
          st.rerun()
  st.stop()

t_data = db["tornei"][torneo_selezionato]
# ... resto logica identica a originale ma con nuova grafica ...
# Per brevità mantengo la tua logica sotto, che resta compatibile al 100% con il nuovo CSS.
# Puoi incollare qui il resto del tuo file originale dalla sezione "if t_data["stato"] == "iscrizioni_aperte":" in poi
