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

# --- STILE GLOBALE V3 - ADMIN CENTRALE + MEGA LEGGIBILE ---
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=Inter:wght@600;800&display=swap');
        :root { --neon:#00F0FF; --gold:#FFD60A; --green:#00FF88; }
        .stApp { background: radial-gradient(1200px 600px at 50% -10%, #1a1450 0%, #0d0a2a 35%, #050510 100%); color:#fff; font-family:'Inter',sans-serif; }
        .block-container { padding-top:1.2rem !important; max-width:760px; }
        h1 { font-family:'Space Grotesk',sans-serif !important; font-size:32px !important; text-shadow:0 0 30px rgba(0,240,255,0.6); }
        .cyber-card { background: linear-gradient(180deg, rgba(22,26,70,0.96) 0%, rgba(10,12,35,0.98) 100%); border:1.5px solid rgba(0,240,255,0.35); border-radius:20px; padding:18px; margin-bottom:14px; box-shadow:0 8px 30px rgba(0,0,0,0.4); }
        .cyber-card-gold { background: radial-gradient(600px 300px at 50% 0%, rgba(255,214,10,0.25) 0%, rgba(20,18,40,0.95) 60%); border:2px solid var(--gold); border-radius:22px; padding:22px; box-shadow:0 0 40px rgba(255,214,10,0.35); text-align:center; }
        .match-live-card { background: linear-gradient(180deg, #2a1e06 0%, #140e02 100%); border:2px solid #FFB020; border-radius:20px; padding:20px; text-align:center; box-shadow:0 0 30px rgba(255,176,32,0.35); }
        div.stButton > button { border-radius:18px !important; font-weight:800 !important; border:2px solid var(--neon) !important; background: linear-gradient(180deg, #1E3AFF 0%, #101050 100%) !important; color:#fff !important; height:74px !important; font-size:19px !important; text-transform:uppercase; box-shadow:0 6px 20px rgba(0,240,255,0.25) !important; }
        .admin-central { background: linear-gradient(180deg, rgba(15,23,42,0.95) 0%, rgba(5,5,16,0.98) 100%); border:2.5px solid #00F0FF; border-radius:24px; padding:24px; text-align:center; box-shadow:0 0 40px rgba(0,240,255,0.3); margin:20px 0; }
        .admin-panel { background: linear-gradient(135deg, rgba(30,10,60,0.9) 0%, rgba(10,5,30,0.95) 100%); border:2px solid #7C3AED; border-radius:20px; padding:20px; margin:16px 0; }
        div[data-baseweb="select"] > div { background: #12133A !important; border:3px solid var(--neon) !important; border-radius:20px !important; min-height:76px !important; }
        div[data-baseweb="select"] span { color:#fff !important; font-size:20px !important; font-weight:800 !important; }
        .stTextInput input { background:#0F102A !important; border:2px solid #7C3AED !important; border-radius:16px !important; color:white !important; font-size:20px !important; min-height:60px !important; text-align:center; letter-spacing:4px; }
        .rank-card { display:flex; align-items:center; justify-content:space-between; background: linear-gradient(180deg, rgba(18,20,50,0.95), rgba(10,10,30,0.95)); border-radius:18px; padding:14px 16px; margin-bottom:12px; border-left:6px solid; }
        .pill { display:inline-flex; padding:6px 14px; border-radius:999px; font-size:12px; font-weight:800; letter-spacing:1px; }
        #MainMenu, footer, header { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

DB_FILE = "coppie_data_multi.json"

def carica_dati():
  dati_default = {"tornei": {}, "admin_pin": "0000"}
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r") as f:
        dati = json.load(f)
        if "tornei" not in dati: return dati_default
        return dati
    except: pass
  return dati_default

def salva_dati(data):
  with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

if "db" not in st.session_state: st.session_state.db = carica_dati()
if "show_admin_login" not in st.session_state: st.session_state.show_admin_login = False
if "admin_pin_input" not in st.session_state: st.session_state.admin_pin_input = ""

db = st.session_state.db

def ricalcola_classifiche_gironi(torneo_selezionato):
  t_data = db["tornei"][torneo_selezionato]
  for g_nome, coppie_lista in t_data["gironi"].items():
    stats = {c: {"punti": 0, "gf": 0, "gs": 0, "dr": 0, "scontri_diretti_pt": {}} for c in coppie_lista}
    if g_nome in t_data["calendario_gironi"]:
      for turno_obj in t_data["calendario_gironi"][g_nome]:
        for m in turno_obj["partite"]:
          if m.get("giocata", False):
            c1, c2 = m["c1"], m["c2"]; g1, g2 = m["gol1"], m["gol2"]; diff = abs(g1 - g2)
            if g1 > g2: pt_s1, pt_s2 = (3, 0) if diff >= 2 else (2, 1)
            elif g2 > g1: pt_s1, pt_s2 = (0, 3) if diff >= 2 else (1, 2)
            else: pt_s1, pt_s2 = 2, 2
            stats[c1]["punti"] += pt_s1; stats[c2]["punti"] += pt_s2
            stats[c1]["gf"] += g1; stats[c1]["gs"] += g2; stats[c2]["gf"] += g2; stats[c2]["gs"] += g1
      for c in coppie_lista: stats[c]["dr"] = stats[c]["gf"] - stats[c]["gs"]
      punti_gruppo = {}
      for c in coppie_lista:
        p = stats[c]["punti"]
        punti_gruppo.setdefault(p, []).append(c)
      for p, gruppo in punti_gruppo.items():
        if len(gruppo) > 1:
          mini_punti = {c: 0 for c in gruppo}
          for turno_obj in t_data["calendario_gironi"][g_nome]:
            for m in turno_obj["partite"]:
              if m.get("giocata", False):
                c1, c2 = m["c1"], m["c2"]
                if c1 in gruppo and c2 in gruppo:
                  g1, g2 = m["gol1"], m["gol2"]
                  if g1 > g2: mini_punti[c1] += 3
                  elif g2 > g1: mini_punti[c2] += 3
                  else: mini_punti[c1] += 1; mini_punti[c2] += 1
          for c in gruppo: stats[c]["scontri_diretti_pt"] = mini_punti[c]
        else:
          for c in gruppo: stats[c]["scontri_diretti_pt"] = 0
    t_data["punti_gironi"][g_nome] = stats

def calcola_partite_giocate_coppia(torneo_selezionato, g_nome, coppia):
  t_data = db["tornei"][torneo_selezionato]; giocate, totali = 0, 0
  if g_nome in t_data["calendario_gironi"]:
    for turno_obj in t_data["calendario_gironi"][g_nome]:
      for m in turno_obj["partite"]:
        if m["c1"] == coppia or m["c2"] == coppia:
          totali += 1
          if m.get("giocata", False): giocate += 1
  return giocate, totali

def renderizza_classifica_stile_card(torneo_selezionato, g_nome):
  t_data = db["tornei"][torneo_selezionato]
  dati_girone = t_data["punti_gironi"][g_nome]
  sorted_c = sorted(dati_girone.items(), key=lambda x: (x[1]["punti"], x[1]["scontri_diretti_pt"], x[1]["dr"], x[1]["gf"]), reverse=True)
  for idx, (coppia, info) in enumerate(sorted_c):
    gioc, tot = calcola_partite_giocate_coppia(torneo_selezionato, g_nome, coppia)
    is_a = idx < 4; border = "#00FF88" if is_a else "#FF3B3B"; badge = "QUALIFICATO" if is_a else "FASCIA B"
    st.markdown(f"""<div class="rank-card" style="border-left-color:{border};"><div style="display:flex;gap:12px;align-items:center;"><div style="background:rgba(255,255,255,0.08);border-radius:12px;padding:8px 0;min-width:54px;text-align:center;font-weight:800;color:{border};">{idx+1}°</div><div><div style="font-weight:800;">{coppia}</div><div style="font-size:11px;color:#9CA3AF;">{badge} • {gioc}/{tot}</div></div></div><div style="text-align:right;"><div style="font-size:22px;font-weight:900;color:#FFD60A;">{info['punti']}</div><div style="font-size:11px;color:#9CA3AF;">DR {info['dr']:+d}</div></div></div>""", unsafe_allow_html=True)

def genera_pdf_coppie(torneo_selezionato):
  t_data = db["tornei"][torneo_selezionato]; pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial","B",16); pdf.cell(0,10,f"Torneo: {torneo_selezionato}",0,1,"C")
  for g_nome, turni in t_data["calendario_gironi"].items():
    pdf.set_font("Arial","B",14); pdf.cell(0,10,f"--- {g_nome} ---",0,1,"L")
    for turno_obj in turni:
      pdf.set_font("Arial","B",11); pdf.cell(0,7,f"Turno {turno_obj['turno']}",0,1,"L"); pdf.set_font("Arial","",10)
      for m in turno_obj["partite"]:
        risultato = f"{m['gol1']} - {m['gol2']}" if m.get("giocata", False) else "Da giocare"
        pdf.cell(0,6,f"  {m['c1']} VS {m['c2']} -> {risultato}".encode("latin-1","ignore").decode("latin-1"),0,1,"L")
  return bytes(pdf.output())

def ottieni_nome_turno_dinamico(n):
  if n==1: return "🏆 FINALE"
  if n==2: return "⚔️ SEMIFINALI"
  if n==4: return "🔥 QUARTI DI FINALE"
  if n==8: return "⭐ OTTAVI DI FINALE"
  return f"Eliminazione Diretta ({n*2} Coppie)"

def crea_abbinamenti_fascia_a_perfetti(classificate):
  nomi_g=list(classificate.keys())
  if len(nomi_g)<4: return crea_abbinamenti_rigorosi_generico(classificate)
  g0,g1,g2,g3=nomi_g[0],nomi_g[1],nomi_g[2],nomi_g[3]; squadre={g:classificate[g] for g in nomi_g}
  def get_sq(g_nome,pos_idx):
    lst=squadre.get(g_nome,[])
    return (lst[pos_idx],g_nome,pos_idx+1) if pos_idx < len(lst) else ("RIPOSO",g_nome,pos_idx+1)
  return [(get_sq(g0,0),get_sq(g1,3)),(get_sq(g2,2),get_sq(g3,1)),(get_sq(g2,1),get_sq(g3,2)),(get_sq(g1,0),get_sq(g0,3)),(get_sq(g0,1),get_sq(g1,2)),(get_sq(g2,3),get_sq(g3,0)),(get_sq(g2,0),get_sq(g3,3)),(get_sq(g1,1),get_sq(g0,2))]

def crea_abbinamenti_rigorosi_generico(classificate):
  nomi=list(classificate.keys()); prime,seconde,terze,quarte=[],[],[],[]
  for g_n in nomi:
    lst=classificate[g_n]
    if len(lst)>0: prime.append((lst[0],g_n,1))
    if len(lst)>1: seconde.append((lst[1],g_n,2))
    if len(lst)>2: terze.append((lst[2],g_n,3))
    if len(lst)>3: quarte.append((lst[3],g_n,4))
  ab=[]
  for i in range(len(prime)): ab.append((prime[i], quarte[(i+1)%len(quarte)] if quarte else ("RIPOSO","",4)))
  for i in range(len(seconde)): ab.append((seconde[i], terze[(i+1)%len(terze)] if terze else ("RIPOSO","",3)))
  return ab

def crea_abbinamenti_fascia_b(classificate):
  tutte=[]; 
  for g_n,lista in classificate.items():
    for idx in range(4,len(lista)): tutte.append((lista[idx],g_n,idx+1))
  random.shuffle(tutte); ab=[]
  for i in range(0,len(tutte),2):
    if i+1<len(tutte): ab.append((tutte[i],tutte[i+1]))
    else: ab.append((tutte[i],("RIPOSO","",0)))
  return ab

def posticipa_partita_coda(torneo_selezionato, match_id):
  t_data=db["tornei"][torneo_selezionato]
  for g_nome, turni in t_data["calendario_gironi"].items():
    tutte=[]; 
    for t in turni: tutte.extend(t["partite"])
    idx=-1
    for i,m in enumerate(tutte):
      if m["id"]==match_id: idx=i; break
    if idx!=-1 and idx+2 < len(tutte):
      p=tutte.pop(idx); tutte.insert(idx+2,p)
      it=iter(tutte)
      for t_obj in turni: t_obj["partite"]=[next(it) for _ in range(len(t_obj["partite"]))]
      for t_obj in turni:
        for m in t_obj["partite"]:
          if m["id"]==match_id: m["in_corso"]=False; m["tavolo"]=None
      salva_dati(db); return True
  return False

# ========== LOGICA ADMIN CENTRALE NUOVA ==========
admin_param = st.query_params.get("admin", "false")
is_admin_autenticato = admin_param == "true"

# HEADER
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;">
<div><span class="pill" style="background:rgba(0,240,255,0.12);border:1px solid #00F0FF;color:#00F0FF;">LIVE CIRCUIT</span> <span class="pill" style="background:rgba(255,214,10,0.12);border:1px solid #FFD60A;color:#FFD60A;">RAVENNA • RIMINI</span>
<h1 style="margin:8px 0 0 0;">🏆 Torneo Coppie<br><span style="color:#00F0FF;">Fisse Live</span></h1></div>
<div style="width:54px;height:54px;border-radius:16px;background:radial-gradient(circle at 30% 30%,#00F0FF,#7C3AED);display:flex;align-items:center;justify-content:center;box-shadow:0 0 25px rgba(0,240,255,0.6);font-size:28px;">⚽</div>
</div>""", unsafe_allow_html=True)

# PANNELLO ACCESSO ADMIN AL CENTRO (se non autenticato)
if not is_admin_autenticato:
    st.markdown('<div class="admin-central">', unsafe_allow_html=True)
    st.markdown("### 🔐 Area Organizzatori")
    st.markdown('<p style="color:#94A3B8;font-size:14px;">Solo gli organizzatori possono creare tornei e gestire i risultati.<br>Giocatori: selezionate la vostra coppia più sotto.</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.2,0.6,0.2])
    with col2:
        if not st.session_state.show_admin_login:
            if st.button("🛡️ ACCEDI COME ADMIN", use_container_width=True, key="btn_show_admin"):
                st.session_state.show_admin_login = True
                st.rerun()
        else:
            st.markdown('<p style="font-weight:800;color:#00F0FF;letter-spacing:1px;">INSERISCI PIN ADMIN</p>', unsafe_allow_html=True)
            pin = st.text_input("PIN", type="password", placeholder="0000", label_visibility="collapsed", key="pin_input_center")
            c_a, c_b = st.columns(2)
            with c_a:
                if st.button("✅ CONFERMA", use_container_width=True, key="btn_confirm_pin"):
                    if pin == db["admin_pin"]:
                        st.query_params["admin"] = "true"
                        st.session_state.show_admin_login = False
                        st.rerun()
                    else:
                        st.error("PIN errato")
            with c_b:
                if st.button("❌ CHIUDI", use_container_width=True, key="btn_close_pin"):
                    st.session_state.show_admin_login = False
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # SE ADMIN AUTENTICATO - MOSTRA PANNELLO DI CONTROLLO VISIBILE AL CENTRO
    st.markdown('<div class="admin-panel">', unsafe_allow_html=True)
    st.markdown("### 🛡️ PANNELLO DI CONTROLLO ADMIN - ATTIVO")
    col_admin1, col_admin2 = st.columns([0.7,0.3])
    with col_admin1:
        st.markdown(f'<span class="pill" style="background:rgba(0,255,136,0.2);border:1px solid #00FF88;color:#00FF88;">● LIVE • PIN: {db["admin_pin"]}</span>', unsafe_allow_html=True)
    with col_admin2:
        if st.button("🔒 LOGOUT", use_container_width=True, key="logout_center"):
            st.query_params["admin"] = "false"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

is_admin = is_admin_autenticato

# SELEZIONE TORNEO
tornei_disponibili = [t for t in db["tornei"].keys() if t not in ["Torneo Principale (PRO)", "Torneo Secondario (Amatoriale)"]]
torneo_selezionato = st.selectbox("🎯 Seleziona Torneo:", options=tornei_disponibili if tornei_disponibili else ["Nessun Torneo Disponibile"], key="sel_torneo")

if not tornei_disponibili:
    if is_admin:
        st.markdown("#### ➕ Crea il primo torneo")
        with st.form("crea_primo"):
            nome = st.text_input("Nome Torneo")
            c1,c2,c3 = st.columns(3)
            with c1: nt = st.number_input("Biliardini",1,10,6)
            with c2: ng = st.number_input("Gironi",1,8,4)
            with c3: nm = st.number_input("Max Coppie",2,128,32)
            if st.form_submit_button("🚀 CREA TORNEO", use_container_width=True):
                if nome.strip():
                    db["tornei"][nome.strip().upper()] = {"stato":"iscrizioni_aperte","coppie":[],"coda":[],"max_coppie":int(nm),"num_tavoli":int(nt),"num_gironi":int(ng),"gironi":{},"calendario_gironi":{},"punti_gironi":{},"pagamenti":{},"fasi_finali_configurate":False,"tabellone_a":[],"tabellone_b":[],"terzo_quarto_a":[],"terzo_quarto_b":[]}
                    salva_dati(db); st.rerun()
    else:
        st.info("Nessun torneo attivo. Chiedi all'organizzatore di crearne uno.")
    st.stop()

t_data = db["tornei"][torneo_selezionato]
t_data.setdefault("coda", []); t_data.setdefault("max_coppie",32); t_data.setdefault("pagamenti",{}); salva_dati(db)

# SIDEBAR ADMIN (ora secondaria)
if is_admin:
    with st.sidebar:
        st.markdown("### ⚙️ Strumenti Admin")
        if st.button("🔙 Torna ai Gironi (se in finali)", use_container_width=True):
            if t_data["stato"]=="fasi_finali": t_data["stato"]="gironi"; salva_dati(db); st.rerun()
        st.markdown("---")
        st.markdown("#### 🗑️ Elimina Torneo")
        tor_del = st.selectbox("Torneo da rimuovere", options=list(db["tornei"].keys()), key="del_sel")
        conf = st.checkbox("Conferma eliminazione")
        if st.button("Elimina Torneo", use_container_width=True):
            if conf: del db["tornei"][tor_del]; salva_dati(db); st.rerun()
        st.markdown("---")
        st.markdown("#### ⚠️ Reset Torneo")
        conf2 = st.checkbox("Conferma reset", key="conf_reset")
        if st.button("🔄 Azzera Torneo", use_container_width=True):
            if conf2:
                db["tornei"][torneo_selezionato] = {"stato":"iscrizioni_aperte","coppie":[],"coda":[],"max_coppie":t_data.get("max_coppie",32),"num_tavoli":t_data.get("num_tavoli",6),"num_gironi":t_data.get("num_gironi",4),"gironi":{},"calendario_gironi":{},"punti_gironi":{},"pagamenti":{},"fasi_finali_configurate":False,"tabellone_a":[],"tabellone_b":[],"terzo_quarto_a":[],"terzo_quarto_b":[]}
                salva_dati(db); st.rerun()

# ========== FASE ISCRIZIONI ==========
if t_data["stato"] == "iscrizioni_aperte":
  if is_admin:
    st.markdown("### 💶 Gestione Pagamenti - Cerca Coppia")
    tutte = sorted(list(set(t_data.get("coppie",[])+t_data.get("coda",[]))))
    if tutte:
        scelta = st.selectbox("🔍 Cerca:", options=["-- Tutte --"]+tutte, key="search_pay")
        mostra = [scelta] if scelta!="-- Tutte --" else tutte
        for idx,coppia in enumerate(mostra):
            parti=[p.strip() for p in coppia.split("/")]
            g1=parti[0] if len(parti)>0 else "G1"; g2=parti[1] if len(parti)>1 else "G2"
            if coppia not in t_data["pagamenti"] or not isinstance(t_data["pagamenti"][coppia],dict):
                t_data["pagamenti"][coppia]={g1:False,g2:False}
            p1=t_data["pagamenti"][coppia].get(g1,False); p2=t_data["pagamenti"][coppia].get(g2,False)
            st.markdown(f'<div style="background:rgba(15,23,42,0.85);border:2px solid #00F0FF;border-radius:18px;padding:12px;margin-bottom:12px;text-align:center;"><b style="color:#00F0FF;letter-spacing:2px;">COPPIA #{idx+1}</b></div>', unsafe_allow_html=True)
            cL,cM,cR = st.columns([0.15,0.7,0.15])
            with cL:
                if st.button("💶", key=f"pl_{idx}", use_container_width=True): t_data["pagamenti"][coppia][g1]=not p1; salva_dati(db); st.rerun()
            with cM:
                colA = "#ef4444" if p1 else "#00FF88"; txtA="PAGATO ✅" if p1 else "DA PAGARE"
                colB = "#ef4444" if p2 else "#00FF88"; txtB="PAGATO ✅" if p2 else "DA PAGARE"
                st.markdown(f'<div style="background:rgba(0,0,0,0.3);border:2px solid {colA};border-radius:12px;padding:10px;text-align:center;margin-bottom:6px;"><b>{g1}</b><br><span style="color:{colA};font-weight:800;font-size:11px;">{txtA}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="background:rgba(0,0,0,0.3);border:2px solid {colB};border-radius:12px;padding:10px;text-align:center;"><b>{g2}</b><br><span style="color:{colB};font-weight:800;font-size:11px;">{txtB}</span></div>', unsafe_allow_html=True)
            with cR:
                if st.button("💶", key=f"pr_{idx}", use_container_width=True): t_data["pagamenti"][coppia][g2]=not p2; salva_dati(db); st.rerun()
    st.markdown("---")

  st.markdown(f"### 📝 Iscrizione - {torneo_selezionato}")
  st.info(f"Max titolari: {t_data['max_coppie']}")
  with st.form("form_iscr"):
    c1i=st.text_input("Giocatore 1"); c2i=st.text_input("Giocatore 2")
    wp=st.text_area("📋 Incolla lista WhatsApp")
    if st.form_submit_button("Registra 🚀", use_container_width=True):
        nuove=[]
        if c1i.strip() and c2i.strip(): nuove.append(f"{c1i.strip().upper()} / {c2i.strip().upper()}")
        if wp.strip():
            for linea in wp.split("\n"):
                linea=re.sub(r'^\s*(\d+[\.\)]\s*|-\s*)','',linea).strip()
                if not linea: continue
                for sep in ["/","-"," E "," CON "]:
                    if sep.lower() in linea.lower():
                        parti=re.split(sep,linea,flags=re.IGNORECASE)
                        if len(parti)>=2:
                            p1=parti[0].strip().upper(); p2=parti[1].strip().upper()
                            if p1 and p2: nuove.append(f"{p1} / {p2}"); break
        add_t=add_c=0
        for nc in nuove:
            if nc not in t_data["coppie"] and nc not in t_data["coda"]:
                if len(t_data["coppie"])<int(t_data["max_coppie"]): t_data["coppie"].append(nc); add_t+=1
                else: t_data["coda"].append(nc); add_c+=1
        salva_dati(db); st.success(f"Aggiunte {add_t} titolari, {add_c} in coda"); st.rerun()
  st.markdown("---")
  colA,colB=st.columns(2)
  with colA:
    st.markdown(f"**Titolari ({len(t_data['coppie'])}/{t_data['max_coppie']})**")
    for i,c in enumerate(t_data["coppie"],1):
        cc1,cc2=st.columns([0.8,0.2])
        with cc1: st.markdown(f"<div style='padding:8px;background:rgba(0,240,255,0.05);border:1px solid rgba(0,240,255,0.2);border-radius:8px;margin-bottom:5px;'><b>{i}.</b> {c}</div>", unsafe_allow_html=True)
        with cc2:
            if st.button("🗑️", key=f"del_{i}", use_container_width=True): t_data["coppie"].remove(c); 
            # promuovi
            if t_data["coda"]:
                t_data["coppie"].append(t_data["coda"].pop(0))
            salva_dati(db); st.rerun()
  with colB:
    st.markdown(f"**Coda ({len(t_data['coda'])})**")
    for i,c in enumerate(t_data["coda"],1):
        cc1,cc2=st.columns([0.8,0.2])
        with cc1: st.markdown(f"<div style='padding:8px;background:rgba(245,158,11,0.05);border-radius:8px;margin-bottom:5px;color:#fbbf24;'><b>{i}.</b> {c}</div>", unsafe_allow_html=True)
        with cc2:
            if st.button("🗑️", key=f"delc_{i}", use_container_width=True): t_data["coda"].remove(c); salva_dati(db); st.rerun()

  if is_admin:
    st.markdown("---")
    st.markdown("### ⚙️ Configura e Avvia")
    cc1,cc2,cc3=st.columns(3)
    with cc1: t_data["num_tavoli"]=st.number_input("Biliardini",1,10,int(t_data.get("num_tavoli",6)))
    with cc2: t_data["num_gironi"]=st.number_input("Gironi",1,8,int(t_data.get("num_gironi",4)))
    with cc3: t_data["max_coppie"]=st.number_input("Max",2,128,int(t_data.get("max_coppie",32)))
    if st.button("🚀 Avvia Torneo (Gironi Casuali)", use_container_width=True):
        num_g=int(t_data["num_gironi"]); coppie=[str(c).upper() for c in t_data["coppie"]]
        if len(coppie) < num_g*2: st.error("Poche coppie")
        else:
            random.shuffle(coppie); nomi=[chr(65+i) for i in range(num_g)]; gironi={f"Girone {g}":[] for g in nomi}
            for idx,c in enumerate(coppie): gironi[f"Girone {nomi[idx%num_g]}"].append(c)
            t_data["gironi"]=gironi; t_data["punti_gironi"]={g:{c:{"punti":0,"gf":0,"gs":0,"dr":0,"scontri_diretti_pt":0} for c in lst} for g,lst in gironi.items()}
            cal={}
            for g_nome,lista in gironi.items():
                sq=lista.copy()
                if len(sq)%2!=0: sq.append("RIPOSO")
                n=len(sq); turni=[]
                for t in range(n-1):
                    partite=[]
                    for i in range(n//2):
                        s1=sq[i]; s2=sq[n-1-i]
                        if s1!="RIPOSO" and s2!="RIPOSO": partite.append({"id":f"{g_nome}_t{t+1}_m{i}","girone":g_nome,"c1":s1,"c2":s2,"giocata":False,"in_corso":False,"tavolo":None,"gol1":0,"gol2":0})
                    turni.append({"turno":t+1,"partite":partite}); sq=[sq[0]]+[sq[-1]]+sq[1:-1]
                cal[g_nome]=turni
            t_data["calendario_gironi"]=cal; t_data["stato"]="gironi"; t_data["fasi_finali_configurate"]=False; salva_dati(db); st.rerun()
  st.stop()

# FASE GIRONI E FINALI (mantiene logica tua)
tutte_le_coppie=[]
for g_lst in t_data["gironi"].values(): tutte_le_coppie.extend(g_lst)
opzioni=["-- Seleziona la tua coppia --"]+sorted([str(c).upper() for c in tutte_le_coppie])
coppia_url=st.query_params.get("coppia","-- Seleziona la tua coppia --").upper()
if coppia_url not in opzioni: coppia_url="-- Seleziona la tua coppia --"
coppia_sel=st.selectbox("📱 La tua coppia:", options=opzioni, index=opzioni.index(coppia_url), key="sel_coppia")
if coppia_sel!=coppia_url: st.query_params["coppia"]=coppia_sel; st.rerun()
if not is_admin and coppia_sel=="-- Seleziona la tua coppia --": st.warning("Seleziona la tua coppia per vedere partite e risultati."); st.stop()

if t_data["stato"]=="gironi":
  ricalcola_classifiche_gironi(torneo_selezionato)
  num_tavoli=t_data.get("num_tavoli",6)
  max_turni=max([len(v) for v in t_data["calendario_gironi"].values()]) if t_data["calendario_gironi"] else 0
  per_gir={}
  for t_num in range(1,max_turni+1):
    for g_nome,turni in t_data["calendario_gironi"].items():
      for t_obj in turni:
        if t_obj["turno"]==t_num:
          per_gir.setdefault(g_nome,[]).extend(t_obj["partite"])
  tutte_miste=[]
  max_len=max([len(v) for v in per_gir.values()]) if per_gir else 0
  for i in range(max_len):
    for g in sorted(per_gir.keys()):
      if i < len(per_gir[g]): tutte_miste.append(per_gir[g][i])
  in_corso=[m for m in tutte_miste if m.get("in_corso") and not m.get("giocata")]
  da_gioc=[m for m in tutte_miste if not m.get("giocata") and not m.get("in_corso")]
  occupati=[p.get("tavolo") for p in in_corso if p.get("tavolo")]; liberi=[t for t in range(1,num_tavoli+1) if t not in occupati]
  if liberi and da_gioc:
    changed=False
    for tav in liberi:
      if da_gioc:
        nxt=da_gioc.pop(0); nxt["in_corso"]=True; nxt["tavolo"]=tav; in_corso.append(nxt); changed=True
    if changed: salva_dati(db)
  in_corso=sorted(in_corso,key=lambda x:x.get("tavolo") or 999)
  st.subheader(f"⚡ Biliardini - {torneo_selezionato}")
  col_ic,col_coda=st.columns(2)
  with col_ic:
    st.markdown("#### 🔥 In Corso")
    if not in_corso: st.info("Nessuna in corso")
    for m in in_corso:
      tavolo=f"🏟️ Biliardino {m.get('tavolo')} - {m['girone']}" if m.get('tavolo') else f"🏟️ {m['girone']}"
      st.markdown(f'<div class="match-live-card" style="margin-bottom:12px;"><div style="font-size:14px;color:#f59e0b;font-weight:bold;">{tavolo}</div><div style="font-size:16px;font-weight:bold;">{m["c1"]}</div><div>VS</div><div style="font-size:16px;font-weight:bold;">{m["c2"]}</div></div>', unsafe_allow_html=True)
      if st.button("🔄 Posticipa di 2", key=f"post_{m['id']}", use_container_width=True):
        if posticipa_partita_coda(torneo_selezionato,m['id']): st.success("Posticipata"); st.rerun()
      if is_admin or coppia_sel in [m["c1"],m["c2"]]:
        with st.expander(f"📝 Risultato Tav {m.get('tavolo','')}"):
          g1=st.selectbox(f"Gol {m['c1']}",[0,1,2,3,4,5,6,7],index=int(m.get("gol1",0)),key=f"g1_{m['id']}")
          g2=st.selectbox(f"Gol {m['c2']}",[0,1,2,3,4,5,6,7],index=int(m.get("gol2",0)),key=f"g2_{m['id']}")
          if st.button("✅ Conferma", key=f"save_{m['id']}", use_container_width=True):
            m["gol1"]=int(g1); m["gol2"]=int(g2); m["giocata"]=True; m["in_corso"]=False; m["tavolo"]=None; ricalcola_classifiche_gironi(torneo_selezionato); salva_dati(db); st.rerun()
  with col_coda:
    st.markdown("#### ⏳ Prossime")
    for idx,m in enumerate(da_gioc[:num_tavoli]):
      st.markdown(f'<div style="background:linear-gradient(135deg,#06241a 0%,#030f0a 100%);border:1.5px solid #10b981;padding:14px;border-radius:10px;margin-bottom:10px;text-align:center;color:#34d399;"><b>⏳ {idx+1}. {m["girone"]}</b><br><b style="color:#fff;">{m["c1"]} vs {m["c2"]}</b></div>', unsafe_allow_html=True)
  st.markdown("---")
  st.subheader("📊 Classifiche")
  nomi=list(t_data["gironi"].keys())
  for i in range(0,len(nomi),2):
    cols=st.columns(2)
    for j in range(2):
      if i+j < len(nomi):
        g=nomi[i+j]
        with cols[j]: st.markdown(f"<h3 style='text-align:center;color:#00F0FF;'>📁 {g}</h3>", unsafe_allow_html=True); renderizza_classifica_stile_card(torneo_selezionato,g)
  if is_admin and st.button("🏆 Genera Fasi Finali", use_container_width=True):
    class_a,class_b_raw={},{}; 
    for g_nome in t_data["gironi"]:
      dati=t_data["punti_gironi"][g_nome]; sorted_c=sorted(dati.items(),key=lambda x:(x[1]["punti"],x[1]["scontri_diretti_pt"],x[1]["dr"],x[1]["gf"]),reverse=True); sq=[str(c[0]).upper() for c in sorted_c]; class_a[g_nome]=sq[:4]; class_b_raw[g_nome]=sq
    ab_a=crea_abbinamenti_fascia_a_perfetti(class_a); ab_b=crea_abbinamenti_fascia_b(class_b_raw)
    turno_a=[{"id":f"fa_t1_m{i}","s1":str(s1[0]).upper(),"g1":s1[1],"p1":s1[2],"s2":str(s2[0]).upper(),"g2":s2[1],"p2":s2[2],"giocata":False,"vincente":None} for i,(s1,s2) in enumerate(ab_a)]
    turno_b=[{"id":f"fb_t1_m{i}","s1":str(s1[0]).upper(),"g1":s1[1],"p1":s1[2],"s2":str(s2[0]).upper(),"g2":s2[1],"p2":s2[2],"giocata":False,"vincente":None} for i,(s1,s2) in enumerate(ab_b)]
    t_data["tabellone_a"]=[{"turno":1,"partite":turno_a}]; t_data["tabellone_b"]=[{"turno":1,"partite":turno_b}]; t_data["terzo_quarto_a"]=[]; t_data["terzo_quarto_b"]=[]; t_data["stato"]="fasi_finali"; t_data["fasi_finali_configurate"]=True; salva_dati(db); st.rerun()

elif t_data["stato"]=="fasi_finali":
  st.subheader(f"🏆 Fasi Finali - {torneo_selezionato}")
  tabA,tabB=st.tabs(["⭐ Fascia A","🔻 Fascia B"])
  def gestisci(chiave,chiave34,titolo):
    st.markdown(f"### 📋 {titolo}"); turni=t_data[chiave]; mappa={}
    for g_nome,lista in t_data["gironi"].items():
      dati=t_data["punti_gironi"][g_nome]; sorted_c=sorted(dati.items(),key=lambda x:(x[1]["punti"],x[1]["scontri_diretti_pt"],x[1]["dr"],x[1]["gf"]),reverse=True)
      for idx,(sq,_) in enumerate(sorted_c): mappa[str(sq).upper()]=(g_nome,idx+1)
    import math; tot=len(turni[0]["partite"])*2 if turni else 0; need=math.ceil(math.log2(tot)) if tot>1 else 1
    while len(turni)<need:
      n=len(turni)+1; num=max(1,len(turni[-1]["partite"])//2); turni.append({"turno":n,"partite":[{"id":f"{chiave}_t{n}_m{i}","s1":"In attesa...","g1":"","p1":"","s2":"In attesa...","g2":"","p2":"","giocata":False,"vincente":None} for i in range(num)]})
    salva_dati(db); campione=None
    for t_idx,turno_obj in enumerate(turni):
      nome=ottieni_nome_turno_dinamico(len(turno_obj["partite"]))
      st.markdown(f'<div style="background:linear-gradient(90deg,#1e3a8a 0%,#00F0FF 100%);padding:10px;border-radius:8px;margin:15px 0;text-align:center;color:white;"><b>{nome}</b></div>', unsafe_allow_html=True)
      if t_idx+1 < len(turni):
        succ=turni[t_idx+1]
        for m_i,mc in enumerate(turno_obj["partite"]):
          if mc["giocata"] and mc.get("vincente"):
            vinc=str(mc["vincente"]).upper(); gv,pv=mappa.get(vinc,("","")); tgt=m_i//2; slot="s1" if m_i%2==0 else "s2"; slotg="g1" if m_i%2==0 else "g2"
            if tgt < len(succ["partite"]) and succ["partite"][tgt][slot] in ["In attesa...",""]: succ["partite"][tgt][slot]=vinc; succ["partite"][tgt][slotg]=gv; salva_dati(db)
      perd=[]
      for m in turno_obj["partite"]:
        s1=str(m["s1"]).upper(); s2=str(m["s2"]).upper()
        if s1 in ["In attesa...",""] or s2 in ["In attesa...",""]: st.markdown(f'<div class="cyber-card" style="text-align:center;"><b>{s1} vs {s2}</b><br><span style="color:#93c5fd;">In attesa</span></div>', unsafe_allow_html=True); continue
        if m["giocata"]: perd.append(s2 if str(m["vincente"]).upper()==s1 else s1); centro=f"<b style='color:#10b981;'>Vince: {str(m['vincente']).upper()}</b>"
        else: centro="<b>VS</b>"
        st.markdown(f'<div class="cyber-card" style="text-align:center;"><b>{s1}</b> vs <b>{s2}</b><br>{centro}</div>', unsafe_allow_html=True)
        if is_admin:
          with st.expander(f"⚙️ Vincitore {s1} vs {s2}"):
            c1,c2=st.columns(2)
            with c1:
              if st.button(f"🏆 {s1}", key=f"w1_{m['id']}"): m["giocata"]=True; m["vincente"]=s1; salva_dati(db); st.rerun()
            with c2:
              if st.button(f"🏆 {s2}", key=f"w2_{m['id']}"): m["giocata"]=True; m["vincente"]=s2; salva_dati(db); st.rerun()
      if nome=="🏆 FINALE" and len(turno_obj["partite"])==1 and turno_obj["partite"][0]["giocata"]: campione=str(turno_obj["partite"][0]["vincente"]).upper()
      if nome=="⚔️ SEMIFINALI" and len(perd)==2 and not t_data[chiave34] and is_admin:
        p1,p2=perd[0],perd[1]; gp1,pp1=mappa.get(p1,("","")); gp2,pp2=mappa.get(p2,("","")); t_data[chiave34]=[{"id":f"{chiave}_tq","s1":p1,"g1":gp1,"p1":pp1,"s2":p2,"g2":gp2,"p2":pp2,"giocata":False,"vincente":None}]; salva_dati(db)
    if t_data[chiave34]:
      st.markdown("### 🥉 Finale 3°/4°")
      tq=t_data[chiave34][0]; st.markdown(f"<div class='cyber-card' style='text-align:center;'><b>{str(tq['s1']).upper()} vs {str(tq['s2']).upper()}</b><br>Vincitore: {str(tq.get('vincente','Da assegnare')).upper()}</div>", unsafe_allow_html=True)
      if is_admin:
        c1,c2=st.columns(2)
        with c1:
          if st.button(f"🥉 {str(tq['s1']).upper()}", key=f"tq1_{chiave}"): tq["giocata"]=True; tq["vincente"]=str(tq['s1']).upper(); salva_dati(db); st.rerun()
        with c2:
          if st.button(f"🥉 {str(tq['s2']).upper()}", key=f"tq2_{chiave}"): tq["giocata"]=True; tq["vincente"]=str(tq['s2']).upper(); salva_dati(db); st.rerun()
    if campione: st.markdown(f'<div class="cyber-card-gold"><h2>🏆 PODIO - {titolo} 🏆</h2><p style="font-size:18px;color:#fbbf24;">🥇 {campione}</p></div>', unsafe_allow_html=True)
  with tabA: gestisci("tabellone_a","terzo_quarto_a","Fascia A")
  with tabB: gestisci("tabellone_b","terzo_quarto_b","Fascia B")
