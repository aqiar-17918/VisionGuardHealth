
import cv2
import face_recognition
import os
import time
import requests
import csv
import threading
from collections import deque
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import subprocess

# CONFIG 
KNOWN_FACES_DIR = "known_faces"
TOLERANCE = 0.5
LOG_FILE = "log.csv"
ALERT_COOLDOWN = 10

BUFFER_SECONDS = 5
FPS = 20
TELEGRAM_TOKEN = "YOUR_TOKEN"
CHAT_ID = "your_chat_id"
#  INIT 
prev_gray = None
frame_buffer = deque(maxlen=BUFFER_SECONDS * FPS)

fall_history = deque(maxlen=10)
FALL_RATIO_THRESHOLD = 1.2
FALL_CONFIRM_FRAMES = 5

known_encodings = []
known_names = []

#  LOAD FACES 
for file in os.listdir(KNOWN_FACES_DIR):
    if file.startswith("."):
        continue

    path = os.path.join(KNOWN_FACES_DIR, file)
    img = face_recognition.load_image_file(path)
    enc = face_recognition.face_encodings(img)

    if enc:
        known_encodings.append(enc[0])
        known_names.append(os.path.splitext(file)[0])

#  AUDIO 
def record_audio(filename, duration=5, fs=44100):
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, audio)

# MERGE
def merge_audio_video(video_path, audio_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

#  TELEGRAM 
def send_telegram_video(path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
    try:
        with open(path, "rb") as vid:
            requests.post(url, data={"chat_id": CHAT_ID}, files={"video": vid})
    except Exception as e:
        print("[ERROR TELEGRAM]", e)

#  LOG 
def log_entry(name, status, file):
    exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["Name", "Time", "Status", "File"])
        writer.writerow([name, time.strftime("%Y-%m-%d %H:%M:%S"), status, file])

#  SAVE VIDEO 
def save_video(frames, filename):
    if not frames:
        return None

    h, w, _ = frames[0].shape
    out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (w, h))

    for f in frames:
        out.write(f)

    out.release()
    return filename

#  ALERT
def handle_alert(reason):
    timestamp = int(time.time())

    video_file = f"{reason}_{timestamp}.mp4"
    audio_file = f"{reason}_{timestamp}.wav"
    final_file = f"{reason}_{timestamp}_final.mp4"

    frames = list(frame_buffer)
    video_path = save_video(frames, video_file)

    audio_thread = threading.Thread(target=record_audio, args=(audio_file, 5))
    audio_thread.start()
    audio_thread.join()

    final_path = merge_audio_video(video_path, audio_file, final_file)

    send_telegram_video(final_path)
    log_entry(reason, "Alert", final_path)

#  REGISTER PATIENT 
def register_new_face(frame):
    global known_encodings, known_names

    name = input("Enter Patient Name: ")

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, faces)

    if len(encodings) > 0:
        known_encodings.append(encodings[0])
        known_names.append(name)

        filename = f"{KNOWN_FACES_DIR}/{name}_{int(time.time())}.jpg"
        cv2.imwrite(filename, frame)

        print(f"[INFO] {name} added successfully!")
    else:
        print("[ERROR] No face detected!")

#  CAMERA 
cap = cv2.VideoCapture(0)
last_alert_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_buffer.append(frame.copy())

    #  MOTION 
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if prev_gray is not None:
        diff = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        motion_score = np.sum(thresh)

        if motion_score > 500000:
            cv2.putText(frame, "Motion", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    prev_gray = gray

    #  FACE 
    small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    faces = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, faces)

    for (top, right, bottom, left), enc in zip(faces, encodings):

        distances = face_recognition.face_distance(known_encodings, enc)

        name = "Unknown"
        if len(distances) > 0:
            idx = np.argmin(distances)
            if distances[idx] < TOLERANCE:
                name = known_names[idx]

        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        # FALL
        width = right - left
        height = bottom - top

        if height != 0:
            ratio = width / height
            posture = 1 if ratio > FALL_RATIO_THRESHOLD else 0
            fall_history.append(posture)

            if len(fall_history) == 10:
                first = list(fall_history)[:5]
                second = list(fall_history)[5:]

                if sum(first) < 2 and sum(second) > FALL_CONFIRM_FRAMES:
                    cv2.putText(frame, "FALL!", (left, bottom + 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                    if time.time() - last_alert_time > ALERT_COOLDOWN:
                        threading.Thread(target=handle_alert, args=("Fall",)).start()
                        last_alert_time = time.time()

        #  INTRUDER
        if name == "Unknown":
            if time.time() - last_alert_time > ALERT_COOLDOWN:
                threading.Thread(target=handle_alert, args=("Intruder",)).start()
                last_alert_time = time.time()
        else:
            log_entry(name, "Authorized", "-")

        cv2.putText(frame, name, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow("AI Healthcare Monitoring", frame)

    key = cv2.waitKey(1) & 0xFF

    # 🔥 REAL-TIME PATIENT ADD
    if key == ord('n'):
        print("[INFO] Add new patient")
        register_new_face(frame)

    elif key == 27:
        break

cap.release()
cv2.destroyAllWindows()