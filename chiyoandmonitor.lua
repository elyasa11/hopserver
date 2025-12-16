--[[
    GRAND MASTER SCRIPT (PRIVATE SERVER SUPPORT)
    Fitur:
    1. Auto Farm (Cheat)
    2. Monitor & Hop (Support VIP: Disable Hop if VIP)
    3. Potato Graphics
]]

local Http = game:GetService("HttpService")
local TPS = game:GetService("TeleportService")
local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local Workspace = game:GetService("Workspace")

local myUser = Players.LocalPlayer.Name
local myStatusFile = "status_" .. myUser .. ".json"

-- Deteksi apakah ini Private Server?
-- (Jika OwnerId ada dan bukan 0, biasanya VIP)
local isPrivateServer = (game.PrivateServerId ~= "" and game.PrivateServerOwnerId ~= 0)

print("--- SYSTEM START (VIP MODE: " .. tostring(isPrivateServer) .. ") ---")

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

    -- Fungsi Blacklist (Non-Aktif jika di VIP)
    local function GetBlacklist()
        if isPrivateServer then return {} end -- Jangan blacklist siapapun di VIP

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
        if isPrivateServer then
            print("🔒 Sedang di Private Server. Hop dimatikan.")
            return 
        end

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
            -- JIKA DI VIP SERVER, ABAIKAN PERINTAH HOP!
            if isPrivateServer then
                 print("⚠️ Perintah HOP diterima tapi diabaikan (VIP Server).")
                 -- Tetap reset flag agar Python tidak spam
                 local cleanData = {
                    username = myUser,
                    jobId = game.JobId,
                    placeId = game.PlaceId,
                    timestamp = os.time(),
                    action = "NONE",
                    status = "ACTIVE",
                    isPrivate = true
                }
                pcall(function() writefile(myStatusFile, Http:JSONEncode(cleanData)) end)
            else
                print("⚠️ Perintah HOP Diterima! Pindah...")
                local cleanData = {
                    username = myUser,
                    jobId = game.JobId,
                    placeId = game.PlaceId,
                    timestamp = os.time(),
                    action = "NONE",
                    status = "HOPPING",
                    isPrivate = false
                }
                pcall(function() writefile(myStatusFile, Http:JSONEncode(cleanData)) end)
                task.wait(0.5) 
                SmartServerHop()
                task.wait(10) 
            end
        else
            -- Laporan Rutin Normal (Kirim status VIP ke Python)
            local data = {
                username = myUser,
                jobId = game.JobId,
                placeId = game.PlaceId,
                timestamp = os.time(),
                action = "NONE",
                status = "ACTIVE",
                isPrivate = isPrivateServer -- Flag Penting!
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
