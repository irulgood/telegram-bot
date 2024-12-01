#!/bin/bash

# Menentukan URL repositori GitHub Anda
REPO_URL="https://github.com/username/repository_name.git"  # Gantilah dengan URL repositori Anda

# Menentukan direktori tempat repositori akan di-clone
INSTALL_DIR="$HOME/telegram-bot"  # Ganti jika Anda ingin direktori lain

# Memeriksa apakah git sudah terinstal, jika belum, menginstalnya
if ! command -v git &> /dev/null; then
    echo "Git tidak ditemukan, menginstal Git..."
    sudo apt update
    sudo apt install git -y
else
    echo "Git sudah terinstal."
fi

# Memeriksa apakah Python3 sudah terinstal, jika belum, menginstalnya
if ! command -v python3 &> /dev/null; then
    echo "Python3 tidak ditemukan, menginstal Python3..."
    sudo apt install python3 -y
fi

# Memeriksa apakah pip sudah terinstal, jika belum, menginstalnya
if ! command -v pip &> /dev/null; then
    echo "pip tidak ditemukan, menginstal pip..."
    sudo apt install python3-pip -y
fi

# Membuat direktori untuk repositori jika belum ada
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Membuat direktori $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
fi

# Clone repositori dari GitHub
echo "Meng-clone repositori dari $REPO_URL..."
git clone "$REPO_URL" "$INSTALL_DIR"

# Masuk ke direktori repositori
cd "$INSTALL_DIR"

# Memastikan dependensi yang diperlukan diinstal
if [ -f "requirements.txt" ]; then
    echo "Menginstal dependensi dari requirements.txt..."
    pip install -r requirements.txt
else
    echo "Tidak ada file requirements.txt ditemukan, menginstal dependensi umum..."
    pip install python-telegram-bot requests
fi

# Menjalankan bot.py
echo "Menjalankan bot.py..."
python3 bot.py

echo "Instalasi dan eksekusi bot selesai."
