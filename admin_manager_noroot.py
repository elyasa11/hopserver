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

def force_close(pkg):
    clean = get_pkg_name(pkg)
    try:
        # Menggunakan dua metode kill agar benar-benar mati
        os.system(f"am force-stop {clean} > /dev/null 2>&1")
        os.system(f"killall {clean} > /dev/null 2>&1") 
    except:
        pass

# FUNGSI UTAMA: MENJALANKAN AKUN (Dipakai di Awal & Restart)
def jalankan_akun(pkg):
    clean_pkg = get_pkg_name(pkg)
    
    # 1. Ambil Settingan
    if pkg not in PACKAGE_SETTINGS:
        return False
        
    place_id = PACKAGE_SETTINGS[pkg]['place_id']
    vip_code = PACKAGE_SETTINGS[pkg]['vip_code']
    
    if not place_id:
        return False

    # 2. Matikan Proses Lama (Wajib untuk restart yang bersih)
    print(f"   -> Menutup paksa {clean_pkg}...")
    force_close(pkg)
    time.sleep(2) # Beri napas sistem Android untuk kill process

    # 3. Buat Link Baru
    final_uri = ""
    if vip_code and ("http" in vip_code or "roblox.com" in vip_code):
        final_uri = vip_code.strip()
        tipe_server = "🔗 Private Link"
    elif vip_code and vip_code.strip() != "":
        final_uri = f"roblox://placeId={place_id}&privateServerLinkCode={vip_code.strip()}"
        tipe_server = "🔒 Private Code"
    else:
        final_uri = f"roblox://placeId={place_id}"
        tipe_server = "🎲 Public Server"

    # 4. Eksekusi Perintah Launch
    print(f"   -> Meluncurkan: {tipe_server}")
    # Flag --activity-clear-task memastikaan Roblox mulai dari awal, bukan resume
    cmd = f"am start --user 0 -a android.intent.action.VIEW -d \"{final_uri}\" --activity-clear-task {clean_pkg}"
    os.system(f"{cmd} > /dev/null 2>&1")
    
    # 5. Jeda Wajib 25 Detik (Sesuai Request)
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
    print("✅ Konfigurasi berhasil disimpan.")

def setup_configuration():
    global PACKAGE_SETTINGS
    
    saved_data = load_last_config()
    loaded_packages = False
    
    # Load Data Akun Lama
    if saved_data:
        print(f"\n📂 Ditemukan data {len(saved_data.get('packages', {}))} akun tersimpan.")
        pilih = input("Gunakan ID/Link game yang tersimpan? (y/n): ").lower().strip()
        if pilih == 'y':
            PACKAGE_SETTINGS = saved_data['packages']
            loaded_packages = True

    # Jika user ingin input baru
    if not loaded_packages:
        print("\n--- PENGATURAN MODE GAME BARU ---")
        print("1. SATU GAME untuk SEMUA AKUN")
        print("2. BEDA GAME setiap AKUN")
        mode = input("Pilih Mode (1/2): ").strip()

        if mode == "1":
            print("\n[MODE SERAGAM]")
            pid = input("Masukkan Place ID: ").strip()
            print("Masukkan Link Private Server (Share Link / Code):")
            vip = input("(Kosongkan jika Public): ").strip()
            
            for pkg in BASE_PACKAGES:
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
        else:
            print("\n[MODE INDIVIDUAL]")
            for pkg in BASE_PACKAGES:
                clean = get_pkg_name(pkg)
                print(f"\nSetting untuk {clean}:")
                pid = input(f"  - Place ID: ").strip()
                vip = ""
                if pid:
                    print(f"  - Link Private Server (Enter jika Public):")
                    vip = input(f"    > ").strip()
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}

    # Input Waktu Restart (Selalu Ditanyakan)
    print("\n" + "="*40)
    print("🕒 PENGATURAN DURASI DALAM GAME")
    print("="*40)
    print("Berapa lama akun diam di game sebelum direstart ulang?")
    print("(Input '0' untuk mematikan fitur restart)")
    
    try:
        default_menit = 0
        if saved_data and 'restart_seconds' in saved_data:
            default_menit = int(saved_data['restart_seconds'] / 60)
            
        inp = input(f"Masukkan Menit (Enter untuk default {default_menit} mnt): ").strip()
        
        if inp == "":
            restart_seconds = default_menit * 60
        else:
            restart_seconds = int(inp) * 60
    except:
        restart_seconds = 0
    
    save_current_config(restart_seconds)
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (PERFECT RESTART) ===")
    
    RESTART_INTERVAL = setup_configuration()
    
    # 1. PELUNCURAN AWAL (PHASE 1)
    print(f"\n[PHASE 1] INITIAL LAUNCH")
    
    for pkg in BASE_PACKAGES:
        # Cek apakah akun ini disetting
        if pkg not in PACKAGE_SETTINGS or not PACKAGE_SETTINGS[pkg]['place_id']:
            continue
            
        print(f"\n--> Memproses: {get_pkg_name(pkg)}")
        
        # PANGGIL FUNGSI UTAMA
        sukses = jalankan_akun(pkg)
        
        if sukses:
            ACTIVE_PACKAGES.append(pkg)
        
    print("\n" + "="*50)
    print(f"✅ SELESAI. {len(ACTIVE_PACKAGES)} AKUN BERJALAN.")
    
    if len(ACTIVE_PACKAGES) == 0:
        return

    if RESTART_INTERVAL > 0:
        print(f"⏳ Jadwal Restart Aktif: Setiap {int(RESTART_INTERVAL/60)} Menit")
    else:
        print("⏸️  Mode Standby (Tanpa Auto-Restart)")
    print("="*50)

    # 2. LOOP AUTO RESTART (PHASE 2)
    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(10)
            
            if RESTART_INTERVAL > 0:
                elapsed = time.time() - last_restart_time
                
                if elapsed >= RESTART_INTERVAL:
                    print("\n\n⏰ WAKTU HABIS! MEMULAI PROSES RESTART...")
                    print("   (Menggunakan metode yang sama dengan awal login)")
                    
                    for pkg in ACTIVE_PACKAGES:
                        print(f"\n♻️  Restarting {get_pkg_name(pkg)}...")
                        
                        # PANGGIL FUNGSI YANG SAMA PERSIS DENGAN PHASE 1
                        jalankan_akun(pkg)
                        
                    last_restart_time = time.time()
                    print(f"\n✅ Semua akun telah direstart. Menunggu {int(RESTART_INTERVAL/60)} menit lagi.")
                    
        except KeyboardInterrupt:
            print("\n🛑 Script Dihentikan.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
