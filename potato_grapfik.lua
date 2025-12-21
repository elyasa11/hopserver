-- [[ GABUNGAN SCRIPT: CHIYO + FPS BOOST + RENDER TOGGLE ]] --

local RunService = game:GetService("RunService")
local CoreGui = game:GetService("CoreGui")
local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")

-- ==================================================================
-- 1. EKSEKUSI SCRIPT CHIYO (AUTO-LOAD)
-- ==================================================================
task.spawn(function()
    print("🚀 Meluncurkan Chiyo Loader...")
    local success, err = pcall(function()
        loadstring(game:HttpGet("https://raw.githubusercontent.com/kaisenlmao/loader/refs/heads/main/chiyo.lua"))()
    end)
    
    if success then
        print("✅ Chiyo berhasil dijalankan!")
    else
        warn("⚠️ Gagal menjalankan Chiyo: " .. tostring(err))
    end
end)

-- ==================================================================
-- 2. FPS BOOST / GRAPHIC OPTIMIZER (AMAN)
-- ==================================================================
local function optimize_graphics()
    -- Settingan Lighting
    Lighting.GlobalShadows = false
    Lighting.FogEnd = 9e9
    Lighting.Brightness = 0
    
    -- Hapus Efek Berat
    for _, v in pairs(Lighting:GetChildren()) do
        if v:IsA("PostEffect") then v.Enabled = false end
    end

    -- Settingan Terrain
    local Terrain = workspace.Terrain
    Terrain.WaterWaveSize = 0
    Terrain.WaterWaveSpeed = 0
    Terrain.WaterReflectance = 0
    Terrain.WaterTransparency = 0
    
    -- Paksa Settingan Render
    setsimulationradius(100, 100) -- Jika didukung executor
    settings().Rendering.QualityLevel = "Level01"

    -- Fungsi Pembersih Object
    local function clear_obj(v)
        pcall(function()
            if v:IsA("Part") or v:IsA("CornerWedgePart") or v:IsA("TrussPart") then
                v.Material = Enum.Material.SmoothPlastic
                v.Reflectance = 0
                v.CastShadow = false
            elseif v:IsA("MeshPart") then
                v.Material = Enum.Material.SmoothPlastic
                v.Reflectance = 0
                v.CastShadow = false
                v.TextureID = ""
            elseif v:IsA("Decal") or v:IsA("Texture") then
                v.Transparency = 1
            elseif v:IsA("ParticleEmitter") or v:IsA("Trail") or v:IsA("Smoke") or v:IsA("Fire") or v:IsA("Sparkles") then
                v.Enabled = false
            end
        end)
    end

    -- Proses Workspace
    for _, v in pairs(workspace:GetDescendants()) do
        clear_obj(v)
    end

    -- Auto-Optimize Object Baru
    workspace.DescendantAdded:Connect(function(v)
        task.spawn(function()
            task.wait(0.1)
            clear_obj(v)
        end)
    end)
end

-- Jalankan Optimizer
task.spawn(optimize_graphics)

-- ==================================================================
-- 3. TOMBOL TOGGLE 3D RENDER (LAYAR HITAM)
-- ==================================================================
task.spawn(function()
    -- Buat GUI
    local ScreenGui = Instance.new("ScreenGui")
    ScreenGui.Name = "SuperSaverGUI"
    
    -- Coba masukkan ke CoreGui (lebih aman dari reset), fallback ke PlayerGui
    pcall(function() ScreenGui.Parent = CoreGui end)
    if not ScreenGui.Parent then ScreenGui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui") end

    -- Buat Tombol
    local Button = Instance.new("TextButton")
    Button.Parent = ScreenGui
    Button.Size = UDim2.new(0, 150, 0, 50)
    Button.
