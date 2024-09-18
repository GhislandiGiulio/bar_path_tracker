import streamlit as st
import numpy as np
import cv2
import os
import time
from matplotlib import pyplot as plt
from PIL import Image

st.set_page_config(
    layout="wide",
    page_title="Bar Path Tracker",
    page_icon="resources/logo.png")


# caricamento logo
logo = Image.open("resources/logo.png")

st.logo(logo)

###
### FUNZIONI DI ELABORAZIONE
###

def track_frame(frame, roi_hist, term_crit, track_window):
    
    # converti il frame nello spazio colore HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # proietta l'istogramma della ROI sul nuovo frame (usando il canale hue)
    dst = cv2.calcBackProject([hsv], [0], roi_hist, [0, 180], 1)

    # applica il mean shift per ottenere la nuova posizione
    ret, new_track_window = cv2.meanShift(dst, track_window, term_crit)

    # disegna la nuova finestra di tracciamento sul frame
    x, y, w, h = track_window
    tracked_frame = cv2.rectangle(frame.copy(), (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    return tracked_frame, new_track_window

# funzione di elaborazione: esempio di conversione in scala di grigi
def process_video(cap):
    
    # proprietà del video
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # usa il codec H264 per la codifica del video
    fourcc = cv2.VideoWriter_fourcc(*'H264')

    # definisci il percorso del video elaborato
    processed_video_path = os.path.join("videos", f"processed_{uploaded_file.name}")
    out = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height))

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # inizializza il tracciamento del percorso
    first_frame = get_first_frame(cap)
    roi_hist, term_crit, track_window = selectROI(first_frame)

    # calcolo spostamento
    y_positions = []
    y_positions.append(track_window[1]) # y

    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break

        # elabora il frame
        processed_frame, track_window = track_frame(frame, roi_hist, term_crit, track_window)

        # scrivi il frame elaborato
        out.write(processed_frame)

        # salva spostamento finestra
        y_positions.append(track_window[1])

        # aggiorna la barra di avanzamento
        progress_bar.progress((i + 1) / frame_count)

    velocities = compute_movement(
        y_positions,        # array di y
        track_window[3],    # altezza window di tracking
        fps,                # fps video
        )
    
    processed_plot_path = os.path.join("plots", f"processed_{uploaded_file.name}.png")
    save_plot(velocities, path = processed_plot_path)

    # rilascia le risorse
    cap.release()
    out.release()

    return processed_video_path, processed_plot_path
    

def get_first_frame(cap):

    ret, frame = cap.read()

    return frame

def create_video_copy(file_name):
    
    save_path = os.path.join("videos", file_name)  # salva nella cartella 'videos'

    # crea la directory se non esiste
    if not os.path.exists("videos"):
        os.makedirs("videos")

    # salva il file caricato localmente
    with open(save_path, "wb") as f:
        f.write(uploaded_file.read())

    return save_path

def selectROI(frame):
    # consenti all'utente di selezionare la ROI
    roi_box = cv2.selectROI("Select ROI", frame, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Select ROI")

    # estrai le coordinate della ROI
    x, y, w, h = map(int, roi_box)
    roi = frame[y:y+h, x:x+w]

    # converti la ROI nello spazio colore HSV
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # crea una maschera per filtrare la bassa luminosità (questo rimuove i pixel scuri dal calcolo dell'istogramma)
    mask = cv2.inRange(hsv_roi, np.array((0., 60., 32.)), np.array((180., 255., 255.)))

    # calcola l'istogramma della ROI nello spazio colore HSV (usando solo il canale hue)
    roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0, 180])

    # normalizza l'istogramma
    cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)

    # definisci i criteri di terminazione: o 10 iterazioni o spostamento di almeno 1 punto
    term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 1)

    # crea la finestra iniziale per il tracciamento
    track_window = (x, y, w, h)

    return roi_hist, term_crit, track_window

def compute_movement(y_positions, window_height, video_fps):

    from matplotlib import pyplot as plt

    altezza_reale = 0.45 # altezza disco in metri

    # calcolo del rapporto tra movimento in metri e in pixel
    meters_per_pixel = altezza_reale / window_height

    # calcolo i delta
    y_deltas = np.diff(y_positions)
    # inverto il segno dei delta
    y_deltas = y_deltas * -1

    velocities = y_deltas * meters_per_pixel * video_fps

    return velocities

def save_plot(velocities, path):
        
    # Plot the velocity graph
    plt.figure(figsize=(10, 5))
    plt.plot(velocities, label="Velocity (meters/second)", color="b", marker="o")
    plt.xlabel("Frame Index")
    plt.ylabel("Velocity (meters/second)")

    # Limit the y-axis values between -2 and 2
    plt.ylim(-2, 2)

    plt.title("Velocity of Y Movement")
    plt.legend()
    plt.grid(True)
    plt.savefig(str(path))


###
### PAGE LAYOUT
###

st.title("Bar Path Tracker")

# creazione delle colonne
left_col, right_col = st.columns(2)

uploaded_file = None
processed_video_path = None
processed_plot_path = None

with left_col:
    uploaded_file = st.file_uploader(
        "Scegli un file video (.mp4 / .mov)",
        type=["mp4", "mov"]
    )

    if uploaded_file is not None:

        st.info("Elaborazione del video in corso...")
        progress_bar = st.progress(0)

        # definisci il percorso del file video
        save_path = create_video_copy(uploaded_file.name)
       
        # elaborazione del video con OpenCV
        cap = cv2.VideoCapture(save_path)

        if cap.isOpened():
            processed_video_path, processed_plot_path = process_video(cap)

            # assicurati che il file sia completamente salvato
            time.sleep(5)  # pausa per dare tempo di completare la scrittura

            progress_bar.empty()

        else:
            st.error("Errore nell'apertura del file video.")

with right_col:
    if uploaded_file is not None:
        st.subheader("Video Originale")
        st.video(save_path)

lower_left_col, lower_right_col = st.columns(2)

with lower_left_col:
    if processed_video_path:
        st.subheader("Video Elaborato")
        st.video(processed_video_path)

with lower_right_col:
    if processed_plot_path:
        st.subheader("Grafico della Velocità")
        st.image(processed_plot_path)