import os
import time
import subprocess
import sys

# ================= KONFIGURASI PAKET =================
# Daftar nama paket Roblox yang kamu gunakan (Clone)
BASE_PACKAGES = [
    "com.roblox.client",
    "com.roblox.clienu",
    "com.roblox.clienv",
    "com.roblox.clienw"
]

# Penyimpanan Setting
PACKAGE_SETTINGS = {}

# Daftar Paket yang AKTIF (Punya ID Game/Link)
ACTIVE_PACKAGES = []

# Status Cooldown (Agar tidak spam launch saat baru dibuka)
LAUNCH_COOLDOWN = {}

# ================= FUNGSI SISTEM =================

def get_pkg_name(pkg):
    """Membersihkan nama paket jika ada format folder"""
    return pkg.split('/')[0].strip()

def is_app_running(pkg):
    """Cek apakah aplikasi hidup menggunakan pidof"""
    clean_pkg = get_pkg_name(pkg)
    try:
        # Cek PID, jika output ada berarti jalan
        subprocess.check_output(["pidof", clean_pkg])
        return True
    except subprocess.CalledProcessError:
        return False

def force_close(pkg):
    """Mematikan paksa aplikasi"""
    clean = get_pkg_name(pkg)
    try:
        os.system(f"am force-stop {clean} > /dev/null 2>&1")
    except:
        pass

def launch_game(pkg, specific_place_id=None, vip_link_input=None):
    """Meluncurkan Game dengan Link Inject atau Place ID"""
    clean = get_pkg_name(pkg)
    
    # Ambil setting dari memori jika tidak dipassing argumen
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    final_uri = ""
    
    # === LOGIKA LINK INJECT (PRIORITAS UTAMA) ===
    # Jika input terdeteksi sebagai Link HTTP/HTTPS (Link Share Private Server)
    if vip_link_input and ("http" in vip_link_input or "roblox.com" in vip_link_input):
        final_uri = vip_link_input.strip()
        print(f"    [🚀] Inject Link Private Server...")
        
    # Jika input hanya Place ID (Public Server)
    elif specific_place_id:
        final_uri = f"roblox://placeId={specific_place_id}"
        print(f"    [🎲] Masuk ke Public Server (ID: {specific_place_id})...")
        
    else:
        print(f"    [X] Gagal: Tidak ada Link atau ID untuk {clean}")
        return

    # === EKSEKUSI INTENT ===
    # Flag -d untuk data link, paket di akhir agar tidak buka browser
    cmd = f"am start --user 0 -a android.intent.action.VIEW -d \"{final_uri}\" {clean}"
    
    try:
        os.system(f"{cmd} > /dev/null 2>&1")
        # Set cooldown 15 detik agar monitoring tidak mendeteksi crash palsu saat loading
        LAUNCH_COOLDOWN[pkg] = time.time() + 15 
        print(f"    [✓] Perintah terkirim ke {clean}")
    except Exception as e:
        print(f"    [!] Error Launch: {e}")

# ================= INPUT MENU =================

def setup_configuration():
    print("\n--- PENGATURAN MODE GAME ---")
    print("1. SETTING SERAGAM (Satu Link untuk Semua Akun)")
    print("2. SETTING BEDA-BEDA (Tiap Akun Link/Game Sendiri)")
    mode = input("Pilih Mode (1/2): ").strip()

    if mode == "1":
        print("\n[MODE SERAGAM]")
        print("Masukkan Link Private Server (https://...) ATAU Place ID:")
        input_data = input("Link/ID: ").strip()
        
        # Deteksi apakah ini Link atau ID Angka
        pid = ""
        vip = ""
        
        if "http" in input_data:
            vip = input_data # Input dianggap Link
            pid = "LINK_MODE" # Dummy ID agar lolos filter
        else:
            pid = input_data # Input dianggap ID Angka
        
        for pkg in BASE_PACKAGES:
            PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
            
    else:
        print("\n[MODE INDIVIDUAL]")
        print("Tip: Kosongkan jika ingin menonaktifkan akun tersebut.")
        for pkg in BASE_PACKAGES:
            clean = get_pkg_name(pkg)
            print(f"\nSetting untuk {clean}:")
            print("Masukkan Link Private Server (https://...) ATAU Place ID:")
            input_data = input("  > Link/ID: ").strip()
            
            pid = ""
            vip = ""
            
            if not input_data:
                pid = "" # Kosong berarti skip
            elif "http" in input_data:
                vip = input_data
                pid = "LINK_MODE"
            else:
                pid = input_data
            
            PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    return

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER + ANTI CRASH MONITOR ===")
    
    setup_configuration()
    
    # 1. PELUNCURAN AWAL
    print(f"\n[PHASE 1] INITIAL LAUNCH")
    
    for pkg in BASE_PACKAGES:
        settings = PACKAGE_SETTINGS.get(pkg)
        
        # Filter akun yang tidak di-setting
        if not settings or not settings['place_id']:
            continue 
        
        # Masukkan ke daftar aktif
        ACTIVE_PACKAGES.append(pkg)
        
        print(f"\n--> Memproses: {get_pkg_name(pkg)}")
        force_close(pkg)
        time.sleep(1)
        launch_game(pkg)
        
    if not ACTIVE_PACKAGES:
        print("❌ Tidak ada akun yang dijalankan.")
        return

    print("\n" + "="*50)
    print(f"✅ MONITORING AKTIF UNTUK {len(ACTIVE_PACKAGES)} AKUN.")
    print("   Script akan mengecek status aplikasi setiap 5 detik.")
    print("   Tekan CTRL+C untuk berhenti.")
    print("="*50)

    # 2. MONITORING LOOP (ANTI FORCE CLOSE)
    try:
        while True:
            time.sleep(5) # Cek setiap 5 detik
            
            # Cek setiap paket yang aktif
            for pkg in ACTIVE_PACKAGES:
                # Cek apakah sedang masa cooldown (baru diluncurkan)?
                if pkg in LAUNCH_COOLDOWN:
                    if time.time() < LAUNCH_COOLDOWN[pkg]:
                        continue # Skip pengecekan, masih loading awal
                    else:
                        del LAUNCH_COOLDOWN[pkg] # Hapus dari cooldown

                # Cek apakah aplikasi mati?
                if not is_app_running(pkg):
                    print(f"\n[⚠️] CRASH DETECTED: {get_pkg_name(pkg)}")
                    print(f"    -> Meluncurkan ulang otomatis...")
                    launch_game(pkg)
                
            # Print detak jantung (opsional, biar tau script jalan)
            # sys.stdout.write(".")
            # sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n🛑 Script Dihentikan Pengguna.")

if __name__ == "__main__":
    main()
