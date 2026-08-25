import streamlit as st
import random
import re
from collections import defaultdict
from datetime import datetime

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5000, key="live_refresh")
except Exception:
    pass

st.set_page_config(
    page_title="Torneo Coppie Fisse LIVE",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# REGOLE FISSE DEL TORNEO
# ============================================================
ADMIN_PIN = "0000"
MAX_GOALS = 7
LIVE_REFRESH_MS = 5000
# Regola fissa: chi perde resta al tavolo.
LOSER_STAYS = True

# ============================================================
# GRAFICA
# ============================================================
st.markdown("""
<style>
.stApp {
    background:
      radial-gradient(circle at 50% -5%, #173a50 0%, #071119 32%, #020407 75%);
    color: #f5fbff;
}
.block-container { max-width: 1250px; padding-top: 18px; }
.neon-title {
    text-align:center;
    font-size:clamp(32px,7vw,62px);
    font-weight:1000;
    line-height:.92;
    margin:4px 0 18px;
    text-shadow:0 0 8px #fff,0 0 20px #19ff72,0 0 40px #ff3fd4;
}
.subtitle { text-align:center; color:#b9c8d3; font-size:18px; margin-bottom:20px; }
.panel,.card {
    background:linear-gradient(145deg,#091923,#02070c);
    border:1px solid #1b455e;
    border-radius:20px;
    padding:18px;
    margin-bottom:15px;
    box-shadow:0 0 28px #0008;
}
.personal {
    border-color:#19ff72;
    box-shadow:0 0 28px #19ff7220;
    background:linear-gradient(145deg,#06251a,#03100c);
}
.personal h2 { color:#19ff72; margin:0; font-size:30px; }
.live {
    border-color:#ffd21a;
    box-shadow:0 0 30px #ffd21a22;
    background:linear-gradient(145deg,#1c1602,#070602);
}
.table-title {
    text-align:center;
    color:#ffd21a;
    font-size:25px;
    font-weight:1000;
    padding:10px;
    border-radius:13px;
    background:linear-gradient(90deg,#241900,#695000,#241900);
}
.section-title {
    font-size:clamp(24px,5vw,36px);
    font-weight:1000;
    margin:25px 0 12px;
}
.team {
    border:1px solid #19ff72;
    border-radius:18px;
    padding:18px;
    text-align:center;
    background:linear-gradient(145deg,#003d24,#02130d);
    min-height:105px;
}
.team.blue {
    border-color:#19a7ff;
    background:linear-gradient(145deg,#062f4e,#020d16);
}
.team-name {
    font-size:clamp(19px,4vw,29px);
    font-weight:1000;
    line-height:1.05;
}
.vs { text-align:center; font-size:32px; font-weight:1000; padding-top:25px; }
.queue {
    border:1px solid #17394c;
    border-radius:14px;
    padding:13px;
    margin:7px 0;
    background:#040b11;
    font-size:17px;
}
.badge {
    display:inline-block;
    padding:6px 11px;
    border-radius:999px;
    border:1px solid #28516a;
    margin-right:5px;
    font-weight:900;
}
.gold { color:#ffd21a; border-color:#ffd21a; }
.green { color:#19ff72; border-color:#19ff72; }
.blue-text { color:#19a7ff; border-color:#19a7ff; }
.score {
    text-align:center;
    font-size:38px;
    font-weight:1000;
    padding:10px;
}
.small { color:#aabac6; }
.podium {
    text-align:center;
    border:1px solid #ffd21a;
    border-radius:24px;
    padding:28px;
    background:radial-gradient(circle,#211900,#070501);
    box-shadow:0 0 40px #ffd21a20;
}
.podium .winner { color:#ffd21a; font-size:40px; font-weight:1000; }
.stButton > button {
    min-height:46px;
    border-radius:13px;
    font-size:17px;
    font-weight:900;
    border:1px solid #187fbe;
    background:linear-gradient(180deg,#0b4f8e,#062d51);
}
@media(max-width:800px) {
    .block-container { padding-left:10px; padding-right:10px; }
    .vs { padding-top:0; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# STATO
# ============================================================
def new_state():
    return {
        "phase": "setup",
        "tavoli": 2,
        "gironi_n": 2,
        "coppie": [],
        "giocatori": {},
        "gironi": {},
        "matches": [],
        "finals": {"A": [], "B": []},
        "fasce": {"A": [], "B": []},
        "podio": {"A": None, "B": None},
        "created_at": None,
    }

if "torneo" not in st.session_state:
    st.session_state.torneo = new_state()
if "player" not in st.session_state:
    st.session_state.player = None
if "admin" not in st.session_state:
    st.session_state.admin = False
if "scores" not in st.session_state:
    st.session_state.scores = {}

S = st.session_state.torneo

# ============================================================
# UTILITÀ
# ============================================================
def clean_line(line):
    line = re.sub(r"^[\s\d\-\.\)\(•]+", "", line.strip())
    line = re.sub(r"[⚽🏆🎮🔥⭐️]", "", line).strip()
    return line

def parse_couples(text):
    result = []
    for line in text.splitlines():
        line = clean_line(line)
        if not line:
            continue
        # Formati supportati:
        # Mario / Luigi
        # Mario + Luigi
        # Mario - Luigi
        # Mario e Luigi
        parts = re.split(r"\s*(?:/|\+| - | e )\s*", line, maxsplit=1, flags=re.I)
        if len(parts) == 2 and all(parts):
            p1, p2 = parts[0].strip(), parts[1].strip()
        else:
            p1, p2 = line, ""
        result.append({
            "id": f"C{len(result)+1}",
            "p1": p1,
            "p2": p2,
        })
    return result

def couple_name(cid):
    c = next((x for x in S["coppie"] if x["id"] == cid), None)
    if not c:
        return "—"
    return f"{c['p1']} / {c['p2']}" if c["p2"] else c["p1"]

def players(c):
    return [p for p in (c["p1"], c["p2"]) if p]

def round_robin(ids):
    arr = list(ids)
    if len(arr) % 2:
        arr.append(None)
    rounds = []
    for _ in range(len(arr)-1):
        games = []
        for i in range(len(arr)//2):
            a, b = arr[i], arr[-1-i]
            if a is not None and b is not None:
                games.append((a, b))
        rounds.append(games)
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]
    return rounds

def all_matches():
    for m in S["matches"]:
        yield m
    for fs in ("A", "B"):
        for m in S["finals"][fs]:
            yield m

def match_by_id(mid):
    return next((m for m in all_matches() if m["id"] == mid), None)

def player_cid():
    return S["giocatori"].get(st.session_state.player)

def player_live_match():
    cid = player_cid()
    if not cid:
        return None
    return next(
        (m for m in all_matches()
         if m["status"] == "live" and cid in (m["a"], m["b"])),
        None
    )

def player_queue():
    cid = player_cid()
    if not cid:
        return []
    return [
        m for m in all_matches()
        if m["status"] == "queue" and cid in (m["a"], m["b"])
    ]

# ============================================================
# CALENDARIO / CODA
# ============================================================
def current_queue_matches():
    return [m for m in S["matches"] if m["status"] == "queue"]

def assign_initial_tables():
    """Assegna le prime partite ai tavoli liberi.
    Non crea partite artificiali: usa il calendario esistente."""
    occupied = {
        m["table"] for m in S["matches"]
        if m["status"] == "live" and m["table"] is not None
    }
    free = [t for t in range(1, S["tavoli"]+1) if t not in occupied]
    for m in S["matches"]:
        if not free:
            break
        if m["status"] == "queue":
            m["status"] = "live"
            m["table"] = free.pop(0)

def loser_stays_after_result(match):
    """Regola fissa:
    chi perde resta al tavolo;
    la prossima coppia in coda sfida chi è rimasto.
    """
    if match["phase"] != "gironi":
        return
    if match["ga"] is None or match["gb"] is None:
        return

    if match["ga"] == match["gb"]:
        # In caso di pareggio, nessuno viene dichiarato "campione del tavolo".
        # Per non bloccare il torneo, entrambe lasciano e il tavolo viene
        # riempito con le prossime due coppie.
        match["table"] = None
        assign_initial_tables()
        return

    loser = match["b"] if match["ga"] > match["gb"] else match["a"]

    # La partita successiva è la prima in coda che NON sia il perdente.
    # Il perdente rimane sul tavolo.
    next_match = next(
        (m for m in S["matches"]
         if m["status"] == "queue"
         and loser not in (m["a"], m["b"])),
        None
    )

    if next_match:
        next_match["status"] = "live"
        next_match["table"] = match["table"]
        # Il match concluso non occupa più il tavolo.
        match["table"] = None

        # Ricostruisce la partita LIVE usando il perdente + la coppia
        # che era in testa alla coda.
        newcomer = next_match["a"]
        if newcomer == loser:
            newcomer = next_match["b"]

        # Rimuove il match teorico dalla coda e lo trasforma nel match reale.
        next_match["a"] = loser
        next_match["b"] = newcomer
    else:
        match["table"] = None
        assign_initial_tables()

def finish_match(match, ga, gb):
    match["ga"] = int(ga)
    match["gb"] = int(gb)
    match["status"] = "done"
    match["winner"] = (
        match["a"] if ga > gb else
        match["b"] if gb > ga else
        None
    )
    old_table = match.get("table")
    match["table"] = None

    if match["phase"] == "gironi":
        # Nel girone il tavolo passa secondo la regola fissa.
        if old_table is not None:
            match["_last_table"] = old_table
        loser_stays_after_result(match)

# ============================================================
# CLASSIFICHE
# ============================================================
def standings(group):
    ids = S["gironi"].get(group, [])
    rows = {
        cid: {
            "id": cid,
            "Coppia": couple_name(cid),
            "PT": 0,
            "GF": 0,
            "GS": 0,
            "DR": 0,
            "V": 0,
            "N": 0,
            "S": 0,
        }
        for cid in ids
    }
    direct = defaultdict(dict)

    for m in S["matches"]:
        if m["phase"] != "gironi" or m["group"] != group or m["status"] != "done":
            continue
        a, b, ga, gb = m["a"], m["b"], m["ga"], m["gb"]
        rows[a]["GF"] += ga
        rows[a]["GS"] += gb
        rows[b]["GF"] += gb
        rows[b]["GS"] += ga

        if ga == gb:
            rows[a]["PT"] += 2
            rows[b]["PT"] += 2
            rows[a]["N"] += 1
            rows[b]["N"] += 1
            direct[a][b] = direct[b][a] = 0
        elif ga > gb:
            diff = ga - gb
            rows[a]["PT"] += 3 if diff >= 2 else 2
            rows[b]["PT"] += 0 if diff >= 2 else 1
            rows[a]["V"] += 1
            rows[b]["S"] += 1
            direct[a][b] = 1
            direct[b][a] = -1
        else:
            diff = gb - ga
            rows[b]["PT"] += 3 if diff >= 2 else 2
            rows[a]["PT"] += 0 if diff >= 2 else 1
            rows[b]["V"] += 1
            rows[a]["S"] += 1
            direct[a][b] = -1
            direct[b][a] = 1

    for r in rows.values():
        r["DR"] = r["GF"] - r["GS"]
        r["_H2H"] = sum(direct[r["id"]].values())

    return sorted(
        rows.values(),
        key=lambda r: (r["PT"], r["_H2H"], r["DR"], r["GF"]),
        reverse=True
    )

# ============================================================
# FASI FINALI
# ============================================================
def generate_final_bracket(fs):
    ids = list(S["fasce"][fs])
    if len(ids) < 2:
        S["finals"][fs] = []
        return

    pairs = []
    while len(ids) >= 2:
        pairs.append((ids.pop(0), ids.pop(-1)))

    total = len(pairs) * 2
    if total >= 16:
        phase = "OTTAVI"
    elif total >= 8:
        phase = "QUARTI"
    elif total >= 4:
        phase = "SEMIFINALI"
    else:
        phase = "FINALE"

    S["finals"][fs] = []
    for i, (a, b) in enumerate(pairs, 1):
        S["finals"][fs].append({
            "id": f"{fs}-{phase}-{i}",
            "phase": phase,
            "group": None,
            "a": a,
            "b": b,
            "ga": None,
            "gb": None,
            "winner": None,
            "status": "queue",
            "table": None,
        })

def generate_finals():
    a, b = [], []
    for g in sorted(S["gironi"]):
        rows = standings(g)
        a.extend([r["id"] for r in rows[:4]])
        b.extend([r["id"] for r in rows[4:]])

    S["fasce"]["A"] = a
    S["fasce"]["B"] = b
    S["phase"] = "finali"
    generate_final_bracket("A")
    generate_final_bracket("B")

def advance_final(fs):
    matches = S["finals"][fs]
    if not matches or not all(m["status"] == "done" for m in matches):
        return

    winners = [m["winner"] for m in matches]
    losers = [
        m["b"] if m["winner"] == m["a"] else m["a"]
        for m in matches
    ]

    phase = matches[0]["phase"]

    if phase == "SEMIFINALI":
        S["podio"][fs] = {"finalists": winners, "third_fourth": losers}
        S["finals"][fs] = [
            {
                "id": f"{fs}-FINALE-1",
                "phase": "FINALE 1°/2°",
                "group": None,
                "a": winners[0],
                "b": winners[1],
                "ga": None, "gb": None, "winner": None,
                "status": "queue", "table": None,
            },
            {
                "id": f"{fs}-3P-1",
                "phase": "FINALE 3°/4°",
                "group": None,
                "a": losers[0],
                "b": losers[1],
                "ga": None, "gb": None, "winner": None,
                "status": "queue", "table": None,
            },
        ]
        return

    if phase in ("OTTAVI", "QUARTI"):
        next_phase = "QUARTI" if phase == "OTTAVI" else "SEMIFINALI"
        new = []
        for i in range(0, len(winners), 2):
            if i+1 >= len(winners):
                break
            new.append({
                "id": f"{fs}-{next_phase}-{i//2+1}",
                "phase": next_phase,
                "group": None,
                "a": winners[i],
                "b": winners[i+1],
                "ga": None, "gb": None, "winner": None,
                "status": "queue", "table": None,
            })
        S["finals"][fs] = new

# ============================================================
# CREAZIONE TORNEO
# ============================================================
def create_tournament(text, tavoli, gironi_n):
    couples = parse_couples(text)
    if len(couples) < 2:
        return None, "Inserisci almeno 2 coppie."

    random.shuffle(couples)

    groups = defaultdict(list)
    for i, c in enumerate(couples):
        groups[chr(65 + (i % gironi_n))].append(c["id"])

    matches = []
    serial = 1
    for group, ids in sorted(groups.items()):
        for rnd in round_robin(ids):
            for a, b in rnd:
                matches.append({
                    "id": f"G-{group}-{serial}",
                    "phase": "gironi",
                    "group": group,
                    "round": serial,
                    "a": a,
                    "b": b,
                    "ga": None,
                    "gb": None,
                    "winner": None,
                    "status": "queue",
                    "table": None,
                })
                serial += 1

    players_map = {}
    for c in couples:
        for p in players(c):
            if p in players_map:
                return None, f"Nome duplicato: {p}. Ogni giocatore deve avere un nome univoco."
            players_map[p] = c["id"]

    return {
        "phase": "gironi",
        "tavoli": int(tavoli),
        "gironi_n": int(gironi_n),
        "coppie": couples,
        "giocatori": players_map,
        "gironi": dict(groups),
        "matches": matches,
        "finals": {"A": [], "B": []},
        "fasce": {"A": [], "B": []},
        "podio": {"A": None, "B": None},
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }, None

# ============================================================
# LOGIN
# ============================================================
if not st.session_state.player and not st.session_state.admin:
    st.markdown(
        "<div class='neon-title'>⚽<br>TORNEO COPPIE FISSE<br>"
        "<span style='color:#19ff72'>LIVE</span></div>",
        unsafe_allow_html=True,
    )

    if S["phase"] == "setup":
        st.markdown(
            "<div class='subtitle'>Il torneo non è ancora stato avviato.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='subtitle'>Seleziona il tuo nome per entrare nel torneo</div>",
            unsafe_allow_html=True,
        )
        names = sorted(S["giocatori"].keys())
        selected = st.selectbox(
            "👤 IL TUO NOME",
            ["— Seleziona il tuo nome —"] + names,
        )
        if st.button("🚀 ENTRA NEL TORNEO", use_container_width=True):
            if selected == "— Seleziona il tuo nome —":
                st.error("Devi selezionare il tuo nome.")
            else:
                st.session_state.player = selected
                st.rerun()

    st.divider()
    with st.expander("👑 Accesso amministratore"):
        pin = st.text_input("PIN Admin", type="password")
        if st.button("🔐 ENTRA COME ADMIN", use_container_width=True):
            if pin == ADMIN_PIN:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("PIN non corretto.")
    st.stop()

# ============================================================
# ASSEGNAZIONE INIZIALE
# ============================================================
if S["phase"] == "gironi":
    assign_initial_tables()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        "<div class='neon-title' style='font-size:30px'>⚽<br>TORNEO<br>"
        "<span style='color:#19ff72'>LIVE</span></div>",
        unsafe_allow_html=True,
    )

    if st.session_state.admin:
        st.success("👑 ADMIN")
        page = st.radio(
            "MENU",
            ["👑 Admin", "⚡ Live", "🏆 Classifica", "🗓️ Calendario", "🥇 Fasi Finali"],
        )
    else:
        cid = player_cid()
        st.markdown(
            f"<div class='personal'><h2>👤 {st.session_state.player}</h2>"
            f"<div class='small'>{couple_name(cid)}</div></div>",
            unsafe_allow_html=True,
        )
        page = st.radio(
            "MENU",
            ["👤 La mia area", "⚡ Live", "🏆 Classifica", "🗓️ Le mie partite", "🥇 Fasi Finali"],
        )

    if st.button("🚪 Esci"):
        st.session_state.player = None
        st.session_state.admin = False
        st.rerun()

# ============================================================
# AREA PERSONALE
# ============================================================
if page == "👤 La mia area":
    cid = player_cid()
    st.markdown("<div class='neon-title'>🏆 TORNEO COPPIE FISSE LIVE</div>", unsafe_allow_html=True)

    st.markdown(
        f"<div class='panel personal'><h2>👤 {st.session_state.player}</h2>"
        f"<div class='team-name'>{couple_name(cid)}</div>"
        f"<div class='small'>La tua area personale</div></div>",
        unsafe_allow_html=True,
    )

    live = player_live_match()

    if live:
        opponent = live["b"] if live["a"] == cid else live["a"]
        st.markdown(
            f"<div class='panel live'><div class='table-title'>🟢 PARTITA IN CORSO · "
            f"🎱 BILIARDINO {live['table']}</div>"
            f"<div class='score'>{couple_name(cid)}<br>"
            f"<span style='color:#ffd21a'>VS</span><br>{couple_name(opponent)}</div>"
            f"<div style='text-align:center;color:#ffd21a;font-weight:900'>"
            f"Regola LIVE: chi perde resta al tavolo</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown("### 📝 INSERISCI IL RISULTATO")
        st.caption("Tocca un numero da 0 a 7. Nessuna tastiera.")

        score_key = live["id"]
        current = st.session_state.scores.setdefault(score_key, {"self": None, "opp": None})

        left, right = st.columns(2)

        def score_selector(col, label, slot):
            with col:
                st.markdown(f"**{label}**")
                cols = st.columns(8)
                for n, c in enumerate(cols):
                    selected = current[slot] == n
                    text = f"● {n}" if selected else f"○ {n}"
                    if c.button(text, key=f"{score_key}-{slot}-{n}"):
                        current[slot] = n
                        st.rerun()

        score_selector(left, couple_name(cid), "self")
        score_selector(right, couple_name(opponent), "opp")

        if current["self"] is not None and current["opp"] is not None:
            my_first = live["a"] == cid
            ga, gb = (
                (current["self"], current["opp"])
                if my_first else
                (current["opp"], current["self"])
            )

            st.markdown(
                f"<div class='panel score'>"
                f"{current['self']} — {current['opp']}</div>",
                unsafe_allow_html=True,
            )

            if st.button("✅ CONFERMA RISULTATO", use_container_width=True):
                # Nei gironi il pareggio è ammesso.
                finish_match(live, ga, gb)
                st.session_state.scores.pop(score_key, None)
                st.success("Risultato registrato! La coda è stata aggiornata.")
                st.rerun()
    else:
        q = player_queue()
        if q:
            queue = [m for m in S["matches"] if m["status"] == "queue"]
            pos = next(
                (i+1 for i, m in enumerate(queue) if cid in (m["a"], m["b"])),
                1,
            )
            st.markdown(
                f"<div class='panel' style='text-align:center'>"
                f"<div class='section-title'>⏳ PREPARATI</div>"
                f"<div style='font-size:32px;font-weight:1000;color:#ffd21a'>"
                f"POSIZIONE #{pos}</div>"
                f"<div class='small'>Sarai chiamato automaticamente quando arriva il tuo turno.</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Nessuna partita LIVE per la tua coppia.")

    # Classifica del girone.
    group = next((g for g, ids in S["gironi"].items() if cid in ids), None)
    if group:
        rows = standings(group)
        mine = next(r for r in rows if r["id"] == cid)
        st.markdown(f"<div class='section-title'>📊 GIRONE {group}</div>", unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("POSIZIONE", rows.index(mine)+1)
        c2.metric("PUNTI", mine["PT"])
        c3.metric("GF", mine["GF"])
        c4.metric("DR", mine["DR"])
        st.dataframe(
            [{k:v for k,v in r.items() if not k.startswith("_") and k != "id"} for r in rows],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### 📅 LE MIE PARTITE")
    for m in [x for x in all_matches() if cid in (x["a"], x["b"])]:
        opponent = m["b"] if m["a"] == cid else m["a"]
        status = {"done":"✅ TERMINATA","live":"🟢 IN CORSO","queue":"⏳ IN CODA"}.get(m["status"], m["status"])
        score = f"{m['ga']} — {m['gb']}" if m["status"] == "done" else "—"
        table = f" · 🎱 Biliardino {m['table']}" if m["status"] == "live" else ""
        st.markdown(
            f"<div class='queue'><span class='badge green'>{status}</span>"
            f"{couple_name(opponent)} · <b>{score}</b>{table}</div>",
            unsafe_allow_html=True,
        )

# ============================================================
# LIVE
# ============================================================
elif page == "⚡ Live":
    st.markdown("<div class='neon-title'>⚡ LIVE</div>", unsafe_allow_html=True)
    live = [m for m in all_matches() if m["status"] == "live"]

    if not live:
        st.info("Nessuna partita in corso.")

    for m in live:
        st.markdown(
            f"<div class='panel live'><div class='table-title'>🎱 BILIARDINO {m['table']}</div>"
            f"<div class='team'><div class='team-name'>{couple_name(m['a'])}</div></div>"
            f"<div class='vs'>VS</div>"
            f"<div class='team blue'><div class='team-name'>{couple_name(m['b'])}</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("### ⏳ CODA")
    queue = [m for m in S["matches"] if m["status"] == "queue"]
    if not queue:
        st.success("Coda vuota.")
    for i,m in enumerate(queue[:30], 1):
        st.markdown(
            f"<div class='queue'><span class='badge gold'>#{i}</span>"
            f"<b>{couple_name(m['a'])}</b> VS <b>{couple_name(m['b'])}</b></div>",
            unsafe_allow_html=True,
        )

# ============================================================
# CLASSIFICA
# ============================================================
elif page == "🏆 Classifica":
    st.markdown("<div class='neon-title'>🏆 CLASSIFICHE</div>", unsafe_allow_html=True)
    for g in sorted(S["gironi"]):
        st.markdown(f"<div class='section-title'>GIRONE {g}</div>", unsafe_allow_html=True)
        rows = standings(g)
        st.dataframe(
            [{k:v for k,v in r.items() if not k.startswith("_") and k != "id"} for r in rows],
            use_container_width=True,
            hide_index=True,
        )

# ============================================================
# CALENDARIO
# ============================================================
elif page in ("🗓️ Le mie partite", "🗓️ Calendario"):
    st.markdown("<div class='neon-title'>🗓️ CALENDARIO</div>", unsafe_allow_html=True)

    if st.session_state.admin:
        matches = list(all_matches())
    else:
        cid = player_cid()
        matches = [m for m in all_matches() if cid in (m["a"],m["b"])]

    for m in matches:
        score = f"{m['ga']} — {m['gb']}" if m["status"] == "done" else "—"
        st.markdown(
            f"<div class='queue'><span class='badge'>{m['status'].upper()}</span>"
            f"<b>{couple_name(m['a'])}</b> VS <b>{couple_name(m['b'])}</b>"
            f" · {score}</div>",
            unsafe_allow_html=True,
        )

# ============================================================
# FINALI
# ============================================================
elif page == "🥇 Fasi Finali":
    st.markdown("<div class='neon-title'>🥇 FASI FINALI</div>", unsafe_allow_html=True)

    for fs in ("A", "B"):
        st.markdown(f"<div class='section-title'>🏆 FASCIA {fs}</div>", unsafe_allow_html=True)
        finals = S["finals"][fs]

        if not finals:
            st.info("Tabellone non ancora generato.")
            continue

        for m in finals:
            st.markdown(
                f"<div class='panel live'><div class='table-title'>{m['phase']}</div>"
                f"<div class='score'>{couple_name(m['a'])}<br>"
                f"<span style='color:#ffd21a'>VS</span><br>{couple_name(m['b'])}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        if st.session_state.admin and all(m["status"] == "done" for m in finals):
            if st.button(f"➡️ AVANZA FASCIA {fs}", key=f"advance-{fs}"):
                advance_final(fs)
                st.rerun()

    for fs in ("A","B"):
        p = S["podio"].get(fs)
        if p:
            st.markdown(
                f"<div class='podium'><div class='winner'>🏆 FASCIA {fs}</div>"
                f"<div style='font-size:22px;margin-top:10px'>"
                f"🥇 {couple_name(p['finalists'][0])}<br>"
                f"🥈 {couple_name(p['finalists'][1])}<br>"
                f"🥉/4° {couple_name(p['third_fourth'][0])} · "
                f"{couple_name(p['third_fourth'][1])}</div></div>",
                unsafe_allow_html=True,
            )

# ============================================================
# ADMIN
# ============================================================
elif page == "👑 Admin":
    st.markdown("<div class='neon-title'>👑 ADMIN</div>", unsafe_allow_html=True)
    st.success("PIN amministratore: 0000")
    st.info("Regola fissa del torneo: **chi perde resta al tavolo**. Non è configurabile.")

    tabs = st.tabs(["⚙️ Setup", "🎱 Tavoli", "✏️ Risultati", "🏆 Fasi Finali", "🔄 Reset"])

    with tabs[0]:
        st.markdown("### 👥 Crea il torneo")
        text = st.text_area(
            "Inserisci le coppie, una per riga. Esempio: Mario / Luigi",
            height=220,
        )
        c1,c2 = st.columns(2)
        tavoli = c1.number_input("🎱 Biliardini", min_value=1, max_value=10, value=int(S["tavoli"]))
        gironi = c2.number_input("🏆 Gironi", min_value=1, max_value=20, value=int(S["gironi_n"]))

        if st.button("🎲 CREA SORTEGGIO E CALENDARIO", use_container_width=True):
            new, error = create_tournament(text, int(tavoli), int(gironi))
            if error:
                st.error(error)
            else:
                st.session_state.torneo = new
                st.session_state.player = None
                st.session_state.scores = {}
                st.success("Torneo creato. I giocatori possono ora entrare con il proprio nome.")
                st.rerun()

        if S["coppie"]:
            st.markdown("### 👥 Coppie registrate")
            for c in S["coppie"]:
                st.write(f"**{c['id']}** — {couple_name(c['id'])}")

    with tabs[1]:
        st.markdown("### 🎱 Tavoli LIVE")
        for table in range(1, S["tavoli"]+1):
            m = next(
                (x for x in all_matches()
                 if x["status"] == "live" and x.get("table") == table),
                None
            )
            if m:
                st.markdown(
                    f"<div class='queue'><b>🎱 {table}</b> · 🟢 "
                    f"{couple_name(m['a'])} VS {couple_name(m['b'])}</div>",
                    unsafe_allow_html=True,
                )
                if st.button(f"🔓 LIBERA TAVOLO {table}", key=f"free-{table}"):
                    m["status"] = "queue"
                    m["table"] = None
                    assign_initial_tables()
                    st.rerun()
            else:
                st.markdown(
                    f"<div class='queue'><b>🎱 {table}</b> · LIBERO</div>",
                    unsafe_allow_html=True,
                )

        if st.button("⚡ RIEMPI I TAVOLI"):
            assign_initial_tables()
            st.rerun()

    with tabs[2]:
        st.markdown("### ✏️ Correzione risultati")
        for m in list(all_matches()):
            if m["status"] == "done":
                with st.expander(
                    f"{m['id']} · {couple_name(m['a'])} VS {couple_name(m['b'])} · {m['ga']}-{m['gb']}"
                ):
                    ga = st.number_input("Gol A", 0, MAX_GOALS, int(m["ga"]), key=f"ga-{m['id']}")
                    gb = st.number_input("Gol B", 0, MAX_GOALS, int(m["gb"]), key=f"gb-{m['id']}")
                    if st.button("💾 SALVA", key=f"save-{m['id']}"):
                        m["ga"] = ga
                        m["gb"] = gb
                        m["winner"] = m["a"] if ga > gb else (m["b"] if gb > ga else None)
                        st.success("Risultato corretto.")
                        st.rerun()

    with tabs[3]:
        all_done = bool(S["matches"]) and all(m["status"] == "done" for m in S["matches"])
        if S["phase"] == "gironi" and all_done:
            if st.button("🏆 GENERA FASCIA A / FASCIA B", use_container_width=True):
                generate_finals()
                st.rerun()
        elif S["phase"] == "gironi":
            st.warning("Completa tutte le partite dei gironi prima di generare le fasi finali.")

        st.write(f"Fascia A: {len(S['fasce']['A'])} coppie")
        st.write(f"Fascia B: {len(S['fasce']['B'])} coppie")

        for fs in ("A","B"):
            finals = S["finals"][fs]
            if finals and all(m["status"] == "done" for m in finals):
                if st.button(f"➡️ AVANZA FASCIA {fs}", key=f"admin-advance-{fs}"):
                    advance_final(fs)
                    st.rerun()

    with tabs[4]:
        st.warning("Questa operazione cancella completamente il torneo.")
        if st.button("🔴 AZZERA TUTTO", use_container_width=True):
            st.session_state.torneo = new_state()
            st.session_state.player = None
            st.session_state.scores = {}
            st.session_state.admin = True
            st.rerun()
