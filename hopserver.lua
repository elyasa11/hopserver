--[[
    SCRIPT PENGECEK STATUS HOP SERVER
    Dibuat untuk: Delta Executor
]]

local filename = "last_server_check.txt" -- Nama file untuk menyimpan data
local currentJobId = game.JobId
local StarterGui = game:GetService("StarterGui")

print("--- SYSTEM CHECK: SERVER HOP ---")

-- 1. Cek apakah file catatan sudah ada
if isfile(filename) then
    local lastJobId = readfile(filename)

    if lastJobId == currentJobId then
        -- KONDISI: ID SAMA (GAGAL HOP)
        warn("STATUS: HOP GAGAL / Rejoined Same Server")
        
        StarterGui:SetCore("SendNotification", {
            Title = "Hop Server Status",
            Text = "⚠️ GAGAL! Masih di server yang sama.",
            Duration = 5
        })
        
        -- Opsional: Paksa hop lagi jika gagal (hapus tanda komen di bawah jika mau)
        -- task.wait(2)
        -- game:GetService("TeleportService"):Teleport(game.PlaceId, game.Players.LocalPlayer)
        
    else
        -- KONDISI: ID BEDA (BERHASIL HOP)
        print("STATUS: HOP SUKSES")
        
        StarterGui:SetCore("SendNotification", {
            Title = "Hop Server Status",
            Text = "✅ BERHASIL! Ini server baru.",
            Duration = 5
        })
    end
else
    -- KONDISI: BARU PERTAMA KALI JALAN
    print("STATUS: Script baru dijalankan pertama kali.")
    StarterGui:SetCore("SendNotification", {
        Title = "Hop Server Status",
        Text = "ℹ️ Script dimulai. Data server disimpan.",
        Duration = 5
    })
end

-- 2. Simpan ID server sekarang ke file untuk pengecekan nanti
writefile(filename, currentJobId)
