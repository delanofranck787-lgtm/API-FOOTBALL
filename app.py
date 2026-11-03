
import math, sqlite3, json, os
from datetime import datetime, date, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import plotly.express as px

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "bet_intelligence.db"
LEAGUES = {
    "Bundesliga (Allemagne)": "bl1",
    "2. Bundesliga (Allemagne)": "bl2",
    "Premier League (Angleterre)": "pl",
    "La Liga (Espagne)": "pd",
    "Serie A (Italie)": "sa",
    "Ligue 1 (France)": "l1",
    "Ligue des champions": "ucl",
}

st.set_page_config(page_title="BET INTELLIGENCE AI", page_icon="⚽", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#070b16;--panel:rgba(15,24,43,.82);--line:rgba(65,219,255,.22);--cyan:#35e7ff;--violet:#9b75ff;--green:#5dffbd;--muted:#9eacc5}
.stApp{background:radial-gradient(ellipse at 15% 0%,rgba(30,104,160,.22),transparent 36%),radial-gradient(ellipse at 90% 10%,rgba(117,55,190,.18),transparent 32%),linear-gradient(145deg,#070b16 0%,#0a1020 55%,#080b17 100%);color:#edf5ff;font-family:'Inter',sans-serif}
.block-container{max-width:1500px;padding-top:2rem;padding-bottom:3rem}
h1,h2,h3{font-family:'Orbitron','Inter',sans-serif!important;letter-spacing:.3px}
h1{color:#f4fbff!important;text-shadow:0 0 22px rgba(53,231,255,.18)}
h2,h3{color:#dcecff!important}
p, label, .stMarkdown{color:#d5e2f4}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0c1426 0%,#090e1c 100%);border-right:1px solid var(--line)}
[data-testid="stSidebar"] h1{font-size:1.12rem!important;color:var(--cyan)!important}
[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(19,35,59,.94),rgba(12,20,37,.9));border:1px solid var(--line);padding:17px 18px;border-radius:16px;box-shadow:0 8px 28px rgba(0,0,0,.22),inset 0 1px rgba(255,255,255,.04)}
[data-testid="stMetricLabel"]{color:#9fb5d1!important;font-weight:600}
[data-testid="stMetricValue"]{color:#f4fbff!important;font-family:'Orbitron',sans-serif}
div.stButton>button,div.stDownloadButton>button{border:1px solid rgba(53,231,255,.55);border-radius:11px;background:linear-gradient(100deg,rgba(28,135,174,.28),rgba(111,74,191,.28));color:#eafaff;font-weight:800;min-height:2.8rem;box-shadow:0 0 18px rgba(53,231,255,.08);transition:.2s}
div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:var(--cyan);box-shadow:0 0 22px rgba(53,231,255,.24);color:white;transform:translateY(-1px)}
.stTextInput input,.stNumberInput input,.stSelectbox div[data-baseweb="select"]>div,.stMultiSelect div[data-baseweb="select"]>div{background:#0d1729!important;color:#f3f8ff!important;border:1px solid rgba(105,143,190,.3)!important;border-radius:10px!important}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid var(--line);border-radius:13px;overflow:hidden}
hr{border-color:rgba(80,150,200,.2)!important}
.small-muted{color:var(--muted);font-size:.88rem}
.badge{display:inline-block;padding:7px 13px;border-radius:30px;background:rgba(35,255,184,.09);border:1px solid rgba(93,255,189,.38);color:var(--green);font-size:.78rem;font-weight:800;letter-spacing:1px;text-transform:uppercase}
.hero-panel{padding:26px 28px;border:1px solid rgba(53,231,255,.28);border-radius:20px;background:linear-gradient(115deg,rgba(14,42,65,.88),rgba(29,20,57,.82));box-shadow:0 14px 40px rgba(0,0,0,.25),inset 0 1px rgba(255,255,255,.05);margin-bottom:22px}
.hero-kicker{font-family:'Orbitron',sans-serif;color:var(--cyan);font-size:.72rem;letter-spacing:2px;text-transform:uppercase}
.hero-title{font-family:'Orbitron',sans-serif;font-size:clamp(1.35rem,3vw,2.3rem);font-weight:800;color:#f4fbff;margin:8px 0;text-shadow:0 0 24px rgba(53,231,255,.25)}
.hero-sub{color:#aebed5;font-size:.96rem}
.section-tag{color:var(--cyan);font-family:'Orbitron',sans-serif;font-size:.72rem;letter-spacing:1.5px;text-transform:uppercase}
.stAlert{border-radius:12px}

.match-card{background:linear-gradient(145deg,rgba(15,29,50,.96),rgba(10,17,32,.98));border:1px solid rgba(53,231,255,.25);border-radius:18px;padding:17px 18px;margin:12px 0 5px;box-shadow:0 10px 28px rgba(0,0,0,.2),inset 0 1px rgba(255,255,255,.035)}
.match-top{display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap}.match-league{font-size:.72rem;color:#45e8ff;font-weight:800;letter-spacing:1.2px;text-transform:uppercase}.match-time{font-size:.78rem;color:#a9bad2}
.match-teams{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:17px 0 4px;color:#f2f7ff;font-size:clamp(.95rem,2.4vw,1.25rem);font-weight:800}.match-teams b{font-size:.68rem;color:#9b80ff;border:1px solid rgba(155,128,255,.4);padding:5px 8px;border-radius:8px;white-space:nowrap}.match-teams span:last-child{text-align:right}.match-status{font-size:.72rem;color:#9fb2cb;margin-bottom:15px}.prob-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.prob-grid small{display:block;color:#9eafc7;font-size:.61rem;letter-spacing:.4px;font-weight:800}.prob-grid strong{display:block;color:#f5fbff;font-family:'Orbitron',sans-serif;font-size:1.15rem;margin:5px 0 8px}.prob-track{height:6px;background:#252d3d;border-radius:10px;overflow:hidden}.prob-track i{display:block;height:100%;border-radius:10px;background:linear-gradient(90deg,#27dfff,#9676ff)}.match-pick{display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap;margin-top:15px;padding-top:12px;border-top:1px solid rgba(120,160,200,.15)}.match-pick span{font-size:.65rem;letter-spacing:.8px;color:#9eafc7}.match-pick b{font-size:.82rem;color:#63ffc0}
@media(max-width:600px){.block-container{padding-left:.75rem;padding-right:.75rem}.match-card{padding:14px 12px}.prob-grid{gap:7px}.prob-grid small{font-size:.55rem}.prob-grid strong{font-size:1rem}.match-teams{font-size:.94rem}}

</style>
""", unsafe_allow_html=True)

def db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("""CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, league TEXT,
        home TEXT, away TEXT, p_home REAL, p_draw REAL, p_away REAL,
        predicted_score TEXT, over25 REAL, btts REAL, odds_home REAL,
        odds_draw REAL, odds_away REAL, actual_result TEXT, notes TEXT
    )""")
    con.commit()
    return con

def poisson(k, lam):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def dc_matrix(lh, la, rho=-0.08, max_goals=10):
    # Dixon-Coles low-score adjustment; probabilities normalized afterwards.
    matrix = []
    for h in range(max_goals + 1):
        row = []
        for a in range(max_goals + 1):
            p = poisson(h, lh) * poisson(a, la)
            if h == 0 and a == 0:
                tau = 1 - (lh * la * rho)
            elif h == 0 and a == 1:
                tau = 1 + (lh * rho)
            elif h == 1 and a == 0:
                tau = 1 + (la * rho)
            elif h == 1 and a == 1:
                tau = 1 - rho
            else:
                tau = 1
            row.append(max(0.0, p * tau))
        matrix.append(row)
    total = sum(sum(r) for r in matrix)
    return [[x / total for x in r] for r in matrix]

def metrics(lh, la):
    m = dc_matrix(lh, la)
    ph = sum(m[h][a] for h in range(len(m)) for a in range(len(m)) if h > a)
    pd = sum(m[h][a] for h in range(len(m)) for a in range(len(m)) if h == a)
    pa = 1 - ph - pd
    over25 = sum(m[h][a] for h in range(len(m)) for a in range(len(m)) if h + a >= 3)
    btts = sum(m[h][a] for h in range(len(m)) for a in range(len(m)) if h > 0 and a > 0)
    score = max(((m[h][a], h, a) for h in range(len(m)) for a in range(len(m))), key=lambda x:x[0])
    # Asian handicap home -0.5 equals home win; home +0.5 equals home win or draw.
    return {
        "home": ph, "draw": pd, "away": pa, "over25": over25, "under25": 1-over25,
        "btts": btts, "no_btts": 1-btts, "score": f"{score[1]}–{score[2]}",
        "score_prob": score[0], "matrix": m,
        "over15": sum(m[h][a] for h in range(11) for a in range(11) if h+a>=2),
        "over35": sum(m[h][a] for h in range(11) for a in range(11) if h+a>=4),
        "home_ah_m05": ph, "home_ah_p05": ph+pd,
        "away_ah_m05": pa, "away_ah_p05": pa+pd,
    }

def fair_odds(p):
    return (1/p) if p and p > 0 else None

def value_edge(p, odds):
    if odds is None or odds <= 1 or p <= 0: return None
    return p * odds - 1

def load_openligadb(league_code, season):
    url = f"{OPENLIGADB}/getmatchdata/{league_code}/{season}"
    r = requests.get(url, timeout=12, headers={"User-Agent":"BetIntelligenceAI/1.0"})
    r.raise_for_status()
    data = r.json()
    rows = []
    for m in data:
        teams = m.get("team1",{}), m.get("team2",{})
        home, away = teams[0].get("teamName","Domicile"), teams[1].get("teamName","Extérieur")
        results = m.get("matchResults",[])
        final = next((x for x in results if x.get("resultTypeID") == 2), None)
        if final is None and results:
            final = results[-1]
        rows.append({
            "Date": m.get("matchDateTimeUTC") or m.get("matchDateTime"),
            "Domicile": home, "Extérieur": away,
            "Buts domicile": final.get("pointsTeam1") if final else None,
            "Buts extérieur": final.get("pointsTeam2") if final else None,
            "Terminé": bool(final),
        })
    return pd.DataFrame(rows)


def get_api_football_key():
    """Lit la clé depuis les secrets Streamlit ou une variable d'environnement."""
    try:
        key = st.secrets.get("API_FOOTBALL_KEY", "")
    except Exception:
        key = ""
    return key or os.environ.get("API_FOOTBALL_KEY", "")


@st.cache_data(ttl=900, show_spinner=False)
def load_all_upcoming_matches(days_ahead=10):
    """Récupère les matchs à venir via API-Football en une requête."""
    columns = ["Date", "Domicile", "Extérieur", "Buts domicile", "Buts extérieur", "Terminé", "Championnat", "Statut", "ID_match"]
    key = get_api_football_key()
    if not key:
        return pd.DataFrame(columns=columns), ["Clé API absente : configurez API_FOOTBALL_KEY dans les secrets Streamlit."]
    today = date.today()
    params = {"from": today.isoformat(), "to": (today + timedelta(days=days_ahead)).isoformat(), "timezone": "Africa/Douala"}
    try:
        response = requests.get("https://v3.football.api-sports.io/fixtures",
            headers={"x-apisports-key": key}, params=params, timeout=25)
        if response.status_code == 401:
            return pd.DataFrame(columns=columns), ["Clé API invalide ou non autorisée (HTTP 401)."]
        if response.status_code == 403:
            return pd.DataFrame(columns=columns), ["Accès refusé : vérifiez les droits et la couverture du forfait (HTTP 403)."]
        if response.status_code == 429:
            return pd.DataFrame(columns=columns), ["Quota API-Football atteint (HTTP 429)."]
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            return pd.DataFrame(columns=columns), [f"API-Football : {str(payload['errors'])[:350]}"]
        rows = []
        for item in payload.get("response", []):
            fixture, teams = item.get("fixture") or {}, item.get("teams") or {}
            goals, league = item.get("goals") or {}, item.get("league") or {}
            status = fixture.get("status") or {}
            short_status = status.get("short") or ""
            rows.append({
                "Date": fixture.get("date"),
                "Domicile": (teams.get("home") or {}).get("name", "Équipe domicile"),
                "Extérieur": (teams.get("away") or {}).get("name", "Équipe extérieure"),
                "Buts domicile": goals.get("home"), "Buts extérieur": goals.get("away"),
                "Terminé": short_status in {"FT", "AET", "PEN"},
                "Championnat": league.get("name") or "Compétition",
                "Statut": status.get("long") or "Programmé",
                "ID_match": str(fixture.get("id", "")),
            })
        if not rows:
            return pd.DataFrame(columns=columns), ["Aucun match renvoyé sur cette période. La couverture dépend du forfait API-Football."]
        frame = pd.DataFrame(rows).drop_duplicates(subset=["ID_match"])
        frame["Date tri"] = pd.to_datetime(frame["Date"], utc=True, errors="coerce")
        now = datetime.now(timezone.utc)
        frame = frame[(frame["Date tri"] >= now - timedelta(hours=4)) & (~frame["Terminé"].astype(bool))]
        frame = frame.sort_values("Date tri").drop(columns=["Date tri"])
        return frame.reset_index(drop=True), []
    except requests.exceptions.Timeout:
        return pd.DataFrame(columns=columns), ["Délai dépassé pendant la connexion à API-Football."]
    except requests.exceptions.RequestException as exc:
        return pd.DataFrame(columns=columns), [f"Erreur réseau API-Football : {str(exc)[:250]}"]
    except (ValueError, TypeError, KeyError) as exc:
        return pd.DataFrame(columns=columns), [f"Réponse API-Football illisible : {str(exc)[:200]}"]


def team_rates(df, home, away):
    played = df[df["Terminé"] == True].copy()
    if played.empty:
        return None
    played["Buts domicile"] = pd.to_numeric(played["Buts domicile"], errors="coerce")
    played["Buts extérieur"] = pd.to_numeric(played["Buts extérieur"], errors="coerce")
    played = played.dropna(subset=["Buts domicile","Buts extérieur"])
    if len(played) < 8:
        return None
    league_home = max(0.2, played["Buts domicile"].mean())
    league_away = max(0.2, played["Buts extérieur"].mean())
    league_total = max(0.4, (league_home + league_away)/2)
    def stats(team):
        h = played[played["Domicile"] == team]
        a = played[played["Extérieur"] == team]
        gf = (h["Buts domicile"].sum() + a["Buts extérieur"].sum())
        ga = (h["Buts extérieur"].sum() + a["Buts domicile"].sum())
        n = len(h) + len(a)
        if n == 0: return (1.0,1.0)
        return (max(.35, gf/n/league_total), max(.35, ga/n/league_total))
    ha, hd = stats(home)
    aa, ad = stats(away)
    # Home advantage from the league's observed home/away scoring ratio.
    home_adv = league_home / max(.2, league_away)
    lam_home = max(.15, league_home * ha * ad)
    lam_away = max(.15, league_away * aa * hd / max(.75, home_adv**0.25))
    return lam_home, lam_away

def upcoming_rows(df):
    if df.empty: return df
    return df[df["Terminé"] != True].copy()

def fmt_pct(x): return f"{x*100:.1f}%"

with st.sidebar:
    st.title("⚽ BET INTELLIGENCE AI")
    st.caption("Analyse statistique • Dixon–Coles / Poisson")
    page = st.radio("Navigation", ["Tableau de bord", "Analyser un match", "Historique & résultats", "Guide"])
    st.divider()
    st.caption("API-FOOTBALL • Connexion par clé privée")

if "matches" not in st.session_state:
    st.session_state.matches = pd.DataFrame()
if "league_label" not in st.session_state:
    st.session_state.league_label = "Toutes les compétitions"
if "fixtures_loaded" not in st.session_state:
    with st.spinner("Chargement automatique des rencontres de football…"):
        auto_df, auto_errors = load_all_upcoming_matches()
        st.session_state.matches = auto_df
        st.session_state.fixture_errors = auto_errors
        st.session_state.fixtures_loaded = True

if page == "Tableau de bord":
    st.markdown('<div class="hero-panel"><div class="hero-kicker">Football intelligence system • Match center</div><div class="hero-title">BET INTELLIGENCE AI</div><div class="hero-sub">Tous les matchs et leurs analyses réunis dans un seul tableau de bord. Les rencontres les plus proches apparaissent en premier.</div><br><span class="badge">● CENTRE DE MATCHS AUTOMATIQUE</span></div>', unsafe_allow_html=True)
    df = st.session_state.matches.copy()
    if df.empty:
        st.warning("Aucun calendrier n'a été reçu pour le moment.")
        errors_now = st.session_state.get("fixture_errors", [])
        if errors_now:
            st.info(errors_now[0])
        st.caption('Configurez votre clé dans Streamlit Cloud → Settings → Secrets : API_FOOTBALL_KEY = "votre_clé".')
    else:
        # Horaires locaux Cameroun et filtres utilisables directement depuis le tableau de bord.
        df["Date locale"] = pd.to_datetime(df["Date"], utc=True, errors="coerce").dt.tz_convert("Africa/Douala")
        now_local = pd.Timestamp.now(tz="Africa/Douala")
        live_mask = df.get("Statut", pd.Series("", index=df.index)).astype(str).str.contains("live|1st|2nd|half|period|temps", case=False, regex=True)
        upcoming_count = int((df["Date locale"] >= now_local).sum())
        c1,c2,c3 = st.columns(3)
        c1.metric("MATCHS DISPONIBLES", len(df))
        c2.metric("EN DIRECT", int(live_mask.sum()))
        c3.metric("À VENIR", upcoming_count)

    action_col, note_col = st.columns([1, 2])
    if action_col.button("⟳  ACTUALISER LES MATCHS", use_container_width=True):
        load_all_upcoming_matches.clear()
        with st.spinner("Synchronisation des calendriers…"):
            auto_df, auto_errors = load_all_upcoming_matches()
            st.session_state.matches = auto_df
            st.session_state.fixture_errors = auto_errors
        st.rerun()
    note_col.caption("API-Football • Synchronisation automatique • Horaires affichés en heure du Cameroun")

    if not df.empty:
        st.markdown('<div class="section-tag">02 / Recherche & filtres</div>', unsafe_allow_html=True)
        search_col, league_col, day_col = st.columns([2, 1.4, 1])
        query = search_col.text_input("⌕ Rechercher un match ou une équipe", placeholder="Ex. : Real Madrid, Arsenal, PSG…", key="dashboard_search")
        leagues = ["Toutes les compétitions"] + sorted(df["Championnat"].dropna().astype(str).unique().tolist())
        selected_league = league_col.selectbox("Compétition", leagues)
        day_options = ["Toutes les dates", "Aujourd'hui", "Demain", "7 prochains jours"]
        selected_day = day_col.selectbox("Période", day_options)
        filtered = df.copy()
        if query.strip():
            q = query.strip().casefold()
            filtered = filtered[filtered.apply(lambda r: q in f"{r.get('Domicile','')} {r.get('Extérieur','')} {r.get('Championnat','')}".casefold(), axis=1)]
        if selected_league != "Toutes les compétitions":
            filtered = filtered[filtered["Championnat"] == selected_league]
        today_local = now_local.date()
        if selected_day == "Aujourd'hui": filtered = filtered[filtered["Date locale"].dt.date == today_local]
        elif selected_day == "Demain": filtered = filtered[filtered["Date locale"].dt.date == today_local + timedelta(days=1)]
        elif selected_day == "7 prochains jours": filtered = filtered[filtered["Date locale"] <= now_local + pd.Timedelta(days=7)]

        st.markdown(f'<div class="section-tag">03 / Centre des pronostics — {len(filtered)} rencontre(s)</div>', unsafe_allow_html=True)
        if filtered.empty:
            st.info("Aucun match ne correspond à votre recherche. Essayez un autre nom d'équipe ou une autre compétition.")
        else:
            for idx, row in filtered.iterrows():
                home, away = str(row["Domicile"]), str(row["Extérieur"])
                league = str(row.get("Championnat", "Compétition"))
                kickoff = row.get("Date locale")
                kickoff_text = kickoff.strftime("%a %d %b • %H:%M") if pd.notna(kickoff) else "Horaire à confirmer"
                status_text = str(row.get("Statut", "Programmé"))
                # Paramètres génériques explicitement signalés en attendant un historique vérifié par équipe.
                history_df = st.session_state.get("history", pd.DataFrame())
                rates = team_rates(history_df, home, away) if not history_df.empty else None
                lh, la = rates if rates else (1.45, 1.10)
                pred = metrics(float(lh), float(la))
                best_label, best_prob = max([(home,pred["home"]),("Nul",pred["draw"]),(away,pred["away"])], key=lambda x:x[1])
                card_html = f'''<div class="match-card">
                  <div class="match-top"><span class="match-league">{league}</span><span class="match-time">{kickoff_text}</span></div>
                  <div class="match-teams"><span>{home}</span><b>VS</b><span>{away}</span></div>
                  <div class="match-status">{status_text}</div>
                  <div class="prob-grid">
                    <div><small>1 • DOMICILE</small><strong>{fmt_pct(pred['home'])}</strong><div class="prob-track"><i style="width:{pred['home']*100:.1f}%"></i></div></div>
                    <div><small>N • NUL</small><strong>{fmt_pct(pred['draw'])}</strong><div class="prob-track"><i style="width:{pred['draw']*100:.1f}%"></i></div></div>
                    <div><small>2 • EXTÉRIEUR</small><strong>{fmt_pct(pred['away'])}</strong><div class="prob-track"><i style="width:{pred['away']*100:.1f}%"></i></div></div>
                  </div>
                  <div class="match-pick"><span>ISSUE LA PLUS PROBABLE</span><b>{best_label} · {fmt_pct(best_prob)}</b></div>
                </div>'''
                st.markdown(card_html, unsafe_allow_html=True)
                with st.expander(f"Voir tous les pronostics · {home} – {away}", expanded=False):
                    d1,d2,d3 = st.columns(3)
                    d1.metric("Score probable", pred["score"])
                    d2.metric("Over 2.5", fmt_pct(pred["over25"]))
                    d3.metric("BTTS — Oui", fmt_pct(pred["btts"]))
                    d4,d5,d6 = st.columns(3)
                    d4.metric("Under 2.5", fmt_pct(pred["under25"]))
                    d5.metric("Over 1.5", fmt_pct(pred["over15"]))
                    d6.metric("Over 3.5", fmt_pct(pred["over35"]))
                    st.caption(f"Buts attendus utilisés : {home} {lh:.2f} — {away} {la:.2f}.")
                    if not rates:
                        st.warning("Estimation indicative : aucun historique suffisant n'est disponible pour ces deux équipes. Les probabilités reposent sur des paramètres de départ et ne doivent pas être interprétées comme des statistiques spécifiques aux équipes.")
                    if st.button("Ouvrir l'analyse complète", key=f"analyse_{idx}", use_container_width=True):
                        st.session_state.quick_match = (home, away, league)
                        st.session_state.page = "Analyser un match"
                        st.rerun()

        if st.session_state.get("fixture_errors"):
            with st.expander("État des sources de calendrier"):
                st.caption(f"{len(st.session_state.fixture_errors)} compétition(s) n'ont pas répondu. Les autres calendriers restent disponibles.")
                st.write(st.session_state.fixture_errors[:8])

    st.markdown('<div class="small-muted">Les probabilités affichées sont des estimations mathématiques, pas des garanties. Leur fiabilité dépend de la disponibilité de données historiques propres à chaque équipe.</div>', unsafe_allow_html=True)

elif page == "Analyser un match":
    st.markdown('<div class="hero-panel"><div class="hero-kicker">Prediction lab • Statistical engine</div><div class="hero-title">ANALYSE DE MATCH</div><div class="hero-sub">Modélisation Poisson / Dixon–Coles, marchés de buts et probabilités 1N2.</div></div>', unsafe_allow_html=True)
    df = st.session_state.matches
    quick_match = st.session_state.pop("quick_match", None)
    home = quick_match[0] if quick_match else None
    away = quick_match[1] if quick_match else None
    league = quick_match[2] if quick_match else "Toutes les compétitions"
    if not df.empty:
        options = [f"{pd.to_datetime(r['Date'], utc=True).tz_convert('Africa/Douala').strftime('%d/%m %H:%M')} | {r.get('Championnat','')} | {r['Domicile']} — {r['Extérieur']}" for _,r in df.iterrows()]
        choice = st.selectbox("Choisir un match (liste automatiquement classée par proximité)", options)
        row = df.iloc[options.index(choice)]
        home, away = str(row["Domicile"]), str(row["Extérieur"])
        league = str(row.get("Championnat", "Toutes les compétitions"))
    else:
        st.warning("Aucune rencontre n'a été renvoyée par les sources gratuites pour le moment. Actualisez le tableau de bord ou utilisez la saisie manuelle.")
    x,y = st.columns(2)
    home = x.text_input("Équipe à domicile", value=home or "")
    away = y.text_input("Équipe à l'extérieur", value=away or "")
    st.caption("Les équipes du match sont préremplies automatiquement. L'import d'un historique CSV reste facultatif et sert uniquement à affiner les estimations.")
    history_df = st.session_state.get("history", pd.DataFrame())
    mode = st.radio("Source des paramètres", ["Calcul depuis l'historique chargé", "Saisie manuelle des buts attendus"], horizontal=True)
    if mode == "Calcul depuis l'historique chargé":
        rates = team_rates(history_df, home, away) if not history_df.empty and home and away else None
        if rates:
            lh,la = rates
            st.success(f"Paramètres estimés sur {int((df['Terminé']==True).sum())} matchs terminés.")
        else:
            st.warning("Aucun historique CSV suffisant n'est importé. Des valeurs de départ sont proposées automatiquement ; ajustez-les si vous disposez de statistiques fiables.")
            lh,la = 1.45,1.10
    else:
        lh,la = 1.45,1.10
    if mode == "Saisie manuelle des buts attendus":
        p,q = st.columns(2)
        lh = p.number_input("xG domicile estimé", .1, 5.0, 1.45, .05)
        la = q.number_input("xG extérieur estimé", .1, 5.0, 1.10, .05)
    odds_on = st.checkbox("J'ai les cotes du bookmaker (pour calculer la value)")
    odds = [None,None,None]
    if odds_on:
        o1,o2,o3 = st.columns(3)
        odds = [o1.number_input("Cote 1",1.01,100.0,2.0,.01),o2.number_input("Cote N",1.01,100.0,3.2,.01),o3.number_input("Cote 2",1.01,100.0,3.8,.01)]
    if st.button("LANCER L'ANALYSE", type="primary", use_container_width=True):
        if not home.strip() or not away.strip() or home.strip().lower()==away.strip().lower():
            st.error("Indiquez deux équipes différentes.")
        else:
            res = metrics(float(lh),float(la))
            st.session_state.last_analysis = (home,away,league,res,odds,float(lh),float(la))
    if "last_analysis" in st.session_state:
        home,away,league,res,odds,lh,la = st.session_state.last_analysis
        st.divider()
        st.subheader(f"{home}  VS  {away}")
        st.caption(f"Buts attendus estimés : {home} {lh:.2f} — {away} {la:.2f}")
        c1,c2,c3 = st.columns(3)
        c1.metric("Victoire domicile",fmt_pct(res["home"]))
        c2.metric("Match nul",fmt_pct(res["draw"]))
        c3.metric("Victoire extérieur",fmt_pct(res["away"]))
        st.subheader("Marchés de buts")
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Over 1.5",fmt_pct(res["over15"]))
        m2.metric("Over 2.5",fmt_pct(res["over25"]))
        m3.metric("Over 3.5",fmt_pct(res["over35"]))
        m4.metric("BTTS — Oui",fmt_pct(res["btts"]))
        st.subheader("Handicap asiatique — probabilités indicatives")
        h1,h2,h3,h4 = st.columns(4)
        h1.metric(f"{home} -0.5",fmt_pct(res["home_ah_m05"]))
        h2.metric(f"{home} +0.5",fmt_pct(res["home_ah_p05"]))
        h3.metric(f"{away} -0.5",fmt_pct(res["away_ah_m05"]))
        h4.metric(f"{away} +0.5",fmt_pct(res["away_ah_p05"]))
        st.subheader("Score exact le plus probable")
        s1,s2 = st.columns(2)
        s1.metric("Score modal",res["score"])
        s2.metric("Probabilité du score",fmt_pct(res["score_prob"]))
        chart = pd.DataFrame({"Issue":[home,"Nul",away],"Probabilité":[res["home"],res["draw"],res["away"]]})
        st.plotly_chart(px.bar(chart,x="Issue",y="Probabilité",text=chart["Probabilité"].map(fmt_pct),title="Probabilités 1X2"),use_container_width=True)
        if odds_on:
            st.subheader("Détection de value bet")
            rows=[]
            for label,p,odd in zip([home,"Nul",away],[res["home"],res["draw"],res["away"]],odds):
                edge=value_edge(p,odd)
                rows.append({"Marché":label,"Probabilité modèle":fmt_pct(p),"Cote":odd,"Cote juste":round(fair_odds(p),2),"Value estimée":f"{edge*100:+.1f}%" if edge is not None else "—","Signal":"Value potentielle" if edge is not None and edge>=.03 else "Pas de value claire"})
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            st.caption("La value est calculée par p × cote − 1. Elle ne garantit ni gain ni rentabilité.")
        if st.button("Enregistrer ce pronostic"):
            con=db()
            con.execute("""INSERT INTO predictions(created_at,league,home,away,p_home,p_draw,p_away,predicted_score,over25,btts,odds_home,odds_draw,odds_away)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",(datetime.now().isoformat(timespec="seconds"),league,home,away,res["home"],res["draw"],res["away"],res["score"],res["over25"],res["btts"],*odds))
            con.commit()
            st.success("Pronostic enregistré dans l'historique local.")

elif page == "Historique & résultats":
    st.markdown('<div class="hero-panel"><div class="hero-kicker">Performance tracking</div><div class="hero-title">HISTORIQUE & RÉSULTATS</div><div class="hero-sub">Mesurez vos analyses dans le temps et confrontez les prévisions aux résultats réels.</div></div>', unsafe_allow_html=True)
    con=db()
    data=pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC",con)
    if data.empty:
        st.info("Aucun pronostic enregistré. Analysez un match puis cliquez sur « Enregistrer ce pronostic ».")
    else:
        st.dataframe(data[["created_at","league","home","away","predicted_score","p_home","p_draw","p_away","actual_result"]],use_container_width=True,hide_index=True)
        st.download_button("Télécharger l'historique CSV",data.to_csv(index=False).encode("utf-8"),"historique_pronostics.csv","text/csv")
        st.subheader("Saisir le résultat réel")
        ids=data["id"].tolist()
        selected=st.selectbox("Pronostic",ids,format_func=lambda i: f"#{i} — {data.loc[data.id==i,'home'].iloc[0]} vs {data.loc[data.id==i,'away'].iloc[0]}")
        result=st.selectbox("Résultat final",["1","N","2"])
        if st.button("Mettre à jour le résultat"):
            con.execute("UPDATE predictions SET actual_result=? WHERE id=?",(result,int(selected)))
            con.commit()
            st.success("Résultat enregistré.")
        evaluated=data.dropna(subset=["actual_result"])
        if not evaluated.empty:
            correct=((evaluated["p_home"]>=evaluated["p_draw"]) & (evaluated["p_home"]>=evaluated["p_away"]) & (evaluated["actual_result"]=="1")) | ((evaluated["p_draw"]>evaluated["p_home"]) & (evaluated["p_draw"]>=evaluated["p_away"]) & (evaluated["actual_result"]=="N")) | ((evaluated["p_away"]>evaluated["p_home"]) & (evaluated["p_away"]>evaluated["p_draw"]) & (evaluated["actual_result"]=="2"))
            st.metric("Taux de réussite 1X2 sur les résultats saisis",f"{correct.mean()*100:.1f}%",f"{len(evaluated)} matchs évalués")

else:
    st.markdown('<div class="hero-panel"><div class="hero-kicker">System documentation</div><div class="hero-title">CENTRE D’AIDE</div><div class="hero-sub">Comprendre les outils, les données et les limites du moteur de pronostics.</div></div>', unsafe_allow_html=True)
    st.markdown("""
    ### 1. Charger des rencontres
    Depuis le tableau de bord, choisissez un championnat et une saison. Les rencontres sont récupérées automatiquement depuis API-Football. Configurez votre clé dans les secrets Streamlit sous le nom API_FOOTBALL_KEY. Vous pouvez aussi importer un CSV.

    ### 2. Préparer les données
    Pour estimer les forces des équipes, importez un historique comportant les colonnes `Domicile`, `Extérieur`, `Buts domicile`, `Buts extérieur`. Ajoutez `Terminé` (True/False) si vous le souhaitez.

    ### 3. Analyser
    Sélectionnez deux équipes, utilisez l'historique ou saisissez les buts attendus. Le moteur calcule 1X2, scores, Over/Under, BTTS et lignes de handicap indicatives.

    ### 4. Value betting
    Saisissez les cotes 1/N/2 pour comparer la probabilité du modèle à la cote proposée. Une value positive est un écart mathématique potentiel, pas une garantie.

    ### 5. Sauvegarder
    Enregistrez les analyses et ajoutez les résultats réels pour suivre la performance. Les données sont conservées dans la base SQLite locale du déploiement.

    **Limites importantes :** le modèle n'est pas une IA qui connaît l'avenir. La précision dépend de la qualité et de la quantité des données. Les blessures, compositions, suspensions, météo et mouvements de cotes ne sont pas automatiquement intégrés. Ne misez jamais de l'argent nécessaire à vos besoins.
    """)
    st.download_button("Télécharger un modèle CSV", "Domicile,Extérieur,Buts domicile,Buts extérieur,Terminé\nEquipe A,Equipe B,2,1,True\nEquipe B,Equipe C,0,0,True\nEquipe C,Equipe A,1,2,True\n".encode("utf-8"), "modele_historique.csv", "text/csv")

st.markdown("---")
st.markdown('<p class="small-muted">BET INTELLIGENCE AI • Outil d’aide à l’analyse statistique • Les probabilités ne constituent pas une garantie de gain.</p>', unsafe_allow_html=True)
