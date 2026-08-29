import json
import os
import random
import re
from fpdf import FPDF
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Aggiornato a 3 secondi per una fluidità e reattività elevata con tanti utenti
st_autorefresh(interval=3000, debounce=False, key="auto_refresh_coppie")
st.set_page_config(
    page_title="Torneo Coppie Fisse Live",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- STILE GLOBALE ---
st.markdown(
    """
    <style>
        .stApp {
            background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #0d091e 50%, #030712 100%);
            color: #f0f6fc;
            font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #130f26, #070510);
            border-right: 1px solid #2e1a47;
        }
        .cyber-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 27, 75, 0.7) 100%);
            border: 1px solid #00f0ff;
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 14px;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.15);
        }
        .cyber-card-gold {
            background: linear-gradient(135deg, rgba(30, 27, 75, 0.95) 0%, rgba(60, 40, 10, 0.8) 100%);
            border: 1.5px solid #ffd700;
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 0 25px rgba(255, 215, 0, 0.3);
            text-align: center;
        }
        .match-live-card {
            background: linear-gradient(135deg, #2b1f07 0%, #120d02 100%);
            border: 2px solid #f59e0b;
            border-radius: 16px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 0 25px rgba(245, 158, 11, 0.4);
        }
        h1, h2, h3, h4 {
            color: #ffffff !important;
            letter-spacing: 0.8px;
        }
        h1 {
            text-shadow: 0 0 20px rgba(0, 240, 255, 0.5);
        }
        div.stButton > button {
            border-radius: 10px;
            font-weight: 700;
            border: 1px solid #00f0ff;
            background: linear-gradient(180deg, #1e3a8a, #0f172a);
            color: #f3e8ff;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            border-color: #38bdf8;
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.6);
            color: #ffffff;
        }
        div[data-baseweb="select"] > div {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 27, 75, 0.95) 100%) !important;
            border: 2.5px solid #00f0ff !important;
            border-radius: 16px !important;
            box-shadow: 0 0 25px rgba(0, 240, 255, 0.6) !important;
            color: #ffffff !important;
            min-height: 60px !important;
            display: flex !important;
            align-items: center !important;
        }
        div[data-baseweb="select"] span {
            color: #ffffff !important;
            font-size: 20px !important;
            font-weight: 800 !important;
            letter-spacing: 0.5px !important;
        }
        div[data-baseweb="select"] svg {
            fill: #00f0ff !important;
            width: 28px !important;
            height: 28px !important;
        }
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
        
        tornei_da_rimuovere = ["TORNEO GIOVEDÌ 3 MASSA LOMBARDA", "TORNEO GIOVEDÌ 3 MASSALOMBARDA", "Torneo Principale (PRO)", "Torneo Secondario (Amatoriale)"]
        for t_rem in tornei_da_rimuovere:
          if t_rem in dati_salvati["tornei"]:
            del dati_salvati["tornei"][t_rem]

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
    border_color = "#4ade80" if is_fascia_a else "#f87171"
    bg_gradient = "linear-gradient(135deg, rgba(6, 36, 26, 0.8) 0%, rgba(3, 15, 10, 0.8) 100%)" if is_fascia_a else "linear-gradient(135deg, rgba(36, 6, 15, 0.8) 0%, rgba(15, 3, 7, 0.8) 100%)"
    shadow_color = "rgba(74, 222, 128, 0.2)" if is_fascia_a else "rgba(248, 113, 113, 0.2)"
    dot_color = "#4ade80" if is_fascia_a else "#f87171"

    st.markdown(
        f"""
        <div style="background: {bg_gradient}; border: 1.5px solid {border_color}; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0 0 15px {shadow_color}; display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 10px; height: 10px; background-color: {dot_color}; border-radius: 50%; box-shadow: 0 0 8px {dot_color};"></div>
                <span style="font-size: 16px; font-weight: 800; color: {dot_color}; min-width: 30px;">{idx+1}°</span>
                <span style="font-size: 15px; font-weight: bold; color: #ffffff;">⚽🏆 {coppia}</span>
            </div>
            <div style="display: flex; gap: 14px; text-align: right; font-size: 13px;">
                <div>
                    <span style="font-size: 9px; color: #94a3b8; display: block;">PT</span>
                    <span style="font-weight: 800; color: #ffd700; font-size: 15px;">{info['punti']}</span>
                </div>
                <div>
                    <span style="font-size: 9px; color: #94a3b8; display: block;">G</span>
                    <span style="color: #f0f6fc; font-weight: 600;">{gioc}/{tot}</span>
                </div>
                <div>
                    <span style="font-size: 9px; color: #94a3b8; display: block;">DR</span>
                    <span style="color: {"#4ade80" if info['dr'] >= 0 else "#f87171"}; font-weight: 600;">{info['dr']:+d}</span>
                </div>
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
  elif num_partite_turno == 16:
    return "🌟 SEDICESIMI DI FINALE"
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

# --- GESTIONE ADMIN DALLA SIDEBAR ---
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

st.sidebar.markdown("---")

# --- SELETTORE TORNEO IN EVIDENZA IN ALTO ---
st.markdown(
    """
    <div style="text-align: left; margin-bottom: 8px;">
        <span style="color: #00f0ff; font-size: 13px; letter-spacing: 2px; font-weight: bold;">TOURNAMENT CIRCUIT SELECTION</span>
        <h1 style="font-size: 28px; margin: 4px 0 12px 0; color: #ffffff; text-shadow: 0 0 25px rgba(0,240,255,0.6);">
            🏆 Torneo Coppie Fisse Live
        </h1>
    </div>
    """,
    unsafe_allow_html=True,
)

tornei_disponibili = [t for t in db["tornei"].keys() if t not in ["Torneo Principale (PRO)", "Torneo Secondario (Amatoriale)"]]

if not tornei_disponibili:
  st.info("Nessun torneo attivo al momento. Utilizza il pannello laterale admin per crearne uno nuovo.")

torneo_selezionato = st.selectbox(
    "🎯 Seleziona il Torneo a cui vuoi partecipare o consultare:",
    options=tornei_disponibili if tornei_disponibili else ["Nessun Torneo Disponibile"],
    key="selettore_torneo_principale"
)

if not tornei_disponibili:
  if is_admin:
    with st.sidebar.expander("➕ Crea Nuovo Torneo con Parametri", expanded=True):
      nuovo_nome_torneo = st.text_input("Nome del Torneo / Categoria")
      col_nc1, col_nc2 = st.columns(2)
      with col_nc1:
        nc_tavoli = st.number_input("N. Biliardini", min_value=1, max_value=10, value=6)
        nc_gironi = st.number_input("N. Gironi", min_value=1, max_value=8, value=4)
      with col_nc2:
        nc_max = st.number_input("Max Coppie (Titolari)", min_value=2, max_value=128, value=32)
        
      if st.button("Crea Torneo Avanzato", use_container_width=True):
        if nuovo_nome_torneo.strip() and nuovo_nome_torneo.strip().upper() not in db["tornei"]:
          db["tornei"][nuovo_nome_torneo.strip().upper()] = {
              "stato": "iscrizioni_aperte",
              "coppie": [],
              "coda": [],
              "max_coppie": int(nc_max),
              "num_tavoli": int(nc_tavoli),
              "num_gironi": int(nc_gironi),
              "gironi": {},
              "calendario_gironi": {},
              "punti_gironi": {},
              "fasi_finali_configurate": False,
              "tabellone_a": [],
              "tabellone_b": [],
              "terzo_quarto_a": [],
              "terzo_quarto_b": []
          }
          salva_dati(db)
          st.success("Torneo creato con successo!")
          st.rerun()
  st.stop()

t_data = db["tornei"][torneo_selezionato]

if "coda" not in t_data:
  t_data["coda"] = []
if "max_coppie" not in t_data:
  t_data["max_coppie"] = 32
salva_dati(db)

if is_admin:
  with st.sidebar.expander("➕ Crea Nuovo Torneo con Parametri"):
    nuovo_nome_torneo = st.text_input("Nome del Torneo / Categoria")
    col_nc1, col_nc2 = st.columns(2)
    with col_nc1:
      nc_tavoli = st.number_input("N. Biliardini", min_value=1, max_value=10, value=6)
      nc_gironi = st.number_input("N. Gironi", min_value=1, max_value=8, value=4)
    with col_nc2:
      nc_max = st.number_input("Max Coppie (Titolari)", min_value=2, max_value=128, value=32)
      
    if st.button("Crea Torneo Avanzato", use_container_width=True):
      if nuovo_nome_torneo.strip() and nuovo_nome_torneo.strip().upper() not in db["tornei"]:
        db["tornei"][nuovo_nome_torneo.strip().upper()] = {
            "stato": "iscrizioni_aperte",
            "coppie": [],
            "coda": [],
            "max_coppie": int(nc_max),
            "num_tavoli": int(nc_tavoli),
            "num_gironi": int(nc_gironi),
            "gironi": {},
            "calendario_gironi": {},
            "punti_gironi": {},
            "fasi_finali_configurate": False,
            "tabellone_a": [],
            "tabellone_b": [],
            "terzo_quarto_a": [],
            "terzo_quarto_b": []
        }
        salva_dati(db)
        st.success("Torneo creato con successo!")
        st.rerun()

  # --- BLOCCO ELIMINAZIONE TORNEO ---
  st.sidebar.markdown("---")
  st.sidebar.subheader("🗑️ Elimina Torneo")
  
  tornei_eliminabili = list(db["tornei"].keys())
  
  if tornei_eliminabili:
    torneo_da_eliminare = st.sidebar.selectbox("Seleziona torneo da rimuovere", options=tornei_eliminabili, key="sel_del_torneo")
    conferma_canc_torneo = st.sidebar.checkbox("Conferma eliminazione definitiva", key="chk_del_torneo")
    
    if st.sidebar.button("Elimina Torneo Selezionato", use_container_width=True):
      if conferma_canc_torneo:
        if torneo_da_eliminare in db["tornei"]:
          del db["tornei"][torneo_da_eliminare]
          salva_dati(db)
          st.success(f"Torneo '{torneo_da_eliminare}' eliminato con successo!")
          st.rerun()
      else:
        st.sidebar.warning("⚠️ Spunta la casella di conferma per procedere.")
  else:
    st.sidebar.info("Nessun torneo disponibile.")

st.sidebar.markdown("⚙️ Pannello di Controllo")

if t_data["stato"] != "iscrizioni_aperte" and t_data["stato"] != "setup":
  pdf_data = genera_pdf_coppie(torneo_selezionato)
  st.sidebar.download_button(
      label="📥 Scarica Schema in PDF",
      data=pdf_data,
      file_name=f"schema_gironi_{torneo_selezionato.lower().replace(' ', '_')}.pdf",
      mime="application/pdf",
      use_container_width=True,
  )
  st.sidebar.markdown("---")

if is_admin and t_data["stato"] == "fasi_finali":
  if st.sidebar.button("🔙 Torna temporaneamente ai Gironi", use_container_width=True):
    t_data["stato"] = "gironi"
    salva_dati(db)
    st.rerun()
  st.sidebar.markdown("---")

st.sidebar.subheader("⚠️ Zona Pericolo")
if is_admin:
  conferma_reset = st.sidebar.checkbox("Spunta per confermare il reset di questo torneo", key="checkbox_reset_gara")
  if st.sidebar.button("🔄 Ricomincia questo torneo da zero", use_container_width=True):
    if conferma_reset:
      db["tornei"][torneo_selezionato] = {
          "stato": "iscrizioni_aperte",
          "coppie": [],
          "coda": [],
          "max_coppie": t_data.get("max_coppie", 32),
          "num_tavoli": t_data.get("num_tavoli", 6),
          "num_gironi": t_data.get("num_gironi", 4),
          "gironi": {},
          "calendario_gironi": {},
          "punti_gironi": {},
          "fasi_finali_configurate": False,
          "tabellone_a": [],
          "tabellone_b": [],
          "terzo_quarto_a": [],
          "terzo_quarto_b": []
      }
      salva_dati(db)
      st.success("Torneo azzerato con successo!")
      st.rerun()
    else:
      st.sidebar.warning("⚠️ Spunta la casella di conferma sopra per procedere.")
else:
  st.sidebar.info("🔐 Accedi come admin per resettare.")

st.sidebar.markdown("---")

with st.expander("ℹ️ Come funziona il torneo"):
  st.markdown(
      """
        L'app consente l'iscrizione autonoma o l'incolla rapido da WhatsApp. Se si supera il limite massimo di coppie configurato, i partecipanti in eccesso vengono inseriti automaticamente in **Lista d'Attesa (Coda)**. Quando l'Admin fa partire il torneo, vengono creati i gironi casuali dei titolari.
        """,
      unsafe_allow_html=True,
  )

# --- GESTIONE ISCRIZIONI APERTE CON CODA E MAIUSCOLA FORZATA ---
if t_data["stato"] == "iscrizioni_aperte":
  st.markdown(f"### 📝 Registrazione Autonoma & Incolla WhatsApp - {torneo_selezionato}")
  st.info(f"Limite massimo coppie titolari impostato: **{t_data['max_coppie']}**. Se il limite è raggiunto, le successive iscrizioni entreranno automaticamente in coda.")

  with st.form(f"form_iscrizione_{torneo_selezionato}"):
    c1_input = st.text_input("Nome Giocatore 1")
    c2_input = st.text_input("Nome Giocatore 2")
    
    st.markdown("---")
    whatsapp_paste = st.text_area("📋 Incolla qui la lista WhatsApp (es. 1. Mario/Luigi, oppure righe separate)")
    
    submit_isc = st.form_submit_button("Registra / Importa Coppie 🚀", use_container_width=True)

    if submit_isc:
      nuove_inserite = []
      
      if c1_input.strip() and c2_input.strip():
        nuova_c = f"{c1_input.strip().upper()} / {c2_input.strip().upper()}"
        nuove_inserite.append(nuova_c)

      if whatsapp_paste.strip():
        linee = whatsapp_paste.split("\n")
        for linea in linee:
          linea_pulita = re.sub(r'^\s*(\d+[\.\)]\s*|-\s*)', '', linea).strip()
          if not linea_pulita:
            continue
          
          separatori = ["/", "-", " E ", " CON "]
          coppia_formattata = None
          
          for sep in separatori:
            if sep.lower() in linea_pulita.lower():
              parti = re.split(sep, linea_pulita, flags=re.IGNORECASE)
              if len(parti) >= 2:
                p1 = parti[0].strip().upper()
                p2 = parti[1].strip().upper()
                if p1 and p2:
                  coppia_formattata = f"{p1} / {p2}"
                  break
          
          if not coppia_formattata:
            parole = linea_pulita.split()
            if len(parole) >= 2:
              meta = len(parole) // 2
              p1 = " ".join(parole[:meta]).upper()
              p2 = " ".join(parole[meta:]).upper()
              if p1 and p2:
                coppia_formattata = f"{p1} / {p2}"

          if coppia_formattata:
            nuove_inserite.append(coppia_formattata)

      aggiunte_titolari = 0
      aggiunte_coda = 0

      for nc in nuove_inserite:
        nc_upper = nc.upper()
        if nc_upper not in t_data["coppie"] and nc_upper not in t_data["coda"]:
          if len(t_data["coppie"]) < int(t_data["max_coppie"]):
            t_data["coppie"].append(nc_upper)
            aggiunte_titolari += 1
          else:
            t_data["coda"].append(nc_upper)
            aggiunte_coda += 1

      if aggiunte_titolari > 0 or aggiunte_coda > 0:
        salva_dati(db)
        st.success(f"Aggiunte: {aggiunte_titolari} tra i Titolari e {aggiunte_coda} in Coda (tutto in MAIUSCOLO).")
        st.rerun()
      else:
        st.warning("Nessuna nuova coppia valida o coppie già presenti nelle liste.")

  st.markdown("---")
  col_tit_vista, col_cod_vista = st.columns(2)
  
  with col_tit_vista:
    st.markdown(f"### 📋 Coppie Titolari ({len(t_data['coppie'])}/{t_data['max_coppie']})")
    if not t_data["coppie"]:
      st.info("Nessun titolare iscritto.")
    else:
      for idx, c in enumerate(t_data["coppie"], 1):
        col_ic1, col_ic2 = st.columns([0.80, 0.20])
        with col_ic1:
          st.markdown(f"<div style='padding: 6px 10px; background: rgba(0,240,255,0.05); border: 1px solid rgba(0,240,255,0.2); border-radius: 8px; margin-bottom: 5px; font-size: 14px;'><b>{idx}.</b> ⚽ {c}</div>", unsafe_allow_html=True)
        with col_ic2:
          if st.button("🗑️", key=f"del_isc_{torneo_selezionato}_{idx}", use_container_width=True):
            t_data["coppie"].remove(c)
            if t_data["coda"]:
              promossa = t_data["coda"].pop(0)
              t_data["coppie"].append(promossa)
            salva_dati(db)
            st.rerun()

  with col_cod_vista:
    st.markdown(f"### ⏳ Coppie in Lista d'Attesa / Coda ({len(t_data['coda'])})")
    if not t_data["coda"]:
      st.info("Nessuna coppia in coda.")
    else:
      for idx_c, c_coda in enumerate(t_data["coda"], 1):
        col_cc1, col_cc2 = st.columns([0.80, 0.20])
        with col_cc1:
          st.markdown(f"<div style='padding: 6px 10px; background: rgba(245,158,11,0.05); border: 1px solid rgba(245,158,11,0.2); border-radius: 8px; margin-bottom: 5px; font-size: 14px; color: #fbbf24;'><b>{idx_c}.</b> ⏳ {c_coda}</div>", unsafe_allow_html=True)
        with col_cc2:
          if st.button("🗑️", key=f"del_coda_{torneo_selezionato}_{idx_c}", use_container_width=True):
            t_data["coda"].remove(c_coda)
            salva_dati(db)
            st.rerun()

  if is_admin:
    st.markdown("---")
    st.markdown("### ⚙️ Pannello Admin: Configurazione e Avvio Torneo")
    col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    with col_cfg1:
      t_data["num_tavoli"] = st.number_input("N. Biliardini", min_value=1, max_value=10, value=int(t_data.get("num_tavoli", 6)), key=f"tav_{torneo_selezionato}")
    with col_cfg2:
      t_data["num_gironi"] = st.number_input("N. Gironi", min_value=1, max_value=8, value=int(t_data.get("num_gironi", 4)), key=f"gir_{torneo_selezionato}")
    with col_cfg3:
      t_data["max_coppie"] = st.number_input("Max Titolari", min_value=2, max_value=128, value=int(t_data.get("max_coppie", 32)), key=f"maxc_{torneo_selezionato}")

    if st.button("🚀 Avvia Torneo (Crea Gironi Casuali)", use_container_width=True):
      num_g = int(t_data["num_gironi"])
      coppie = [str(c).upper() for c in t_data["coppie"]]
      if len(coppie) < (num_g * 2):
        st.error(f"Hai {len(coppie)} coppie titolari. Con {num_g} gironi servono almeno {num_g * 2} coppie.")
      else:
        random.shuffle(coppie)
        nomi_gironi = [chr(65 + i) for i in range(num_g)]
        gironi_dict = {f"Girone {g}": [] for g in nomi_gironi}

        for idx, c in enumerate(coppie):
          g_scelto = f"Girone {nomi_gironi[idx % num_g]}"
          gironi_dict[g_scelto].append(c)

        t_data["gironi"] = gironi_dict
        t_data["punti_gironi"] = {
            g: {c: {"punti": 0, "gf": 0, "gs": 0, "dr": 0, "scontri_diretti_pt": 0} for c in lst}
            for g, lst in gironi_dict.items()
        }

        calendario_totale = {}
        for g_nome, lista_c in gironi_dict.items():
          squadre = lista_c.copy()
          if len(squadre) % 2 != 0:
            squadre.append("RIPOSO")
          n = len(squadre)
          turni_girone = []
          for t in range(n - 1):
            partite_turno = []
            for i in range(n // 2):
              s1 = squadre[i]
              s2 = squadre[n - 1 - i]
              if s1 != "RIPOSO" and s2 != "RIPOSO":
                match_id = f"{g_nome}_t{t+1}_m{i}"
                partite_turno.append({
                    "id": match_id,
                    "girone": g_nome,
                    "c1": s1,
                    "c2": s2,
                    "giocata": False,
                    "in_corso": False,
                    "tavolo": None,
                    "gol1": 0,
                    "gol2": 0,
                })
            turni_girone.append({"turno": t + 1, "partite": partite_turno})
            squadre = [squadre[0]] + [squadre[-1]] + squadre[1:-1]
          calendario_totale[g_nome] = turni_girone

        t_data["calendario_gironi"] = calendario_totale
        t_data["stato"] = "gironi"
        t_data["fasi_finali_configurate"] = False
        salva_dati(db)
        st.success("Torneo avviato con successo e gironi casuali creati!")
        st.rerun()

  st.stop()

# --- SELETTORE COPPIA PER CHI HA GIÀ AVVIATO IL TORNEO ---
tutte_le_coppie = []
for g_lst in t_data["gironi"].values():
  tutte_le_coppie.extend(g_lst)
if not tutte_le_coppie and t_data.get("coppie"):
  tutte_le_coppie = t_data["coppie"]

opzioni_selettore = ["-- Seleziona la tua coppia per accedere --"] + sorted([str(c).upper() for c in tutte_le_coppie])
coppia_url = st.query_params.get("coppia", "-- Seleziona la tua coppia per accedere --").upper()
if coppia_url not in opzioni_selettore:
  coppia_url = "-- Seleziona la tua coppia per accedere --"

coppia_selezionata = st.selectbox(
    "📱 Seleziona la tua coppia:",
    options=opzioni_selettore,
    index=opzioni_selettore.index(coppia_url),
    key="widget_selezione_coppia",
)

if coppia_selezionata != coppia_url:
  st.query_params["coppia"] = coppia_selezionata
  st.rerun()

if is_admin:
  st.success("🛡️ **Modalità Amministratore attiva:** Accesso completo sbloccato.")
elif coppia_selezionata == "-- Seleziona la tua coppia per accedere --":
  st.warning("⚠️ **Attenzione:** Seleziona la tua coppia dal menu a tendina per vedere le tue partite e inserire i risultati.")
  st.stop()
else:
  st.success(f"✅ Accesso effettuato come: **{coppia_selezionata}**")

if coppia_selezionata != "-- Seleziona la tua coppia per accedere --":
  with st.expander(f"👁️ Segui la tua coppia: {coppia_selezionata}", expanded=True):
    girone_mio, pos_mia, info_mie = None, None, None
    for g_nome, lista_c in t_data["gironi"].items():
      if coppia_selezionata in lista_c:
        girone_mio = g_nome
        ricalcola_classifiche_gironi(torneo_selezionato)
        if g_nome in t_data["punti_gironi"]:
          dati_g = t_data["punti_gironi"][g_nome]
          sorted_c = sorted(
              dati_g.items(),
              key=lambda x: (x[1]["punti"], x[1]["scontri_diretti_pt"], x[1]["dr"], x[1]["gf"]),
              reverse=True,
          )
          for idx, (c_nome, stats) in enumerate(sorted_c):
            if c_nome == coppia_selezionata:
              pos_mia = idx + 1
              info_mie = stats
        break

    st.markdown(
        f"""
        <div class="cyber-card" style="border-color: #00f0ff; text-align: left; padding: 20px;">
            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #00f0ff; font-weight: bold; margin-bottom: 2px;">LA TUA COPPIA</div>
            <div style="font-size: 22px; font-weight: 800; color: #ffffff; margin-bottom: 14px; text-shadow: 0 0 10px rgba(0,240,255,0.4);">🤝 {coppia_selezionata}</div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #1e3a8a; border-radius: 10px; padding: 10px; flex: 1; min-width: 100px; text-align: center;">
                    <div style="font-size: 10px; color: #94a3b8; font-weight: bold;">POSIZIONE</div>
                    <div style="font-size: 16px; font-weight: 700; color: #4ade80; margin-top: 2px;">{str(pos_mia) + '° POSTO' if pos_mia else 'N.D.'}</div>
                </div>
                <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #1e3a8a; border-radius: 10px; padding: 10px; flex: 1; min-width: 100px; text-align: center;">
                    <div style="font-size: 10px; color: #94a3b8; font-weight: bold;">GIRONE</div>
                    <div style="font-size: 16px; font-weight: 700; color: #00f0ff; margin-top: 2px;">{girone_mio if girone_mio else 'N.D.'}</div>
                </div>
                <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #1e3a8a; border-radius: 10px; padding: 10px; flex: 1; min-width: 100px; text-align: center;">
                    <div style="font-size: 10px; color: #94a3b8; font-weight: bold;">PUNTI / DR</div>
                    <div style="font-size: 16px; font-weight: 700; color: #fbbf24; margin-top: 2px;">{info_mie['punti'] if info_mie else 0} PT <span style="font-size: 11px; font-weight: normal; color: #94a3b8;">(DR: {info_mie['dr'] if info_mie else 0})</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 2. FASE A GIRONI LIVE
if t_data["stato"] == "gironi":
  ricalcola_classifiche_gironi(torneo_selezionato)
  num_tavoli = t_data.get("num_tavoli", 6)

  max_turni = max([len(turni) for turni in t_data["calendario_gironi"].values()]) if t_data["calendario_gironi"] else 0
  partite_per_girone_dict = {}
  for t_num in range(1, max_turni + 1):
    for g_nome, turni_girone in t_data["calendario_gironi"].items():
      for t_obj in turni_girone:
        if t_obj["turno"] == t_num:
          if g_nome not in partite_per_girone_dict:
            partite_per_girone_dict[g_nome] = []
          partite_per_girone_dict[g_nome].extend(t_obj["partite"])

  partite_miste_totali = []
  max_len_partite = max([len(v) for v in partite_per_girone_dict.values()]) if partite_per_girone_dict else 0
  for idx_misto in range(max_len_partite):
    for g_chiave in sorted(partite_per_girone_dict.keys()):
      lista_p = partite_per_girone_dict[g_chiave]
      if idx_misto < len(lista_p):
        partite_miste_totali.append(lista_p[idx_misto])

  partite_in_corso, partite_da_giocare = [], []
  for m in partite_miste_totali:
    if not m.get("giocata", False):
      if m.get("in_corso", False):
        partite_in_corso.append(m)
      else:
        partite_da_giocare.append(m)

  tavoli_occupati_ids = [p.get("tavolo") for p in partite_in_corso if p.get("tavolo") is not None]
  tavoli_liberi_disponibili = [t for t in range(1, num_tavoli + 1) if t not in tavoli_occupati_ids]

  if tavoli_liberi_disponibili and partite_da_giocare:
    cambiato = False
    for tavolo_libero in tavoli_liberi_disponibili:
      if partite_da_giocare:
        prossima_partita = partite_da_giocare.pop(0)
        prossima_partita["in_corso"] = True
        prossima_partita["tavolo"] = tavolo_libero
        partite_in_corso.append(prossima_partita)
        cambiato = True
    if cambiato:
      salva_dati(db)

  partite_in_corso = sorted(partite_in_corso, key=lambda x: x.get("tavolo") if x.get("tavolo") is not None else 999)

  st.subheader(f"⚡ Stato Biliardini e Incontri - {torneo_selezionato}")
  col_ic, col_coda = st.columns(2)

  with col_ic:
    st.markdown("#### 🔥 Partite in Corso ai Tavoli")
    if not partite_in_corso:
      st.info("Nessuna partita in corso.")
    else:
      for m in partite_in_corso:
        tavolo_str = f"<b>🏟️ Biliardino {m.get('tavolo')} - {m['girone']}</b>" if m.get("tavolo") else f"<b>🏟️ In campo - {m['girone']}</b>"
        match_id = m["id"]
        fa_al_caso_nostro = is_admin or coppia_selezionata == m["c1"] or coppia_selezionata == m["c2"]

        st.markdown(
            f"""
            <div class="match-live-card" style="margin-bottom: 12px;">
                <div style="font-size: 14px; color: #f59e0b; font-weight: bold; margin-bottom: 8px;">{tavolo_str}</div>
                <div style="font-size: 16px; font-weight: bold; color: #ffffff;">🤝 {m['c1']}</div>
                <div style="margin: 4px 0; font-size: 12px; font-weight: bold; color: #94a3b8;">VS</div>
                <div style="font-size: 16px; font-weight: bold; color: #ffffff;">🤝 {m['c2']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🔄 Posticipa di 2 partite", key=f"post_{torneo_selezionato}_{match_id}", use_container_width=True):
          if posticipa_partita_coda(torneo_selezionato, match_id):
            st.success("Partita posticipata!")
            st.rerun()

        if fa_al_caso_nostro:
          with st.expander(f"📝 Inserisci Risultato Tavolo {m.get('tavolo', '')}"):
            gol_p1 = st.selectbox(f"Gol {m['c1']}", options=[0, 1, 2, 3, 4, 5, 6, 7], index=int(m.get("gol1", 0)), key=f"g1_{torneo_selezionato}_{match_id}")
            gol_p2 = st.selectbox(f"Gol {m['c2']}", options=[0, 1, 2, 3, 4, 5, 6, 7], index=int(m.get("gol2", 0)), key=f"g2_{torneo_selezionato}_{match_id}")
            if st.button("✅ Conferma Risultato", key=f"save_{torneo_selezionato}_{match_id}", use_container_width=True):
              m["gol1"] = int(gol_p1) if gol_p1 is not None else 0
              m["gol2"] = int(gol_p2) if gol_p2 is not None else 0
              m["giocata"] = True
              m["in_corso"] = False
              m["tavolo"] = None
              ricalcola_classifiche_gironi(torneo_selezionato)
              salva_dati(db)
              st.success("Risultato registrato!")
              st.rerun()

  with col_coda:
    partite_in_coda_correnti = partite_da_giocare[:num_tavoli]
    st.markdown("#### ⏳ In Coda (Prossimi Incontri)")
    if not partite_in_coda_correnti:
      st.info("Coda vuota.")
    else:
      for idx, m in enumerate(partite_in_coda_correnti):
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #06241a 0%, #030f0a 100%); border: 1.5px solid #10b981; padding: 14px; border-radius: 10px; margin-bottom: 10px; color: #34d399; text-align: center;">
                <b style="font-size: 13px;">⏳ {idx+1}. {m['girone']}</b><br>
                <b style="color: #ffffff; font-size: 14px;">{m['c1']} vs {m['c2']}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

  st.markdown("---")
  st.subheader("📊 Classifiche dei Gironi")
  nomi_gironi_chiavi = list(t_data["gironi"].keys())
  for i in range(0, len(nomi_gironi_chiavi), 2):
    col_gironi = st.columns(2)
    for j in range(2):
      if i + j < len(nomi_gironi_chiavi):
        g_nome = nomi_gironi_chiavi[i + j]
        with col_gironi[j]:
          st.markdown(f"<h3 style='text-align: center; color: #00f0ff;'>📁 {g_nome}</h3>", unsafe_allow_html=True)
          renderizza_classifica_stile_card(torneo_selezionato, g_nome)

  if is_admin:
    st.markdown("---")
    if st.button("🏆 Genera Fasi Finali per questo Torneo", use_container_width=True):
      classificate_a, classificate_b_raw = {}, {}
      for g_nome in t_data["gironi"]:
        dati_girone = t_data["punti_gironi"][g_nome]
        sorted_c = sorted(dati_girone.items(), key=lambda x: (x[1]["punti"], x[1]["scontri_diretti_pt"], x[1]["dr"], x[1]["gf"]), reverse=True)
        squadre_girone = [str(c[0]).upper() for c in sorted_c]
        classificate_a[g_nome] = squadre_girone[:4]
        classificate_b_raw[g_nome] = squadre_girone

      abbinamenti_a = crea_abbinamenti_fascia_a_perfetti(classificate_a)
      abbinamenti_b = crea_abbinamenti_fascia_b(classificate_b_raw)

      turno_a_iniziale = [{"id": f"fa_t1_m{i}", "s1": str(s1[0]).upper(), "g1": s1[1], "p1": s1[2], "s2": str(s2[0]).upper(), "g2": s2[1], "p2": s2[2], "giocata": False, "vincente": None} for i, (s1, s2) in enumerate(abbinamenti_a)]
      turno_b_iniziale = [{"id": f"fb_t1_m{i}", "s1": str(s1[0]).upper(), "g1": s1[1], "p1": s1[2], "s2": str(s2[0]).upper(), "g2": s2[1], "p2": s2[2], "giocata": False, "vincente": None} for i, (s1, s2) in enumerate(abbinamenti_b)]

      t_data["tabellone_a"] = [{"turno": 1, "partite": turno_a_iniziale}]
      t_data["tabellone_b"] = [{"turno": 1, "partite": turno_b_iniziale}]
      t_data["terzo_quarto_a"] = []
      t_data["terzo_quarto_b"] = []
      t_data["stato"] = "fasi_finali"
      t_data["fasi_finali_configurate"] = True
      salva_dati(db)
      st.success("Fasi finali generate!")
      st.rerun()

# 3. FASI FINALI
elif t_data["stato"] == "fasi_finali":
  st.subheader(f"🏆 Fasi Finali - {torneo_selezionato}")
  tab_a_view, tab_b_view = st.tabs(["⭐ Fascia A", "🔻 Fascia B"])

  def gestisci_tabellone(chiave_tabellone, chiave_34, titolo_tab):
    st.markdown(f"### 📋 {titolo_tab}")
    turni_tab = t_data[chiave_tabellone]

    mappa_girone_pos = {}
    for g_nome, lista_sq in t_data["gironi"].items():
      dati_girone = t_data["punti_gironi"][g_nome]
      sorted_c = sorted(dati_girone.items(), key=lambda x: (x[1]["punti"], x[1]["scontri_diretti_pt"], x[1]["dr"], x[1]["gf"]), reverse=True)
      for idx, (sq, info) in enumerate(sorted_c):
        mappa_girone_pos[str(sq).upper()] = (g_nome, idx + 1)

    campione, secondo_posto, terzo_posto, quarto_posto = None, None, None, None
    tot_partite_turno_1 = len(turni_tab[0]["partite"])
    num_totale_squadre_tab = tot_partite_turno_1 * 2

    import math
    num_turni_totali = math.ceil(math.log2(num_totale_squadre_tab)) if num_totale_squadre_tab > 1 else 1

    while len(turni_tab) < num_turni_totali:
      prossimo_t_num = len(turni_tab) + 1
      num_match_prossimo = max(1, len(turni_tab[-1]["partite"]) // 2)
      partite_nuovo_turno = [{"id": f"{chiave_tabellone}_t{prossimo_t_num}_m{m_idx}", "s1": "In attesa...", "g1": "", "p1": "", "s2": "In attesa...", "g2": "", "p2": "", "giocata": False, "vincente": None} for m_idx in range(num_match_prossimo)]
      turni_tab.append({"turno": prossimo_t_num, "partite": partite_nuovo_turno})
    salva_dati(db)

    for t_idx, turno_obj in enumerate(turni_tab):
      t_num = turno_obj["turno"]
      partite_turno = turno_obj["partite"]
      nome_etichetta = ottieni_nome_turno_dinamico(len(partite_turno))

      st.markdown(f"""<div style="background: linear-gradient(90deg, #1e3a8a 0%, #00f0ff 100%); padding: 10px; border-radius: 8px; margin: 15px 0; text-align: center; color: white;"><b>{nome_etichetta}</b></div>""", unsafe_allow_html=True)

      if t_idx + 1 < len(turni_tab):
        turno_successivo = turni_tab[t_idx + 1]
        for m_i, match_corrente in enumerate(partite_turno):
          if match_corrente["giocata"] and match_corrente.get("vincente"):
            vincitore_corrente = str(match_corrente["vincente"]).upper()
            g_v, p_v = mappa_girone_pos.get(vincitore_corrente, ("", ""))
            target_match_idx = m_i // 2
            slot_squadra = "s1" if (m_i % 2 == 0) else "s2"
            slot_g = "g1" if (m_i % 2 == 0) else "g2"
            slot_p = "p1" if (m_i % 2 == 0) else "p1"

            if target_match_idx < len(turno_successivo["partite"]):
              dest_match = turno_successivo["partite"][target_match_idx]
              if dest_match[slot_squadra] in ["In attesa...", ""]:
                dest_match[slot_squadra] = vincitore_corrente
                dest_match[slot_g] = g_v
                dest_match[slot_p] = p_v
                salva_dati(db)

      perdenti_turno = []
      for idx, m in enumerate(partite_turno):
        match_id = m["id"]
        s1_nome, s2_nome = str(m["s1"]).upper(), str(m["s2"]).upper()
        if s1_nome in ["In attesa...", ""] or s2_nome in ["In attesa...", ""]:
          st.markdown(f"""<div class="cyber-card" style="text-align: center;"><b>{s1_nome} vs {s2_nome}</b><br><span style="color: #93c5fd;">In attesa di squadre</span></div>""", unsafe_allow_html=True)
          continue

        if m["giocata"]:
          perdente_match = s2_nome if str(m["vincente"]).upper() == s1_nome else s1_nome
          perdenti_turno.append(perdente_match)
          centro_testo = f"<b style='color: #10b981;'>Vince: {str(m['vincente']).upper()}</b>"
        else:
          centro_testo = "<b>VS</b>"

        st.markdown(f"""<div class="cyber-card" style="text-align: center;"><b>{s1_nome}</b> vs <b>{s2_nome}</b><br>{centro_testo}</div>""", unsafe_allow_html=True)

        if is_admin:
          with st.expander(f"⚙️ Imposta Vincitore ({s1_nome} vs {s2_nome})"):
            col_wv1, col_wv2 = st.columns(2)
            with col_wv1:
              if st.button(f"🏆 {s1_nome}", key=f"win1_{match_id}"):
                m["giocata"] = True
                m["vincente"] = s1_nome
                salva_dati(db)
                st.rerun()
            with col_wv2:
              if st.button(f"🏆 {s2_nome}", key=f"win2_{match_id}"):
                m["giocata"] = True
                m["vincente"] = s2_nome
                salva_dati(db)
                st.rerun()

      if nome_etichetta == "🏆 FINALE" and len(partite_turno) == 1 and partite_turno[0]["giocata"]:
        campione = str(partite_turno[0]["vincente"]).upper()
        secondo_posto = str(partite_turno[0]["s2"]).upper() if campione == str(partite_turno[0]["s1"]).upper() else str(partite_turno[0]["s1"]).upper()

      if nome_etichetta == "⚔️ SEMIFINALI" and len(perdenti_turno) == 2 and not t_data[chiave_34]:
        if is_admin:
          p1, p2 = perdenti_turno[0], perdenti_turno[1]
          g_p1, pos_p1 = mappa_girone_pos.get(p1, ("", ""))
          g_p2, pos_p2 = mappa_girone_pos.get(p2, ("", ""))
          t_data[chiave_34] = [{"id": f"{chiave_tabellone}_tq", "s1": p1, "g1": g_p1, "p1": pos_p1, "s2": p2, "g2": g_p2, "p2": pos_p2, "giocata": False, "vincente": None}]
          salva_dati(db)

    if t_data[chiave_34]:
      st.markdown("### 🥉 Finale 3° / 4° Posto")
      tq_match = t_data[chiave_34][0]
      if tq_match["giocata"]:
        terzo_posto = str(tq_match["vincente"]).upper()
        quarto_posto = str(tq_match["s2"]).upper() if terzo_posto == str(tq_match["s1"]).upper() else str(tq_match["s1"]).upper()
      st.markdown(f"<div class='cyber-card' style='text-align: center;'><b>{str(tq_match['s1']).upper()} vs {str(tq_match['s2']).upper()}</b><br>Vincitore 3° posto: {str(tq_match.get('vincente', 'Da assegnare')).upper()}</div>", unsafe_allow_html=True)
      if is_admin:
        col_tq1, col_tq2 = st.columns(2)
        with col_tq1:
          if st.button(f"🥉 Vince {str(tq_match['s1']).upper()}", key=f"tq1_{chiave_tabellone}"):
            tq_match["giocata"] = True
            tq_match["vincente"] = str(tq_match["s1"]).upper()
            salva_dati(db)
            st.rerun()
        with col_tq2:
          if st.button(f"🥉 Vince {str(tq_match['s2']).upper()}", key=f"tq2_{chiave_tabellone}"):
            tq_match["giocata"] = True
            tq_match["vincente"] = str(tq_match["s2"]).upper()
            salva_dati(db)
            st.rerun()

    if campione:
      st.markdown(
          f"""
          <div class="cyber-card-gold" style="padding: 20px; margin-top: 15px;">
              <h2>🏆 PODIO - {titolo_tab} 🏆</h2>
              <p style="font-size: 18px; color: #fbbf24;">🥇 1° POSTO: <b>{campione}</b></p>
              <p style="font-size: 16px;">🥈 2° POSTO: {secondo_posto}</p>
              <p style="font-size: 16px;">🥉 3° POSTO: {terzo_posto if terzo_posto else 'N.D.'}</p>
          </div>
          """,
          unsafe_allow_html=True,
      )

  with tab_a_view:
    gestisci_tabellone("tabellone_a", "terzo_quarto_a", "Fascia A")
  with tab_b_view:
    gestisci_tabellone("tabellone_b", "terzo_quarto_b", "Fascia B")
