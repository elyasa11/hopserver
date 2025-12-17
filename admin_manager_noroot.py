import os
import time
import subprocess
import json

# ================= KONFIGURASI PAKET =================
BASE_PACKAGES = [
    "com.roblox.client",
    "com.roblox.clienu",
    "com.roblox.clienv",
    "com.roblox.clienw"
]

# Variabel Global
PACKAGE_SETTINGS = {}
ACTIVE_PACKAGES = []
CONFIG_FILE = "config_manager.json"

# ================= FUNGSI SISTEM (INTI) =================

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

# FUNGSI UNTUK MEMATIKAN PAKSA (Sangat Penting untuk Restart)
def force_kill_app(pkg):
    clean = get_pkg_name(pkg)
    try:
        # Kita bom dengan 2 metode agar benar-benar mati dari RAM
        os.system(f"am force-stop {clean} > /dev/null 2>&1")
        time.sleep(1) 
        os.system(f"killall {clean} > /dev/null 2>&1")
    except:
        pass

# FUNGSI SATU PINTU (Dipakai Awal & Restart sama persis)
def eksekusi_akun(pkg):
    clean_pkg = get_pkg_name(pkg)
    
    # 1. Cek Data
    if pkg not in PACKAGE_SETTINGS:
        return False
        
    place_id = PACKAGE_SETTINGS[pkg]['place_id']
    vip_input = PACKAGE_SETTINGS[pkg]['vip_code']
    
    if not place_id:
        return False

    # 2. PROSES LINK (Agar tidak nyasar ke Public/Home)
    final_uri = ""
    tipe_server = ""
    vip_clean = vip_input.strip()

    # Logika Link: Ubah HTTPS jadi roblox:// agar AM START mau membacanya
    if vip_clean == "":
        final_uri = f"roblox://placeId={place_id}"
        tipe_server = "🎲 Public Server"
    elif "privateServerLinkCode=" in vip_clean:
        # Ambil KODE-nya saja dari link panjang
        try:
            code = vip_clean.split("privateServerLinkCode=")[1].split("&")[0]
            final_uri = f"roblox://placeId={place_id}&privateServerLinkCode={code}"
            tipe_server = "🔗 Private Link (Fixed)"
        except:
            final_uri = vip_clean # Fallback
    else:
        # Asumsi user memasukkan kode pendek atau link share
        if "http" in vip_clean:
             # Link share susah, kita coba raw tapi biasanya gagal
             final_uri = vip_clean 
             tipe_server = "⚠️ Link Raw (Cek Lagi)"
        else:
             # Kode VIP pendek
             final_uri = f"roblox://placeId={place_id}&privateServerLinkCode={vip_clean}"
             tipe_server = "🔒 Private Code"

    # 3. PROSES MATIKAN LAMA (HARD KILL)
    # Ini kunci agar restart tidak diam di Home
    print(f"   -> 🛑 Mematikan paksa {clean_pkg}...")
    force_kill_app(pkg)
    
    # JEDA PENTING: Beri waktu HP membuang cache aplikasi (3-5 detik)
    # Jika terlalu cepat, Android akan menganggap aplikasi masih jalan -> Masuk Home
    time.sleep(4) 

    # 4. PELUNCURAN
    print(f"   -> 🚀 Meluncurkan: {tipe_server}")
    # Flag --activity-clear-task wajib agar Roblox reload dari nol
    cmd = f"am start --user 0 -a android.intent.action.VIEW -d \"{final_uri}\" --activity-clear-task {clean_pkg}"
    os.system(f"{cmd} > /dev/null 2>&1")
    
    # Jeda agar stabil sebelum lanjut ke akun berikutnya
    print(f"   ⏳ Menunggu loading game...")
    time.sleep(20) 
    
    return True

# ================= MENU INPUT & SAVE =================

def load_last_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_current_config(restart_time):
    data = {
        "restart_seconds": restart_time,
        "packages": PACKAGE_SETTINGS
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def setup_configuration():
    global PACKAGE_SETTINGS
    saved_data = load_last_config()
    loaded = False
    
    if saved_data:
        print(f"\n📂 Data lama ditemukan.")
        if input("Pakai data lama? (y/n): ").lower() == 'y':
            PACKAGE_SETTINGS = saved_data['packages']
            loaded = True

    if not loaded:
        print("\n--- SETUP BARU ---")
        mode = input("1. Semua Sama / 2. Beda-beda: ").strip()
        if mode == "1":
            pid = input("Place ID: ").strip()
            vip = input("Link Private (Enter jika Public): ").strip()
            for pkg in BASE_PACKAGES:
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
        else:
            for pkg in BASE_PACKAGES:
                print(f"\n{get_pkg_name(pkg)}:")
                pid = input("Place ID: ").strip()
                vip = ""
                if pid: vip = input("Link Private: ").strip()
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    # Setup Waktu
    try:
        def_time = 0
        if saved_data: def_time = int(saved_data.get('restart_seconds', 0)/60)
        inp = input(f"\nRestart setiap berapa menit? (Enter={def_time}): ").strip()
        menit = int(inp) if inp else def_time
        detik = menit * 60
    except:
        detik = 0
    
    save_current_config(detik)
    return detik

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (SYNCED RESTART) ===")
    
    RESTART_INTERVAL = setup_configuration()
    
    # --- PHASE 1: INITIAL LAUNCH ---
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    
    for pkg in BASE_PACKAGES:
        # Filter: Hanya jalankan yang punya Place ID
        if pkg in PACKAGE_SETTINGS and PACKAGE_SETTINGS[pkg]['place_id']:
            print(f"\n📦 Akun: {get_pkg_name(pkg)}")
            
            # PANGGIL FUNGSI INTI
            if eksekusi_akun(pkg):
                ACTIVE_PACKAGES.append(pkg)

    if not ACTIVE_PACKAGES:
        print("❌ Tidak ada akun aktif.")
        return

    print(f"\n✅ Selesai Phase 1. {len(ACTIVE_PACKAGES)} akun berjalan.")
    if RESTART_INTERVAL > 0:
        print(f"⏰ Auto-Restart aktif setiap {int(RESTART_INTERVAL/60)} menit.")
    
    # --- PHASE 2: RESTART LOOP ---
    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(10)
            
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                if elapsed >= RESTART_INTERVAL:
                    print("\n" + "="*40)
                    print("🔄 WAKTUNYA RESTART (Siklus Baru)")
                    print("="*40)
                    
                    for pkg in ACTIVE_PACKAGES:
                        print(f"\n♻️  Restarting {get_pkg_name(pkg)}...")
                        
                        # >>> DISINI KUNCINYA <<<
                        # Kita memanggil fungsi yang SAMA PERSIS dengan Phase 1.
                        # Fungsi ini akan mematikan paksa dulu, baru launch lagi.
                        eksekusi_akun(pkg)
                        
                    last_restart_time = time.time()
                    print(f"\n✅ Siklus selesai. Menunggu {int(RESTART_INTERVAL/60)} menit lagi.")

        except KeyboardInterrupt:
            print("\n🛑 Stop.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
