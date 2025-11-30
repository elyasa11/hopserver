--[[
    GRAND MASTER SCRIPT (3 THREADS)
    Thread A: Auto Farm (Cheat)
    Thread B: Monitor & Hop (Database)
    Thread C: Potato Graphics (Anti-Lag)
]]

local Http = game:GetService("HttpService")
local TPS = game:GetService("TeleportService")
local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local Workspace = game:GetService("Workspace")

-- === KONFIGURASI UMUM ===
local myUser = Players.LocalPlayer.Name
local myStatusFile = "status_" .. myUser .. ".json"

print("--- SYSTEM START: 3 JALUR PARALEL ---")

-- =========================================================
-- JALUR 1: AUTO FARM (CHEAT)
-- =========================================================
task.spawn(function()
    print(">>> [THREAD 1] Memuat Script Cheat...")
    task.wait(2) -- Beri jeda sedikit agar game stabil dulu
    
    local success, err = pcall(function()
        -- GANTI LINK INI DENGAN SCRIPT FARM KAMU
        loadstring(game:HttpGet("https://raw.githubusercontent.com/Omgshit/Scripts/main/MainLoader.lua"))()
    end)
    
    if success then
        print(">>> [THREAD 1] Cheat Berhasil Jalan.")
    else
        warn(">>> [THREAD 1] Gagal memuat Cheat: " .. tostring(err))
    end
end)

-- =========================================================
-- JALUR 2: MONITOR & HOP (KOMUNIKASI PYTHON)
-- =========================================================
task.spawn(function()
    print(">>> [THREAD 2] Memuat Monitor...")
    
    -- Fungsi Hop Server
    local function ServerHop()
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
                TPS:Teleport(PlaceID, Players.LocalPlayer)
            end
        else
            TPS:Teleport(PlaceID, Players.LocalPlayer)
        end
    end

    -- Loop Absen & Cek Perintah
    while true do
        task.wait(3) -- Lapor setiap 3 detik

        -- A. BACA FILE (Cek Perintah HOP)
        local shouldHop = false
        if isfile(myStatusFile) then
            local success, content = pcall(readfile, myStatusFile)
            if success and content and content ~= "" then
                local parseSuccess, data = pcall(Http.JSONDecode, Http, content)
                -- Jika ada bendera ACTION: HOP dari Python
                if parseSuccess and data and data.action == "HOP" then
                    shouldHop = true
                end
            end
        end

        if shouldHop then
            print("⚠️ [THREAD 2] Menerima Perintah HOP dari Python!")
            ServerHop()
        else
            -- B. TULIS LAPORAN (Update Timestamp untuk Anti-Freeze)
            local data = {
                username = myUser,
                jobId = game.JobId,
                placeId = game.PlaceId,
                timestamp = os.time(), -- Kunci Anti-Freeze
                action = "NONE",
                status = "ACTIVE"
            }
            pcall(function()
                writefile(myStatusFile, Http:JSONEncode(data))
            end)
        end
    end
end)

-- =========================================================
-- JALUR 3: POTATO GRAPHICS (OPTIMASI VISUAL)
-- =========================================================
task.spawn(function()
    print(">>> [THREAD 3] Memuat Potato Graphics...")
    task.wait(0.5) -- Jalan paling awal

    -- Fungsi Hapus Aman
    local function SafeClear(v)
        pcall(function()
            if v:IsA("BasePart") and not v:IsA("Terrain") then
                v.Material = Enum.Material.SmoothPlastic
                v.Reflectance = 0
                v.CastShadow = false
            elseif v:IsA("Texture") or v:IsA("Decal") then
                v.Transparency = 1
            elseif v:IsA("ParticleEmitter") or v:IsA("Trail") or v:IsA("Smoke") or v:IsA("Fire") or v:IsA("Sparkles") then
                v.Enabled = false
            end
        end)
    end

    -- 1. Bersihkan Lighting
    pcall(function()
        Lighting.GlobalShadows = false
        Lighting.FogEnd = 9e9
        Lighting.Brightness = 0
        for _, v in pairs(Lighting:GetChildren()) do
            if v:IsA("PostEffect") or v:IsA("Sky") or v:IsA("Atmosphere") then v:Destroy() end
        end
    end)

    -- 2. Bersihkan Map Awal
    for _, v in pairs(Workspace:GetDescendants()) do
        SafeClear(v)
    end
    
    -- 3. Monitor Map Baru (StreamingEnabled)
    Workspace.DescendantAdded:Connect(function(v)
        SafeClear(v)
    end)
    
    print(">>> [THREAD 3] Grafik Dioptimalkan.")
end)

print("✅ SEMUA SISTEM BERJALAN AMAN")
