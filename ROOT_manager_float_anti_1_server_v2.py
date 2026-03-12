import os
import time
import subprocess
import json
import sys

# ================= KONFIGURASI PAKET =================
BASE_PACKAGES = [
    "com.roblox.client",
    "com.roblox.clienu",
    "com.roblox.clienv",
    "com.roblox.clienw"
]

WORKSPACE_PATH = "/storage/emulated/0/Delta/Workspace"

# Variabel Global
PACKAGE_SETTINGS = {}
ACTIVE_PACKAGES = []
CONFIG_FILE = "config_manager.json"

# ================= FUNGSI ROOT =================

def run_as_root(cmd):
    full_cmd = f"su -c '{cmd}'"
    os.system(f"{full_cmd} > /dev/null 2>&1")

def run_root_output(cmd):
    try:
        # Menangkap stdout & stderr agar error permission tidak tersembunyi
        result = subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True)
        return result.stdout.strip() if result.stdout else result.stderr.strip()
    except Exception as e:
        return str(e)

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

def force_close(pkg):
    clean = get_pkg_name(pkg)
    run_as_root(f"am force-stop {clean}")

def launch_game(pkg, specific_place_id=None, vip_link_input=None):
    clean = get_pkg_name(pkg)
    
    if not specific_place_id and pkg in PACKAGE_SETTINGS:
        specific_place_id = PACKAGE_SETTINGS[pkg]['place_id']
        vip_link_input = PACKAGE_SETTINGS[pkg]['vip_code']

    if not specific_place_id: return

    final_uri = ""
    if vip_link_input and ("http" in vip_link_input or "roblox.com" in vip_link_input):
        final_uri = vip_link_input.strip()
    elif vip_link_input and vip_link_input.strip() != "":
        final_uri = f"roblox://placeId={specific_place_id}&privateServerLinkCode={vip_link_input.strip()}"
    else:
        final_uri = f"roblox://placeId={specific_place_id}"

    print(f"    -> 🚀 Meluncurkan {clean} (MODE FLOATING ID:5)...")
    
    cmd = (
        f"am start --user 0 "
        f"--windowingMode 5 " 
        f"-a android.intent.action.VIEW "
        f"-d \"{final_uri}\" "
        f"--activity-clear-task {clean}"
    )
    run_as_root(cmd)

# === FUNGSI BACA/TULIS STATUS (ANTI-TABRAKAN) ===
def get_status_files():
    # Menggunakan 'find' karena terbukti berhasil di Android 13 kamu
    output = run_root_output(f"find {WORKSPACE_PATH} -maxdepth 1 -name 'status_*.json' 2>/dev/null")
    
    if not output or "No such file" in output: 
        return []
    
    files = []
    for f in output.split('\n'):
        f = f.strip()
        # Perintah 'find' sudah mengembalikan full path, jadi kita tinggal filter
        if f.endswith(".json"):
            files.append(f)
            
    return files

def read_json_root(filepath):
    try:
        content = run_root_output(f"cat '{filepath}'")
        if content: return json.loads(content)
    except: pass
    return None

def write_json_root(filepath, data):
    try:
        json_str = json.dumps(data).replace('"', '\\"')
        run_root_output(f"echo \"{json_str}\" > '{filepath}'")
    except Exception as e: 
        print(f"\n[ERROR WRITE] Gagal menulis ke file: {e}")

def inject_hop_signal(filepath, data):
    data['action'] = "HOP"
    write_json_root(filepath, data)

# === FUNGSI SIKLUS ===
def jalankan_peluncuran_saja(pkg):
    clean_pkg = get_pkg_name(pkg)
    print(f"\n--> Memproses: {clean_pkg}")
    launch_game(pkg)
    print("    ⏳ Menunggu 25 detik agar stabil...")
    time.sleep(25) 

# ================= INPUT & SAVE MENU =================
# ... (Bagian Setup Configuration Tetap Sama) ...

def load_last_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f: return json.load(f)
        except: return None
    return None

def save_current_config(restart_time):
    data = {"restart_seconds": restart_time, "packages": PACKAGE_SETTINGS}
    with open(CONFIG_FILE, 'w') as f: json.dump(data, f, indent=4)
    print("✅ Konfigurasi berhasil disimpan.")

def setup_configuration():
    global PACKAGE_SETTINGS
    saved_data = load_last_config()
    loaded_packages = False
    
    if saved_data:
        pilih = input("Gunakan settingan lama? (y/n): ").lower().strip()
        if pilih == 'y':
            PACKAGE_SETTINGS = saved_data['packages']
            loaded_packages = True

    if not loaded_packages:
        print("\n--- PENGATURAN BARU ---")
        mode = input("1. Satu Game / 2. Beda Game: ").strip()
        if mode == "1":
            pid = input("Masukkan Place ID: ").strip()
            vip = input("Link Private (Enter jika Public): ").strip()
            for pkg in BASE_PACKAGES: PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
        else:
            for pkg in BASE_PACKAGES:
                print(f"\nSetting untuk {get_pkg_name(pkg)}:")
                pid = input(f"  - Place ID: ").strip()
                vip = input(f"  - Link Private: ").strip() if pid else ""
                PACKAGE_SETTINGS[pkg] = {'place_id': pid, 'vip_code': vip}
    
    try:
        default_menit = int(saved_data['restart_seconds'] / 60) if saved_data and 'restart_seconds' in saved_data else 0
        inp = input(f"\nRestart tiap berapa menit? (Enter={default_menit} mnt): ").strip()
        restart_seconds = int(inp) * 60 if inp else default_menit * 60
    except:
        restart_seconds = 0
    
    save_current_config(restart_seconds)
    return restart_seconds

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER (FIXED ANTI-TABRAKAN & MONITOR) ===")
    os.system("su -c 'echo ✅ Akses Root OK' || echo '⚠️ Cek izin Root...'")

    RESTART_INTERVAL = setup_configuration()
    
    for pkg in BASE_PACKAGES:
        if PACKAGE_SETTINGS.get(pkg, {}).get('place_id'): ACTIVE_PACKAGES.append(pkg)
    
    if len(ACTIVE_PACKAGES) == 0: return print("❌ Tidak ada akun aktif.")

    print(f"\n[PHASE 1] PELUNCURAN PERTAMA")
    for pkg in ACTIVE_PACKAGES:
        force_close(pkg)
        time.sleep(1)
        jalankan_peluncuran_saja(pkg)

    print(f"\n✅ {len(ACTIVE_PACKAGES)} AKUN BERJALAN. Memulai sistem Monitor...\n")
    print("="*50)

    last_restart_time = time.time()
    
    while True:
        try:
            time.sleep(5) 
            
            # A. LOGIKA AUTO RESTART
            if RESTART_INTERVAL > 0 and (time.time() - last_restart_time) >= RESTART_INTERVAL:
                print("\n\n⏰ WAKTU HABIS! RESTARTING...")
                for pkg in ACTIVE_PACKAGES: force_close(pkg)
                time.sleep(5)
                for pkg in ACTIVE_PACKAGES: jalankan_peluncuran_saja(pkg)
                last_restart_time = time.time()
                continue 

            # B. LOGIKA ANTI-TABRAKAN
            server_map = {}
            all_files = get_status_files()
            current_time = time.time()
            
            # Visual Feedback untuk Debugging (Agar tahu script tidak macet)
            sys.stdout.write(f"\r[MONITOR] Membaca {len(all_files)} file status... ")
            sys.stdout.flush()
            
            for f in all_files:
                d = read_json_root(f)
                if d and 'jobId' in d and 'timestamp' in d:
                    if (current_time - d.get('timestamp', 0)) < 180: 
                        jid = d['jobId']
                        if jid not in server_map: server_map[jid] = []
                        server_map[jid].append({'file': f, 'data': d, 'user': d.get('username', 'Unknown')})
            
            # Cek Tabrakan Server
            tabrakan_ditemukan = False
            for jid, sessions in server_map.items():
                if len(sessions) > 1:
                    sample_data = sessions[0]['data']
                    if sample_data.get('isPrivate', False):
                        continue 
                    else:
                        tabrakan_ditemukan = True
                        for victim in sessions[1:]:
                            if victim['data'].get('action') != "HOP":
                                print(f"\n⚠️ [ANTI-TABRAKAN] {victim['user']} ada di server yang sama! Menyuntikkan perintah HOP...")
                                inject_hop_signal(victim['file'], victim['data'])
            
            if tabrakan_ditemukan:
                sys.stdout.write("Menangani tabrakan...         \n")
            
        except KeyboardInterrupt:
            print("\n🛑 Stop.")
            break
        except Exception as e:
            # FIX: Jangan sembunyikan error lagi! Tampilkan agar kita tahu jika path/file bermasalah
            print(f"\n[ERROR LOOP] {e}")

if __name__ == "__main__":
    main()
