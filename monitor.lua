--[[
    ALL-IN-ONE: MONITOR, AUTO HOP, & POTATO GRAPHICS
    Fitur:
    1. Melapor status ke Python (Shared Storage Support).
    2. Menunggu perintah Hop dari Python.
    3. Mengubah grafik jadi 'Smooth Plastic' & Hapus Partikel agar ringan.
]]

local Http = game:GetService("HttpService")
local TPS = game:GetService("TeleportService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")
local Workspace = game:GetService("Workspace")
local Terrain = Workspace:FindFirstChildOfClass("Terrain")

-- === CONFIG VARIABLES ===
local myUser = Players.LocalPlayer.Name
local myStatusFile = "status_" .. myUser .. ".json"
local myHopCommand = "hop_" .. myUser .. ".txt"

print("--- SCRIPT AKTIF: MONITOR (" .. myUser .. ") & POTATO GRAPHICS ---")

-- ====================================================
-- BAGIAN 1: POTATO GRAPHICS (PENGHAPUS LAG)
-- ====================================================

-- 1. Bersihkan Lighting (Bayangan & Efek Cahaya)
Lighting.GlobalShadows = false
Lighting.FogEnd = 9e9
Lighting.Brightness = 0

for _, v in pairs(Lighting:GetChildren()) do
    if v:IsA("PostEffect") or v:IsA("Sky") or v:IsA("Atmosphere") then
        v:Destroy()
    end
end

-- 2. Bersihkan Terrain (Air & Rumput)
if Terrain then
    Terrain.WaterWaveSize = 0
    Terrain.WaterWaveSpeed = 0
    Terrain.WaterReflectance = 0
    Terrain.WaterTransparency = 0
    Terrain.Decoration = false
end

-- 3. Fungsi Pembersih Objek (Aman: Tidak Menghapus Lantai/Dinding)
local function ClearObject(v)
    -- Jika Part/Dinding -> Ubah jadi Plastik (Jangan Destroy!)
    if v:IsA("BasePart") and not v:IsA("Terrain") then
        v.Material = Enum.Material.SmoothPlastic
        v.Reflectance = 0
        v.CastShadow = false
    
    -- Jika Gambar/Texture -> Sembunyikan
    elseif v:IsA("Texture") or v:IsA("Decal") then
        v.Transparency = 1
        
    -- Jika Efek Partikel (Api, Asap, Ledakan) -> Matikan
    elseif v:IsA("ParticleEmitter") or v:IsA("Trail") or v:IsA("Smoke") or v:IsA("Fire") or v:IsA("Sparkles") then
        v.Enabled = false
    end
end

-- 4. Scan Awal (Bersihkan map yang sudah loading)
for _, v in pairs(Workspace:GetDescendants()) do
    ClearObject(v)
end

-- 5. Auto Monitor Map Baru (StreamingEnabled Support)
-- Jika ada map baru loading, langsung dibersihkan otomatis
Workspace.DescendantAdded:Connect(function(v)
    task.wait(0.1) -- Tunggu properti load sebentar
    ClearObject(v)
end)

print("✅ Grafik telah dioptimalkan (Mode Ringan Aktif).")

-- ====================================================
-- BAGIAN 2: MONITOR & HOP LOGIC
-- ====================================================

-- Fungsi Hop Server (API V2)
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
            TPS:Teleport(PlaceID, Players.LocalPlayer) -- Rejoin jika server cuma 1
        end
    else
        TPS:Teleport(PlaceID, Players.LocalPlayer)
    end
end

-- Loop Utama (Heartbeat & Command Listener)
task.spawn(function()
    while true do
        task.wait(3) -- Lapor setiap 3 detik

        -- A. Tulis Laporan (Absen ke File JSON)
        local data = {
            username = myUser,
            jobId = game.JobId,
            placeId = game.PlaceId,
            timestamp = os.time() -- Penting untuk Anti-Freeze Python
        }
        
        pcall(function()
            writefile(myStatusFile, Http:JSONEncode(data))
        end)

        -- B. Cek Perintah Pindah dari Python
        if isfile(myHopCommand) then
            delfile(myHopCommand) -- Hapus surat perintah
            ServerHop()           -- Laksanakan
        end
    end
end)
