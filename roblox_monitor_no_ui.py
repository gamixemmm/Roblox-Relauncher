import http.server
import socketserver
import threading
import time
import requests
import json
from datetime import datetime

# Configuration
PORT = 8080
TIMEOUT_SECONDS = 2
RAM_API_URL = "http://localhost:7963"  # Default Roblox Account Manager API port
RAM_PASSWORD = "passwd547s"  # RAM API password
PLACE_ID = "5571328985"  # Roblox Place ID to launch

class RobloxMonitor:
    def __init__(self):
        self.running = True
        self.accounts = {}  # Dictionary to track each account separately
        self.lock = threading.Lock()
        
    def update_signal(self, data=None):
        """Update the last signal time for a specific account"""
        if not data or not data.get('player_name'):
            return
        
        player_name = data.get('player_name')
        
        with self.lock:
            self.accounts[player_name] = {
                'last_signal_time': time.time(),
                'player_id': data.get('player_id'),
                'process_id': data.get('process_id')
            }
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Signal received - Player: {player_name} (Total accounts: {len(self.accounts)})")
    
    def check_timeouts(self):
        """Check all accounts for timeouts and return list of timed out accounts"""
        timed_out = []
        current_time = time.time()
        
        with self.lock:
            for player_name, info in self.accounts.items():
                if (current_time - info['last_signal_time']) > TIMEOUT_SECONDS:
                    # Only restart if not already marked as restarting
                    if not info.get('restarting', False):
                        info['restarting'] = True
                        timed_out.append((player_name, info))
        
        return timed_out
    
    def kill_process(self, process_id):
        """Kill a specific Roblox process by PID"""
        if not process_id:
            return False
        
        try:
            import subprocess
            # Use taskkill on Windows to force kill the process
            subprocess.run(['taskkill', '/F', '/PID', str(process_id)], 
                          capture_output=True, timeout=5)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Killed process {process_id}")
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to kill process {process_id}: {e}")
            return False
    
    def restart_roblox(self, player_name, info):
        """Restart Roblox for a specific account using RAM API"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No signal for {TIMEOUT_SECONDS}s - {player_name} may have crashed")
        
        # Try to kill the specific Roblox process first
        process_id = info.get('process_id')
        if process_id:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Killing Roblox process {process_id} for {player_name}")
            self.kill_process(process_id)
            time.sleep(1)  # Wait for process to die
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Attempting to restart via RAM API...")
        
        try:
            # Build launch URL with parameters
            params = {
                "Account": player_name,
                "Password": RAM_PASSWORD,
                "PlaceId": PLACE_ID
            }
            
            launch_url = f"{RAM_API_URL}/LaunchAccount"
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Launching {player_name} to PlaceId: {PLACE_ID}")
            
            # Launch Roblox account
            response = requests.get(launch_url, params=params)
            
            # Always treat as success (RAM returns 400 with empty error on success)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Successfully launched Roblox for player: {player_name}")
            # Reset timer to give 60 seconds for the game to load and send heartbeat
            with self.lock:
                if player_name in self.accounts:
                    self.accounts[player_name]['last_signal_time'] = time.time()
                    self.accounts[player_name]['restarting'] = False
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Timer reset to {TIMEOUT_SECONDS}s for {player_name}")
                
        except requests.exceptions.ConnectionError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Cannot connect to RAM API at {RAM_API_URL}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Make sure Roblox Account Manager is running")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {str(e)}")

monitor = RobloxMonitor()

class SignalHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests (heartbeat signals)"""
        if self.path == "/heartbeat" or self.path == "/signal":
            monitor.update_signal()
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/heartbeat" or self.path == "/signal":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    monitor.update_signal(data)
                else:
                    monitor.update_signal()
            except:
                monitor.update_signal()
            
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_server():
    """Run the HTTP server"""
    with socketserver.TCPServer(("", PORT), SignalHandler) as httpd:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Listener started on http://localhost:{PORT}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for signals from Roblox...")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Timeout: {TIMEOUT_SECONDS} seconds")
        httpd.serve_forever()

def monitor_timeout():
    """Monitor for timeout and restart if needed"""
    while monitor.running:
        time.sleep(5)  # Check every 5 seconds
        
        # Check all accounts for timeouts
        timed_out_accounts = monitor.check_timeouts()
        
        for player_name, info in timed_out_accounts:
            monitor.restart_roblox(player_name, info)
            time.sleep(2)  # Small delay between relaunches

if __name__ == "__main__":
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Start timeout monitor
    try:
        monitor_timeout()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Shutting down...")
        monitor.running = False
