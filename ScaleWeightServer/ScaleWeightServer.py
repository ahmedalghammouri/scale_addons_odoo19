# -*- coding: utf-8 -*-
"""
Scale Weight Server - Desktop Application
Professional GUI for managing scale weight readings with simulation and real hardware modes
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import random
import serial
import serial.tools.list_ports
from flask import Flask, jsonify, request
from datetime import datetime
import logging
import os
import socket
from werkzeug.serving import make_server
from PIL import Image, ImageDraw
import pystray

class ScaleWeightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scale Weight Server - Professional Edition")
        self.root.geometry("1400x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#ecf0f1")
        
        # Center window on screen
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (1400 // 2)
        y = (screen_height // 2) - (700 // 2)
        self.root.geometry(f"1400x700+{x}+{y}")
        
        # Variables
        self.mode = tk.StringVar(value="simulation")
        self.serial_port = tk.StringVar(value="COM3")
        self.baudrate = tk.IntVar(value=9600)
        self.server_port = tk.IntVar(value=5000)
        self.current_weight = 0.0
        self.server_running = False
        self.serial_connection = None
        self.flask_server = None
        self.server_thread = None
        self.local_ip = self.get_local_ip()
        
        # System tray icon
        self.tray_icon = None
        self.setup_tray_icon()
        
        # Logging setup (before Flask)
        self.setup_logging()
        
        # Flask app
        self.app = Flask(__name__)
        self.setup_flask_routes()
        
        # UI Setup
        self.setup_ui()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initial log
        self.root.after(100, lambda: self.log("Application started successfully", "SUCCESS"))
        self.root.after(200, lambda: self.log(f"Local IP Address: {self.local_ip}", "INFO"))
        
    def get_local_ip(self):
        """Get local machine IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def create_tray_image(self):
        """Create system tray icon image"""
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='#2c3e50')
        dc = ImageDraw.Draw(image)
        
        # Draw scale icon
        dc.rectangle([10, 35, 54, 40], fill='#ecf0f1')
        dc.polygon([32, 15, 20, 35, 44, 35], fill='#3498db')
        dc.ellipse([28, 40, 36, 48], fill='#e74c3c')
        
        return image
    
    def setup_tray_icon(self):
        """Setup system tray icon"""
        image = self.create_tray_image()
        
        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self.show_window, default=True),
            pystray.MenuItem("Start Server", self.start_server_from_tray),
            pystray.MenuItem("Stop Server", self.stop_server_from_tray),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("scale_server", image, "Scale Weight Server", menu)
    
    def run_tray_icon(self):
        """Run tray icon in separate thread"""
        self.tray_icon.run()
    
    def show_window(self, icon=None, item=None):
        """Show main window"""
        self.root.after(0, self._show_window)
    
    def _show_window(self):
        """Show window in main thread"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide_window(self):
        """Hide window to tray"""
        self.root.withdraw()
        self.log("Application minimized to tray", "INFO")
    
    def on_closing(self):
        """Handle window close button"""
        if messagebox.askyesno("Minimize to Tray", "Minimize to system tray?\n\n(Click 'No' to exit completely)"):
            self.hide_window()
        else:
            self.quit_app()
    
    def start_server_from_tray(self, icon=None, item=None):
        """Start server from tray menu"""
        if not self.server_running:
            self.root.after(0, self.start_server)
    
    def stop_server_from_tray(self, icon=None, item=None):
        """Stop server from tray menu"""
        if self.server_running:
            self.root.after(0, self.stop_server)
    
    def quit_app(self, icon=None, item=None):
        """Quit application completely"""
        if self.server_running:
            self.stop_server()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.root.quit()
        self.root.destroy()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#1a252f", height=90)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text="⚖️ Scale Weight Server", 
                        font=("Arial", 26, "bold"), bg="#1a252f", fg="#ecf0f1")
        title.pack(pady=10)
        
        # IP Display
        ip_frame = tk.Frame(header, bg="#1a252f")
        ip_frame.pack(pady=(0, 10))
        
        tk.Label(ip_frame, text=f"🌐 Server IP: {self.local_ip}", 
                font=("Arial", 11), bg="#1a252f", fg="#3498db").pack(side=tk.LEFT, padx=5)
        
        tk.Button(ip_frame, text="⚙️ Settings", command=self.open_settings,
                 bg="#ecf0f1", font=("Arial", 9), 
                 relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(ip_frame, text="📥 Minimize to Tray", command=self.hide_window,
                 bg="#f39c12", fg="white", font=("Arial", 9), 
                 relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        # Main container with two columns
        container = tk.Frame(self.root, bg="#ecf0f1")
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left side - Controls
        left_frame = tk.Frame(container, bg="#ecf0f1")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        # Right side - Activity Log
        right_frame = tk.Frame(container, bg="#ecf0f1")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Mode Selection
        mode_frame = tk.LabelFrame(left_frame, text="⚙️ Operating Mode", font=("Arial", 11, "bold"),
                                   bg="#ecf0f1", fg="#2c3e50", padx=15, pady=12)
        mode_frame.pack(fill=tk.X, pady=(0, 12))
        
        tk.Radiobutton(mode_frame, text="🔄 Simulation Mode", variable=self.mode,
                      value="simulation", font=("Arial", 10), bg="#ecf0f1",
                      command=self.on_mode_change).pack(anchor=tk.W, pady=4)
        
        tk.Radiobutton(mode_frame, text="🔌 Real Hardware Scale", variable=self.mode,
                      value="hardware", font=("Arial", 10), bg="#ecf0f1",
                      command=self.on_mode_change).pack(anchor=tk.W, pady=4)
        
        # Hardware Configuration
        self.hw_frame = tk.LabelFrame(left_frame, text="🔧 Hardware Configuration", 
                                     font=("Arial", 11, "bold"),
                                     bg="#ecf0f1", fg="#2c3e50", padx=15, pady=12)
        self.hw_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Serial Port
        port_row = tk.Frame(self.hw_frame, bg="#ecf0f1")
        port_row.pack(fill=tk.X, pady=5)
        tk.Label(port_row, text="Serial Port:", font=("Arial", 10), 
                bg="#ecf0f1", width=15, anchor=tk.W).pack(side=tk.LEFT)
        self.port_combo = ttk.Combobox(port_row, textvariable=self.serial_port, 
                                       font=("Arial", 10), width=15)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        tk.Button(port_row, text="🔍 Refresh", command=self.refresh_ports,
                 bg="#3498db", fg="white", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Baudrate
        baud_row = tk.Frame(self.hw_frame, bg="#ecf0f1")
        baud_row.pack(fill=tk.X, pady=5)
        tk.Label(baud_row, text="Baud Rate:", font=("Arial", 10), 
                bg="#ecf0f1", width=15, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Combobox(baud_row, textvariable=self.baudrate, 
                    values=[4800, 9600, 19200, 38400, 57600, 115200],
                    font=("Arial", 10), width=15).pack(side=tk.LEFT, padx=5)
        
        # Weight Display
        weight_frame = tk.LabelFrame(left_frame, text="📊 Current Weight", 
                                    font=("Arial", 11, "bold"),
                                    bg="#ecf0f1", fg="#2c3e50", padx=15, pady=12)
        weight_frame.pack(fill=tk.X, pady=(0, 12))
        
        self.weight_label = tk.Label(weight_frame, text="0.00 kg", 
                                     font=("Arial", 36, "bold"), 
                                     bg="#ecf0f1", fg="#27ae60")
        self.weight_label.pack(pady=10)
        
        self.last_update = tk.Label(weight_frame, text="Last update: Never", 
                                    font=("Arial", 9), bg="#ecf0f1", fg="#7f8c8d")
        self.last_update.pack()
        
        # Status
        status_frame = tk.LabelFrame(left_frame, text="📡 Server Status", 
                                    font=("Arial", 11, "bold"),
                                    bg="#ecf0f1", fg="#2c3e50", padx=15, pady=10)
        status_frame.pack(fill=tk.X, pady=(0, 12))
        
        self.status_label = tk.Label(status_frame, text="● STOPPED", 
                                     font=("Arial", 12, "bold"),
                                     bg="#ecf0f1", fg="#e74c3c")
        self.status_label.pack()
        
        # Control Buttons
        btn_frame = tk.Frame(left_frame, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, pady=(0, 0))
        
        self.start_btn = tk.Button(btn_frame, text="▶ START SERVER", 
                                   command=self.start_server,
                                   bg="#27ae60", fg="white", 
                                   font=("Arial", 12, "bold"),
                                   height=2, cursor="hand2")
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stop_btn = tk.Button(btn_frame, text="⏹ STOP SERVER", 
                                  command=self.stop_server,
                                  bg="#e74c3c", fg="white", 
                                  font=("Arial", 12, "bold"),
                                  height=2, state=tk.DISABLED, cursor="hand2")
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Log Viewer (Right Side)
        log_frame = tk.LabelFrame(right_frame, text="📋 Activity Log", 
                                 font=("Arial", 11, "bold"),
                                 bg="#ecf0f1", fg="#2c3e50", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log controls
        log_ctrl = tk.Frame(log_frame, bg="#ecf0f1")
        log_ctrl.pack(fill=tk.X, pady=(0, 5))
        
        tk.Button(log_ctrl, text="🗑️ Clear Log", command=self.clear_log,
                 bg="#95a5a6", fg="white", font=("Arial", 9), width=12).pack(side=tk.LEFT, padx=2)
        
        tk.Label(log_ctrl, text="📁 Auto-saved daily to logs/ folder", 
                font=("Arial", 8), bg="#ecf0f1", fg="#7f8c8d").pack(side=tk.LEFT, padx=10)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=30, width=70,
                                                  font=("Consolas", 9),
                                                  bg="#1a252f", fg="#ecf0f1",
                                                  wrap=tk.WORD, state=tk.DISABLED,
                                                  relief=tk.FLAT, borderwidth=2)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure log tags
        self.log_text.tag_config("INFO", foreground="#5dade2")
        self.log_text.tag_config("SUCCESS", foreground="#52be80")
        self.log_text.tag_config("WARNING", foreground="#f8b739")
        self.log_text.tag_config("ERROR", foreground="#ec7063")
        self.log_text.tag_config("WEIGHT", foreground="#bb8fce")
        
        # Initialize
        self.refresh_ports()
        self.on_mode_change()
        
    def open_settings(self):
        """Open settings dialog"""
        if self.server_running:
            messagebox.showwarning("Warning", "Please stop the server before changing settings.")
            return
        
        # Create settings window
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Server Settings")
        settings_win.geometry("400x200")
        settings_win.resizable(False, False)
        settings_win.configure(bg="#ecf0f1")
        settings_win.transient(self.root)
        settings_win.grab_set()
        
        # Center window
        settings_win.update_idletasks()
        x = (settings_win.winfo_screenwidth() // 2) - (400 // 2)
        y = (settings_win.winfo_screenheight() // 2) - (200 // 2)
        settings_win.geometry(f"400x200+{x}+{y}")
        
        # Title
        tk.Label(settings_win, text="⚙️ Server Settings", 
                font=("Arial", 16, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(pady=20)
        
        # Port setting
        port_frame = tk.Frame(settings_win, bg="#ecf0f1")
        port_frame.pack(pady=20)
        
        tk.Label(port_frame, text="Server Port:", font=("Arial", 11), 
                bg="#ecf0f1", fg="#2c3e50").pack(side=tk.LEFT, padx=10)
        
        port_entry = tk.Entry(port_frame, font=("Arial", 11), width=10)
        port_entry.insert(0, str(self.server_port.get()))
        port_entry.pack(side=tk.LEFT, padx=10)
        
        tk.Label(port_frame, text="(1024-65535)", font=("Arial", 9), 
                bg="#ecf0f1", fg="#7f8c8d").pack(side=tk.LEFT)
        
        # Buttons
        btn_frame = tk.Frame(settings_win, bg="#ecf0f1")
        btn_frame.pack(pady=20)
        
        def save_settings():
            try:
                new_port = int(port_entry.get())
                if new_port < 1024 or new_port > 65535:
                    messagebox.showerror("Error", "Port must be between 1024 and 65535")
                    return
                
                old_port = self.server_port.get()
                self.server_port.set(new_port)
                self.log(f"Server port changed from {old_port} to {new_port}", "INFO")
                messagebox.showinfo("Success", f"Server port updated to {new_port}")
                settings_win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid port number")
        
        tk.Button(btn_frame, text="💾 Save", command=save_settings,
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                 width=10, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Cancel", command=settings_win.destroy,
                 bg="#95a5a6", fg="white", font=("Arial", 10, "bold"),
                 width=10, cursor="hand2").pack(side=tk.LEFT, padx=5)
    
    def setup_logging(self):
        """Setup file logging"""
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'scale_server_{datetime.now().strftime("%Y%m%d")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log(self, message, level="INFO"):
        """Add log entry to UI and file"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add icon based on level
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "WEIGHT": "⚖️"
        }
        icon = icons.get(level, "•")
        log_entry = f"[{timestamp}] {icon} {message}\n"
        
        # Log to file
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "SUCCESS":
            self.logger.info(f"✓ {message}")
        else:
            self.logger.info(message)
        
        # Log to UI (thread-safe)
        def update_ui():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry, level)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        if threading.current_thread() == threading.main_thread():
            update_ui()
        else:
            self.root.after(0, update_ui)
    
    def clear_log(self):
        """Clear log display"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.after(100, lambda: self.log("Log display cleared", "INFO"))
    
    def setup_flask_routes(self):
        @self.app.route('/get_weight', methods=['GET'])
        def get_weight():
            client_ip = request.remote_addr
            self.log(f"Request from {client_ip} → Weight: {self.current_weight:,.2f} kg", "WEIGHT")
            return jsonify({'weight': self.current_weight, 'success': True})
    
    def on_mode_change(self):
        mode = self.mode.get()
        self.log(f"Mode changed to: {mode.upper()}", "INFO")
        
        if mode == "simulation":
            for child in self.hw_frame.winfo_children():
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Combobox, tk.Entry, tk.Button)):
                        widget.config(state=tk.DISABLED if not isinstance(widget, tk.Button) or widget.cget('text') != '🔍 Refresh' else tk.NORMAL)
        else:
            for child in self.hw_frame.winfo_children():
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Combobox, tk.Entry, tk.Button)):
                        widget.config(state=tk.NORMAL)
    
    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports if ports else ['No ports found']
        if ports:
            self.log(f"Found {len(ports)} serial port(s): {', '.join(ports)}", "INFO")
            if self.serial_port.get() not in ports:
                self.serial_port.set(ports[0])
        else:
            self.log("No serial ports detected", "WARNING")
    
    def read_weight(self):
        if self.mode.get() == "simulation":
            # Simulation mode
            if random.random() > 0.5:
                return round(random.uniform(25000, 35000), 2)
            else:
                return round(random.uniform(10000, 15000), 2)
        else:
            # Hardware mode
            try:
                if not self.serial_connection or not self.serial_connection.is_open:
                    self.serial_connection = serial.Serial(
                        self.serial_port.get(), 
                        self.baudrate.get(), 
                        timeout=1
                    )
                    self.log(f"Connected to {self.serial_port.get()}", "SUCCESS")
                
                raw_line = self.serial_connection.readline().decode('utf-8').strip()
                # Parse weight from serial data (adjust parsing as needed)
                weight = float(''.join(filter(str.isdigit or '.'.__eq__, raw_line)))
                return round(weight, 2)
            except serial.SerialException as e:
                self.log(f"Serial error: {e}", "ERROR")
                return self.current_weight
            except Exception as e:
                self.log(f"Error reading weight: {e}", "WARNING")
                return self.current_weight
    
    def update_weight_display(self):
        if self.server_running:
            self.current_weight = self.read_weight()
            self.weight_label.config(text=f"{self.current_weight:,.2f} kg")
            self.last_update.config(text=f"Last update: {datetime.now().strftime('%H:%M:%S')}")
            self.root.after(1000, self.update_weight_display)
    
    def start_server(self):
        try:
            self.log("Starting server...", "INFO")
            
            self.server_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="● RUNNING", fg="#27ae60")
            
            # Create Flask server
            self.flask_server = make_server('0.0.0.0', self.server_port.get(), self.app)
            
            # Start Flask in thread
            self.server_thread = threading.Thread(target=self.run_flask, daemon=True)
            self.server_thread.start()
            
            # Start weight updates
            self.update_weight_display()
            
            self.log(f"Server started successfully on port {self.server_port.get()}", "SUCCESS")
            self.log(f"Access URL: http://{self.local_ip}:{self.server_port.get()}/get_weight", "INFO")
            self.log(f"Operating mode: {self.mode.get().upper()}", "INFO")
            
            messagebox.showinfo("Success", 
                              f"Server started successfully!\n\n"
                              f"URL: http://{self.local_ip}:{self.server_port.get()}/get_weight\n"
                              f"Mode: {self.mode.get().upper()}")
        except Exception as e:
            self.log(f"Failed to start server: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to start server: {e}")
            self.stop_server()
    
    def run_flask(self):
        """Run Flask server in thread"""
        try:
            self.flask_server.serve_forever()
        except Exception as e:
            if self.server_running:
                self.log(f"Server error: {e}", "ERROR")
    
    def stop_server(self):
        self.log("Stopping server...", "INFO")
        
        self.server_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="● STOPPED", fg="#e74c3c")
        
        # Stop Flask server
        if self.flask_server:
            try:
                self.flask_server.shutdown()
                self.flask_server = None
                self.log("Flask server stopped successfully", "SUCCESS")
            except Exception as e:
                self.log(f"Error stopping Flask server: {e}", "WARNING")
        
        # Close serial connection
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                self.log("Serial connection closed", "INFO")
            except Exception as e:
                self.log(f"Error closing serial: {e}", "WARNING")
        
        messagebox.showinfo("Stopped", "Server has been stopped successfully")

def main():
    root = tk.Tk()
    app = ScaleWeightApp(root)
    
    # Start tray icon in separate thread
    tray_thread = threading.Thread(target=app.run_tray_icon, daemon=True)
    tray_thread.start()
    
    root.mainloop()

if __name__ == '__main__':
    main()
