# Hardware Copilot

Eigenständiges Desktop-Tool für Hardware-Entwicklung auf Basis von:

- Tauri
- React
- TypeScript
- FastAPI

---

# 1. Voraussetzungen installieren

## Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  nodejs \
  npm \
  libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libxdo-dev \
  libssl-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev
```

---

# 2. Rust installieren

Falls noch nicht vorhanden:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

---

# 3. Projekt vorbereiten (nur beim ersten Mal oder auf neuem Rechner)

```bash
./bootstrap.sh
```

Dieses Skript erledigt:

- Python virtual environment erzeugen
- Python-Abhängigkeiten installieren
- Node-Abhängigkeiten installieren

---

# 4. Entwicklung starten

```bash
./start_dev.sh
```

Dieses Skript startet:

- FastAPI Backend
- Tauri Frontend

---

# 5. Einzelstart falls nötig

## Backend

```bash
./start_backend.sh
```

## Tauri

```bash
./start_tauri.sh
```

---

# 6. Projektstruktur

```text
hardware-copilot/
├── backend/
│   ├── app/
│   │   └── main.py
│   ├── requirements.txt
│   └── .venv/
│
├── src/
├── src-tauri/
│
├── bootstrap.sh
├── start_backend.sh
├── start_tauri.sh
├── start_dev.sh
│
├── package.json
├── package-lock.json
├── README.md
└── .gitignore
```

---

# 7. Auf neuem Rechner weiterarbeiten

```bash
git clone <repo>
cd hardware-copilot
./bootstrap.sh
./start_dev.sh
```

---

# 8. Versionsprüfung

```bash
python3 --version
node -v
npm -v
rustc --version
cargo --version
```