--[[
    GABUNGAN SCRIPT: CHEAT FARM & MONITORING
    Teknik: Multithreading (task.spawn)
]]

print("--- SYSTEM START: PARALLEL EXECUTION ---")

-- 1. JALANKAN SCRIPT CHEAT (FARMING)
-- Kita bungkus pakai task.spawn agar loop di dalam script cheat tidak memacetkan script monitor
task.spawn(function()
    print(">>> [THREAD 1] Meluncurkan Script Cheat...")
    local success, err = pcall(function()
        loadstring(game:HttpGet("https://raw.githubusercontent.com/Omgshit/Scripts/main/MainLoader.lua"))()
    end)
    
    if success then
        print(">>> [THREAD 1] Script Cheat Berhasil Dimuat.")
    else
        warn(">>> [THREAD 1] Script Cheat Error: " .. tostring(err))
    end
end)

-- Beri jeda sedikit (2 detik) agar script cheat loading duluan
task.wait(2)

-- 2. JALANKAN SCRIPT MONITOR (ANTI-TABRAKAN)
-- Ini script yang melapor ke Python dan menunggu perintah Hop
task.spawn(function()
    print(">>> [THREAD 2] Meluncurkan Script Monitor...")
    local success, err = pcall(function()
        loadstring(game:HttpGet("https://raw.githubusercontent.com/elyasa11/hopserver/refs/heads/main/monitor.lua"))()
    end)

    if success then
        print(">>> [THREAD 2] Script Monitor Aktif.")
    else
        warn(">>> [THREAD 2] Script Monitor Error: " .. tostring(err))
    end
end)

print("--- SEMUA SISTEM BERJALAN ---")
