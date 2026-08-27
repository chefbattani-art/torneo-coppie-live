from collections import defaultdict
import json
import os
import random
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Torneo Coppie Fisse Live - Cyber Gaming Edition",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- STILE GRAFICO GLOBALE ---
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Orbitron:wght@600;800;900&family=Inter:wght@400;600;800&display=swap');

        :root { color-scheme: dark !important; }

        .stApp {
            background-color: #05070f;
            background-image: 
                radial-gradient(circle at 50% 10%, rgba(0, 242, 254, 0.08) 0%, transparent 60%),
                radial-gradient(circle at 10% 90%, rgba(255, 0, 127, 0.06) 0%, transparent 50%);
            color: #f0f6fc;
            font-family: 'Inter', sans-serif;
            color-scheme: dark !important;
        }
        
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #070a17, #020408);
            border-right: 2px solid rgba(0, 242, 254, 0.2);
        }

        div[data-baseweb="select"] > div { background-color: #161f30 !important; color: white !important; border-color: #00f2fe !important; }
        div[data-baseweb="select"] span { color: white !important; }
        div[data-baseweb="popover"] div { background-color: #161f30 !important; color: white !important; }
        ul[data-baseweb="menu"] { background-color: #161f30 !important; }
        li[data-baseweb="option"] { background-color: #161f30 !important; color: white !important; }
        li[data-baseweb="option"]:hover { background-color: #1d3557 !important; color: #00f2fe !important; }

        .neon-title-box {
            border: 2px solid #00f2fe;
            box-shadow: 0 0 25px rgba(0, 242, 254, 0.4);
            border-radius: 18px;
            padding: 24px;
            text-align: center;
            background: linear-gradient(135deg, rgba(16, 22, 36, 0.95) 0%, rgba(8, 12, 20, 0.98) 100%);
            margin-bottom: 20px;
        }
        .neon-title-text {
            color: #00ff66 !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-size: 34px;
            font-weight: 900;
            text-shadow: 0 0 15px rgba(0,255,102,0.9);
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .neon-subtitle { color: #8b949e; font-size: 14px; margin-top: 6px; font-weight: 600; }
        .neon-box-main {
            background: linear-gradient(135deg, rgba(16, 22, 36, 0.95) 0%, rgba(8, 12, 20, 0.98) 100%);
            border: 2px solid #00f2fe;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
        }
        .match-live-card {
            background: linear-gradient(135deg, rgba(30, 20, 10, 0.95) 0%, rgba(12, 8, 4, 0.98) 100%);
            border: 2px solid #ffaa00;
            border-radius: 16px;
            padding: 22px;
            text-align: center;
        }
        .neon-gold { color: #ffaa00 !important; }
        .neon-blue { color: #00f2fe !important; }
        .neon-green { color: #00ff66 !important; }
        h1, h2, h3, h4 { font-family: 'Rajdhani', sans-serif !important; color: #ffffff !important; letter-spacing: 1.5px; text-transform: uppercase; }

        div.stButton > button {
            border-radius: 12px;
            font-weight: 800;
            font-family: 'Rajdhani', sans-serif;
            font-size: 18px;
            height: 50px !important;
            border: 1.5px solid rgba(0, 242, 254, 0.5);
            background: linear-gradient(180deg, #132238, #0a111c);
            color: #00f2fe;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

DB_FILE = "coppie_data.json"


def carica_dati():
  dati_default = {
      "stato": "setup",
      "coppie": [],
      "num_tavoli": 6,
      "num_gironi": 4,
      "admin_pin": "0000",
      "gironi": {},
      "calendario_gironi": {},
      "punti_gironi": {},
  }
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r") as f:
        dati_salvati = json.load(f)
        for k, v in dati_default.items():
          if k not in dati_salvati:
            dati_salvati[k] = v
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


def pulisci_nome(testo):
  testo = testo.replace("🤝", "").replace("⚽", "").replace("🏆", "")
  testo = re.sub(r"^\d+[\.\-\)]?\s*", "", testo)
  return testo.strip()


def ricalcola_classifiche_gironi():
  for g_nome, coppie_lista in db["gironi"].items():
    stats = {
        c: {
            "punti": 0,
            "partite_giocate": 0,
            "vinte": 0,
            "perse": 0,
            "gf": 0,
            "gs": 0,
            "dr": 0,
            "scontri_diretti_pt": {},
        }
        for c in coppie_lista
    }
    if g_nome in db["calendario_gironi"]:
      for turno_obj in db["calendario_gironi"][g_nome]:
        for m in turno_obj["partite"]:
          if m.get("giocata", False):
            c1, c2 = m["c1"], m["c2"]
            g1, g2 = m["gol1"], m["gol2"]
            diff = abs(g1 - g2)
            stats[c1]["partite_giocate"] += 1
            stats[c2]["partite_giocate"] += 1
            if g1 > g2:
              pt_s1, pt_s2 = (3, 0) if diff >= 2 else (2, 1)
              stats[c1]["vinte"] += 1
              stats[c2]["perse"] += 1
            elif g2 > g1:
              pt_s1, pt_s2 = (0, 3) if diff >= 2 else (1, 2)
              stats[c2]["vinte"] += 1
              stats[c1]["perse"] += 1
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
          for turno_obj in db["calendario_gironi"][g_nome]:
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
    db["punti_gironi"][g_nome] = stats


def selettore_gol_bottoni(prefix, default_val=0):
  if prefix not in st.session_state:
    st.session_state[prefix] = int(default_val)
  val_corrente = st.session_state[prefix]
  st.markdown(
      f"<div style='font-size: 13px; color: #8b949e; margin-bottom: 4px;'>Gol: <b class='neon-blue'>{val_corrente}</b></div>",
      unsafe_allow_html=True,
  )
  cols = st.columns(8)
  for g in range(8):
    with cols[g]:
      if st.button(
          str(g), key=f"btn_gol_{prefix}_{g}", use_container_width=True
      ):
        st.session_state[prefix] = g
        st.rerun()
  return st.session_state[prefix]


# --- BARRA LATERALE ---
st.sidebar.header("⚙️ Pannello Controllo")
if st.sidebar.button("🔄 Aggiorna Pagina", use_container_width=True):
  st.rerun()

st.sidebar.markdown("---")
modalita_admin = st.sidebar.checkbox("Modalità Amministratore (PIN)")
is_admin = False
if modalita_admin:
  pin_inserito = st.sidebar.text_input("Inserisci PIN Admin", type="password")
  if pin_inserito == db["admin_pin"]:
    is_admin = True
    st.sidebar.success("Accesso Admin Autorizzato ✅")
  else:
    st.sidebar.error("PIN errato.")

st.sidebar.markdown("---")
if is_admin:
  if st.sidebar.button(
      "⚙️ Mostra / Nascondi Setup Iniziale", use_container_width=True
  ):
    st.session_state["mostra_setup"] = not st.session_state.get(
        "mostra_setup", False
    )

st.sidebar.subheader("⚠️ Zona Pericolo")
if is_admin:
  conferma_reset = st.sidebar.checkbox(
      "Spunta per confermare il reset totale", key="checkbox_reset_gara"
  )
  if st.sidebar.button(
      "🔄 Ricomincia la gara da zero", use_container_width=True
  ):
    if conferma_reset:
      if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
      for key in list(st.session_state.keys()):
        del st.session_state[key]
      st.success("Torneo azzerato!")
      st.rerun()
    else:
      st.sidebar.warning("⚠️ Spunta la casella di conferma sopra.")
else:
  st.sidebar.info("🔐 Accedi come admin per resettare.")

# --- INTERFACCIA PRINCIPALE ---
st.markdown(
    """
    <div class="neon-title-box">
        <div class="neon-title-text">⚡ TORNEO COPPIE FISSE LIVE</div>
        <div class="neon-subtitle">Regolamento 3 Tocchi Uisp • Cyber Gaming & Esports Edition</div>
    </div>
    """,
    unsafe_allow_html=True,
)

tutte_le_coppie = []
for g_lst in db["gironi"].values():
  tutte_le_coppie.extend(g_lst)
if not tutte_le_coppie and db.get("coppie"):
  tutte_le_coppie = db["coppie"]

opzioni_selettore = ["-- Seleziona la tua coppia per accedere --"] + sorted(
    tutte_le_coppie
)
coppia_url = st.query_params.get(
    "coppia", "-- Seleziona la tua coppia per accedere --"
)
if coppia_url not in opzioni_selettore:
  coppia_url = "-- Seleziona la tua coppia per accedere --"

coppia_selezionata = st.selectbox(
    "📱 Seleziona la tua coppia (Fallo subito per entrare):",
    options=opzioni_selettore,
    index=opzioni_selettore.index(coppia_url),
    key="widget_selezione_coppia",
)

if coppia_selezionata != coppia_url:
  st.query_params["coppia"] = coppia_selezionata
  st.rerun()

if not is_admin and coppia_selezionata == "-- Seleziona la tua coppia per accedere --":
  st.markdown(
      """
      <div style="padding: 16px; background: rgba(40, 32, 10, 0.95); border: 2px solid #ffaa00; border-radius: 14px; color: #ffaa00; margin-top: 15px; font-weight: bold; text-align: center;">
          ⚠️ Per favore seleziona la tua coppia dal menu a tendina qui sopra per sbloccare la tua dashboard e inserire i risultati.
      </div>
      """,
      unsafe_allow_html=True,
  )
  st.stop()

if is_admin or coppia_selezionata != "-- Seleziona la tua coppia per accedere --":
  target_coppia = (
      tutte_le_coppie[0]
      if (is_admin and coppia_selezionata == "-- Seleziona la tua coppia per accedere --")
      else coppia_selezionata
  )

  with st.expander(f"👁️ Stato Squadra: {target_coppia}", expanded=True):
    girone_mio, pos_mia, info_mie = None, None, None
    for g_nome, lista_c in db["gironi"].items():
      if target_coppia in lista_c:
        girone_mio = g_nome
        ricalcola_classifiche_gironi()
        if g_nome in db["punti_gironi"]:
          dati_g = db["punti_gironi"][g_nome]
          sorted_c = sorted(
              dati_g.items(),
              key=lambda x: (
                  x[1]["punti"],
                  x[1]["scontri_diretti_pt"],
                  x[1]["dr"],
                  x[1]["gf"],
              ),
              reverse=True,
          )
          for idx, (c_nome, stats) in enumerate(sorted_c):
            if c_nome == target_coppia:
              pos_mia = idx + 1
              info_mie = stats
        break

    match_in_corso_coppia = None
    if db["stato"] == "gironi":
      max_turni = (
          max([len(turni) for turni in db["calendario_gironi"].values()])
          if db["calendario_gironi"]
          else 0
      )
      for t_num in range(1, max_turni + 1):
        for g_n, turni_girone in db["calendario_gironi"].items():
          for t_obj in turni_girone:
            if t_obj["turno"] == t_num:
              for m in t_obj["partite"]:
                if (
                    not m.get("giocata", False)
                    and (m["c1"] == target_coppia or m["c2"] == target_coppia)
                    and m.get("in_corso", False)
                ):
                  match_in_corso_coppia = m

    st.markdown(
        f"""
        <div class="neon-box-main">
            <div style="font-size: 16px; font-weight: 800; color: #ffffff; margin-bottom: 10px;">🤝 {target_coppia}</div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <div style="background: rgba(8, 12, 20, 0.85); border: 1px solid #00f2fe; border-radius: 10px; padding: 10px; flex: 1; text-align: center;">
                    <span style="font-size: 10px; color: #8b949e;">GIRONE</span><br><b class="neon-blue">{girone_mio or 'N.D.'}</b>
                </div>
                <div style="background: rgba(8, 12, 20, 0.85); border: 1px solid #00ff66; border-radius: 10px; padding: 10px; flex: 1; text-align: center;">
                    <span style="font-size: 10px; color: #8b949e;">POSIZIONE</span><br><b class="neon-green">{str(pos_mia) + '°' if pos_mia else 'N.D.'}</b>
                </div>
                <div style="background: rgba(8, 12, 20, 0.85); border: 1px solid #ffaa00; border-radius: 10px; padding: 10px; flex: 1; text-align: center;">
                    <span style="font-size: 10px; color: #8b949e;">PUNTI</span><br><b class="neon-gold">{info_mie['punti'] if info_mie else 0} pt</b>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if match_in_corso_coppia:
      avversario = (
          match_in_corso_coppia["c2"]
          if match_in_corso_coppia["c1"] == target_coppia
          else match_in_corso_coppia["c1"]
      )
      match_id = match_in_corso_coppia["id"]
      st.markdown(
          f"""
            <div style="background: rgba(30, 20, 10, 0.95); border: 2px solid #ffaa00; border-radius: 12px; padding: 14px; text-align: center; margin-bottom: 15px;">
                <b class="neon-gold">🔴 PARTITA ATTIVA AL TAVOLO {match_in_corso_coppia.get('tavolo')}!</b><br>Contro: <b>{avversario}</b>
            </div>
            """,
          unsafe_allow_html=True,
      )

      col_ins1, col_ins2 = st.columns(2)
      with col_ins1:
        st.markdown(f"**Gol {match_in_corso_coppia['c1']}**")
        gp1 = selettore_gol_bottoni(
            f"ur_g1_{match_id}", int(match_in_corso_coppia.get("gol1", 0))
        )
      with col_ins2:
        st.markdown(f"**Gol {match_in_corso_coppia['c2']}**")
        gp2 = selettore_gol_bottoni(
            f"ur_g2_{match_id}", int(match_in_corso_coppia.get("gol2", 0))
        )

      if st.button("✅ Salva Risultato", key=f"s_save_{match_id}", use_container_width=True):
        match_in_corso_coppia["gol1"] = int(gp1)
        match_in_corso_coppia["gol2"] = int(gp2)
        match_in_corso_coppia["giocata"] = True
        match_in_corso_coppia["in_corso"] = False
        match_in_corso_coppia["tavolo"] = None
        ricalcola_classifiche_gironi()
        salva_dati(db)
        st.success("Salvato!")
        st.rerun()

      if st.button("⏳ Rimanda Partita", key=f"rimanda_{match_id}", use_container_width=True):
        match_in_corso_coppia["in_corso"] = False
        match_in_corso_coppia["tavolo"] = None
        salva_dati(db)
        st.warning("Partita rimandata in coda!")
        st.rerun()

# SETUP INIZIALE
if db["stato"] == "setup" or st.session_state.get("mostra_setup", False):
  st.subheader("1. Configurazione Iniziale Torneo")
  if not is_admin:
    st.info("Accedi come admin con il PIN per modificare la configurazione.")
  else:
    whatsapp_text = st.text_area(
        "Incolla elenco coppie da WhatsApp:", height=120
    )
    col1, col2 = st.columns(2)
    with col1:
      db["num_tavoli"] = st.number_input("Biliardini", value=int(db["num_tavoli"]))
    with col2:
      db["num_gironi"] = st.number_input("Gironi", value=int(db["num_gironi"]))

    if st.button("🚀 Crea Gironi", use_container_width=True):
      coppie = [pulisci_nome(l) for l in whatsapp_text.split("\n") if pulisci_nome(l)]
      if len(coppie) >= db["num_gironi"] * 2:
        db["coppie"] = coppie
        random.shuffle(coppie)
        nomi_g = [chr(65 + i) for i in range(db["num_gironi"])]
        g_dict = {f"Girone {g}": [] for g in nomi_g}
        for i, c in enumerate(coppie):
          g_dict[f"Girone {nomi_g[i % db['num_gironi']}}"].append(c)
        db["gironi"] = g_dict
        db["punti_gironi"] = {
            g: {
                c: {
                    "punti": 0,
                    "partite_giocate": 0,
                    "vinte": 0,
                    "perse": 0,
                    "gf": 0,
                    "gs": 0,
                    "dr": 0,
                    "scontri_diretti_pt": 0,
                }
                for c in lst
            }
            for g, lst in g_dict.items()
        }

        cal_tot = {}
        for g_nome, lista_c in g_dict.items():
          squadre = lista_c.copy()
          if len(squadre) % 2 != 0:
            squadre.append("RIPOSO")
          n = len(squadre)
          t_list = []
          for t in range(n - 1):
            p_turno = []
            for i in range(n // 2):
              s1, s2 = squadre[i], squadre[n - 1 - i]
              if s1 != "RIPOSO" and s2 != "RIPOSO":
                p_turno.append({
                    "id": f"{g_nome}_t{t+1}_m{i}",
                    "girone": g_nome,
                    "c1": s1,
                    "c2": s2,
                    "giocata": False,
                    "in_corso": False,
                    "tavolo": None,
                    "gol1": 0,
                    "gol2": 0,
                })
            t_list.append({"turno": t + 1, "partite": p_turno})
            squadre = [squadre[0]] + [squadre[-1]] + squadre[1:-1]
          cal_tot[g_nome] = t_list

        db["calendario_gironi"] = cal_tot
        db["stato"] = "gironi"
        salva_dati(db)
        st.success("Creato!")
        st.session_state["mostra_setup"] = False
        st.rerun()

# FASE A GIRONI E GESTIONE TAVOLI
if db["stato"] == "gironi":
  ricalcola_classifiche_gironi()
  num_tavoli = db.get("num_tavoli", 6)

  max_turni = (
      max([len(t) for t in db["calendario_gironi"].values()])
      if db["calendario_gironi"]
      else 0
  )
  partite_per_girone = {}
  for t_num in range(1, max_turni + 1):
    for g_n, turni in db["calendario_gironi"].items():
      for t_obj in turni:
        if t_obj["turno"] == t_num:
          if g_n not in partite_per_girone:
            partite_per_girone[g_n] = []
          partite_per_girone[g_n].extend(t_obj["partite"])

  partite_miste = []
  max_len = max([len(v) for v in partite_per_girone.values()]) if partite_per_girone else 0
  for i in range(max_len):
    for g in sorted(partite_per_girone.keys()):
      if i < len(partite_per_girone[g]):
        partite_miste.append(partite_per_girone[g][i])

  partite_in_corso, partite_da_giocare = [], []
  for m in partite_miste:
    if not m.get("giocata", False):
      if m.get("in_corso", False):
        partite_in_corso.append(m)
      else:
        partite_da_giocare.append(m)

  tavoli_occupati = [p.get("tavolo") for p in partite_in_corso if p.get("tavolo")]
  tavoli_liberi = [t for t in range(1, num_tavoli + 1) if t not in tavoli_occupati]

  if tavoli_liberi and partite_da_giocare:
    cambiato = False
    for t_lib in tavoli_liberi:
      if partite_da_giocare:
        nx = partite_da_giocare.pop(0)
        nx["in_corso"] = True
        nx["tavolo"] = t_lib
        partite_in_corso.append(nx)
        cambiato = True
    if cambiato:
      salva_dati(db)

  st.subheader("⚡ Tavoli Live & Coda")
  col_ic, col_coda = st.columns(2)

  with col_ic:
    st.markdown("#### 🔥 Partite in Corso")
    if not partite_in_corso:
      st.info("Nessuna partita in corso.")
    else:
      for m in partite_in_corso:
        st.markdown(
            f"""
                <div class="match-live-card">
                    <b>🏟️ Tavolo {m.get('tavolo')} - {m['girone']}</b><br>
                    {m['c1']} vs {m['c2']}
                </div>
                """,
            unsafe_allow_html=True,
        )
        if is_admin or coppia_selezionata in [m["c1"], m["c2"]]:
          with st.expander(f"📝 Gestisci Tavolo {m.get('tavolo')}"):
            g1 = selettore_gol_bottoni(f"l_g1_{m['id']}", m.get("gol1", 0))
            g2 = selettore_gol_bottoni(f"l_g2_{m['id']}", m.get("gol2", 0))
            if st.button("✅ Salva Risultato", key=f"sv_{m['id']}", use_container_width=True):
              m["gol1"] = int(g1)
              m["gol2"] = int(g2)
              m["giocata"] = True
              m["in_corso"] = False
              m["tavolo"] = None
              ricalcola_classifiche_gironi()
              salva_dati(db)
              st.rerun()

            if st.button("⏳ Rimanda in Coda", key=f"rim_{m['id']}", use_container_width=True):
              m["in_corso"] = False
              m["tavolo"] = None
              salva_dati(db)
              st.rerun()

  with col_coda:
    st.markdown("#### ⏳ Prossimi in Coda")
    for i, m in enumerate(partite_da_giocare[:num_tavoli]):
      st.markdown(
          f"<div style='background: rgba(8,36,20,0.8); border: 1px solid #00ff66; padding: 10px; border-radius: 10px; margin-bottom: 8px;'><b>#{i+1} ({m['girone']})</b>: {m['c1']} vs {m['c2']}</div>",
          unsafe_allow_html=True,
      )

  st.markdown("---")
  st.subheader("📊 Classifiche Gironi")
  for g_nome, dati_g in db["punti_gironi"].items():
    st.markdown(f"### 📁 {g_nome}")
    sorted_c = sorted(
        dati_g.items(),
        key=lambda x: (
            x[1]["punti"],
            x[1]["scontri_diretti_pt"],
            x[1]["dr"],
            x[1]["gf"],
        ),
        reverse=True,
    )
    for idx, (c, info) in enumerate(sorted_c):
      st.markdown(
          f"<div style='background: rgba(16,22,36,0.9); border: 1px solid #00f2fe; padding: 8px 12px; border-radius: 8px; margin-bottom: 5px; display: flex; justify-content: space-between;'><b>{idx+1}° {c}</b> <span><b>{info['punti']} pt</b> (V:{info['vinte']} P:{info['perse']} DR:{info['dr']:+d})</span></div>",
          unsafe_allow_html=True,
      )
