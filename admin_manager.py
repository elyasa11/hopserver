import os
import subprocess
import time
import json
import random

# ================= KONFIGURASI =================
BASE_PACKAGES = [
    "com.roblox.client",
    "com.roblox.clienu",
    "com.roblox.clienv",
    "com.roblox.clienw"
]

# Path Shared Workspace (Sesuai hasil tes kamu)
WORKSPACE_PATH = "/storage/emulated/0/Delta/Workspace"

# Toleransi Freeze (Detik)
FREEZE_THRESHOLD = 120 
MAPPING_TIMEOUT = 60

# ================= FUNGSI ROOT =================

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

# ================= FUNGSI FILE & DATABASE =================

def get_status_files():
    files = run_root(f"ls {WORKSPACE_PATH}/status_*.json")
    if "No such file" in files or not files:
        return []
    return [f for f in files.split('\n') if f.strip()]

def read_json_root(filepath):
    try:
        content = run_root(f"cat {filepath}")
        if content:
            return json.loads(content)
    except:
        pass
    return None

def write_json_root(filepath, data):
    """Fungsi Admin: Menulis/Update file JSON via Root"""
    try:
        json_str = json.dumps(data)
        # Escape quote untuk command shell
        json_str = json_str.replace('"', '\\"') 
        run_root(f"echo \"{json_str}\" > {filepath}")
        return True
    except Exception as e:
        print(f"Error writing JSON: {e}")
        return False

def inject_hop_signal(filepath, data):
    """Menyuntikkan perintah HOP ke dalam file JSON"""
    print(f"   >>> [WASIT] Menyuntikkan Flag 'HOP' ke {os.path.basename(filepath)}...")
    data['action'] = "HOP"
    write_json_root(filepath, data)

def inject_anti_zombie(filepath, data):
    """Menyuntikkan Timestamp baru agar tidak terdeteksi freeze di loop berikutnya"""
    print(f"   >>> [ANTI-FREEZE] Menyuntikkan Timestamp Baru ke {os.path.basename(filepath)}...")
    data['timestamp'] = time.time() # Update waktu jadi SEKARANG
    data['status'] = "RESTARTING"
    write_json_root(filepath, data)

# ================= MAIN LOGIC =================

def main():
    print("=== ROBLOX MANAGER: DATABASE METHOD (V2) ===")
    
    place_id = input("Masukkan Place ID: ").strip()
    if not place_id: return

    # Mapping: { 'com.roblox.clienu': { 'file': path, 'user': name } }
    package_map = {}

    print(f"\n[PHASE 1] AUTO-MAPPING (Tidak Menghapus File)")
    
    for pkg in BASE_PACKAGES:
        clean_pkg = get_pkg_name(pkg)
        print(f"\n--> Meluncurkan: {clean_pkg}")
        
        # Snapshot timestamp file sebelum launch
        files_state_before = {}
        for f in get_status_files():
            d = read_json_root(f)
            if d and 'timestamp' in d:
                files_state_before[f] = float(d['timestamp'])
        
        force_close(pkg)
        time.sleep(1)
        launch_game(pkg, place_id)
        
        # Waktu kita meluncurkan app ini
        launch_ts = time.time()
        
        print("    Menunggu update file JSON...", end="", flush=True)
        detected_info = None

        for _ in range(MAPPING_TIMEOUT):
            time.sleep(1)
            files_now = get_status_files()
            
            for f in files_now:
                data = read_json_root(f)
                if data and 'timestamp' in data:
                    ts = float(data['timestamp'])
                    
                    # Logic: File baru ATAU File lama yang baru saja diupdate
                    is_new = f not in files_state_before
                    is_updated = (f in files_state_before) and (ts > files_state_before[f])
                    
                    if (is_new or is_updated) and ts >= launch_ts:
                        detected_info = {
                            'file': f,
                            'user': data.get('username', 'Unknown')
                        }
                        break
            if detected_info: break
        
        if detected_info:
            print(f" OK! ({detected_info['user']})")
            package_map[pkg] = detected_info
        else:
            print(" Timeout!")

    print("\n" + "="*50)
    print(f"[PHASE 2] MONITORING AKTIF ({len(package_map)} akun)")
    print("="*50)

    while True:
        now = time.time()
        
        # A. LOOP STATUS (ANTI-FREEZE)
        for pkg in BASE_PACKAGES:
            if pkg not in package_map: continue
            
            clean = get_pkg_name(pkg)
            info = package_map[pkg]
            fpath = info['file']
            
            # 1. Cek Crash
            if not is_app_running(pkg):
                print(f"\n[CRASH] {clean} mati. Relaunching...")
                launch_game(pkg, place_id)
                # Suntik timestamp agar saat nyala tidak dianggap freeze
                d = read_json_root(fpath)
                if d: inject_anti_zombie(fpath, d)
                continue
            
            # 2. Cek Freeze
            data = read_json_root(fpath)
            if data and 'timestamp' in data:
                ts = float(data['timestamp'])
                status = data.get('status', 'UNKNOWN')
                
                # Jika status masih 'RESTARTING' (buatan Python), abaikan freeze check
                if status == "RESTARTING":
                    pass
                else:
                    lag = now - ts
                    if lag > FREEZE_THRESHOLD:
                        print(f"\n[FREEZE] {info['user']} macet {int(lag)}s!")
                        
                        # >>> MAGIC METHOD 2: SUNTIK TIMESTAMP <<<
                        inject_anti_zombie(fpath, data)
                        
                        print("         -> Restarting App...")
                        force_close(pkg)
                        time.sleep(2)
                        launch_game(pkg, place_id)

        # B. LOOP COLLISION (ANTI-TABRAKAN)
        server_map = {}
        all_files = get_status_files()
        
        # Kumpulkan data (Filter data basi > 60s)
        for f in all_files:
            d = read_json_root(f)
            if d and 'jobId' in d and 'timestamp' in d:
                if now - float(d['timestamp']) < 60:
                    jid = d['jobId']
                    # Simpan data lengkap untuk keperluan inject
                    if jid not in server_map: server_map[jid] = []
                    server_map[jid].append({'file': f, 'data': d, 'user': d.get('username')})
        
        # Cek Bentrok
        collision = False
        for jid, sessions in server_map.items():
            if len(sessions) > 1:
                collision = True
                users_involved = [s['user'] for s in sessions]
                print(f"\n[TABRAKAN] Server {jid[:8]}.. : {users_involved}")
                
                # Usir user ke-2 dst
                for victim in sessions[1:]:
                    # >>> MAGIC METHOD 2: SUNTIK FLAG 'HOP' <<<
                    inject_hop_signal(victim['file'], victim['data'])
        
        if not collision:
            print(".", end="", flush=True)
            
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStop.")
