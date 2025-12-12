--[[
    GRAND MASTER SCRIPT (FIXED LOOP)
    Fitur:
    1. Auto Farm (Cheat)
    2. Monitor & Hop (DENGAN RESET FLAG SEBELUM TELEPORT)
    3. Potato Graphics
]]

local Http = game:GetService("HttpService")
local TPS = game:GetService("TeleportService")
local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local Workspace = game:GetService("Workspace")

local myUser = Players.LocalPlayer.Name
local myStatusFile = "status_" .. myUser .. ".json"

print("--- SYSTEM START: 3 JALUR (ANTI-LOOP FIX) ---")

-- ================= JALUR 1: CHEAT =================
task.spawn(function()
    print(">>> [THREAD 1] Memuat Script Cheat...")
    task.wait(2)
    pcall(function()
        loadstring(game:HttpGet("https://raw.githubusercontent.com/kaisenlmao/loader/refs/heads/main/chiyo.lua"))()
    end)
end)

-- ================= JALUR 2: MONITOR & SMART HOP =================
task.spawn(function()
    print(">>> [THREAD 2] Memuat Smart Monitor...")

    -- Fungsi Blacklist & Smart Hop
    local function GetBlacklist()
        local blacklist = {}
        blacklist[game.JobId] = true 
        local files = listfiles("") 
        for _, path in pairs(files) do
            if string.find(path, "status_") and string.find(path, ".json") then
                local success, content = pcall(readfile, path)
                if success then
                    local data = Http:JSONDecode(content)
                    if data.jobId and data.timestamp and (os.time() - data.timestamp < 300) then
                        blacklist[data.jobId] = true
                    end
                end
            end
        end
        return blacklist
    end

    local function SmartServerHop()
        print("🕵️ Melakukan Smart Hop...")
        local BannedServers = GetBlacklist()
        local PlaceID = game.PlaceId
        local cursor = ""
        local found = false

        for i = 1, 10 do
            local url = "https://games.roblox.com/v1/games/" .. PlaceID .. "/servers/Public?sortOrder=Desc&limit=100"
            if cursor ~= "" then url = url .. "&cursor=" .. cursor end
            
            local success, result = pcall(function() return Http:JSONDecode(game:HttpGet(url)) end)
            
            if success and result and result.data then
                if result.nextPageCursor then cursor = result.nextPageCursor end
                for _, server in pairs(result.data) do
                    if not BannedServers[server.id] and server.playing < server.maxPlayers then
                        print("✅ Target Aman: " .. server.id)
                        TPS:TeleportToPlaceInstance(PlaceID, server.id, Players.LocalPlayer)
                        found = true
                        break
                    end
                end
            end
            if found then break end
            task.wait(0.2)
        end
        
        if not found then TPS:Teleport(PlaceID, Players.LocalPlayer) end
    end

    -- Loop Utama
    while true do
        task.wait(3)

        local shouldHop = false
        if isfile(myStatusFile) then
            local success, content = pcall(readfile, myStatusFile)
            if success and content and content ~= "" then
                local parseSuccess, data = pcall(Http.JSONDecode, Http, content)
                if parseSuccess and data and data.action == "HOP" then
                    shouldHop = true
                end
            end
        end

        if shouldHop then
            print("⚠️ Perintah HOP Diterima! Mereset status dan pindah...")
            
            -- >>> PERBAIKAN PENTING DI SINI <<<
            -- 1. HAPUS PERINTAH DULU (Reset Action jadi NONE)
            local cleanData = {
                username = myUser,
                jobId = game.JobId,
                placeId = game.PlaceId,
                timestamp = os.time(),
                action = "NONE", -- Matikan Trigger HOP
                status = "HOPPING"
            }
            pcall(function() writefile(myStatusFile, Http:JSONEncode(cleanData)) end)
            
            -- 2. TUNGGU SEBENTAR (Biar file tersimpan)
            task.wait(0.5) 
            
            -- 3. BARU PINDAH SERVER
            SmartServerHop()
            
            -- Stop loop sementara agar tidak spam hop saat teleport process
            task.wait(10) 
        else
            -- Laporan Rutin Normal
            local data = {
                username = myUser,
                jobId = game.JobId,
                placeId = game.PlaceId,
                timestamp = os.time(),
                action = "NONE",
                status = "ACTIVE"
            }
            pcall(function() writefile(myStatusFile, Http:JSONEncode(data)) end)
        end
    end
end)

-- ================= JALUR 3: POTATO GRAPHICS =================
task.spawn(function()
    print(">>> [THREAD 3] Memuat Potato Graphics...")
    task.wait(0.5)
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
    pcall(function()
        Lighting.GlobalShadows = false
        Lighting.FogEnd = 9e9
        Lighting.Brightness = 0
        for _, v in pairs(Lighting:GetChildren()) do
            if v:IsA("PostEffect") or v:IsA("Sky") or v:IsA("Atmosphere") then v:Destroy() end
        end
    end)
    for _, v in pairs(Workspace:GetDescendants()) do SafeClear(v) end
    Workspace.DescendantAdded:Connect(function(v) SafeClear(v) end)
end)

print("✅ SISTEM SIAP")
