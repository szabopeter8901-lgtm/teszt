import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Munkaruha Nyilvántartó", layout="wide")
st.title("👕 Munkaruha Nyilvántartó Rendszer")

# --- Fájlnevek ---
DATA_FILE = "raktar_adatok.csv"
NAPLO_FILE = "kiadas_naplo.csv"

# --- Betöltés ---
if os.path.exists(DATA_FILE):
    raktar_df = pd.read_csv(DATA_FILE)
else:
    raktar_df = pd.DataFrame(columns=["Típus", "Méret", "Mennyiség"])

if os.path.exists(NAPLO_FILE):
    naplo_df = pd.read_csv(NAPLO_FILE)
else:
    naplo_df = pd.DataFrame(columns=["Dátum", "Dolgozó", "Típus", "Méret", "Mennyiség"])

if "raktar" not in st.session_state:
    st.session_state.raktar = raktar_df
if "naplo" not in st.session_state:
    st.session_state.naplo = naplo_df

MIN_KESZLET = 5

# --- Mentés segédfüggvények ---
def mentes_raktar():
    st.session_state.raktar.to_csv(DATA_FILE, index=False)

def mentes_naplo():
    st.session_state.naplo.to_csv(NAPLO_FILE, index=False)

# --- Oldalválasztás ---
menu = st.sidebar.radio("Válasszon oldalt:", ["📦 Raktárkezelés", "🧾 Kiadási napló"])

# --- Sidebar: Legördülő menük szerkesztése ---
st.sidebar.header("🛠 Legördülő menük szerkesztése")

# Típusok szerkesztése
tipus_lista = st.session_state.raktar["Típus"].unique().tolist()
uj_tipus = st.sidebar.text_input("Új típus hozzáadása")
if st.sidebar.button("Típus hozzáadása"):
    if uj_tipus and uj_tipus not in tipus_lista:
        st.session_state.raktar = pd.concat(
            [st.session_state.raktar, pd.DataFrame({"Típus": [uj_tipus], "Méret": [""], "Mennyiség": [0]})],
            ignore_index=True
        )
        mentes_raktar()
        st.sidebar.success(f"{uj_tipus} hozzáadva a típusokhoz!")

# Dolgozók szerkesztése
dolgozo_lista = st.session_state.naplo["Dolgozó"].unique().tolist()
uj_dolgozo = st.sidebar.text_input("Új dolgozó hozzáadása")
if st.sidebar.button("Dolgozó hozzáadása"):
    if uj_dolgozo and uj_dolgozo not in dolgozo_lista:
        st.session_state.naplo = pd.concat(
            [st.session_state.naplo, pd.DataFrame({"Dátum": [""], "Dolgozó": [uj_dolgozo], "Típus": [""], "Méret": [""], "Mennyiség": [0]})],
            ignore_index=True
        )
        mentes_naplo()
        st.sidebar.success(f"{uj_dolgozo} hozzáadva a dolgozókhoz!")

# --- RAKTÁRKEZELÉS ---
if menu == "📦 Raktárkezelés":
    st.header("📦 Raktárkezelés")

    # Bevitel
    with st.form("bevetel_form"):
        st.subheader("Új ruha bevitele")
        col1, col2, col3 = st.columns(3)
        tipus = col1.text_input("Típus")
        meret = col2.text_input("Méret")
        menny = col3.number_input("Mennyiség", min_value=1, value=1)
        hozzaad_btn = st.form_submit_button("Bevitel")

        if hozzaad_btn:
            if tipus and meret:
                df = st.session_state.raktar
                mask = (df["Típus"] == tipus) & (df["Méret"] == meret)
                if mask.any():
                    df.loc[mask, "Mennyiség"] += menny
                else:
                    new_row = pd.DataFrame({"Típus": [tipus], "Méret": [meret], "Mennyiség": [menny]})
                    st.session_state.raktar = pd.concat([df, new_row], ignore_index=True)
                mentes_raktar()
                st.success(f"{menny} db {tipus} ({meret}) hozzáadva.")
            else:
                st.error("Töltse ki a típus és méret mezőket!")

    # Kiadás
    with st.form("kiadas_form"):
        st.subheader("Ruha kiadása")
        col1, col2, col3, col4 = st.columns(4)

        # Dolgozó legördülő
        dolgozok = [d for d in st.session_state.naplo["Dolgozó"].unique() if d]  # csak nem üres
        dolgozo = col1.selectbox("Dolgozó neve (kötelező)", options=dolgozok)

        # Típus legördülő
        tipusok = st.session_state.raktar["Típus"].unique().tolist()
        tipus_k = col2.selectbox("Típus", options=tipusok)

        # Méret legördülő a kiválasztott típushoz
        meretek = st.session_state.raktar[st.session_state.raktar["Típus"] == tipus_k]["Méret"].unique().tolist()
        meret_k = col3.selectbox("Méret", options=meretek)

        menny_k = col4.number_input("Mennyiség", min_value=1, value=1)
        kiad_btn = st.form_submit_button("Kiadás")

        if kiad_btn:
            if not dolgozo.strip():
                st.error("Adja meg a dolgozó nevét!")
            else:
                df = st.session_state.raktar
                mask = (df["Típus"] == tipus_k) & (df["Méret"] == meret_k)
                if mask.any():
                    idx = df.index[mask][0]
                    if df.loc[idx, "Mennyiség"] >= menny_k:
                        df.loc[idx, "Mennyiség"] -= menny_k
                        if df.loc[idx, "Mennyiség"] == 0:
                            df = df.drop(idx)
                        st.session_state.raktar = df.reset_index(drop=True)
                        mentes_raktar()

                        # Naplózás
                        uj_sor = pd.DataFrame({
                            "Dátum": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                            "Dolgozó": [dolgozo],
                            "Típus": [tipus_k],
                            "Méret": [meret_k],
                            "Mennyiség": [menny_k]
                        })
                        st.session_state.naplo = pd.concat([st.session_state.naplo, uj_sor], ignore_index=True)
                        mentes_naplo()

                        st.success(f"{dolgozo} számára {menny_k} db {tipus_k} ({meret_k}) kiadva.")
                    else:
                        st.error("Nincs elegendő készlet!")
                else:
                    st.error("Nincs ilyen típusú és méretű ruha a raktárban!")

    # Raktárkészlet megjelenítés
    st.subheader("📊 Aktuális raktárkészlet")
    df = st.session_state.raktar.copy()

    if not df.empty:
        def highlight_min(s):
            return ["background-color: #FFCCCC" if v < MIN_KESZLET else "background-color: #CCFFCC" for v in s]

        styled = df.style.apply(highlight_min, subset=["Mennyiség"])
        st.dataframe(styled, use_container_width=True)

        st.download_button("💾 Raktár exportálása CSV-be", data=df.to_csv(index=False), file_name="raktar_export.csv")
    else:
        st.info("Nincs adat a raktárban.")

# --- KIADÁSI NAPLÓ ---
elif menu == "🧾 Kiadási napló":
    st.header("🧾 Kiadási napló dolgozónként és időszak szerint")
    naplo = st.session_state.naplo.copy()

    if not naplo.empty:
        # Dátum formátum konverzió
        naplo["Dátum"] = pd.to_datetime(naplo["Dátum"], errors='coerce')

        # Szűrők
        dolgozok = ["(összes)"] + sorted([d for d in naplo["Dolgozó"].dropna() if d])
        col1, col2, col3 = st.columns(3)
        valasztott = col1.selectbox("Dolgozó kiválasztása:", dolgozok)
        datum_tol = col2.date_input("Dátumtól", value=naplo["Dátum"].min().date() if not naplo.empty else datetime.today().date())
        datum_ig = col3.date_input("Dátumig", value=datetime.today().date())

        # Szűrés dolgozóra és időszakra
        if valasztott != "(összes)":
            naplo = naplo[naplo["Dolgozó"] == valasztott]
        naplo = naplo[(naplo["Dátum"].dt.date >= datum_tol) & (naplo["Dátum"].dt.date <= datum_ig)]

        st.dataframe(naplo.sort_values("Dátum", ascending=False), use_container_width=True)

        # Összesítő statisztika
        st.subheader("📈 Összesítő statisztika dolgozónként")
        osszesito = naplo.groupby("Dolgozó")["Mennyiség"].sum().reset_index().rename(columns={"Mennyiség": "Összes kiadott darab"})
        st.dataframe(osszesito, use_container_width=True)

        # Típusonkénti bontás pivot táblával
        st.subheader("👕 Típusonkénti bontás dolgozónként")
        pivot = naplo.pivot_table(index="Dolgozó", columns="Típus", values="Mennyiség", aggfunc="sum", fill_value=0)
        pivot["Összesen"] = pivot.sum(axis=1)
        st.dataframe(pivot, use_container_width=True)

        st.download_button("💾 Napló exportálása CSV-be", data=naplo.to_csv(index=False), file_name="kiadas_naplo_szurt.csv")
        st.download_button("💾 Típusonkénti statisztika exportálása CSV-be", data=pivot.to_csv(), file_name="tipusonkénti_statisztika.csv")
    else:
        st.info("Még nem történt kiadás.")
