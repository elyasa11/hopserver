import os
import subprocess
import time
import json
import random
import glob

# ================= KONFIGURASI =================
BASE_PACKAGES = [
    "com.roblox.client",
    "com.roblox.clienu",
    "com.roblox.clienv",
    "com.roblox.clienw"
]

WORKSPACE_PATH = "/storage/emulated/0/Delta/Workspace"
FREEZE_THRESHOLD = 120  # Waktu toleransi macet (detik)
MAPPING_TIMEOUT = 60

# ================= FUNGSI DASAR =================

def run_root(cmd):
    return subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True).stdout.strip()

def get_pkg_name(pkg):
    return pkg.split('/')[0].strip()

def force_close(pkg):
    clean = get_pkg_name(pkg)
    os.system(f"/system/bin/am force-stop {clean}")

def launch_game(pkg, place_id):
    clean = get_pkg_name(pkg)
    uri = f"roblox://placeId={place_id}"
    cmd = f"/system/bin/am start --user 0 -a android.intent.action.VIEW -d \"{uri}\" {clean}"
    os.system(f"{cmd} > /dev/null 2>&1")

def is_app_running(pkg):
    clean = get_pkg_name(pkg)
    try:
        cmd = f"/system/bin/pidof {clean}"
        output = subprocess.check_output(cmd, shell=True, text=True).strip()
        return bool(output)
    except:
        return False

# ================= FILE OPERATIONS =================

def get_status_files():
    files = run_root(f"ls {WORKSPACE_PATH}/status_*.json")
    if "No such file" in files or not files: return []
    return [f for f in files.split('\n') if f.strip()]

def read_json_root(filepath):
    try:
        content = run_root(f"cat {filepath}")
        if content: return json.loads(content)
    except: pass
    return None

def write_json_root(filepath, data):
    try:
        json_str = json.dumps(data).replace('"', '\\"')
        run_root(f"echo \"{json_str}\" > {filepath}")
    except: pass

def inject_hop_signal(filepath, data):
    print(f"   >>> [WASIT] Memicu HOP di file {os.path.basename(filepath)}...")
    data['action'] = "HOP"
    write_json_root(filepath, data)

def inject_restart_status(filepath, data):
    # Kita tandai status RESTARTING agar saat app baru buka, dia tidak dianggap freeze
    data['status'] = "RESTARTING"
    # Kita update timestamp biar berubah angkanya
    data['timestamp'] = data.get('timestamp', 0) + 1 
    write_json_root(filepath, data)

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER: STAGNATION LOGIC (V3) ===")
    
    place_id = input("Masukkan Place ID: ").strip()
    if not place_id: return

    # STRUKTUR MEMORI BARU:
    # { 'com.roblox...': { 'file': path, 'user': name, 'last_ts': 12345, 'last_change_time': time.time() } }
    package_map = {}

    print(f"\n[PHASE 1] AUTO-MAPPING")
    
    for pkg in BASE_PACKAGES:
        clean_pkg = get_pkg_name(pkg)
        print(f"\n--> Meluncurkan: {clean_pkg}")
        
        # Snapshot timestamp awal
        files_state_before = {}
        for f in get_status_files():
            d = read_json_root(f)
            if d and 'timestamp' in d: files_state_before[f] = float(d['timestamp'])
        
        force_close(pkg)
        time.sleep(1)
        launch_game(pkg, place_id)
        
        print("    Menunggu file bergerak...", end="", flush=True)
        detected_info = None

        for _ in range(MAPPING_TIMEOUT):
            time.sleep(1)
            files_now = get_status_files()
            for f in files_now:
                data = read_json_root(f)
                if data and 'timestamp' in data:
                    ts = float(data['timestamp'])
                    
                    # Logic: File yang timestampnya BERUBAH dari sebelumnya
                    prev_ts = files_state_before.get(f, 0)
                    if ts > prev_ts:
                        detected_info = {
                            'file': f,
                            'user': data.get('username', 'Unknown'),
                            'last_ts': ts,
                            'last_change_time': time.time() # Waktu terakhir data berubah
                        }
                        break
            if detected_info: break
        
        if detected_info:
            print(f" OK! ({detected_info['user']})")
            package_map[pkg] = detected_info
        else:
            print(" Timeout! (Lanjut tanpa monitoring freeze)")

    print("\n" + "="*50)
    print(f"[PHASE 2] MONITORING AKTIF")
    print("="*50)

    while True:
        now = time.time()
        
        # A. LOOP MONITORING
        for pkg in BASE_PACKAGES:
            if pkg not in package_map: continue
            
            clean = get_pkg_name(pkg)
            info = package_map[pkg]
            fpath = info['file']
            
            # 1. Cek App Crash
            if not is_app_running(pkg):
                print(f"\n[CRASH] {clean} mati. Relaunching...")
                launch_game(pkg, place_id)
                # Reset timer agar dianggap baru mulai
                info['last_change_time'] = now 
                continue
            
            # 2. Cek Freeze (Stagnation Logic)
            data = read_json_root(fpath)
            
            if data and 'timestamp' in data:
                current_file_ts = float(data['timestamp'])
                status = data.get('status', 'UNKNOWN')
                
                # Jika status RESTARTING (buatan Python), jangan dihitung
                if status == "RESTARTING":
                    info['last_change_time'] = now # Terus reset timer selama masih restarting
                    info['last_ts'] = current_file_ts
                    continue

                # Bandingkan timestamp file SEKARANG vs YANG DISIMPAN DI MEMORI
                if current_file_ts > info['last_ts']:
                    # BERGERAK! Update memori
                    info['last_ts'] = current_file_ts
                    info['last_change_time'] = now # Reset timer macet
                else:
                    # DIAM (Stagnant). Hitung sudah berapa lama diamnya?
                    stagnant_duration = now - info['last_change_time']
                    
                    if stagnant_duration > FREEZE_THRESHOLD:
                        print(f"\n[FREEZE] {info['user']} ({clean}) macet {int(stagnant_duration)}s!")
                        
                        # Suntik Status Restarting
                        inject_restart_status(fpath, data)
                        
                        print("         -> Restarting App...")
                        force_close(pkg)
                        time.sleep(2)
                        launch_game(pkg, place_id)
                        
                        # Reset memory
                        info['last_change_time'] = now
                        info['last_ts'] = current_file_ts + 1 # Fake increment biar gak langsung freeze lagi

        # B. LOOP TABRAKAN (Collision)
        # (Sama seperti sebelumnya, tapi validasi file diperlonggar)
        server_map = {}
        all_files = get_status_files()
        
        for f in all_files:
            d = read_json_root(f)
            # Kita anggap valid jika timestamp berubah dalam 2 menit terakhir (relatif ke jam sistem file itu sendiri)
            # Karena logic stagnasi sudah handle freeze, di sini kita longgar saja
            if d and 'jobId' in d:
                jid = d['jobId']
                if jid not in server_map: server_map[jid] = []
                server_map[jid].append({'file': f, 'data': d, 'user': d.get('username')})
        
        for jid, sessions in server_map.items():
            if len(sessions) > 1:
                print(f"\n[TABRAKAN] Server {jid[:8]}.. : {[s['user'] for s in sessions]}")
                for victim in sessions[1:]:
                    inject_hop_signal(victim['file'], victim['data'])
        
        print(".", end="", flush=True)
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStop.")
