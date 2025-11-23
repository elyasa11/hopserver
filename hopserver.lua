--[[
    SIMPLE & ROBUST SERVER HOP V2
    Dibuat untuk mengatasi "Hop Gagal/Rejoin Same Server"
]]

local PlaceID = game.PlaceId
local Http = game:GetService("HttpService")
local TPS = game:GetService("TeleportService")
local Players = game:GetService("Players")

local function ServerHop()
    print("Mencoba mencari server baru...")
    
    -- 1. Ambil daftar server dari API Roblox
    local success, result = pcall(function()
        -- Mengambil server dengan urutan Ascending (dari yang sepi ke ramai) agar lebih mudah masuk
        return Http:JSONDecode(game:HttpGet("https://games.roblox.com/v1/games/" .. PlaceID .. "/servers/Public?sortOrder=Asc&limit=100"))
    end)

    if not success or not result or not result.data then
        warn("Gagal mengambil daftar server! Mencoba lagi nanti...")
        return
    end

    -- 2. Filter Server
    local Servers = {}
    for _, server in pairs(result.data) do
        -- Syarat:
        -- 1. Server bisa dimainkan (playing < maxPlayers)
        -- 2. Server bukan server kita saat ini (id ~= game.JobId)
        if server.playing < server.maxPlayers and server.id ~= game.JobId then
            table.insert(Servers, server.id)
        end
    end

    -- 3. Eksekusi Pindah
    if #Servers > 0 then
        -- Pilih satu server secara acak dari daftar yang valid
        local randomServerId = Servers[math.random(1, #Servers)]
        print("Menemukan " .. #Servers .. " server valid. Pindah ke ID: " .. randomServerId)
        
        TPS:TeleportToPlaceInstance(PlaceID, randomServerId, Players.LocalPlayer)
    else
        warn("Tidak ditemukan server lain yang valid (Mungkin game sepi/cuma 1 server).")
        
        -- Opsi Darurat: Coba teleport biasa (Rejoin) berharap Roblox melempar ke server baru
        -- TPS:Teleport(PlaceID, Players.LocalPlayer) 
    end
end

-- Jalankan Fungsi
ServerHop()
