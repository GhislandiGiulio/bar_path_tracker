import streamlit as st
import numpy as np
import cv2
import os
import time

st.set_page_config(
    layout="wide",
    page_title="Bar Path Tracker")

# Funzione di elaborazione: esempio di conversione in scala di grigi
def process(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    processed_frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return processed_frame

st.title("Bar Path Tracker")

# Creazione delle colonne
left_col, right_col = st.columns(2)

uploaded_file = None
processed_video_path = None

with left_col:
    uploaded_file = st.file_uploader(
        "Scegli un file video (.mp4)",
        type=["mp4"]
    )

    if uploaded_file is not None:
        # Definisci il percorso del file video
        file_name = uploaded_file.name
        save_path = os.path.join("videos", file_name)  # Salva nella cartella 'videos'

        # Crea la directory se non esiste
        if not os.path.exists("videos"):
            os.makedirs("videos")

        # Salva il file caricato localmente
        with open(save_path, "wb") as f:
            f.write(uploaded_file.read())

        # Conferma il percorso del file video
        st.success(f"File salvato con successo in: {save_path}")

        # Elaborazione del video con OpenCV
        cap = cv2.VideoCapture(save_path)
        if not cap.isOpened():
            st.error("Errore nell'apertura del file video.")
        else:
            # Proprietà del video
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Usa il codec H264 per la codifica del video
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')

            # Definisci il percorso del video elaborato
            processed_video_path = os.path.join("videos", f"processed_{file_name}")
            out = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height))

            st.info("Elaborazione del video in corso...")
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            progress_bar = st.progress(0)

            for i in range(frame_count):
                ret, frame = cap.read()
                if not ret:
                    break

                # Elabora il frame
                processed_frame = process(frame)

                # Scrivi il frame elaborato
                out.write(processed_frame)

                # Aggiorna la barra di avanzamento
                progress_bar.progress((i + 1) / frame_count)

            # Rilascia le risorse
            cap.release()
            out.release()

            # Assicurati che il file sia completamente salvato
            time.sleep(1)  # Pausa per dare tempo di completare la scrittura

            progress_bar.empty()

with right_col:
    if uploaded_file is not None:
        st.subheader("Video Originale")
        st.video(save_path)

        if processed_video_path:
            st.subheader("Video Elaborato")
            st.video(processed_video_path)
