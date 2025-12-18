import os
import time
import sys
import json

print("🚀 Memuat Library ADB...")

# === PERUBAHAN DI SINI: TIDAK ADA LAGI TRY/EXCEPT ===
# Kita langsung panggil library-nya karena Dokter bilang sudah OK.
from adb_shell.auth.keygen import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.handle.tcp_handle import TcpHandle
from adb_shell.transport.tcp_transport import TcpTransport

# ================= KONFIGURASI =================
BASE_PACKAGES = [
    "com.roblox.client",
    "com.roblox.clienu",
    "com.roblox.clienv",
    "com.roblox.clienw"
]

ADB_DEVICE = None
CONFIG_FILE = "config_manager.json"
PACKAGE_SETTINGS = {}

# ================= BAGIAN ADB (PAIRING & CONNECT) =================

def get_rsa_signer():
    adbkey = 'adbkey'
    if not os.path.exists(adbkey):
        print("🔑 Membuat kunci identitas baru...")
        keygen(adbkey)
    
    with open(adbkey) as f: priv = f.read()
    with open(adbkey + '.pub') as f: pub = f.read()
    return PythonRSASigner(pub, priv)

def menu_koneksi():
    global ADB_DEVICE
    print("\n--- MENU KONEKSI ADB (PYTHON) ---")
    print("1. PAIRING BARU (Wajib untuk pertama kali)")
    print("2. LANGSUNG CONNECT (Jika IP Connect sudah ada)")
    pilihan = input("Pilih menu (1/2): ").strip()

    signer = get_rsa_signer()

    if pilihan == "1":
        print("\n[MODE PAIRING]")
        print("Buka Developer Options -> Wireless Debugging -> Pair with code")
        target = input("Masukkan IP:PORT (dari popup pairing): ").strip()
        code = input("Masukkan Kode 6 Digit: ").strip()
        
        try:
            ip, port = target.split(":")
            transport = TcpTransport(ip, int(port))
            print("⏳ Mengirim kode pairing...")
            transport.connect()
            success = transport.pair(code)
            transport.close()
            
            if success:
                print("✅ PAIRING SUKSES!")
                print("Sekarang kita lanjut connect ke Port Utama...")
                # Lanjut ke logika connect di bawah
            else:
                print("❌ Pairing Gagal (Salah kode/IP).")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error Pairing: {e}")
            sys.exit(1)

    # === LOGIKA CONNECT ===
    print("\n[MODE CONNECT]")
    print("Lihat menu depan Wireless Debugging (IP & Port berubah).")
    target = input("Masukkan IP:PORT (dari halaman depan): ").strip()
    
    try:
        if not target: target = "127.0.0.1:5555"
        ip, port = target.split(":")
        
        ADB_DEVICE = TcpTransport(ip, int(port))
        ADB_DEVICE.connect(rsa_keys=[signer], auth_timeout_s=5)
        print("✅ TERHUBUNG KE ANDROID!")
    except Exception as e:
        print(f"❌ Gagal Connect: {e}")
        sys.exit(1)

# ================= FUNGSI SISTEM GAME =================

def adb_shell(command):
    try:
        return ADB_DEVICE.shell(command)
    except:
        return ""

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

def force_close(pkg):
    clean = get_pkg_name(pkg)
    print(f"    💀 Mematikan paksa: {clean}")
    adb_shell(f"am force-stop {clean}")

def launch_game(pkg, specific_place_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    if not specific_place_id: return

    final_uri = ""
    if vip_link_input and "http" in vip_link_input:
        final_uri = vip_link_input.strip()
    elif vip_link_input:
        final_uri = f"roblox://placeId={specific_place_id}&privateServerLinkCode={vip_link_input.strip()}"
    else:
        final_uri = f"roblox://placeId={specific_place_id}"

    print(f"    🚀 Meluncurkan {clean}...")
    # Perintah sakti Windowing Mode 5 (Float)
    cmd = f"am start --user 0 --windowingMode 5 --activity-multiple-task --activity-new-task -a android.intent.action.VIEW -d \"{final_uri}\" {clean}"
    adb_shell(cmd)

def jalankan_siklus(pkg):
    force_close(pkg)
    time.sleep(1)
    # Pastikan settings ada
    if pkg in PACKAGE_SETTINGS:
        launch_game(pkg, PACKAGE_SETTINGS[pkg]['place_id'], PACKAGE_SETTINGS[pkg]['vip_code'])
    else:
        print(f"⚠️ Skip {pkg} (Belum disetting)")
        return
        
    print("⏳ Tunggu 25 detik...")
    time.sleep(25)

# ================= SETUP & MAIN =================

def setup_game_config():
    global PACKAGE_SETTINGS
    print("\n--- SETUP GAME ---")
    pid = input("Masukkan Place ID: ").strip()
    vip = input("Link VIP (Enter jika kosong): ").strip()
    for pkg in BASE_PACKAGES:
        PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

def main():
    menu_koneksi()
    setup_game_config()
    
    print("\n[STARTING] Memulai semua akun...")
    for pkg in BASE_PACKAGES:
        jalankan_siklus(pkg)
        
    print("\n✅ Selesai.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStop.")
