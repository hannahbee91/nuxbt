import sys
import subprocess
import webbrowser
import os
import psutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QMessageBox, QLineEdit)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from shutil import which

from .bluez import is_nuxbt_plugin_enabled

class NuxbtGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NUXBT")
        self.setMinimumSize(600, 300)
        
        self.webapp_pid = None
        self.webapp_process = None

        # Setup UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left Half
        left_layout = QVBoxLayout()
        self.logo_label = QLabel()
        self.logo_path = self.find_logo()
        
        if self.logo_path and os.path.exists(self.logo_path):
            pixmap = QPixmap(self.logo_path)
            self.logo_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.logo_label.setText("NUXBT LOGO")
        
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel("NUXBT GUI")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = title_label.font()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        left_layout.addWidget(title_label)
        left_layout.addWidget(self.logo_label)
        main_layout.addLayout(left_layout)

        # Right Half
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status Row
        status_container = QWidget()
        status_row = QHBoxLayout(status_container)
        
        self.status_label = QLabel("Loading...")
        status_font = self.status_label.font()
        status_font.setPointSize(12)
        self.status_label.setFont(status_font)
        
        self.status_light = QLabel("●") # Light indicator
        light_font = self.status_light.font()
        light_font.setPointSize(16)
        self.status_light.setFont(light_font)
        
        self.toggle_btn = QPushButton("Toggle")
        self.toggle_btn.clicked.connect(self.toggle_plugin)
        
        status_row.addWidget(self.status_label)
        status_row.addWidget(self.status_light)
        status_row.addWidget(self.toggle_btn)
        
        right_layout.addWidget(status_container)
        
        # WebApp Section
        webapp_section = QWidget()
        webapp_layout = QVBoxLayout(webapp_section)
        webapp_layout.setContentsMargins(0, 0, 0, 0)
        webapp_layout.setSpacing(0)
        
        # Main Button Row
        btn_row_widget = QWidget()
        btn_row = QHBoxLayout(btn_row_widget)
        btn_row.setContentsMargins(0, 0, 0, 0)
        
        self.main_webapp_btn = QPushButton("Launch WebApp")
        self.main_webapp_btn.clicked.connect(self.handle_webapp_action)
        self.main_webapp_btn.setMinimumHeight(40)

        self.open_webapp_btn = QPushButton("Open WebApp")
        self.open_webapp_btn.clicked.connect(self.open_webapp)
        self.open_webapp_btn.setMinimumHeight(40)
        self.open_webapp_btn.setVisible(False)
        
        self.options_toggle_btn = QPushButton("▼") # or ▶
        self.options_toggle_btn.setFixedSize(40, 40)
        self.options_toggle_btn.setCheckable(True)
        self.options_toggle_btn.toggled.connect(self.toggle_options)
        self.options_toggle_btn.setText("▶") # Start collapsed
        
        btn_row.addWidget(self.main_webapp_btn)
        btn_row.addWidget(self.open_webapp_btn)
        btn_row.addWidget(self.options_toggle_btn)
        
        webapp_layout.addWidget(btn_row_widget)
        
        # Collapsible Options Area
        self.options_container = QWidget()
        options_layout = QVBoxLayout(self.options_container)
        options_layout.setContentsMargins(10, 5, 10, 5) # Indent
        
        # Host Input
        host_row = QHBoxLayout()
        host_label = QLabel("Host:")
        self.host_input = QLineEdit("0.0.0.0")
        host_row.addWidget(host_label)
        host_row.addWidget(self.host_input)
        options_layout.addLayout(host_row)
        
        # Port Input
        port_row = QHBoxLayout()
        port_label = QLabel("Port:")
        self.port_input = QLineEdit("8000")
        port_row.addWidget(port_label)
        port_row.addWidget(self.port_input)
        options_layout.addLayout(port_row)
        
        # Initially hidden
        self.options_container.setVisible(False)
        webapp_layout.addWidget(self.options_container)
        
        right_layout.addWidget(webapp_section)
        
        # Launch TUI Button
        self.launch_tui_btn = QPushButton("Launch TUI")
        self.launch_tui_btn.clicked.connect(self.launch_tui)
        self.launch_tui_btn.setMinimumHeight(40)
        right_layout.addWidget(self.launch_tui_btn)
        
        main_layout.addLayout(right_layout)

        # Timer for updating status
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_status)
        self.refresh_timer.start(2000)
        self.update_status()

    def find_logo(self):
        # Check common paths
        candidates = [
            "docs/img/nuxbt-logo.png", # Dev relative
            "/usr/share/icons/hicolor/512x512/apps/nuxbt.png", # Installed
            os.path.join(os.path.dirname(__file__), "../docs/img/nuxbt-logo.png"), # Relative to file
            "/usr/lib/nuxbt/docs/img/nuxbt-logo.png" # Nfpm current copy?
        ]
        
        # If running from source, find relative to package
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(base_dir, "docs/img/nuxbt-logo.png"))

        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def update_status(self):
        enabled = is_nuxbt_plugin_enabled()
        if enabled:
            self.status_label.setText("NUXBT Plugin Enabled")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.status_light.setStyleSheet("color: green;")
            
            # Check webapp state
            self.check_webapp_state()
            
            self.main_webapp_btn.setEnabled(True)
            self.launch_tui_btn.setEnabled(True)
            
            # Only enable inputs if webapp is NOT running
            if not self.webapp_pid:
                self.host_input.setEnabled(True)
                self.port_input.setEnabled(True)
            
            self.options_toggle_btn.setEnabled(True)
        else:
            self.status_label.setText("NUXBT Plugin Disabled")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.status_light.setStyleSheet("color: red;")
            self.main_webapp_btn.setEnabled(False)
            self.open_webapp_btn.setVisible(False)
            self.launch_tui_btn.setEnabled(False)
            self.host_input.setEnabled(False)
            self.port_input.setEnabled(False)
            self.options_toggle_btn.setEnabled(False) # Disable toggle if plugin is disabled

    def toggle_options(self, checked):
        self.options_container.setVisible(checked)
        self.options_toggle_btn.setText("▼" if checked else "▶")
        # Force layout update and resize
        # If we are expanding, we might need more space.
        # If we are fixed size, it might be clipping.
        # But we removed fixed size below hopefully.
        self.resize(self.sizeHint())

    def toggle_plugin(self):
        try:
            enabled = is_nuxbt_plugin_enabled()
            # We want to toggle to the opposite state
            target_state = not enabled
            
            from .bluez import get_toggle_commands
            commands = get_toggle_commands(target_state)
            
            # Chain commands with &&
            full_cmd = " && ".join(commands)
            
            pkexec_cmd = ["pkexec", "sh", "-c", full_cmd]
            
            ret = subprocess.run(pkexec_cmd, capture_output=True, text=True)
            
            if ret.returncode != 0:
                # User might have cancelled or error
                if "incorrect password" in ret.stderr.lower() or "authentication" in ret.stderr.lower():
                     return # Just cancel
                
                if not ret.stderr.strip():
                     return

                QMessageBox.critical(self, "Error", f"Failed to toggle plugin:\n{ret.stderr}")
            else:
                 self.update_status()
                 
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def find_terminal(self):
        terms = ["gnome-terminal", "konsole", "xfce4-terminal", "lxterminal", "xterm"]
        for t in terms:
            if which(t):
                # gnome-terminal needs '--' before command sometimes
                return t
        
        # generic
        if which("x-terminal-emulator"):
            return "x-terminal-emulator"
        
        return None

    def find_running_webapp(self):
        """Find any running nuxbt webapp process."""
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check for python process running nuxbt webapp
                cmdline = proc.info['cmdline']
                if cmdline:
                    # Check if 'webapp' is an argument
                    if 'webapp' in cmdline:
                        # Check if 'nuxbt' is in any argument (e.g. path to script)
                        if any('nuxbt' in arg for arg in cmdline):
                            if proc.pid != current_pid: 
                                return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return None

    def check_webapp_state(self):
        # Check if our child process is still alive
        if self.webapp_process:
            if self.webapp_process.poll() is not None:
                self.webapp_process = None
                self.webapp_pid = None
        
        # If not, check for external process
        if not self.webapp_process:
            proc = self.find_running_webapp()
            if proc:
                self.webapp_pid = proc.pid
            else:
                self.webapp_pid = None
        
        # Update UI
        if self.webapp_pid:
            self.main_webapp_btn.setText("Stop WebApp")
            self.main_webapp_btn.setStyleSheet("background-color: #d30000;") 
            self.open_webapp_btn.setVisible(True)
            self.host_input.setEnabled(False)
            self.port_input.setEnabled(False)
        else:
            self.main_webapp_btn.setText("Launch WebApp")
            self.main_webapp_btn.setStyleSheet("")
            self.open_webapp_btn.setVisible(False)
            self.host_input.setEnabled(True)
            self.port_input.setEnabled(True)

    def handle_webapp_action(self):
        if self.webapp_pid:
            self.stop_webapp()
        else:
            self.launch_webapp()

    def stop_webapp(self):
        # Update UI first
        self.main_webapp_btn.setText("Stopping...")
        self.main_webapp_btn.setEnabled(False)
        QApplication.processEvents()
        
        # Perform robust cleanup
        self.terminate_all_webapps()
        
        # Refresh status to reset UI state
        self.update_status()

    def terminate_all_webapps(self):
        """Robustly terminate all known and unknown webapp processes."""
        # 1. Terminate our child process if we have the handle
        if self.webapp_process:
            print("Terminating child process...")
            self.webapp_process.terminate()
            try:
                self.webapp_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                 self.webapp_process.kill()
            self.webapp_process = None

        # 2. Terminate tracked pid if different or handle lost
        if self.webapp_pid:
             print(f"Terminating tracked process {self.webapp_pid}...")
             try:
                 proc = psutil.Process(self.webapp_pid)
                 if proc.is_running():
                     proc.terminate()
                     proc.wait(timeout=2)
             except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                 pass # Process gone or timeout handled below
             except Exception as e:
                 print(f"Error terminating tracked: {e}")
             self.webapp_pid = None

        # 3. Sweep for ANY leftover nuxbt webapp processes to be safe
        print("Sweeping for leftover webapp processes...")
        
        # We iterate max 3 times to be sure
        for _ in range(3):
            leftover = self.find_running_webapp()
            if not leftover:
                break
            
            print(f"Found leftover process {leftover.pid}. Killing...")
            try:
                leftover.terminate()
                leftover.wait(timeout=1)
            except psutil.TimeoutExpired:
                try:
                    leftover.kill()
                except:
                    pass
            except psutil.NoSuchProcess:
                pass

    def open_webapp(self):
        host = self.host_input.text()
        if host == "0.0.0.0":
            host = "localhost"
        port = self.port_input.text()
        webbrowser.open(f"http://{host}:{port}")

    def launch_webapp(self):
        try:
            # Check if already running first
            existing = self.find_running_webapp()
            if existing: # Should be covered by update_status but double check
                 self.webapp_pid = existing.pid
                 self.update_status()
                 QMessageBox.information(self, "Info", "WebApp is already running.")
                 self.open_webapp()
                 return

            host = self.host_input.text()
            port = self.port_input.text()
            
            # Validate port
            if not port.isdigit():
                 QMessageBox.warning(self, "Invalid Input", "Port must be a number.")
                 return
            
            # Launch background process
            # nuxbt webapp -i HOST -p PORT
            self.webapp_process = subprocess.Popen(["nuxbt", "webapp", "-i", host, "-p", port], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             start_new_session=True)
            self.webapp_pid = self.webapp_process.pid
            
            # Open browser
            QTimer.singleShot(1000, self.open_webapp)
            self.update_status()
            
        except Exception as e:
             QMessageBox.critical(self, "Error", f"Failed to launch webapp: {e}")

    def launch_tui(self):
        try:
             term = self.find_terminal()
             if term:
                 # nuxbt tui
                 # Need to ensure arguments matching? Just `nuxbt tui`.
                 subprocess.Popen([term, "-e", "nuxbt tui"])
             else:
                 QMessageBox.warning(self, "Error", "Could not find terminal emulator.")
        except Exception as e:
             QMessageBox.critical(self, "Error", f"Failed to launch TUI: {e}")

    def closeEvent(self, event):
        # This method is called when the application main window is closed
        try:
            # Show a popup to inform the user
            popup = QMessageBox(self)
            popup.setWindowTitle("NUXBT")
            popup.setText("Terminating Background Processes...")
            popup.setStandardButtons(QMessageBox.StandardButton.NoButton)
            popup.setWindowModality(Qt.WindowModality.ApplicationModal)
            popup.show()
            
            # Force UI update so the popup draws
            QApplication.processEvents()

            # Check for any running webapp that we know about
            self.check_webapp_state() # Update state one last time
            
            # Use the shared robust cleanup
            self.terminate_all_webapps()
        
        except Exception as e:
            print(f"Error in closeEvent: {e}")
            
        event.accept() # Accept the close event

def start_gui():
    app = QApplication(sys.argv)
    window = NuxbtGUI()
    window.show()
    sys.exit(app.exec())
