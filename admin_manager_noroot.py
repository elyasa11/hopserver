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

# ================= FUNGSI SISTEM (SATU PINTU) =================

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

def force_close_clean(pkg):
    clean = get_pkg_name(pkg)
    try:
        # Kita gunakan metode keras agar RAM benar-benar bersih
        # Ini kunci agar saat restart tidak "nyangkut" di Home
        os.system(f"am force-stop {clean} > /dev/null 2>&1")
        time.sleep(0.5)
        os.system(f"killall {clean} > /dev/null 2>&1") 
    except:
        pass

# FUNGSI UTAMA: MENGGABUNGKAN SEMUA PROSES JADI SATU
# Fungsi ini dipakai baik saat AWAL maupun saat RESTART
def jalankan_siklus_lengkap(pkg):
    clean_pkg = get_pkg_name(pkg)
    
    # 1. Cek Settingan
    if pkg not in PACKAGE_SETTINGS:
        return False
        
    place_id = PACKAGE_SETTINGS[pkg]['place_id']
    vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']
    
    if not place_id:
        return False

    # 2. MATIKAN PAKSA (Sangat Penting!)
    # Kita matikan dulu sebelum menentukan Link, biar HP siap
    print(f"   🛑 Mematikan proses lama {clean_pkg}...")
    force_close_clean(pkg)
    
    # JEDA WAJIB: Agar HP tidak bingung (Dianggap Fresh Start)
    time.sleep(3) 

    # 3. TENTUKAN LINK (Menggunakan logika script awal pilihanmu)
    final_uri = ""
    tipe_server = ""
    
    # Logika Link Original (Sesuai request: HTTP dibiarkan raw)
    if vip_link_input and ("http" in vip_link_input or "roblox.com" in vip_link_input):
        final_uri = vip_link_input.strip()
        tipe_server = "🔗 Private Server (Direct Link)"
    elif vip_link_input and vip_link_input.strip() != "":
        # Hanya ubah ke format roblox:// jika user memasukkan KODE saja
        final_uri = f"roblox://placeId={place_id}&privateServerLinkCode={vip_link_input.strip()}"
        tipe_server = "🔒 Private Server (Code Injection)"
    else:
        final_uri = f"roblox://placeId={place_id}"
        tipe_server = "🎲 Public/Random Server"

    # 4. EKSEKUSI PELUNCURAN
    print(f"   🚀 Meluncurkan: {tipe_server}")
    
    # Tambahkan flag --activity-clear-task agar Roblox reload dari nol
    cmd = f"am start --user 0 -a android.intent.action.VIEW -d \"{final_uri}\" --activity-clear-task {clean_pkg}"
    os.system(f"{cmd} > /dev/null 2>&1")
    
    # 5. JEDA STABILISASI (Langsung di dalam fungsi)
    print(f"   ⏳ Menunggu 25 detik agar stabil...")
    time.sleep(25)
    
    return True

# ================= INPUT & SAVE MENU =================

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
    print("✅ Konfigurasi tersimpan.")

def setup_configuration():
    global PACKAGE_SETTINGS
    saved_data = load_last_config()
    loaded_packages = False
    
    if saved_data:
        print(f"\n📂 Data lama ditemukan.")
        if input("Gunakan data lama? (y/n): ").lower().strip() == 'y':
            PACKAGE_SETTINGS = saved_data['packages']
            loaded_packages = True

    if not loaded_packages:
        print("\n--- PENGATURAN BARU ---")
        mode = input("1. Satu Game Semua Akun / 2. Beda Game: ").strip()

        if mode == "1":
            pid = input("Place ID: ").strip()
            vip = input("Link Private (HTTP/Code): ").strip()
            for pkg in BASE_PACKAGES:
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
        else:
            for pkg in BASE_PACKAGES:
                clean = get_pkg_name(pkg)
                print(f"\n{clean}:")
                pid = input("Place ID: ").strip()
                vip = ""
                if pid: vip = input("Link Private: ").strip()
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    # Waktu Restart
    print("\n--- WAKTU RESTART ---")
    try:
        def_menit = 0
        if saved_data: def_menit = int(saved_data.get('restart_seconds', 0)/60)
        inp = input(f"Restart tiap berapa menit? (Enter={def_menit}): ").strip()
        menit = int(inp) if inp else def_menit
        detik = menit * 60
    except:
        detik = 0
    
    save_current_config(detik)
    return detik

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (IDENTICAL CYCLE) ===")
    
    RESTART_INTERVAL = setup_configuration()
    
    # 1. PELUNCURAN AWAL (PHASE 1)
    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    
    for pkg in BASE_PACKAGES:
        # Filter: Hanya jalankan yang punya ID
        if pkg in PACKAGE_SETTINGS and PACKAGE_SETTINGS[pkg]['place_id']:
            print(f"\n--> Memproses: {get_pkg_name(pkg)}")
            
            # PANGGIL FUNGSI SIKLUS (Sama persis dengan restart nanti)
            jalankan_siklus_lengkap(pkg)
            
            ACTIVE_PACKAGES.append(pkg)

    if not ACTIVE_PACKAGES:
        print("❌ Tidak ada akun aktif.")
        return

    print(f"\n✅ Phase 1 Selesai. {len(ACTIVE_PACKAGES)} akun berjalan.")
    if RESTART_INTERVAL > 0:
        print(f"⏳ Auto-Restart: {int(RESTART_INTERVAL/60)} Menit.")
    else:
        print("⏸️  Tanpa Auto-Restart.")
    print("="*50)

    # 2. LOOP AUTO RESTART (PHASE 2)
    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(10)
            
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                
                if elapsed >= RESTART_INTERVAL:
                    print("\n\n⏰ WAKTU HABIS! MEMULAI SIKLUS BARU...")
                    print("   (Menggunakan metode yang sama persis dengan awal)")
                    
                    for pkg in ACTIVE_PACKAGES:
                        print(f"\n♻️  Restarting {get_pkg_name(pkg)}...")
                        
                        # >>> KUNCI: PANGGIL FUNGSI YANG SAMA DENGAN PHASE 1 <<<
                        jalankan_siklus_lengkap(pkg)
                        
                    last_restart_time = time.time()
                    print(f"\n✅ Siklus selesai. Menunggu {int(RESTART_INTERVAL/60)} menit lagi.")
                    
        except KeyboardInterrupt:
            print("\n🛑 Stop.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
