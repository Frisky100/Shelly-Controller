# Shelly Hotkey Controller

A desktop application to control Shelly smart devices using customizable hotkeys, built with PyQt/PySide.

## Features

- Toggle Shelly devices with keyboard shortcuts
- Customize hotkeys for different devices/actions
- Edit device IP address
- Test connection to devices
- Start automatically with system boot
- **System Tray Integration** - Run in the background with a custom switch icon

## Installation

### Pre-built Executable (Windows)

1. Download `ShellyHotkeyController.exe` from the releases
2. Run the executable - no installation required

### From Source

1. Clone or download this repository
2. Install the required dependencies:

```
pip install -r requirements.txt
```

3. Run the application:

```
python shelly_controller.py
```

4. (Optional) Build your own executable:

```
python -m PyInstaller --onefile --windowed --icon=images/switch.ico --name="ShellyHotkeyController" shelly_controller.py
```

## Usage

### Configuration

- **Shelly IP**: Enter the IP address of your Shelly device
- **Start with system**: Enable to make the application start automatically with system boot
- **Minimize to tray**: When enabled, closing the window will minimize to system tray instead of exiting
- **Hotkeys**: Add, edit, or remove keyboard shortcuts that control your devices

### System Tray

The application runs in the system tray, allowing you to:

- Control your Shelly devices directly from the tray menu
- Hide/show the main configuration window
- Toggle devices even when the main window is hidden
- Get notifications about device status

### Adding Hotkeys

1. Click "Add Hotkey"
2. Edit the new entry in the table:
   - **Name**: A descriptive name for the shortcut
   - **Hotkey**: The keyboard combination (e.g., "Ctrl+Alt+L")
   - **Endpoint**: The Shelly device endpoint (e.g., "relay/0")
   - **Action**: Action to perform (toggle, on, off)

### Testing Connection

Click "Test Connection" to verify that the application can connect to your Shelly device.

### Saving Settings

Click "Save Settings" to store your configuration.

## Shelly Device Information

This application works with Shelly device REST API endpoints. Typical endpoints include:

- `relay/0` - For controlling the first relay
- `relay/1` - For controlling the second relay (if available)

Typical actions include:
- `toggle` - Toggle the current state
- `on` - Turn the device on
- `off` - Turn the device off

## Troubleshooting

If you experience issues:

1. Ensure your Shelly device is properly connected to your network
2. Verify the IP address is correct
3. Check that the device's REST API is accessible (try accessing http://[your-device-ip]/shelly in a browser)
4. Verify that hotkey combinations aren't already in use by other applications
5. If your hotkeys don't work system-wide, try running the application as administrator

## License

This software is provided as-is under the MIT License. 