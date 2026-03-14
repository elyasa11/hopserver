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
        script_key="bsgBGCFyNACsuRuhGPGUWwRDnGVurKWV";
loadstring(game:HttpGet("https://api.luarmor.net/files/v4/loaders/a5a58eeb04e49c77c49e25ad33cf3b36.lua"))()
    end)
end)

-- =========================================================
-- JALUR 2: MONITOR & HOP (KOMUNIKASI PYTHON) - [FIXED VERSION]
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

        local pendingAction = "NONE"
        local currentStatus = "ACTIVE"

        -- A. BACA FILE DULU (Mencegah Race Condition dengan Python)
        if isfile(myStatusFile) then
            local success, content = pcall(readfile, myStatusFile)
            if success and content and content ~= "" then
                local parseSuccess, data = pcall(Http.JSONDecode, Http, content)
                if parseSuccess and data then
                    -- Tangkap perintah dari Python jika ada
                    if data.action == "HOP" then
                        pendingAction = "HOP"
                    end
                    if data.status == "RESTARTING" then
                        currentStatus = "RESTARTING"
                    end
                end
            end
        end

        -- B. EKSEKUSI PERINTAH ATAU UPDATE STATUS
        if pendingAction == "HOP" then
            print("⚠️ [THREAD 2] Menerima Perintah HOP dari Python! Memulai proses pindah server...")
            
            -- [FIX] Pamit ke Python agar tidak dianggap tabrakan lagi selama loading!
            local leavingData = {
                username = myUser,
                jobId = "LEAVING_SERVER", 
                placeId = game.PlaceId,
                isPrivate = false,
                timestamp = os.time(), 
                action = "NONE", 
                status = currentStatus
            }
            pcall(function() writefile(myStatusFile, Http:JSONEncode(leavingData)) end)

            ServerHop()
            task.wait(15) 
        else
            -- C. CEK VIP SERVER (Krusial untuk Anti-Tabrakan di Python)
            local isVip = (game.PrivateServerId ~= "" and game.PrivateServerId ~= nil)

            -- D. TULIS LAPORAN (Update Timestamp untuk Anti-Freeze)
            local data = {
                username = myUser,
                jobId = game.JobId,
                placeId = game.PlaceId,
                isPrivate = isVip, 
                timestamp = os.time(), 
                action = pendingAction, 
                status = currentStatus
            }
            pcall(function() writefile(myStatusFile, Http:JSONEncode(data)) end)
        end
    end
end)
