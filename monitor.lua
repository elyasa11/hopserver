--[[
    AUTO MONITOR & HOP (SHARED STORAGE VERSION)
    Simpan di folder AutoExecute Delta.
]]

local Http = game:GetService("HttpService")
local TPS = game:GetService("TeleportService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

-- Ambil Nama Username Akun Ini
local myUser = Players.LocalPlayer.Name

-- Nama file unik berdasarkan username
local myStatusFile = "status_" .. myUser .. ".json"
local myHopCommand = "hop_" .. myUser .. ".txt"

print("--- MONITOR AKTIF UNTUK: " .. myUser .. " ---")

-- 1. FUNGSI HOP SERVER (Versi API Stabil)
local function ServerHop()
    print("⚠️ DIPERINTAHKAN PINDAH SERVER! MENCARI...")
    
    local PlaceID = game.PlaceId
    local success, result = pcall(function()
        return Http:JSONDecode(game:HttpGet("https://games.roblox.com/v1/games/" .. PlaceID .. "/servers/Public?sortOrder=Asc&limit=100"))
    end)

    if success and result and result.data then
        local Servers = {}
        for _, server in pairs(result.data) do
            if server.playing < server.maxPlayers and server.id ~= game.JobId then
                table.insert(Servers, server.id)
            end
        end
        if #Servers > 0 then
            TPS:TeleportToPlaceInstance(PlaceID, Servers[math.random(1, #Servers)], Players.LocalPlayer)
        else
            TPS:Teleport(PlaceID, Players.LocalPlayer) -- Rejoin jika kepepet
        end
    else
        TPS:Teleport(PlaceID, Players.LocalPlayer)
    end
end

-- 2. LOOP UTAMA (Jalan setiap 3 detik)
task.spawn(function()
    while true do
        task.wait(3)

        -- A. TULIS LAPORAN (Absen)
        local data = {
            username = myUser,
            jobId = game.JobId,
            placeId = game.PlaceId,
            timestamp = os.time()
        }
        
        -- Bungkus pcall agar script gak stop kalau gagal nulis
        pcall(function()
            writefile(myStatusFile, Http:JSONEncode(data))
        end)

        -- B. CEK PERINTAH PINDAH
        if isfile(myHopCommand) then
            -- Hapus file perintahnya dulu biar gak looping
            delfile(myHopCommand)
            -- Eksekusi pindah
            ServerHop()
        end
    end
end)
