# 🏆 Torneo Coppie Fisse LIVE

Versione **iPhone-friendly**: solo 3 file da caricare nel repository GitHub.

## File
- `app.py` — applicazione completa e grafica Dark/Gaming/Neon
- `requirements.txt` — dipendenze
- `README.md` — istruzioni

## Avvio
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Pubblicazione
Su Streamlit Community Cloud seleziona:
- Repository: il tuo repository GitHub
- Branch: `principale` (oppure il nome del branch che usi)
- Main file: `app.py`

## Importante
Questa è una versione iniziale pensata per essere caricata facilmente da iPhone.
Lo stato del torneo vive nella sessione Streamlit. Per un torneo multiutente reale con più telefoni contemporaneamente, il passo successivo è collegare Supabase/PostgreSQL come database condiviso.
