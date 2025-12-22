# Scale Weight Server - Build Instructions

## 📦 Building the EXE File

### Method 1: Automatic Build (Recommended)
Simply double-click `build_exe.bat` and wait for the process to complete.

### Method 2: Manual Build
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Build the EXE:
   ```bash
   pyinstaller --clean --onefile --windowed --name "ScaleWeightServer" --hidden-import=flask --hidden-import=serial --hidden-import=serial.tools.list_ports ScaleWeightServer.py
   ```

## 📁 Output Location
After building, you'll find:
- **EXE File**: `dist\ScaleWeightServer.exe` (This is what you send to clients)
- Build files: `build\` folder (can be deleted)
- Spec file: `ScaleWeightServer.spec` (can be deleted)

## 🚀 Distributing to Clients

### What to Send:
Send ONLY the file: `dist\ScaleWeightServer.exe`

This single EXE file contains:
✅ All Python dependencies
✅ Flask web server
✅ Serial communication libraries
✅ Complete GUI application
✅ No installation required!

### Client Requirements:
- Windows 7/8/10/11
- No Python installation needed
- No additional software needed

### Client Instructions:
1. Copy `ScaleWeightServer.exe` to any folder
2. Double-click to run
3. Select mode (Simulation or Hardware)
4. Configure settings if using hardware
5. Click "START SERVER"

## 🔧 Build Options Explained

- `--onefile`: Creates a single EXE (no folders)
- `--windowed`: No console window (GUI only)
- `--name`: Name of the output EXE
- `--hidden-import`: Includes modules that PyInstaller might miss
- `--clean`: Removes previous build cache

## 📝 Optional: Add Icon
To add a custom icon:
1. Create or download an `.ico` file
2. Add to build command: `--icon=myicon.ico`

## 🐛 Troubleshooting

### EXE is too large?
Normal size: 20-40 MB (includes Python runtime + all libraries)

### Antivirus flags the EXE?
This is common with PyInstaller. Solutions:
- Add exception in antivirus
- Sign the EXE with a code signing certificate
- Use `--upx-dir` to compress (may help)

### Missing modules error?
Add to build command: `--hidden-import=module_name`

## 📊 File Size Optimization (Optional)
To reduce EXE size:
```bash
pip install upx
pyinstaller --clean --onefile --windowed --upx-dir=C:\path\to\upx ScaleWeightServer.py
```

## ✅ Testing Before Distribution
1. Build the EXE
2. Copy to a different computer (without Python)
3. Test both Simulation and Hardware modes
4. Verify server starts correctly
5. Test weight reading functionality
