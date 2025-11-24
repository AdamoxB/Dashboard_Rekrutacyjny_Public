# app.py
import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import os

# 🔐 Konfiguracja bazy danych (ZAMIANA NA TWOJE DANE!)
DB_CONFIG = {
    'host': 'localhost',
    'database': 'rekrutacja',
    'user': 'your_user',
    'password': 'your_password',
    'port': 5432
}

# 🔧 Funkcje pomocnicze
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Błąd połączenia z bazą danych: {e}")
        return None

def get_all_applications():
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        query = "SELECT * FROM job_applications ORDER BY created_at DESC"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Błąd przy odczytywaniu danych: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def add_application(title, company_url, company_name, stage="list_of_wishes", notes=""):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO job_applications (title, company_url, company_name, stage, progress_notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, company_url, company_name, stage, notes))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Błąd podczas dodawania oferty: {e}")
        return False
    finally:
        conn.close()

def update_application_status(app_id, new_stage, notes=""):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE job_applications 
            SET stage = %s, progress_notes = %s, updated_at = NOW()
            WHERE id = %s
        """, (new_stage, notes, app_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Błąd podczas aktualizacji: {e}")
        return False
    finally:
        conn.close()

# 🚀 Główna aplikacja
st.set_page_config(page_title="Dashboard Rekrutacyjny", layout="wide")

st.title("📊 Dashboard Rekrutacyjny")
st.markdown("Zarządzaj ofertami – przesuwaj je między etapami, dodawaj nowe oferty i śledź postępy.")

# --- 1. Dodaj nową ofertę ---
st.header("✅ Dodaj nową ofertę")

with st.form("new_application"):
    title = st.text_input("Tytuł oferty", placeholder="np. Inżynier AI")
    company_url = st.text_input("Link do oferty (URL)", placeholder="https://example.com/jobs")
    company_name = st.text_input("Nazwa firmy", placeholder="TechCorp")
    submit_btn = st.form_submit_button("Dodaj ofertę")

if submit_btn:
    if title and company_url:
        success = add_application(title, company_url, company_name)
        if success:
            st.success("✅ Oferta dodana do listy!")
        else:
            st.error("❌ Błąd podczas dodawania oferty.")
    else:
        st.error("❌ Wprowadź tytuł i link!")

# --- 2. Lista ofert z przesuwaniem ---
st.header("📋 Lista ofert (etapy rekrutacji)")

applications = get_all_applications()

if not applications.empty:
    # Etapy jako kolumny
    cols = ["Tytuł", "Firma", "Link", "Etap", "Postęp"]
    for _, row in applications.iterrows():
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown(f"### {row['title']}")
        with col2:
            st.markdown(f"**{row['company_name']}**")
        with col3:
            st.markdown(f"[{row['company_url']}]({row['company_url']})")
        with col4:
            stage_map = {
                "list_of_wishes": "🔹 Lista życzeń",
                "application_sent": "📧 Aplikacja wysłana",
                "recruitment_process": "🔄 W trakcie procesu",
                "offer_received": "✅ Oferta dostępna"
            }
            stage_text = stage_map.get(row['stage'], 'Brak etapu')
            st.markdown(f"**{stage_text}**")
        with col5:
            # Przyciski do przesuwania
            col_buttons = st.columns(3)
            with col_buttons[0]:
                if st.button("➡️ Aplikacja wysłana", key=f"{row['id']}_sent"):
                    update_application_status(row['id'], "application_sent", f"Aplikacja wysłana: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
            with col_buttons[1]:
                if st.button("➡️ Proces rekrutacyjny", key=f"{row['id']}_process"):
                    update_application_status(row['id'], "recruitment_process", "Zaczął proces rekrutacyjny")
            with col_buttons[2]:
                if st.button("➡️ Oferta dostępna", key=f"{row['id']}_offer"):
                    update_application_status(row['id'], "offer_received", "Oferta została przyjęta")
else:
    st.info("Brak ofert. Dodaj nową ofertę!")

# 📝 Informacja o bieżącym stanie
st.sidebar.header("ℹ️ Informacje")
st.sidebar.write("✅ Aplikacja zapisuje oferty w PostgreSQL.")
st.sidebar.write("🔧 Wymagania: PostgreSQL, Python 3.11+")
