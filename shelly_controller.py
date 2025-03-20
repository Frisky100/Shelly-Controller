import sys
import json
import os
import requests
from pathlib import Path
from functools import partial

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                              QCheckBox, QTableWidget, QTableWidgetItem, 
                              QHeaderView, QMessageBox, QSystemTrayIcon, QMenu)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QKeySequence, QShortcut, QAction, QIcon

class ShellyController(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize settings
        self.settings = QSettings("ShellyController", "ShellyController")
        self.config_file = Path.home() / ".shelly_controller_config.json"
        self.config = self.load_config()
        self._hotkey_cell_changed_connected = False
        self.shortcuts = []
        
        # Initialize UI and setup
        self.init_ui()
        self.setup_shortcuts()
        self.setup_tray()
        
    def load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default configuration
        return {
            "shelly_ip": "192.168.1.100",
            "autostart": False,
            "minimize_to_tray": True,
            "hotkeys": [
                {"name": "Toggle Light", "shortcut": "Ctrl+Alt+L", "endpoint": "relay/0", "action": "toggle"}
            ]
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save configuration: {e}")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Shelly Hotkey Controller")
        self.setMinimumSize(600, 400)
        
        # Main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Shelly IP configuration
        ip_layout = QHBoxLayout()
        self.ip_input = QLineEdit(self.config["shelly_ip"])
        ip_layout.addWidget(QLabel("Shelly IP:"))
        ip_layout.addWidget(self.ip_input)
        
        # Options
        options_layout = QHBoxLayout()
        self.autostart_checkbox = QCheckBox("Start with system")
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to tray")
        
        self.autostart_checkbox.setChecked(self.config["autostart"])
        self.minimize_to_tray_checkbox.setChecked(self.config.get("minimize_to_tray", True))
        
        options_layout.addWidget(self.autostart_checkbox)
        options_layout.addWidget(self.minimize_to_tray_checkbox)
        
        # Hotkeys table
        self.hotkeys_table = QTableWidget(0, 4)
        self.hotkeys_table.setHorizontalHeaderLabels(["Name", "Hotkey", "Endpoint", "Action"])
        self.hotkeys_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("Add Hotkey")
        remove_button = QPushButton("Remove Hotkey")
        test_button = QPushButton("Test Connection")
        save_button = QPushButton("Save Settings")
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(remove_button)
        buttons_layout.addWidget(test_button)
        buttons_layout.addWidget(save_button)
        
        # Connect signals
        add_button.clicked.connect(self.add_hotkey)
        remove_button.clicked.connect(self.remove_hotkey)
        test_button.clicked.connect(self.test_connection)
        save_button.clicked.connect(self.save_settings)
        self.ip_input.textChanged.connect(lambda: self.config.update({"shelly_ip": self.ip_input.text()}))
        self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
        self.minimize_to_tray_checkbox.stateChanged.connect(self.toggle_minimize_to_tray)
        
        # Add all widgets to main layout
        main_layout.addLayout(ip_layout)
        main_layout.addLayout(options_layout)
        main_layout.addWidget(QLabel("Hotkeys:"))
        main_layout.addWidget(self.hotkeys_table)
        main_layout.addLayout(buttons_layout)
        
        self.setCentralWidget(central_widget)
        self.update_hotkeys_table()
    
    def setup_tray(self):
        """Setup system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use custom icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "switch.ico")
        app_icon = QIcon(icon_path)
        
        self.tray_icon.setIcon(app_icon)
        self.setWindowIcon(app_icon)
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Add show/hide action
        self.show_action = QAction("Show", self)
        self.show_action.triggered.connect(self.show_hide_window)
        tray_menu.addAction(self.show_action)
        
        # Add separator
        separator = QAction(self)
        separator.setSeparator(True)
        tray_menu.addAction(separator)
        
        # Add device shortcuts
        for hotkey in self.config["hotkeys"]:
            action_name = f"{hotkey['name']} ({hotkey['action']})"
            action = QAction(action_name, self)
            action.triggered.connect(
                partial(self.toggle_shelly_device, hotkey["endpoint"], hotkey["action"])
            )
            tray_menu.addAction(action)
        
        # Add separator before quit
        separator2 = QAction(self)
        separator2.setSeparator(True)
        tray_menu.addAction(separator2)
        
        # Add quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        # Set up and show
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        self.update_show_action_text()
    
    def update_show_action_text(self):
        """Update show/hide action text based on window visibility"""
        self.show_action.setText("Hide" if self.isVisible() else "Show")
    
    def show_hide_window(self):
        """Toggle the visibility of the main window"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
        
        self.update_show_action_text()
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_hide_window()
    
    def toggle_minimize_to_tray(self, state):
        """Update minimize-to-tray setting"""
        is_checked = state == Qt.Checked
        self.config["minimize_to_tray"] = is_checked
        QApplication.instance().setQuitOnLastWindowClosed(not is_checked)
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.minimize_to_tray_checkbox.isChecked() and self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.update_show_action_text()
            
            # Show notification first time only
            if not self.settings.value("tray_notification_shown", False):
                self.tray_icon.showMessage(
                    "Shelly Controller",
                    "Application is still running in the system tray.",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
                self.settings.setValue("tray_notification_shown", True)
        else:
            self.tray_icon.hide()
            event.accept()
            QApplication.quit()
    
    def update_hotkeys_table(self):
        """Update the hotkeys table with current configuration"""
        self.hotkeys_table.blockSignals(True)
        self.hotkeys_table.setRowCount(0)
        
        for idx, hotkey in enumerate(self.config["hotkeys"]):
            self.hotkeys_table.insertRow(idx)
            
            name_item = QTableWidgetItem(hotkey["name"])
            shortcut_item = QTableWidgetItem(hotkey["shortcut"])
            endpoint_item = QTableWidgetItem(hotkey["endpoint"])
            action_item = QTableWidgetItem(hotkey["action"])
            
            self.hotkeys_table.setItem(idx, 0, name_item)
            self.hotkeys_table.setItem(idx, 1, shortcut_item)
            self.hotkeys_table.setItem(idx, 2, endpoint_item)
            self.hotkeys_table.setItem(idx, 3, action_item)
        
        self.hotkeys_table.blockSignals(False)
        
        if not self._hotkey_cell_changed_connected:
            self.hotkeys_table.cellChanged.connect(self.hotkey_cell_changed)
            self._hotkey_cell_changed_connected = True
    
    def hotkey_cell_changed(self, row, column):
        """Handle changes to the hotkeys table"""
        if row >= len(self.config["hotkeys"]):
            return
            
        item = self.hotkeys_table.item(row, column)
        if not item:
            return
            
        fields = ["name", "shortcut", "endpoint", "action"]
        self.config["hotkeys"][row][fields[column]] = item.text()
        
        self.setup_shortcuts()
        self.setup_tray()  # Rebuild tray menu with new shortcuts
    
    def setup_shortcuts(self):
        """Setup global shortcuts based on configuration"""
        # Clear existing shortcuts
        for shortcut in self.shortcuts:
            shortcut.setEnabled(False)
        
        # Create new shortcuts
        self.shortcuts = []
        for hotkey in self.config["hotkeys"]:
            shortcut = QShortcut(QKeySequence(hotkey["shortcut"]), self)
            shortcut.activated.connect(
                partial(self.toggle_shelly_device, hotkey["endpoint"], hotkey["action"])
            )
            self.shortcuts.append(shortcut)
    
    def toggle_shelly_device(self, endpoint, action):
        """Toggle a Shelly device based on endpoint and action"""
        try:
            ip = self.config["shelly_ip"]
            url = f"http://{ip}/{endpoint}"
            
            if action == "toggle":
                response = requests.get(f"{url}?turn=toggle")
            elif action in ["on", "off"]:
                response = requests.get(f"{url}?turn={action}")
            else:
                self.tray_icon.showMessage(
                    "Shelly Controller",
                    f"Unknown action: {action}",
                    QSystemTrayIcon.MessageIcon.Warning,
                    3000
                )
                return
                
            if response.status_code == 200:
                self.tray_icon.showMessage(
                    "Shelly Controller",
                    f"Successfully toggled: {endpoint}",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
            else:
                self.tray_icon.showMessage(
                    "Shelly Controller",
                    f"Error: Status code {response.status_code}",
                    QSystemTrayIcon.MessageIcon.Warning,
                    3000
                )
                
        except Exception as e:
            self.tray_icon.showMessage(
                "Shelly Controller",
                f"Failed: {e}",
                QSystemTrayIcon.MessageIcon.Critical,
                3000
            )
    
    def add_hotkey(self):
        """Add a new hotkey to the configuration"""
        new_hotkey = {
            "name": "New Hotkey",
            "shortcut": "Ctrl+Alt+N", 
            "endpoint": "relay/0",
            "action": "toggle"
        }
        
        self.config["hotkeys"].append(new_hotkey)
        self.update_hotkeys_table()
        self.setup_shortcuts()
        self.setup_tray()
    
    def remove_hotkey(self):
        """Remove the selected hotkey from configuration"""
        selected_rows = self.hotkeys_table.selectedIndexes()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if row < len(self.config["hotkeys"]):
            self.config["hotkeys"].pop(row)
            self.update_hotkeys_table()
            self.setup_shortcuts()
            self.setup_tray()
    
    def test_connection(self):
        """Test the connection to the Shelly device"""
        try:
            ip = self.config["shelly_ip"]
            endpoints = ["/shelly", "/relay/0", "/"]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"http://{ip}{endpoint}", timeout=3)
                    if response.status_code == 200:
                        QMessageBox.information(self, "Success", "Successfully connected to Shelly device!")
                        return
                except Exception:
                    continue
                    
            QMessageBox.warning(self, "Error", "Failed to connect to the Shelly device")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to connect: {e}")
    
    def save_settings(self):
        """Save all settings"""
        # Update config from UI elements
        self.config["shelly_ip"] = self.ip_input.text()
        self.config["autostart"] = self.autostart_checkbox.isChecked()
        self.config["minimize_to_tray"] = self.minimize_to_tray_checkbox.isChecked()
        
        self.save_config()
        self.configure_autostart()
        
        QMessageBox.information(self, "Success", "Settings saved!")
    
    def toggle_autostart(self, state):
        """Update autostart setting"""
        self.config["autostart"] = state == Qt.Checked
    
    def configure_autostart(self):
        """Configure the application to start with system"""
        if sys.platform == "win32":
            import winreg
            startup_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_path, 0, winreg.KEY_ALL_ACCESS)
                
                if self.config["autostart"]:
                    app_path = os.path.abspath(sys.argv[0])
                    winreg.SetValueEx(key, "ShellyController", 0, winreg.REG_SZ, app_path)
                else:
                    try:
                        winreg.DeleteValue(key, "ShellyController")
                    except FileNotFoundError:
                        pass
                        
                winreg.CloseKey(key)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to configure autostart: {e}")
                
        elif sys.platform == "linux":
            # Linux implementation for autostart
            autostart_dir = Path.home() / ".config/autostart"
            autostart_file = autostart_dir / "shelly_controller.desktop"
            
            try:
                if self.config["autostart"]:
                    if not autostart_dir.exists():
                        autostart_dir.mkdir(parents=True)
                        
                    app_path = os.path.abspath(sys.argv[0])
                    with open(autostart_file, 'w') as f:
                        f.write(f"""[Desktop Entry]
Type=Application
Name=Shelly Controller
Exec={app_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
""")
                elif autostart_file.exists():
                    autostart_file.unlink()
                    
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to configure autostart: {e}")

def main():
    app = QApplication(sys.argv)
    window = ShellyController()
    app.setQuitOnLastWindowClosed(not window.minimize_to_tray_checkbox.isChecked())
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 