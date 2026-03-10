-- Zypheron Hub | Sailor Piece - Cleaned & Formatted
local Rayfield = loadstring(game:HttpGet('https://sirius.menu/rayfield'))()
local Players = game:GetService("Players")
local LP = Players.LocalPlayer
local RS = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")

-- Remotes
local CombatRemote = RS:WaitForChild("CombatSystem"):WaitForChild("Remotes"):WaitForChild("RequestHit")
local AbilityRemote = RS:WaitForChild("AbilitySystem"):WaitForChild("Remotes"):WaitForChild("RequestAbility")
local RemoteEvents = RS:WaitForChild("RemoteEvents")

-- Variables
getgenv().AutoFarm = false
getgenv().AutoKillSelectedBosses = false
getgenv().AutoKillAllBosses = false
getgenv().BusoHaki = false
getgenv().ObservationHaki = false

local selectedMob = "None"
local selectedBoss = "None"
local selectedBossesToKill = {}
local selectedWeapon = "None"
local attackMethod = "Over"
local attackDistance = 10
local selectedSkills = {}

-- [ FUNCTIONS ] --

local function toggleBusoHaki()
    pcall(function()
        local hakiRemote = RemoteEvents:FindFirstChild("HakiRemote")
        if hakiRemote then
            hakiRemote:FireServer("Toggle")
        else
            warn("⚠️ HakiRemote tidak ditemukan!")
        end
    end)
end

local function toggleObservationHaki()
    pcall(function()
        local obsRemote = RemoteEvents:FindFirstChild("ObservationHakiRemote")
        if obsRemote then
            obsRemote:FireServer("Toggle")
        else
            warn("⚠️ ObservationHakiRemote tidak ditemukan!")
        end
    end)
end

local function reactivateAllHakis()
    task.wait(1.5)
    if getgenv().BusoHaki then
        toggleBusoHaki()
        print("✅ Buso Haki diaktifkan kembali!")
    end
    if getgenv().ObservationHaki then
        toggleObservationHaki()
        print("✅ Observation Haki diaktifkan kembali!")
    end
end

-- Death Handler
LP.CharacterAdded:Connect(function(char)
    local hum = char:WaitForChild("Humanoid")
    hum.Died:Connect(function()
        print("💀 Karakter mati! Mengaktifkan Haki dalam 5 detik...")
        task.wait(5)
        reactivateAllHakis()
    end)
    reactivateAllHakis()
end)

-- Haki Check Loop (Every 10s)
task.spawn(function()
    while task.wait(10) do
        pcall(function()
            if getgenv().BusoHaki or getgenv().ObservationHaki then
                local char = LP.Character
                if char and char:FindFirstChild("Humanoid") and char.Humanoid.Health > 0 then
                    if getgenv().BusoHaki then toggleBusoHaki() end
                    if getgenv().ObservationHaki then toggleObservationHaki() end
                end
            end
        end)
    end
end)

-- List Fetchers
local function getMobList()
    local mobs = {"None"}
    local seen = {}
    local npcsFolder = Workspace:FindFirstChild("NPCs")
    if npcsFolder then
        for _, npc in pairs(npcsFolder:GetChildren()) do
            if npc:FindFirstChild("Humanoid") then
                local baseName = npc.Name:gsub("%d+", ""):gsub("Boss", "")
                if not npc.Name:find("Boss") and baseName ~= "" and not seen[baseName] then
                    seen[baseName] = true
                    table.insert(mobs, baseName)
                end
            end
        end
    end
    table.sort(mobs)
    return mobs
end

local function getBossList()
    local bosses = {"None"}
    local npcsFolder = Workspace:FindFirstChild("NPCs")
    if npcsFolder then
        for _, npc in pairs(npcsFolder:GetChildren()) do
            if npc:FindFirstChild("Humanoid") and npc.Name:find("Boss") then
                if not table.find(bosses, npc.Name) then
                    table.insert(bosses, npc.Name)
                end
            end
        end
    end
    table.sort(bosses)
    return bosses
end

local function getAllWeapons()
    local weapons = {"None"}
    local backpack = LP:FindFirstChild("Backpack")
    local char = LP.Character
    if backpack then
        for _, tool in pairs(backpack:GetChildren()) do
            if tool:IsA("Tool") then table.insert(weapons, tool.Name) end
        end
    end
    if char then
        for _, tool in pairs(char:GetChildren()) do
            if tool:IsA("Tool") and not table.find(weapons, tool.Name) then
                table.insert(weapons, tool.Name)
            end
        end
    end
    return weapons
end

-- Utils
local function equipWeapon(name)
    if name == "None" then return end
    local char = LP.Character
    if not char then return end
    for _, tool in pairs(char:GetChildren()) do
        if tool:IsA("Tool") and tool.Name == name then return end
    end
    local backpack = LP:FindFirstChild("Backpack")
    if backpack then
        local tool = backpack:FindFirstChild(name)
        if tool then
            tool.Parent = char
            task.wait(0.3)
        end
    end
end

local function findNPC(name, isBoss)
    if name == "None" then return nil end
    local npcsFolder = Workspace:FindFirstChild("NPCs")
    if not npcsFolder then return nil end
    for _, npc in pairs(npcsFolder:GetChildren()) do
        local hum = npc:FindFirstChild("Humanoid")
        if not hum or hum.Health <= 0 then continue end
        if isBoss then
            if npc.Name == name then return npc end
        else
            if npc.Name:gsub("%d+", "") == name and not npc.Name:find("Boss") then
                return npc
            end
        end
    end
    return nil
end

local function getAttackPos(hrp)
    local d = attackDistance
    if attackMethod == "Over" then
        return hrp.Position + Vector3.new(0, d, 0)
    elseif attackMethod == "Behind" then
        return hrp.Position - (hrp.CFrame.LookVector * d)
    else
        return hrp.Position - Vector3.new(0, d, 0)
    end
end

local function freezeCharacter(char)
    if not char then return end
    local hrp = char:FindFirstChild("HumanoidRootPart")
    local hum = char:FindFirstChild("Humanoid")
    if hrp and hum then
        hrp.Anchored = false
        hrp.Velocity = Vector3.zero
        hum.PlatformStand = true
        hum.AutoRotate = false
    end
end

local function unfreezeCharacter(char)
    if not char then return end
    local hrp = char:FindFirstChild("HumanoidRootPart")
    local hum = char:FindFirstChild("Humanoid")
    if hrp and hum then
        hrp.Anchored = false
        hum.PlatformStand = false
        hum.AutoRotate = true
    end
end

-- [ LOOPS ] --

-- Auto Equip Weapon
task.spawn(function()
    while task.wait(2) do
        if getgenv().AutoFarm or getgenv().AutoKillSelectedBosses or getgenv().AutoKillAllBosses then
            equipWeapon(selectedWeapon)
        end
    end
end)

-- Auto Skills
RunService.Heartbeat:Connect(function()
    pcall(function()
        if table.find(selectedSkills, "1") then AbilityRemote:FireServer(1) end
        if table.find(selectedSkills, "2") then AbilityRemote:FireServer(2) end
    end)
end)

-- Main Farm Loop
task.spawn(function()
    while task.wait(0.05) do
        if getgenv().AutoFarm then
            pcall(function()
                local target = (selectedBoss ~= "None" and findNPC(selectedBoss, true)) 
                                or (selectedMob ~= "None" and findNPC(selectedMob, false))
                
                if target and target:FindFirstChild("HumanoidRootPart") and target.Humanoid.Health > 0 then
                    local char = LP.Character
                    if char and char:FindFirstChild("HumanoidRootPart") and char.Humanoid.Health > 0 then
                        local hrp = char.HumanoidRootPart
                        local pos = getAttackPos(target.HumanoidRootPart)
                        
                        freezeCharacter(char)
                        hrp.CFrame = CFrame.new(pos, target.HumanoidRootPart.Position)
                        CombatRemote:FireServer()
                    end
                end
            end)
        else
            unfreezeCharacter(LP.Character)
        end
    end
end)

-- [ UI WINDOW ] --

local Window = Rayfield:CreateWindow({
    Name = "Zypheron Hub | Sailor Piece",
    LoadingTitle = "Loading Zypheron Hub...",
    LoadingSubtitle = "by Zypheron",
    ConfigurationSaving = { Enabled = true, FolderName = "ZypheronHub", FileName = "SailorPiece" },
    KeySystem = false,
})

-- Main Tab
local MainTab = Window:CreateTab("Main", 4483362458)

MainTab:CreateSection("Mob")
local MobDropdown = MainTab:CreateDropdown({
    Name = "Select Mob",
    Options = getMobList(),
    CurrentOption = {"None"},
    MultipleOptions = false,
    Callback = function(Option) 
        selectedMob = Option[1] 
        selectedBoss = "None"
    end,
})

MainTab:CreateButton({
    Name = "Refresh Dropdown",
    Callback = function() MobDropdown:Refresh(getMobList()) end,
})

MainTab:CreateToggle({
    Name = "Auto Kill Selected Mob",
    CurrentValue = false,
    Callback = function(Value) getgenv().AutoFarm = Value end,
})

MainTab:CreateSection("Bosses")
local BossDropdown = MainTab:CreateDropdown({
    Name = "Select Boss",
    Options = getBossList(),
    CurrentOption = {"None"},
    MultipleOptions = false,
    Callback = function(Option) 
        selectedBoss = Option[1] 
        selectedMob = "None"
    end,
})

MainTab:CreateToggle({
    Name = "Auto Kill Selected Boss",
    CurrentValue = false,
    Callback = function(Value) getgenv().AutoFarm = Value end,
})

MainTab:CreateToggle({
    Name = "Auto Kill All Boss",
    CurrentValue = false,
    Callback = function(Value) getgenv().AutoKillAllBosses = Value end,
})

-- Haki Tab
local HakiTab = Window:CreateTab("Haki", 4483362458)
HakiTab:CreateToggle({
    Name = "🛡️ Buso Haki (Armament)",
    CurrentValue = false,
    Callback = function(Value) 
        getgenv().BusoHaki = Value 
        toggleBusoHaki() 
    end,
})

HakiTab:CreateToggle({
    Name = "👁️ Observation Haki",
    CurrentValue = false,
    Callback = function(Value) 
        getgenv().ObservationHaki = Value 
        toggleObservationHaki() 
    end,
})

-- Misc Tab
local MiscTab = Window:CreateTab("Misc", 4483362458)
local WeaponDropdown = MiscTab:CreateDropdown({
    Name = "Select Weapon",
    Options = getAllWeapons(),
    CurrentOption = {"None"},
    MultipleOptions = false,
    Callback = function(Option) selectedWeapon = Option[1] end,
})

local MethodDropdown = MiscTab:CreateDropdown({
    Name = "Select Method",
    Options = {"Over", "Behind", "Under"},
    CurrentOption = {"Over"},
    MultipleOptions = false,
    Callback = function(Option) attackMethod = Option[1] end,
})

MiscTab:CreateSlider({
    Name = "Distance",
    Range = {3, 20},
    Increment = 1,
    CurrentValue = 10,
    Callback = function(Value) attackDistance = Value end,
})

Rayfield:Notify({ Title = "✅ Zypheron Hub Loaded!", Content = "Script ready to use!", Duration = 5 })
