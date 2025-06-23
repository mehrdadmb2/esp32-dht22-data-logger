# esp32-dht22-data-logger

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)  
[![PlatformIO](https://img.shields.io/badge/PlatformIO-ESP32-blue.svg)]  
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)]  
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-green.svg)]  
[![GitHub Repo Size](https://img.shields.io/github/repo-size/mehrdadmb2/esp32-dht22-data-logger.svg)]  
[![Data Files](https://img.shields.io/badge/Raw%20Data-210%20files-orange.svg)]  
[![Archive Size](https://img.shields.io/badge/esp32.rar-~~6 MB-lightgrey.svg)]  
[![Script Size](https://img.shields.io/badge/app.py-~15 KB-lightgrey.svg)]  

> 🔥 A professional system for logging, storing, and analyzing temperature & humidity data using an ESP32 + DHT22 sensor, complete with Python scripts for chart generation, a Telegram bot, and a PyQt5 GUI. 🔥

---

## 📦 Repository Structure

```text
esp32-dht22-data-logger/
├── Data/
│   └── Raw/
│       └── esp32.rar                 # ⬇️ Contains 210 raw .xlsx files
├── LICENSE                            # 📄 MIT License
├── README.md                          # 📖 This file
├── scripts/
│   └── rename_files.py               # 🔄 Auto-rename raw files
├── src/
│   ├── esp32/
│   │   ├── platformio.ini            # ⚙️ PlatformIO config
│   │   └── main.ino                  # ✏️ Your ESP32 sketch
│   └── python/
│       ├── app.py                    # 🐍 Main Python app (bot + GUI)
│       └── requirements.txt          # 📦 Python dependencies
````

---

## ✨ Features

* 🌡️ **Real-time** local & internet temperature/humidity
* 💲 Live USD/IRR & Gold price tracking
* 📶 Ping latency & Wi-Fi device scanning
* 📥 **210** raw Excel files (`.xlsx`)
* 📊 Python data processing & chart generation
* 🤖 Telegram Bot for remote queries & file delivery
* 🖥️ PyQt5 GUI with dark mode & live log viewer
* 🔄 Auto-rename script for raw data files

---

## 🛠️ Hardware Requirements

1. **ESP32 Dev Board**
2. **DHT22** temperature/humidity sensor
3. **OLED I2C 128×32** display
4. **LED 1.5 V** status indicator
5. Jumper wires & breadboard

*Wiring* → see `src/esp32/main.ino` comments or your own schematic.

---

## ⚙️ Software Setup

### 1. Prepare Raw Data

```bash
# Unpack your 210 Excel files:
cd Data/Raw
unzip esp32.rar   # adjust if .zip; for .rar use your archiver
```

### 2. Flash ESP32 Firmware

```bash
cd src/esp32
# If using Arduino IDE:
#  - Open main.ino
#  - Replace placeholders:
#      WIFI_SSID → "YOUR_WIFI_SSID"
#      WIFI_PASSWORD → "YOUR_WIFI_PASSWORD"
#  - Save & Upload

# If using PlatformIO:
pio run --target upload
```

> **Placeholders in `main.ino`:**
>
> ```cpp
> #define WIFI_SSID     "YOUR_WIFI_SSID"
> #define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
> // ...
> const char* BOT_TOKEN       = "YOUR_TELEGRAM_BOT_TOKEN";
> const char* ESP32_DATA_URL  = "http://YOUR_ESP32_IP/data";
> ```

### 3. Install Python Dependencies

```bash
cd src/python
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Python App

* Open `src/python/app.py`
* Replace:

  * `BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"`
  * `ESP32_DATA_URL = "http://YOUR_ESP32_IP/data"`
  * `OUTPUT_DIRECTORY = "../Data/Raw"`  *(or your desired path)*

---

## 🚀 Quick Start

1. **Clone the repo**

   ```bash
   git clone https://github.com/mehrdadmb2/esp32-dht22-data-logger.git
   cd esp32-dht22-data-logger
   ```

2. **Unpack data archive**

   ```bash
   cd Data/Raw && unrar x esp32.rar && cd ../..
   ```

3. **Flash ESP32** (see step 2)

4. **Run Python App**

   ```bash
   cd src/python
   python app.py
   ```

5. **Interact**

   * **Web UI** → Browse `http://YOUR_ESP32_IP/`
   * **Telegram Bot**:

     * `/esp32` → Latest JSON data
     * `/esp32_all` → Today’s Excel file
     * `/chart` → Chart selection menu
     * `/admin` → Admin panel

---

## 📊 Usage Details

* **Data Logging**: Python thread fetches every 60 s and appends to `data_log_YYYY-MM-DD.xlsx`.
* **Chart Generation**: On-demand or auto every 5 s in GUI (1 h, 1 d, 1 w, 1 m).
* **Rename Script**:

  ```bash
  python ../../scripts/rename_files.py
  ```

  Standardizes raw filenames to `YYYYMMDD_HHMMSS.xlsx`.

---

## 🤝 Contributing

1. Fork this repo 👷
2. Create a branch: `git checkout -b feature/my-feature` 🚀
3. Commit: `git commit -m "Add awesome feature"` 📝
4. Push: `git push origin feature/my-feature` 📤
5. Open a Pull Request ✨

---

## 📝 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

⭐️ If you find this project useful, please give it a ⭐️ on GitHub!

```yaml
# Meta
repository: https://github.com/mehrdadmb2/esp32-dht22-data-logger
```

```
```
