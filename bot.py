import json
import random
import string
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Tentukan ID pengguna admin (ganti dengan ID Anda)
ADMIN_USER_ID = 123456789  # Ganti dengan ID Anda

# Load API keys dari file
def load_api_keys():
    try:
        with open("api_keys.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_api_keys(api_keys):
    with open("api_keys.json", "w") as file:
        json.dump(api_keys, file, indent=4)

API_KEYS = load_api_keys()

# Fungsi untuk menambahkan API Key
async def add_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_USER_ID:
        await update.message.reply_text("Anda tidak memiliki izin untuk menambahkan API key.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Format yang benar: /add_key <nama_akun> <api_key>")
        return
    
    account_name = context.args[0]
    api_key = context.args[1]
    
    # Tambahkan API key ke dictionary
    API_KEYS[account_name] = api_key
    
    # Simpan ke file JSON
    save_api_keys(API_KEYS)

    await update.message.reply_text(f"API Key untuk akun {account_name} berhasil ditambahkan!")

# Fungsi untuk membuat droplet dengan password yang ditentukan
async def create_droplet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_USER_ID:
        await update.message.reply_text("Anda tidak memiliki izin untuk membuat droplet.")
        return

    if len(context.args) != 5:
        await update.message.reply_text("Format yang benar: /create_droplet <nama_akun> <nama_droplet> <ukuran> <data_center> <password>")
        return
    
    account_name = context.args[0]
    droplet_name = context.args[1]
    size = context.args[2]  # Ukuran droplet seperti "s-1vcpu-1gb"
    region = context.args[3]  # Data center region seperti "nyc3"
    password = context.args[4]  # Password yang diinginkan
    
    api_key = API_KEYS.get(account_name)
    if not api_key:
        await update.message.reply_text("API Key tidak ditemukan untuk akun tersebut.")
        return
    
    headers = {"Authorization": f"Bearer {api_key}"}
    droplet_data = {
        "name": droplet_name,
        "region": region,
        "size": size,
        "image": "ubuntu-20-04-x64",  # Anda bisa mengganti ini dengan image lainnya
        "ssh_keys": [],  # Anda bisa menambahkan SSH key jika diperlukan
        "backups": False,
        "ipv6": True,
        "user_data": f"""#cloud-config
users:
  - name: root
    passwd: {password}
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    lock_passwd: false
    chpasswd: { expire: False }
""",
        "private_networking": None,
        "volumes": [],
        "tags": ["telegram-bot"]
    }

    response = requests.post("https://api.digitalocean.com/v2/droplets", headers=headers, json=droplet_data)
    
    if response.status_code == 202:
        droplet = response.json()['droplet']
        
        # Mendapatkan detail droplet yang baru dibuat
        droplet_id = droplet['id']
        droplet_name = droplet['name']
        droplet_ip = droplet['networks'][0]['ip_address'] if droplet.get('networks') else "Tidak tersedia"
        droplet_size = droplet['size']
        droplet_region = droplet['region']['name']
        
        # Kirimkan detail droplet dan password ke Telegram
        message = (
            f"Droplet {droplet_name} berhasil dibuat!\n"
            f"**Detail Droplet**:\n"
            f"- **ID**: {droplet_id}\n"
            f"- **Nama**: {droplet_name}\n"
            f"- **IP Address**: {droplet_ip}\n"
            f"- **Ukuran**: {droplet_size}\n"
            f"- **Region**: {droplet_region}\n"
            f"- **Password**: {password}\n"
            f"Silakan login dan kelola droplet Anda."
        )
        await update.message.reply_text(message)
    else:
        await update.message.reply_text(f"Gagal membuat droplet: {response.text}")

# Fungsi untuk menghapus droplet berdasarkan ID
async def delete_droplet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_USER_ID:
        await update.message.reply_text("Anda tidak memiliki izin untuk menghapus droplet.")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("Format yang benar: /delete_droplet <droplet_id>")
        return
    
    droplet_id = context.args[0]
    
    account_name = context.args[0]  # Menggunakan akun pertama dari argumen
    api_key = API_KEYS.get(account_name)
    
    if not api_key:
        await update.message.reply_text("API Key tidak ditemukan untuk akun tersebut.")
        return
    
    headers = {"Authorization": f"Bearer {api_key}"}
    delete_response = requests.delete(f"https://api.digitalocean.com/v2/droplets/{droplet_id}", headers=headers)
    
    if delete_response.status_code == 204:
        await update.message.reply_text(f"Droplet dengan ID {droplet_id} berhasil dihapus!")
    else:
        await update.message.reply_text(f"Gagal menghapus droplet: {delete_response.text}")

# Fungsi untuk menampilkan daftar droplet
async def list_droplets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_USER_ID:
        await update.message.reply_text("Anda tidak memiliki izin untuk melihat daftar droplet.")
        return

    account_name = context.args[0]  # Nama akun API yang digunakan
    api_key = API_KEYS.get(account_name)
    
    if not api_key:
        await update.message.reply_text("API Key tidak ditemukan untuk akun tersebut.")
        return
    
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://api.digitalocean.com/v2/droplets", headers=headers)
    
    if response.status_code == 200:
        droplets = response.json()['droplets']
        droplet_list = "Daftar Droplet:\n"
        for droplet in droplets:
            droplet_list += f"ID: {droplet['id']} - Nama: {droplet['name']} - IP: {droplet['networks'][0]['ip_address']}\n"
        await update.message.reply_text(droplet_list)
    else:
        await update.message.reply_text(f"Gagal mengambil daftar droplet: {response.text}")

# Fungsi untuk menampilkan sisa saldo
async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_USER_ID:
        await update.message.reply_text("Anda tidak memiliki izin untuk melihat saldo.")
        return
    
    account_name = context.args[0]  # Nama akun API yang digunakan
    api_key = API_KEYS.get(account_name)
    
    if not api_key:
        await update.message.reply_text("API Key tidak ditemukan untuk akun tersebut.")
        return
    
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://api.digitalocean.com/v2/account", headers=headers)
    
    if response.status_code == 200:
        balance = response.json()['account']['balance']
        await update.message.reply_text(f"Sisa saldo untuk akun {account_name}: ${balance}")
    else:
        await update.message.reply_text(f"Gagal mengambil saldo: {response.text}")

# Fungsi utama untuk menjalankan bot
def main():
    application = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    application.add_handler(CommandHandler("add_key", add_api_key))
    application.add_handler(CommandHandler("create_droplet", create_droplet))
    application.add_handler(CommandHandler("delete_droplet", delete_droplet))
    application.add_handler(CommandHandler("list_droplets", list_droplets))
    application.add_handler(CommandHandler("check_balance", check_balance))

    application.run_polling()

if __name__ == "__main__":
    main()
