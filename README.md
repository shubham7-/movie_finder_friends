# Movie Finder — Friends Edition

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```
Open the local Streamlit URL, usually http://localhost:8501.

## Included
- Separate profiles by nickname
- Genre, language, year and minimum-rating preferences
- Personalised ranked discovery
- Watchlist, watched history, favourites and personal ratings
- CSV catalogue import and downloadable template
- SQLite persistence

## Important limitations before inviting friends
- Nicknames are not authentication. Anyone with access can select another profile.
- SQLite is for prototyping; use PostgreSQL and real authentication for a hosted multi-user app.
- The included catalogue is demo content and has no imported IMDb scores or votes.
- Monthly refresh is not enabled until a licensed source is selected.

## IMDb data licensing
IMDb says its free datasets are for personal and non-commercial use and must not be republished or repurposed to create an online/offline movie information database except for individual personal use. Do not assume this permits a shared friends app. Obtain appropriate permission/licensing before using IMDb data in a multi-user app.
Official policy: https://help.imdb.com/article/imdb/general-information/can-i-use-imdb-data-in-my-software/G5JTRESSHJBBHTGX

TMDB may be an alternative for a non-commercial app subject to its API terms and attribution requirements: https://developer.themoviedb.org/docs/faq

## CSV schema
`imdb_id,title,year,genres,language,imdb_rating,vote_count,overview`
Genres are pipe-separated, e.g. `Crime|Mystery|Thriller`. Only upload data you are authorised to use.

## Next steps
1. Add password-protected accounts and friend invitations.
2. Move to PostgreSQL.
3. Integrate a licensed movie metadata/rating provider.
4. Add a monthly scheduled refresh with validation and rollback.
5. Add posters and movie detail pages.
6. Improve recommendations with collaborative filtering as friend activity grows.
