# Roblox Account Monitor

A comprehensive monitoring system that automatically detects when Roblox crashes and restarts it using Roblox Account Manager (RAM). Features both a graphical UI and console-only modes with real-time account tracking and automatic password management.

## Features

- **Real-time Monitoring**: Tracks multiple Roblox accounts simultaneously
- **Automatic Restart**: Uses RAM API to restart crashed accounts
- **Graphical Interface**: Modern dark-themed UI with account status display
- **Password Management**: Secure password storage with show/hide functionality
- **Process Management**: Kills specific Roblox processes before restarting
- **Configurable Timeouts**: Adjustable crash detection timing
- **Status Tracking**: Visual indicators for account health and restart progress

## Quick Start

1. **Download the Files**
   - Download all files to a folder on your computer
   - No manual installation needed - dependencies auto-install!

2. **Setup Roblox Account Manager**
   - Ensure RAM is running with API enabled (default port 7963)
   - Note your RAM password for configuration

3. **Enable HTTP Requests in Roblox**
   - In Roblox Studio: Home > Game Settings > Security > Allow HTTP Requests
   - Or add `--HttpService` launch flag

4. **Run the Monitor**
   ```bash
   python monitor_ui.py
   ```
   *Note: Missing dependencies will be automatically installed on first run*

5. **Add Heartbeat Script**
   - Copy `roblox_heartbeat.lua` to your Roblox game's ServerScriptService

## Installation Options

### Automatic (Recommended)
Simply run `python monitor_ui.py` - missing packages will be installed automatically.

### Manual Installation
If you prefer manual control:
```bash
pip install -r requirements.txt
python monitor_ui.py
```

## User Interface Guide

### Main Window
- **Account List**: Shows all monitored accounts with real-time status
- **Status Colors**: 
  - 🟢 Green: Healthy (>30s remaining)
  - 🟡 Yellow: Warning (10-30s remaining) 
  - 🔴 Red: Critical (<10s remaining)

### Password Configuration
- **RAM Password Field**: Enter your Roblox Account Manager password
- **Show/Hide Button**: Toggle password visibility for editing
- **Update Password**: Save new password (automatically persisted)
- **Auto-Save**: Password is saved to `monitor_config.json` and restored on restart

### Status Information
- **Port Status**: Shows listening port and timeout settings
- **Account Count**: Number of currently monitored accounts
- **Real-time Updates**: Interface refreshes every second

## Configuration Files

### monitor_config.json
Automatically created to store your settings:
```json
{
  "ram_password": "your_password_here"
}
```

### Script Configuration
Edit these values in `monitor_ui.py`:
```python
PORT = 8080              # Heartbeat listener port
TIMEOUT_SECONDS = 60     # Crash detection timeout
RAM_API_URL = "http://localhost:7963"  # RAM API endpoint
PLACE_ID = "5571328985"  # Roblox Place ID to launch
```

### Lua Script Configuration
Edit these values in `roblox_heartbeat.lua`:
```lua
MONITOR_URL = "http://localhost:8080/heartbeat"
HEARTBEAT_INTERVAL = 5   -- Seconds between heartbeats
```

## How It Works

1. **Heartbeat System**: Roblox sends signals every 5 seconds to the monitor
2. **Timeout Detection**: If no signal received for 60 seconds, account is marked as crashed
3. **Process Management**: Monitor kills the specific Roblox process by PID
4. **Automatic Restart**: Uses RAM API to launch the account in the specified place
5. **Status Tracking**: Real-time updates show restart progress and account health

## Account Status States

- **Online**: Receiving regular heartbeats
- **Timeout**: No heartbeat received, restart initiated
- **Killing Process**: Terminating crashed Roblox process
- **Restarting**: Launching account via RAM API
- **Relaunched - Waiting for signal**: Account launched, waiting for new heartbeat
- **Error**: Restart failed with error details

## Advanced Usage

### Multiple Accounts
The monitor automatically handles multiple accounts. Each account sends its own heartbeat with unique identification.

### Custom Place ID
Change `PLACE_ID` in the script to launch accounts into your specific Roblox game.

### Timeout Adjustment
- Increase `TIMEOUT_SECONDS` for slower games or reduce false positives
- Decrease for faster crash detection
- Minimum recommended: 30 seconds (allows for Roblox loading time)

### Console Mode
For headless operation, use:
```bash
python roblox_monitor_no_ui.py
```

## Troubleshooting

### Connection Issues
**"Cannot connect to RAM API"**
- Verify Roblox Account Manager is running
- Check RAM API port (default: 7963)
- Ensure RAM API is enabled in settings

**"Failed to send heartbeat" in Roblox**
- Enable HTTP requests in Roblox game settings
- Check Windows Firewall isn't blocking port 8080
- Verify monitor script is running

### Password Issues
**Password not saving**
- Check file permissions in script directory
- Ensure `monitor_config.json` can be created/modified
- Try running as administrator if needed

**RAM authentication failed**
- Verify password is correct in RAM
- Check if RAM requires specific authentication format
- Ensure account exists in RAM database

### Performance Issues
**High CPU usage**
- Increase heartbeat interval in Lua script
- Reduce UI update frequency if needed
- Close unnecessary Roblox instances

**Memory leaks**
- Restart monitor periodically for long-running sessions
- Monitor system resources during extended use

## File Structure

```
roblox-monitor/
├── monitor_ui.py           # Main GUI application
├── roblox_monitor_no_ui.py # Console-only version
├── roblox_heartbeat.lua    # Roblox game script
├── requirements.txt        # Python dependencies
├── monitor_config.json     # Auto-generated config file
└── README.md              # This documentation
```

## Requirements

- **Python 3.6+** with `requests` library
- **Roblox Account Manager** with API enabled
- **Roblox Studio** or game with HTTP requests enabled
- **Windows OS** (for process management features)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all configuration settings
3. Test with a single account first
4. Check console output for error messages
