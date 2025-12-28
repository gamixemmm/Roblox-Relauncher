import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime
import http.server
import socketserver
import requests
import json
import os

# Configuration
PORT = 8080
TIMEOUT_SECONDS = 60
RAM_API_URL = "http://localhost:7963"
RAM_PASSWORD = "passwd547s"  # Default password, can be changed in UI
PLACE_ID = "5571328985"  # Roblox Place ID to launch
CONFIG_FILE = "monitor_config.json"

def load_config():
    """Load configuration from file"""
    global RAM_PASSWORD
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                RAM_PASSWORD = config.get('ram_password', RAM_PASSWORD)
    except Exception as e:
        print(f"Error loading config: {e}")

def save_config():
    """Save configuration to file"""
    try:
        config = {
            'ram_password': RAM_PASSWORD
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

class RobloxMonitor:
    def __init__(self):
        self.running = True
        self.accounts = {}
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
                'process_id': data.get('process_id'),
                'status': 'Online'
            }
    
    def get_accounts_status(self):
        """Get status of all accounts"""
        current_time = time.time()
        accounts_list = []
        
        with self.lock:
            for player_name, info in self.accounts.items():
                time_since_signal = current_time - info['last_signal_time']
                time_until_timeout = max(0, TIMEOUT_SECONDS - time_since_signal)
                
                accounts_list.append({
                    'name': player_name,
                    'time_until_timeout': time_until_timeout,
                    'status': info.get('status', 'Online')
                })
        
        return accounts_list
    
    def check_timeouts(self):
        """Check all accounts for timeouts"""
        timed_out = []
        current_time = time.time()
        
        with self.lock:
            for player_name, info in self.accounts.items():
                if (current_time - info['last_signal_time']) > TIMEOUT_SECONDS:
                    # Only restart if not already in a restart state
                    status = info.get('status', 'Online')
                    if status not in ['Restarting', 'Killing Process', 'Relaunched']:
                        info['status'] = 'Timeout'
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
            return True
        except Exception as e:
            print(f"Failed to kill process {process_id}: {e}")
            return False
    
    def restart_roblox(self, player_name, info):
        """Restart Roblox for a specific account"""
        with self.lock:
            if player_name in self.accounts:
                self.accounts[player_name]['status'] = 'Killing Process'
        
        # Try to kill the specific Roblox process first
        process_id = info.get('process_id')
        if process_id:
            print(f"Killing Roblox process {process_id} for {player_name}")
            self.kill_process(process_id)
            time.sleep(1)  # Wait for process to die
        
        with self.lock:
            if player_name in self.accounts:
                self.accounts[player_name]['status'] = 'Restarting'
        
        try:
            params = {
                "Account": player_name,
                "Password": RAM_PASSWORD,
                "PlaceId": PLACE_ID
            }
            
            launch_url = f"{RAM_API_URL}/LaunchAccount"
            response = requests.get(launch_url, params=params, timeout=10)
            
            # Always treat as success (RAM returns 400 with empty error on success)
            with self.lock:
                if player_name in self.accounts:
                    # Reset timer to give 60 seconds for the game to load and send heartbeat
                    self.accounts[player_name]['last_signal_time'] = time.time()
                    self.accounts[player_name]['status'] = 'Relaunched - Waiting for signal'
            print(f"Successfully launched {player_name} - Timer reset to {TIMEOUT_SECONDS}s")
                
        except Exception as e:
            with self.lock:
                if player_name in self.accounts:
                    self.accounts[player_name]['status'] = f'Error: {str(e)[:20]}'

monitor = RobloxMonitor()

class SignalHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/heartbeat" or self.path == "/signal":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    monitor.update_signal(data)
            except:
                pass
            
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

class MonitorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Roblox Account Monitor")
        self.root.geometry("700x500")
        self.root.configure(bg='#1e1e1e')
        
        # Load saved password
        load_config()
        
        # Title
        title = tk.Label(root, text="Roblox Account Monitor", 
                        font=("Arial", 16, "bold"), 
                        bg='#1e1e1e', fg='#ffffff')
        title.pack(pady=10)
        
        # Configuration frame
        config_frame = tk.Frame(root, bg='#2d2d2d')
        config_frame.pack(fill='x', padx=10, pady=5)
        
        # Password field
        password_label = tk.Label(config_frame, text="RAM Password:", 
                                 font=("Arial", 10), 
                                 bg='#2d2d2d', fg='#ffffff')
        password_label.pack(side='left', padx=(10, 5), pady=5)
        
        self.password_var = tk.StringVar(value=RAM_PASSWORD)
        self.password_entry = tk.Entry(config_frame, 
                                      textvariable=self.password_var,
                                      font=("Arial", 10),
                                      bg='#3d3d3d', fg='#ffffff',
                                      insertbackground='#ffffff',
                                      width=20,
                                      show='*')
        self.password_entry.pack(side='left', padx=5, pady=5)
        
        # Update password button
        update_btn = tk.Button(config_frame, text="Update Password",
                              command=self.update_password,
                              font=("Arial", 9),
                              bg='#0078d7', fg='#ffffff',
                              relief='flat', padx=10)
        update_btn.pack(side='left', padx=5, pady=5)
        
        # Show/Hide password button
        self.show_password = False
        self.toggle_btn = tk.Button(config_frame, text="Show",
                                   command=self.toggle_password_visibility,
                                   font=("Arial", 9),
                                   bg='#404040', fg='#ffffff',
                                   relief='flat', padx=10)
        self.toggle_btn.pack(side='left', padx=5, pady=5)
        
        # Status bar
        self.status_frame = tk.Frame(root, bg='#2d2d2d')
        self.status_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_label = tk.Label(self.status_frame, 
                                     text=f"Listening on port {PORT} | Timeout: {TIMEOUT_SECONDS}s",
                                     font=("Arial", 10),
                                     bg='#2d2d2d', fg='#00ff00')
        self.status_label.pack(side='left', padx=10, pady=5)
        
        self.account_count = tk.Label(self.status_frame,
                                      text="Accounts: 0",
                                      font=("Arial", 10),
                                      bg='#2d2d2d', fg='#00aaff')
        self.account_count.pack(side='right', padx=10, pady=5)
        
        # Table frame
        table_frame = tk.Frame(root, bg='#1e1e1e')
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                       background="#2d2d2d",
                       foreground="white",
                       fieldbackground="#2d2d2d",
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background="#3d3d3d",
                       foreground="white",
                       borderwidth=1)
        style.map('Treeview', background=[('selected', '#0078d7')])
        
        self.tree = ttk.Treeview(table_frame, 
                                columns=('Player', 'Status', 'Timeout'),
                                show='headings',
                                yscrollcommand=scrollbar.set)
        
        self.tree.heading('Player', text='Player Name')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Timeout', text='Time Until Timeout')
        
        self.tree.column('Player', width=250)
        self.tree.column('Status', width=200)
        self.tree.column('Timeout', width=200)
        
        self.tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Update UI periodically
        self.update_ui()
    
    def update_ui(self):
        """Update the UI with current account status"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get accounts status
        accounts = monitor.get_accounts_status()
        self.account_count.config(text=f"Accounts: {len(accounts)}")
        
        # Add accounts to tree
        for acc in accounts:
            timeout_str = f"{int(acc['time_until_timeout'])}s"
            
            # Color code based on status
            if acc['time_until_timeout'] < 10:
                status_color = 'red'
            elif acc['time_until_timeout'] < 30:
                status_color = 'yellow'
            else:
                status_color = 'green'
            
            self.tree.insert('', 'end', values=(
                acc['name'],
                acc['status'],
                timeout_str
            ), tags=(status_color,))
        
        # Configure tags for colors
        self.tree.tag_configure('red', foreground='#ff4444')
        self.tree.tag_configure('yellow', foreground='#ffaa00')
        self.tree.tag_configure('green', foreground='#44ff44')
        
        # Schedule next update
        self.root.after(1000, self.update_ui)
    
    def update_password(self):
        """Update the RAM password and save it"""
        global RAM_PASSWORD
        new_password = self.password_var.get().strip()
        if new_password:
            RAM_PASSWORD = new_password
            save_config()  # Save the password to file
            # Update status to show password was changed and saved
            self.status_label.config(text=f"Listening on port {PORT} | Timeout: {TIMEOUT_SECONDS}s | Password Updated & Saved")
            # Reset status after 3 seconds
            self.root.after(3000, lambda: self.status_label.config(
                text=f"Listening on port {PORT} | Timeout: {TIMEOUT_SECONDS}s"))
    
    def toggle_password_visibility(self):
        """Toggle password field visibility"""
        self.show_password = not self.show_password
        if self.show_password:
            self.password_entry.config(show='')
            self.toggle_btn.config(text='Hide')
        else:
            self.password_entry.config(show='*')
            self.toggle_btn.config(text='Show')

def run_server():
    """Run the HTTP server"""
    with socketserver.TCPServer(("", PORT), SignalHandler) as httpd:
        httpd.serve_forever()

def monitor_timeout():
    """Monitor for timeout and restart if needed"""
    while monitor.running:
        time.sleep(5)
        timed_out_accounts = monitor.check_timeouts()
        
        for player_name, info in timed_out_accounts:
            monitor.restart_roblox(player_name, info)
            time.sleep(2)

if __name__ == "__main__":
    # Start server thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_timeout, daemon=True)
    monitor_thread.start()
    
    # Start UI
    root = tk.Tk()
    app = MonitorUI(root)
    root.mainloop()
    
    monitor.running = False
