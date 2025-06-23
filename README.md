## 📁 Repository Structure

```
esp32-dht22-data-logger/
├── .gitignore
├── LICENSE
├── README.md
│
├── docs/
│   ├── hardware_setup.md
│   └── wiring_diagram.png
│
├── hardware/
│   └── schematics/
│       └── esp32_dht22_schematic.svg
│
├── src/
│   ├── esp32/
│   │   ├── platformio.ini
│   │   └── src/
│   │       └── main.cpp
│   │
│   └── python/
│       ├── app.py
│       ├── process_data.py
│       └── requirements.txt
│
├── data/
│   ├── raw/
│   │   ├── 20250601_083000.xlsx
│   │   └── … (۲۱۰ فایل با الگوی YYYYMMDD_HHMMSS.xlsx)
│   └── processed/
│
└── scripts/
    └── rename_files.py
```

---

## 📝 `README.md`

````markdown
# esp32-dht22-data-logger

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PlatformIO](https://img.shields.io/badge/PlatformIO-ESP32-blue.svg)]
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)]
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-green.svg)]

> 🔥 A professional system for logging, storing, and analyzing temperature & humidity data using an ESP32 + DHT22 sensor, complete with Python scripts for chart generation, a Telegram bot, and a PyQt5 GUI. 🔥

---

## 📌 Table of Contents

- [✨ Features](#-features)  
- [📦 Repo Structure](#-repo-structure)  
- [🛠️ Hardware Requirements](#️-hardware-requirements)  
- [⚙️ Software Setup](#️-software-setup)  
- [🚀 Quick Start](#-quick-start)  
- [📊 Usage](#-usage)  
- [🎨 Screenshots](#-screenshots)  
- [🤝 Contributing](#-contributing)  
- [📝 License](#-license)

---

## ✨ Features

- 🌡️ **Real-time** local & internet temperature/humidity  
- 💲 Live USD/IRR & Gold price 📈  
- 📶 Ping monitoring & Wi-Fi device scan  
- 📥 **210** raw Excel files logging  
- 📊 **Python** data processing & chart generation  
- 🤖 **Telegram Bot** for remote queries  
- 🖥️ **PyQt5 GUI** with dark mode & live logs  
- 🔄 Auto-rename & organized folder structure  

---

## 📦 Repo Structure

```text
esp32-dht22-data-logger/
├── docs/             # 📖 Documentation & diagrams
├── hardware/         # 🔧 Schematics
├── src/
│   ├── esp32/        # 🖥️ ESP32 firmware (PlatformIO)
│   └── python/       # 🐍 Python app (data+bot+GUI)
├── data/
│   ├── raw/          # 📂 210 raw .xlsx files
│   └── processed/    # 📊 Processed outputs
└── scripts/
    └── rename_files.py  # 🔄 Auto rename raw files
````

---

## 🛠️ Hardware Requirements

* **ESP32 Dev Board**
* **DHT22** temperature/humidity sensor
* **OLED I2C 128×32** display
* **LED 1.5 V** status indicator
* Jumper wires & breadboard

See [docs/hardware\_setup.md](docs/hardware_setup.md) and [docs/wiring\_diagram.png](docs/wiring_diagram.png) for full wiring.

---

## ⚙️ Software Setup

### 1. ESP32 Firmware

```bash
cd src/esp32
# Open in PlatformIO (VSCode) or:
pio run --target upload
```

* Edit `platformio.ini` to set your `upload_port`.
* Replace `WIFI_SSID` / `WIFI_PASSWORD` in `main.cpp`.

### 2. Python App

```bash
cd src/python
pip install -r requirements.txt
python app.py
```

* Replace `BOT_TOKEN` in `app.py` with your Telegram bot token.
* Adjust `ESP32_DATA_URL` if your ESP32 IP changes.

### 3. Data Folder

* Raw logs: `data/raw/YYYYMMDD_HHMMSS.xlsx`
* Processed outputs: `data/processed/`

Rename old files with:

```bash
python ../scripts/rename_files.py
```

---

## 🚀 Quick Start

1. **Clone Repo**

   ```bash
   git clone https://github.com/mehrdadmb2/esp32-dht22-data-logger.git
   cd esp32-dht22-data-logger
   ```

2. **Flash ESP32**

   * Connect board
   * `pio run --target upload`

3. **Run Python App**

   ```bash
   cd src/python
   pip install -r requirements.txt
   python app.py
   ```

4. **Interact**

   * Visit `http://<ESP32_IP>/` for web UI
   * Chat with your bot:

     * `/esp32` → Latest data
     * `/esp32_all` → Today’s Excel
     * `/chart` → Chart menu
     * `/admin` → Admin panel

---

## 📊 Usage

* **Web Dashboard**: auto-refresh every 5 s, switch pages with button.
* **Telegram Bot**: remote queries & file delivery.
* **GUI**: live charts (1h, 1d, 1w, 1m) + real-time logs.

---

## 🎨 Screenshots

<p float="left">
  <img src="docs/screenshot_web.png" width="45%" />
  <img src="docs/screenshot_gui.png" width="45%" />
</p>

---

## 🤝 Contributing

1. Fork it 🍴
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to branch (`git push origin feature/fooBar`)
5. Create a new Pull Request 🚀

---

## 📝 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

```

---

Feel free to **copy** this `README.md` into your repo, tweak any links or badges, and you’re all set! 🚀
```
