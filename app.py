
import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB = Path("movie_finder.db")
COLS = ["imdb_id","title","year","genres","language","imdb_rating","vote_count","overview"]
DEMO = [
("tt1392214","Prisoners",2013,"Crime|Drama|Mystery|Thriller","English",None,None,"Two families search for missing children."),
("tt4857264","The Invisible Guest",2016,"Crime|Mystery|Thriller","Spanish",None,None,"A businessman tries to prove his innocence."),
("tt1130884","Shutter Island",2010,"Mystery|Thriller","English",None,None,"A marshal investigates a disappearance."),
("tt0110912","Pulp Fiction",1994,"Crime|Drama","English",None,None,"Interconnected stories unfold in Los Angeles."),
("tt6751668","Parasite",2019,"Drama|Thriller","Korean",None,None,"Two families become entangled."),
("tt0209144","Memento",2000,"Mystery|Thriller","English",None,None,"A man with memory loss searches for a killer."),
("tt0230600","The Others",2001,"Horror|Mystery|Thriller","English",None,None,"A mother and her children live in a darkened house."),
("tt0469494","There Will Be Blood",2007,"Drama","English",None,None,"An ambitious oil prospector builds an empire."),
("tt0102926","The Silence of the Lambs",1991,"Crime|Drama|Thriller","English",None,None,"An FBI trainee seeks help from an imprisoned killer."),
("tt3011894","Wild Tales",2014,"Comedy|Drama|Thriller","Spanish",None,None,"Six stories explore people pushed to their limits."),
("tt1187043","3 Idiots",2009,"Comedy|Drama","Hindi",None,None,"Three engineering students challenge convention."),
("tt5074352","Dangal",2016,"Biography|Drama|Sport","Hindi",None,None,"A former wrestler trains his daughters."),
("tt0816692","Interstellar",2014,"Adventure|Drama|Sci-Fi","English",None,None,"Explorers travel beyond our galaxy."),
("tt0137523","Fight Club",1999,"Drama","English",None,None,"An office worker forms an underground fight club."),
("tt0482571","The Prestige",2006,"Drama|Mystery|Thriller","English",None,None,"Two magicians become consumed by rivalry."),
("tt0114369","Se7en",1995,"Crime|Drama|Mystery|Thriller","English",None,None,"Two detectives hunt a serial killer."),
("tt0457430","Pan's Labyrinth",2006,"Drama|Fantasy|War","Spanish",None,None,"A young girl discovers a mysterious fantasy world."),
("tt0317248","City of God",2002,"Crime|Drama","Portuguese",None,None,"Two boys take different paths in a violent neighbourhood."),
("tt1160419","Dune",2021,"Adventure|Drama|Sci-Fi","English",None,None,"A young nobleman travels to a desert planet."),
("tt0105236","Reservoir Dogs",1992,"Crime|Thriller","English",None,None,"A jewellery heist goes wrong."),
("tt0364569","Oldboy",2003,"Action|Drama|Mystery|Thriller","Korean",None,None,"A man seeks answers after years of captivity."),
("tt1457767","The Conjuring",2013,"Horror|Mystery|Thriller","English",None,None,"Paranormal investigators help a family."),
("tt1345836","The Dark Knight Rises",2012,"Action|Drama|Thriller","English",None,None,"Batman returns to protect Gotham.")
]

def db():
    c=sqlite3.connect(DB,check_same_thread=False)
    c.row_factory=sqlite3.Row
    return c

def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS movies(imdb_id TEXT PRIMARY KEY,title TEXT,year INTEGER,genres TEXT,language TEXT,imdb_rating REAL,vote_count INTEGER,overview TEXT);
        CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY,genres TEXT DEFAULT '',languages TEXT DEFAULT '',min_rating REAL DEFAULT 0,min_year INTEGER DEFAULT 1990,max_year INTEGER DEFAULT 2026);
        CREATE TABLE IF NOT EXISTS activity(username TEXT,imdb_id TEXT,status TEXT,user_rating REAL,PRIMARY KEY(username,imdb_id));
        """)
        if c.execute("SELECT COUNT(*) FROM movies").fetchone()[0]==0:
            c.executemany("INSERT OR IGNORE INTO movies VALUES(?,?,?,?,?,?,?,?)",DEMO)

def get_user(n):
    with db() as c:
        c.execute("INSERT OR IGNORE INTO users(username) VALUES(?)",(n,))
        return dict(c.execute("SELECT * FROM users WHERE username=?",(n,)).fetchone())

def get_movies():
    with db() as c: return pd.read_sql_query("SELECT * FROM movies ORDER BY title",c)

def get_activity(n):
    with db() as c: return pd.read_sql_query("SELECT * FROM activity WHERE username=?",c,params=(n,))

def activity_set(n,i,s,r=None):
    with db() as c:
        c.execute("""INSERT INTO activity VALUES(?,?,?,?) ON CONFLICT(username,imdb_id)
        DO UPDATE SET status=excluded.status,user_rating=COALESCE(excluded.user_rating,activity.user_rating)""",(n,i,s,r))

def save_prefs(n,g,l,r,y0,y1):
    with db() as c: c.execute("UPDATE users SET genres=?,languages=?,min_rating=?,min_year=?,max_year=? WHERE username=?",("|".join(g),"|".join(l),r,y0,y1,n))

def import_csv(file):
    x=pd.read_csv(file)
    missing=set(COLS)-set(x.columns)
    if missing: raise ValueError("Missing columns: "+", ".join(sorted(missing)))
    x=x[COLS].copy()
    x["imdb_id"]=x.imdb_id.astype(str)
    x["year"]=pd.to_numeric(x.year,errors="coerce")
    x["imdb_rating"]=pd.to_numeric(x.imdb_rating,errors="coerce")
    x["vote_count"]=pd.to_numeric(x.vote_count,errors="coerce")
    x=x[x.title.notna() & x.imdb_id.ne("")]
    rows=[tuple(None if pd.isna(v) else v for v in row) for row in x.itertuples(index=False,name=None)]
    with db() as c:
        c.executemany("""INSERT INTO movies VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(imdb_id) DO UPDATE SET
        title=excluded.title,year=excluded.year,genres=excluded.genres,language=excluded.language,
        imdb_rating=excluded.imdb_rating,vote_count=excluded.vote_count,overview=excluded.overview""",rows)
    return len(rows)

def rank_movies(movies,p,a,prefs):
    watched=set(a.loc[a.status=="Watched","imdb_id"]) if not a.empty else set()
    fav=set(a.loc[a.status=="Favourite","imdb_id"]) if not a.empty else set()
    x=movies[~movies.imdb_id.isin(watched)].copy()
    x=x[(x.year.fillna(0)>=p["min_year"])&(x.year.fillna(9999)<=p["max_year"])]
    if p["min_rating"]>0: x=x[x.imdb_rating.fillna(0)>=p["min_rating"]]
    gs=set(filter(None,p["genres"].split("|"))); ls=set(filter(None,p["languages"].split("|")))
    def score(m):
        mg=set(str(m.genres or "").split("|"))
        genre=len(gs&mg)/max(1,len(gs))
        lang=1 if not ls or m.language in ls else 0
        rating=float(m.imdb_rating)/10 if pd.notna(m.imdb_rating) else .5
        votes=min(1,float(m.vote_count or 0)/100000) if pd.notna(m.vote_count) else 0
        return .55*genre+.15*lang+.20*rating+.10*votes+(.15 if m.imdb_id in fav else 0)
    x["match_score"]=x.apply(score,axis=1)
    return x.sort_values("match_score",ascending=False)

st.set_page_config(page_title="Movie Finder",page_icon="🎬",layout="wide")
init()
st.title("🎬 Movie Finder")
st.caption("A shared movie club for friends — discover, save and rate films.")
with st.sidebar:
    st.header("Your profile")
    n=st.text_input("Name / nickname",st.session_state.get("user",""))
    if n.strip(): st.session_state["user"]=n.strip()
if not st.session_state.get("user"):
    st.info("Enter your name in the sidebar to open your movie profile.")
    st.stop()
n=st.session_state["user"]; p=get_user(n); movies=get_movies(); a=get_activity(n)
discover,watchlist,ratings,settings=st.tabs(["✨ Discover","📌 Watchlist","⭐ My activity","⚙️ Preferences & data"])

with settings:
    st.subheader("Recommendation preferences")
    genres=sorted({g for v in movies.genres.fillna("") for g in str(v).split("|") if g})
    langs=sorted(set(movies.language.dropna()))
    with st.form("preferences"):
        g=st.multiselect("Genres you enjoy",genres,[v for v in p["genres"].split("|") if v in genres])
        l=st.multiselect("Preferred languages (blank = all)",langs,[v for v in p["languages"].split("|") if v in langs])
        r=st.slider("Minimum IMDb rating (requires imported ratings)",0.0,10.0,float(p["min_rating"]),.5)
        y=st.slider("Release year range",1920,2026,(max(1920,int(p["min_year"])),min(2026,int(p["max_year"]))))
        if st.form_submit_button("Save preferences",type="primary"):
            save_prefs(n,g,l,r,y[0],y[1]); st.success("Saved."); st.rerun()
    st.divider(); st.subheader("Catalogue data")
    st.write(f"**{len(movies):,} titles** currently available.")
    st.caption("The included catalogue is demo content; IMDb scores and vote counts are not loaded.")
    st.download_button("Download CSV template",pd.DataFrame(columns=COLS).to_csv(index=False),"movie_catalog_template.csv","text/csv")
    up=st.file_uploader("Import / refresh an authorised movie catalogue",type=["csv"])
    if up and st.button("Import catalogue"):
        try: st.success(f"Imported or updated {import_csv(up):,} titles."); st.rerun()
        except Exception as e: st.error(str(e))
    st.warning("Monthly refresh is not activated. Confirm data licensing before importing or sharing any provider's data.")

with discover:
    st.subheader(f"Recommendations for {n}")
    rec=rank_movies(movies,p,a,prefs=None)
    st.caption("Match score combines your genre/language preferences with available catalogue ratings and vote counts. It is not an IMDb score.")
    if rec.empty: st.info("No matches. Widen your year range or lower the rating threshold.")
    cols=st.columns(3)
    for j,(_,m) in enumerate(rec.head(30).iterrows()):
        with cols[j%3]:
            with st.container(border=True):
                st.subheader(f"{m.title} ({int(m.year) if pd.notna(m.year) else 'Year n/a'})")
                st.caption(str(m.genres).replace("|"," · "))
                rating=f"IMDb {m.imdb_rating:.1f}" if pd.notna(m.imdb_rating) else "IMDb rating not loaded"
                st.write(rating)
                st.write(m.overview or "")
                st.caption(f"Match score: {m.match_score:.0%}")
                c1,c2=st.columns(2)
                if c1.button("＋ Watchlist",key="w"+m.imdb_id): activity_set(n,m.imdb_id,"Watchlist"); st.rerun()
                if c2.button("♥ Favourite",key="f"+m.imdb_id): activity_set(n,m.imdb_id,"Favourite"); st.rerun()
                if st.button("✓ Mark watched",key="d"+m.imdb_id,use_container_width=True): activity_set(n,m.imdb_id,"Watched"); st.rerun()

with watchlist:
    st.subheader("Your watchlist")
    ids=a.loc[a.status=="Watchlist","imdb_id"] if not a.empty else []
    saved=movies[movies.imdb_id.isin(ids)]
    if saved.empty: st.info("Your watchlist is empty.")
    for _,m in saved.iterrows():
        st.write(f"**{m.title} ({m.year})** · {str(m.genres).replace('|',' · ')}")
        if st.button("Remove",key="remove"+m.imdb_id):
            with db() as c: c.execute("DELETE FROM activity WHERE username=? AND imdb_id=?",(n,m.imdb_id))
            st.rerun()

with ratings:
    st.subheader("Watched movies, favourites and ratings")
    if a.empty: st.info("No activity yet. Start saving movies from Discover.")
    for _,v in a.iterrows():
        m=movies[movies.imdb_id==v.imdb_id]
        title=m.iloc[0].title if not m.empty else v.imdb_id
        st.write(f"**{title}** · {v.status}")
        if v.status=="Watched":
            current=float(v.user_rating) if pd.notna(v.user_rating) else 0.0
            score=st.slider(f"Your rating for {title}",0.0,10.0,current,.5,key="rate"+v.imdb_id)
            if st.button("Save rating",key="save"+v.imdb_id): activity_set(n,v.imdb_id,"Watched",score); st.rerun()
        if st.button("Remove activity",key="del"+v.imdb_id):
            with db() as c: c.execute("DELETE FROM activity WHERE username=? AND imdb_id=?",(n,v.imdb_id))
            st.rerun()

st.divider()
st.caption("Movie Finder MVP · Not affiliated with IMDb. IMDb attribution and permission must be handled before using IMDb data.")
