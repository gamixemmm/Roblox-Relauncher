-- Roblox Heartbeat Script
-- For use with Roblox executors (Synapse, Script-Ware, etc.)

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")

-- Configuration
local MONITOR_URL = "http://localhost:8080/heartbeat"
local HEARTBEAT_INTERVAL = 5  -- Send signal every 5 seconds

local player = Players.LocalPlayer

-- Get Roblox Process ID
local function getRobloxPID()
	if getgenv then
		-- Try to get PID from executor environment
		local env = getgenv()
		if env.pid or env.PID then
			return env.pid or env.PID
		end
	end
	
	-- Fallback: Try to get from identifyexecutor or other methods
	if identifyexecutor then
		local executor = identifyexecutor()
		-- Some executors expose PID differently
	end
	
	return nil
end

-- Function to send heartbeat using request()
local function sendHeartbeat()
	local success, response = pcall(function()
		local pid = getRobloxPID()
		
		local data = {
			timestamp = os.time(),
			player_name = player.Name,
			player_display_name = player.DisplayName,
			player_id = player.UserId,
			player_count = #Players:GetPlayers(),
			process_id = pid
		}
		
		local requestData = {
			Url = MONITOR_URL,
			Method = "POST",
			Headers = {
				["Content-Type"] = "application/json"
			},
			Body = HttpService:JSONEncode(data)
		}
		
		return request(requestData)
	end)
	
	if success then
		print("[Heartbeat] Signal sent successfully at", os.date("%H:%M:%S"), "- Player:", player.Name)
	else
		warn("[Heartbeat] Failed to send signal:", response)
	end
end

-- Send initial heartbeat
print("[Heartbeat] Starting heartbeat monitor...")
sendHeartbeat()

-- Main loop using task.spawn for better performance
task.spawn(function()
	while true do
		task.wait(HEARTBEAT_INTERVAL)
		sendHeartbeat()
	end
end)

-- Alternative: Use Heartbeat event for more precise timing
--[[
local lastHeartbeat = tick()
RunService.Heartbeat:Connect(function()
	if tick() - lastHeartbeat >= HEARTBEAT_INTERVAL then
		sendHeartbeat()
		lastHeartbeat = tick()
	end
end)
--]]
