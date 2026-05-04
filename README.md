# 🧠 VisionGuard Health: AI-Based Patient Monitoring & Alert System


## 🧠 Overview

VisionGuard Health is an AI-powered real-time monitoring system designed for healthcare environments.
It enhances traditional surveillance by adding intelligence for detecting critical events such as intrusions, abnormal motion, and patient falls.



## 🚀 Features

* 👤 Face Recognition (Patient Identification)
* 🚨 Intruder Detection (Unknown Person Alert)
* 🎯 Motion Detection
* ⚠️ Temporal Fall Detection (Improved Accuracy)
* 🔊 Audio Recording + 🎥 Video Capture
* 📩 Telegram Alert System (Real-Time Notifications)
* 🧾 Event Logging (CSV)
* ➕ Real-Time Patient Enrollment (Press `n`)



## ⚙️ How It Works

1. Captures live video feed from camera
2. Detects faces and matches with known patients
3. Tracks motion and posture changes
4. Identifies fall events using temporal logic
5. Records audio + video evidence
6. Sends alerts via Telegram

---

## 🛠️ Tech Stack

* Python
* OpenCV
* face-recognition
* NumPy
* SoundDevice
* SciPy
* Requests



## 🧪 Setup & Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/visionguard-health.git
cd visionguard-health
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the System

```bash
python main.py
```



## 🎮 Controls

* Press **`n`** → Add new patient (real-time enrollment)
* Press **`ESC`** → Exit system


## 🔐 Configuration

Before running, update these in code:

```python
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
```



## 📂 Project Structure

```
VisionGuard/
├── main.py
├── known_faces/
├── requirements.txt
├── README.md
└── assets/ (optional: images, demo gif)
```



## ⚠️ Important Notes

* Ensure proper lighting for better face detection
* Microphone permission required for audio recording
* FFmpeg must be installed for audio-video merging



## 🚀 Future Enhancements

* Web dashboard for monitoring
* Mobile app integration
* Database (SQL) for patient management
* YOLO-based human detection
* Pose-based advanced fall detection



## 💡 Key Insight

> This system transforms passive surveillance into intelligent, event-driven monitoring.


## 👨‍💻 Author

AQUIB ASGHAR



## ⭐ Support

If you like this project, give it a ⭐ on GitHub!
