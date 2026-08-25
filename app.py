import random, re
from collections import defaultdict
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Torneo Coppie Fisse LIVE",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

st_autorefresh(interval=5000, key="live_refresh")

# =========================
# STILE DARK / GAMING NEON
# =========================
st.markdown("""
<style>
.stApp {
    background:
      radial-gradient(circle at 50% 0%, #10243a 0%, #04080d 42%, #010204 100%);
    color:#f4f7fb;
}
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#02060b,#07111a);
    border-right:1px solid #163247;
}
.brand {
    text-align:center;
    padding:14px 0 22px;
    font-size:23px;
    line-height:1.05;
    text-shadow:0 0 15px #19ff72;
}
.brand span {color:#19ff72;}
.brand strong {color:#ff4cf0;font-size:31px;}
.header {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:8px 0 14px;
}
.live {
    color:#19ff72;
    text-shadow:0 0 12px #19ff72;
    font-weight:800;
}
.hero,.panel,.match {
    background:linear-gradient(145deg,#08141f,#02070c);
    border:1px solid #1b394d;
    border-radius:18px;
    box-shadow:0 0 28px #000;
}
.hero {padding:22px;margin-bottom:18px;border-color:#ffd21a55;}
.hero-title {font-size:29px;font-weight:900;}
.hero-sub {color:#aab5c0;}
.match {padding:10px;border-color:#ffd21a77;margin-bottom:18px;}
.match-head {
    text-align:center;
    background:linear-gradient(90deg,#2c1d00,#ffd21a66,#2c1d00);
    color:#ffd21a;
    border-radius:12px;
    padding:10px;
    font-size:21px;
    font-weight:900;
}
.teams {
    display:grid;
    grid-template-columns:1fr 90px 1fr;
    gap:12px;
    align-items:center;
    padding:16px;
}
.team {
    padding:18px;
    border-radius:15px;
    border:1px solid #19ff72;
    background:linear-gradient(145deg,#003b22,#02100c);
    box-shadow:0 0 20px #19ff7218;
    min-height:130px;
}
.team.blue {
    border-color:#149cff;
    background:linear-gradient(145deg,#062b48,#020c14);
    box-shadow:0 0 20px #149cff18;
}
.team-name {font-size:20px;font-weight:900;margin-top:7px;}
.vs {
    text-align:center;
    font-size:38px;
    font-weight:1000;
    text-shadow:0 0 16px #fff;
}
.queue,.calendar {
    background:#050b11;
    border:1px solid #173040;
    border-radius:12px;
    padding:12px 15px;
    margin:8px 0;
}
.queue span {color:#ffd21a;font-weight:900;margin-right:14px;}
.section-title {font-size:23px;font-weight:900;margin:24px 0 10px;}
.podium {
    text-align:center;
    padding:30px;
    margin-top:20px;
    border:1px solid #ffd21a;
    border-radius:18px;
    color:#ffd21a;
    background:#100d02;
    font-size:28px;
    box-shadow:0 0 30px #ffd21a18;
}
.your-team {
    border:1px solid #149cff77;
    background:#06111b;
    border-radius:14px;
    padding:12px;
    text-align:center;
}
.stButton>button {
    border-radius:12px;
    border:1px solid #149cff;
    background:linear-gradient(180deg,#0b4d93,#06376b);
    font-weight:900;
}
@media(max-width:800px){
    .teams{grid-template-columns:1fr;}
    .vs{font-size:28px;}
    .team{min-height:auto;}
}
</style>
""", unsafe_allow_html=True)

# =========================
# FUNZIONI
# =========================
def nuovo_stato():
    return {
        "fase":"setup",
        "numero_torneo":1,
        "numero_gironi":2,
        "numero_tavoli":2,
        "coppie":[],
        "partite":{},
        "fasce":{"A":[],"B":[]},
        "finali":{"A":[],"B":[]},
        "podio":None,
        "coppia_selezionata":None,
    }

def parse_coppie(text):
    out=[]
    for line in text.splitlines():
        x=re.sub(r"^[\s\d\-\.\)\(]+","",line.strip())
        x=re.sub(r"[⚽🏆🎮🔥⭐️]+","",x).strip()
        if not x: continue
        parts=re.split(r"\s*(?:/|\+|\s+-\s+|\s+e\s+)\s*",x,maxsplit=1,flags=re.I)
        nome=" & ".join(p.strip() for p in parts) if len(parts)==2 else x
        out.append(nome)
    return out

def round_robin(teams):
    teams=list(teams)
    if len(teams)%2: teams.append(None)
    arr=teams[:]
    rounds=[]
    for _ in range(len(arr)-1):
        giornata=[]
        for i in range(len(arr)//2):
            a,b=arr[i],arr[-1-i]
            if a and b: giornata.append((a,b))
        rounds.append(giornata)
        arr=[arr[0]]+[arr[-1]]+arr[1:-1]
    return rounds

def crea_torneo(coppie, gironi, tavoli):
    s=nuovo_stato()
    s.update({
        "fase":"gironi",
        "numero_gironi":gironi,
        "numero_tavoli":tavoli,
        "coppie":coppie,
    })
    random.shuffle(coppie)
    gruppi=defaultdict(list)
    for i,c in enumerate(coppie):
        gruppi[chr(65+i%gironi)].append(c)

    for g, teams in gruppi.items():
        matches=[]
        n=1
        for giornata in round_robin(teams):
            for a,b in giornata:
                matches.append({
                    "id":f"{g}-{n}",
                    "fase":"GIRONE",
                    "girone":g,
                    "casa":a,"ospite":b,
                    "giocata":False,"in_corso":False,
                    "tavolo":None,"gol_casa":None,"gol_ospite":None
                })
                n+=1
        s["partite"][g]=matches
    return s

def tutte_partite(s):
    for ms in s["partite"].values():
        for m in ms: yield m
    for fascia in ("A","B"):
        for m in s["finali"].get(fascia,[]):
            yield m

def assegna_tavoli(s):
    occupati={m["tavolo"] for m in tutte_partite(s)
               if m.get("in_corso") and m.get("tavolo")}
    liberi=[x for x in range(1,s["numero_tavoli"]+1) if x not in occupati]
    for m in tutte_partite(s):
        if not liberi: break
        if not m["giocata"] and not m["in_corso"] and m.get("casa") and m.get("ospite"):
            m["in_corso"]=True
            m["tavolo"]=liberi.pop(0)

def classifica_girone(matches):
    teams=sorted({m["casa"] for m in matches}|{m["ospite"] for m in matches})
    stats={t:{"Coppia":t,"Punti":0,"GF":0,"GS":0,"DR":0,"V":0,"N":0,"S":0}
           for t in teams}
    h2h=defaultdict(dict)

    for m in matches:
        if not m["giocata"]: continue
        a,b=m["casa"],m["ospite"]
        ga,gb=int(m["gol_casa"]),int(m["gol_ospite"])
        stats[a]["GF"]+=ga; stats[a]["GS"]+=gb
        stats[b]["GF"]+=gb; stats[b]["GS"]+=ga

        if ga==gb:
            stats[a]["Punti"]+=2; stats[b]["Punti"]+=2
            stats[a]["N"]+=1; stats[b]["N"]+=1
            h2h[a][b]=h2h[b][a]=0
        elif ga>gb:
            d=ga-gb
            stats[a]["Punti"]+=3 if d>=2 else 2
            stats[b]["Punti"]+=0 if d>=2 else 1
            stats[a]["V"]+=1; stats[b]["S"]+=1
            h2h[a][b]=1; h2h[b][a]=-1
        else:
            d=gb-ga
            stats[b]["Punti"]+=3 if d>=2 else 2
            stats[a]["Punti"]+=0 if d>=2 else 1
            stats[b]["V"]+=1; stats[a]["S"]+=1
            h2h[a][b]=-1; h2h[b][a]=1

    for x in stats.values():
        x["DR"]=x["GF"]-x["GS"]

    return sorted(
        stats.values(),
        key=lambda x:(x["Punti"],
                      sum(h2h[x["Coppia"]].values()),
                      x["DR"],x["GF"]),
        reverse=True
    )

def classifiche(s):
    return {g:classifica_girone(ms) for g,ms in s["partite"].items()}

def prepara_fasce(s):
    cls=classifiche(s)
    A=[];B=[]
    for rows in cls.values():
        A += [r["Coppia"] for r in rows[:4]]
        B += [r["Coppia"] for r in rows[4:]]
    s["fasce"]={"A":A,"B":B}
    s["fase"]="fasi_finali"

def crea_turno(s, fascia):
    teams=s["fasce"][fascia]
    if len(teams)<2:
        return
    nome="OTTAVI" if len(teams)>=16 else "QUARTI" if len(teams)>=8 else "SEMIFINALI"
    s["finali"][fascia]=[]
    for i,(a,b) in enumerate(zip(teams[::2],teams[1::2]),1):
        s["finali"][fascia].append({
            "id":f"{fascia}-{nome}-{i}",
            "fase":nome,
            "casa":a,"ospite":b,
            "giocata":False,"in_corso":False,
            "tavolo":None,"gol_casa":None,"gol_ospite":None
        })

def avanza(s, fascia):
    matches=s["finali"].get(fascia,[])
    if not matches or not all(m["giocata"] for m in matches):
        return
    winners=[]; losers=[]
    for m in matches:
        if m["gol_casa"]>m["gol_ospite"]:
            winners.append(m["casa"]); losers.append(m["ospite"])
        else:
            winners.append(m["ospite"]); losers.append(m["casa"])

    fase=matches[0]["fase"]
    if fase=="SEMIFINALI":
        s["podio"]={"vincitori_semifinale":winners,
                    "perdenti_semifinale":losers}

    next_name={"OTTAVI":"QUARTI","QUARTI":"SEMIFINALI","SEMIFINALI":"FINALE"}.get(fase)
    if next_name and len(winners)>=2:
        s["finali"][fascia]=[]
        for i,(a,b) in enumerate(zip(winners[::2],winners[1::2]),1):
            s["finali"][fascia].append({
                "id":f"{fascia}-{next_name}-{i}",
                "fase":next_name,
                "casa":a,"ospite":b,
                "giocata":False,"in_corso":False,
                "tavolo":None,"gol_casa":None,"gol_ospite":None
            })

def registra(s, match_id, a, b):
    for m in tutte_partite(s):
        if m["id"]==match_id:
            m["gol_casa"]=int(a); m["gol_ospite"]=int(b)
            m["giocata"]=True; m["in_corso"]=False; m["tavolo"]=None
            return

# =========================
# STATO SESSIONE
# =========================
if "state" not in st.session_state:
    st.session_state.state=nuovo_stato()
s=st.session_state.state

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown(
        "<div class='brand'>⚽<br><b>TORNEO</b><br>"
        "<span>COPPIE FISSE</span><br><strong>LIVE</strong></div>",
        unsafe_allow_html=True
    )
    page=st.radio(
        "MENU",
        ["⚡ Live","🏆 Gironi & Classifiche","🗓️ Calendario",
         "🥇 Fasi Finali","📊 Statistiche","🔐 Admin"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    if s.get("coppia_selezionata"):
        st.markdown(
            f"<div class='your-team'>👥 LA TUA COPPIA<br>"
            f"<b>{s['coppia_selezionata']}</b></div>",
            unsafe_allow_html=True
        )
    st.caption("🟢 Aggiornamento automatico · 5 secondi")

# =========================
# SETUP
# =========================
if s["fase"]=="setup":
    st.markdown(
        "<div class='hero'><div class='hero-title'>🏆 TORNEO COPPIE FISSE LIVE</div>"
        "<div class='hero-sub'>Setup iniziale · sorteggio · gironi · biliardini</div></div>",
        unsafe_allow_html=True
    )
    c1,c2=st.columns([1.2,0.8])
    with c1:
        testo=st.text_area(
            "📥 INCOLLA LE COPPIE",
            height=250,
            placeholder="Mario Rossi / Luigi Bianchi\nPaolo Verdi / Marco Neri\n..."
        )
    with c2:
        gironi=st.number_input("🏆 Numero gironi",1,16,2)
        tavoli=st.number_input("⚽ Biliardini disponibili",1,30,2)
        st.info("Puoi incollare direttamente un elenco copiato da WhatsApp.")
        if st.button("🚀 CREA TORNEO",use_container_width=True):
            coppie=parse_coppie(testo)
            if len(coppie)<2:
                st.error("Inserisci almeno 2 coppie.")
            elif gironi>len(coppie):
                st.error("Il numero di gironi è superiore alle coppie.")
            else:
                st.session_state.state=crea_torneo(coppie,int(gironi),int(tavoli))
                st.rerun()
    st.stop()

assegna_tavoli(s)

# =========================
# LIVE
# =========================
if page=="⚡ Live":
    st.markdown(
        "<div class='header'><h1>⚔️ TURNO LIVE</h1>"
        "<div class='live'>● AGGIORNAMENTO LIVE · 5s</div></div>",
        unsafe_allow_html=True
    )

    live=[m for m in tutte_partite(s) if m["in_corso"]]
    queue=[m for m in tutte_partite(s) if not m["giocata"] and not m["in_corso"]]

    st.markdown("### 🏆 PARTITE NEI BILIARDINI")
    if not live:
        st.info("Nessuna partita in corso.")
    for m in live:
        st.markdown(
            f"<div class='match'><div class='match-head'>🏆 BILIARDINO {m['tavolo']}</div>"
            f"<div class='teams'><div class='team'>⚽<br><div class='team-name'>{m['casa']}</div>"
            f"</div><div class='vs'>VS</div><div class='team blue'>⚽<br>"
            f"<div class='team-name'>{m['ospite']}</div></div></div></div>",
            unsafe_allow_html=True
        )
        a,b,go=st.columns([1,1,1])
        with a: ga=st.number_input("Gol A",0,20,0,key=f"ga-{m['id']}")
        with b: gb=st.number_input("Gol B",0,20,0,key=f"gb-{m['id']}")
        with go:
            st.write("")
            st.write("")
            if st.button("🏆 REGISTRA",key=f"reg-{m['id']}",use_container_width=True):
                registra(s,m["id"],ga,gb)
                st.rerun()

    st.markdown("### 🕒 IN CODA")
    if queue:
        for i,m in enumerate(queue[:10],1):
            st.markdown(
                f"<div class='queue'><span>CODA #{i}</span>"
                f"<b>{m['casa']}</b> ⚡ VS ⚡ <b>{m['ospite']}</b></div>",
                unsafe_allow_html=True
            )
    else:
        st.success("Coda vuota.")

    st.markdown("### 📊 CLASSIFICHE")
    for g,rows in classifiche(s).items():
        st.markdown(f"#### GIRONE {g}")
        st.dataframe(rows,use_container_width=True,hide_index=True)

# =========================
# GIRONI
# =========================
elif page=="🏆 Gironi & Classifiche":
    st.title("🏆 GIRONI & CLASSIFICHE")
    for g,rows in classifiche(s).items():
        st.markdown(f"<div class='section-title'>🏆 GIRONE {g}</div>",unsafe_allow_html=True)
        st.dataframe(rows,use_container_width=True,hide_index=True)

    if st.button("🥇 CHIUDI GIRONI → CREA FASCE A/B",use_container_width=True):
        prepara_fasce(s)
        crea_turno(s,"A")
        crea_turno(s,"B")
        st.rerun()

# =========================
# CALENDARIO
# =========================
elif page=="🗓️ Calendario":
    st.title("🗓️ CALENDARIO PARTITE")
    for g,ms in s["partite"].items():
        st.markdown(f"### GIRONE {g}")
        for m in ms:
            stato="🟢 LIVE" if m["in_corso"] else ("✅ GIOCATA" if m["giocata"] else "⏳ CODA")
            score=f"{m['gol_casa']} — {m['gol_ospite']}" if m["giocata"] else "—"
            st.markdown(
                f"<div class='calendar'><b>{m['id']}</b> · {m['casa']} "
                f"<strong>VS</strong> {m['ospite']} · <b>{score}</b> · {stato}</div>",
                unsafe_allow_html=True
            )

# =========================
# FINALI
# =========================
elif page=="🥇 Fasi Finali":
    st.title("🥇 FASI FINALI")
    for fascia in ("A","B"):
        st.markdown(f"<div class='section-title'>🏆 FASCIA {fascia}</div>",unsafe_allow_html=True)
        ms=s["finali"].get(fascia,[])
        if not ms:
            st.info("Tabellone non ancora disponibile.")
            continue

        for m in ms:
            st.markdown(
                f"<div class='match'><div class='match-head'>{m['fase']} · FASCIA {fascia}</div>"
                f"<div class='teams'><div class='team'>⚽<br><div class='team-name'>{m['casa']}</div></div>"
                f"<div class='vs'>VS</div><div class='team blue'>⚽<br>"
                f"<div class='team-name'>{m['ospite']}</div></div></div></div>",
                unsafe_allow_html=True
            )
            if not m["giocata"]:
                a,b,go=st.columns([1,1,1])
                with a: ga=st.number_input("Gol A",0,20,0,key=f"fga-{m['id']}")
                with b: gb=st.number_input("Gol B",0,20,0,key=f"fgb-{m['id']}")
                with go:
                    st.write("")
                    st.write("")
                    if st.button("🏆 REGISTRA",key=f"freg-{m['id']}",use_container_width=True):
                        registra(s,m["id"],ga,gb)
                        st.rerun()
            else:
                st.success(f"RISULTATO · {m['gol_casa']} — {m['gol_ospite']}")

        if all(m["giocata"] for m in ms):
            if st.button(f"➡️ AVANZA FASCIA {fascia}",key=f"av-{fascia}",use_container_width=True):
                avanza(s,fascia)
                st.rerun()

    if s.get("podio"):
        st.markdown(
            "<div class='podium'>🏆<br><b>PODIO FINALE</b><br>"
            "🥇 1° · 🥈 2° · 🥉 3° · 4°</div>",
            unsafe_allow_html=True
        )

# =========================
# STATISTICHE
# =========================
elif page=="📊 Statistiche":
    st.title("📊 STATISTICHE TORNEO")
    total=sum(len(x) for x in s["partite"].values())
    done=sum(m["giocata"] for m in tutte_partite())
    c1,c2,c3=st.columns(3)
    c1.metric("PARTITE",total)
    c2.metric("GIOCATE",done)
    c3.metric("COMPLETAMENTO",f"{done/total*100:.0f}%" if total else "0%")
    for g,rows in classifiche(s).items():
        st.markdown(f"#### Girone {g}")
        st.dataframe(rows,use_container_width=True,hide_index=True)

# =========================
# ADMIN
# =========================
elif page=="🔐 Admin":
    st.title("🔐 PANNELLO ADMIN")
    pin=st.text_input("PIN amministratore",type="password")
    if pin!="1234":
        st.warning("Inserisci il PIN amministratore.")
    else:
        st.success("Admin autorizzato.")
        st.caption("PIN iniziale: 1234 — cambialo nel codice prima di un uso pubblico.")
        for tavolo in range(1,s["numero_tavoli"]+1):
            if st.button(f"🔓 LIBERA BILIARDINO {tavolo}",key=f"free-{tavolo}"):
                for m in tutte_partite(s):
                    if m.get("tavolo")==tavolo:
                        m["in_corso"]=False
                        m["tavolo"]=None
                st.rerun()

        if st.button("⚠️ RESET TORNEO",use_container_width=True):
            st.session_state.state=nuovo_stato()
            st.rerun()
