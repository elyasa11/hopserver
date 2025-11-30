--[[
    ALL-IN-ONE: MONITOR V2 (DATABASE METHOD)
    Fitur: Potato Graphics + Reader/Writer Config JSON
]]

local Http = game:GetService("HttpService")
local TPS = game:GetService("TeleportService")
local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local Workspace = game:GetService("Workspace")
local Terrain = Workspace:FindFirstChildOfClass("Terrain")

-- === CONFIG ===
local myUser = Players.LocalPlayer.Name
local myStatusFile = "status_" .. myUser .. ".json"

print("--- SCRIPT AKTIF: " .. myUser .. " (MODE DATABASE) ---")

-- ====================================================
-- BAGIAN 1: POTATO GRAPHICS (OPTIMASI)
-- ====================================================
Lighting.GlobalShadows = false
Lighting.FogEnd = 9e9
Lighting.Brightness = 0
for _, v in pairs(Lighting:GetChildren()) do
    if v:IsA("PostEffect") or v:IsA("Sky") or v:IsA("Atmosphere") then v:Destroy() end
end
if Terrain then
    Terrain.WaterWaveSize = 0
    Terrain.WaterReflectance = 0
    Terrain.Decoration = false
end
local function ClearObject(v)
    if v:IsA("BasePart") and not v:IsA("Terrain") then
        v.Material = Enum.Material.SmoothPlastic
        v.Reflectance = 0
        v.CastShadow = false
    elseif v:IsA("Texture") or v:IsA("Decal") then
        v.Transparency = 1
    elseif v:IsA("ParticleEmitter") or v:IsA("Trail") or v:IsA("Smoke") or v:IsA("Fire") or v:IsA("Sparkles") then
        v.Enabled = false
    end
end
for _, v in pairs(Workspace:GetDescendants()) do ClearObject(v) end
Workspace.DescendantAdded:Connect(function(v) task.wait(0.1); ClearObject(v) end)

-- ====================================================
-- BAGIAN 2: DATABASE LOGIC (READ & WRITE)
-- ====================================================

local function ServerHop()
    print("⚠️ PERINTAH 'HOP' DITERIMA DARI FILE CONFIG!")
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

-- Loop Utama
task.spawn(function()
    while true do
        task.wait(3) -- Interval lapor

        -- 1. BACA FILE DULU (Cek apakah ada surat dari Python?)
        local shouldHop = false
        
        if isfile(myStatusFile) then
            local success, content = pcall(readfile, myStatusFile)
            if success and content then
                local data = Http:JSONDecode(content)
                -- Cek apakah ada bendera ACTION: HOP
                if data.action == "HOP" then
                    shouldHop = true
                end
            end
        end

        if shouldHop then
            -- Jika disuruh Hop, lakukan Hop (Script akan berhenti di sini karena teleport)
            ServerHop()
        else
            -- 2. JIKA AMAN, TULIS LAPORAN (ABSEN)
            -- Kita reset 'action' jadi 'NONE'
            local data = {
                username = myUser,
                jobId = game.JobId,
                placeId = game.PlaceId,
                timestamp = os.time(),
                action = "NONE", -- Status normal
                status = "ACTIVE"
            }
            pcall(function()
                writefile(myStatusFile, Http:JSONEncode(data))
            end)
        end
    end
end)
