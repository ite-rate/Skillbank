# Platform-Specific Differences

This document details the differences in printing behavior across operating systems.

## Summary Table

| Feature | macOS | Linux | Windows |
|---------|-------|-------|---------|
| Backend | CUPS | CUPS | LPR / pdf-to-printer |
| Default printer | `lpstat -d` | `lpstat -d` | PowerShell / Registry |
| List printers | `lpstat -e` + `lpstat -p` | `lpstat -e` + `lpstat -p` | PowerShell / Registry |
| Print command | `lp` | `lp` | `lpr.exe` / pdf-to-printer |
| Office conversion | LibreOffice | LibreOffice | LibreOffice |
| Duplex support | ✓ | ✓ | Limited |
| Paper size | ✓ | ✓ | Limited |
| Dry-run support | ✓ | ✓ | ✓ |

## macOS (Darwin)

### Printing Backend
**CUPS** (Common Unix Printing System) - pre-installed on macOS.

### Commands

**Get default printer:**
```bash
lpstat -d
# Output: system default destination: Printer_Name
```

**List all printers:**
```bash
lpstat -e
lpstat -p
```

**Print command:**
```bash
lp -d "Printer_Name" -n 2 -o sides=two-sided-long-edge -o media=a4 file.pdf
```

### Path Considerations
- LibreOffice: `/Applications/LibreOffice.app/Contents/MacOS/soffice`
- CUPS config: `/etc/cups/`

### Common Issues
1. **"lp: command not found"** - CUPS not installed (rare on macOS)
2. **"lp: Unable to connect to printer"** - Printer offline or network issue
3. **"libreoffice: command not found"** - Install via Homebrew: `brew install --cask libreoffice`

## Linux

### Printing Backend
**CUPS** - standard on most distributions. May need installation on minimal installs.

### Installation
```bash
# Debian/Ubuntu
sudo apt-get install cups libcups2-dev

# RHEL/CentOS/Fedora
sudo yum install cups cups-devel

# Arch Linux
sudo pacman -S cups
```

### Commands
Same as macOS (CUPS-based).

### Distribution-Specific Notes

**Ubuntu/Debian:**
```bash
# Start CUPS service
sudo systemctl start cups
sudo systemctl enable cups
```

**RHEL/CentOS:**
```bash
# May need to configure SELinux for printing
sudo setsebool -P cupsd_disable_configfilecheck 1
```

### Common Issues
1. **"lp: command not found"** - Install CUPS package
2. **Permission denied** - Add user to `lp` group: `sudo usermod -aG lp $USER`
3. **Printer not detected** - Check CUPS web interface at `http://localhost:631`

## Windows

### Printing Backend
Two options:
1. **LPR Port Monitor** - native Windows component (may require enabling)
2. **pdf-to-printer** - npm package (fallback)

### Option 1: LPR Port Monitor

**Enable LPR:**
1. Settings → Apps → Optional Features
2. Add Feature → "Print Management" or "LPR Port Monitor"
3. Or via PowerShell (Admin):
```powershell
Add-WindowsCapability -Online -Name Print.Management.Client~~~~0.0.1.0
```

**Command:**
```cmd
lpr -P "Printer Name" -#2 file.pdf
```

**Limitations:**
- No duplex option (uses printer default)
- No paper size option (uses printer default)
- No orientation option (uses printer default)

### Option 2: pdf-to-printer (Node module)

**Install:**
```bash
npm install -g pdf-to-printer
```

**Advantages:**
- Full parameter support
- Better error handling
- PDF-only (requires pre-conversion)

### Get Default Printer (Preferred: PowerShell)
```powershell
Get-CimInstance Win32_Printer | Where-Object {$_.Default -eq $true} | Select-Object -ExpandProperty Name
```

### Get Default Printer (Registry fallback)
```python
import winreg
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Windows") as key:
    device = winreg.QueryValueEx(key, "Device")[0]
    printer_name = device.split(",")[0]
```

### List Printers (Preferred: PowerShell)
```powershell
Get-CimInstance Win32_Printer | Select-Object Name,PrinterStatus,Default
```

### Common Issues
1. **"lpr is not recognized"** - LPR Port Monitor not enabled
2. **"Access denied"** - Run as Administrator
3. **Printer name has spaces** - Quote the name: `"HP LaserJet Pro"`

## File Format Handling

### PDF Files
- Direct printing on all platforms
- No conversion required

### Office Files (Word/Excel/PowerPoint)
- **All platforms:** Convert to PDF using LibreOffice first
- Conversion command: `soffice --headless --convert-to pdf input.docx`
- Then print the converted PDF

### Image Files (PNG/JPG/etc)
- macOS/Linux: Direct print via CUPS
- Windows: May need conversion to PDF first

## Environment Variables

The print scripts respect these environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `PRINT_PRINTER` | Default printer name | System default |
| `PRINT_COPIES` | Default number of copies | 1 |
| `PRINT_DUPLEX` | Default duplex mode | System default |
| `PRINT_PAPER` | Default paper size | System default |

Example:
```bash
export PRINT_PRINTER="Office Printer"
export PRINT_DUPLEX="long-edge"
python scripts/print_file.py document.pdf
```

## Exit Codes

All platforms use consistent exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | File not found |
| 3 | Conversion failed |
| 4 | Print backend unavailable |
| 5 | Printer not found |

## Unicode and Filenames

### macOS/Linux
- UTF-8 filenames fully supported
- No special handling needed

### Windows
- May have issues with non-ASCII characters in filenames
- Recommendation: use ASCII filenames or quote paths:
```cmd
python scripts/print_file.py "文件.pdf"
```

## Troubleshooting by Platform

### macOS
```bash
# Check CUPS status
sudo launchctl list | grep cups

# Restart CUPS
sudo launchctl stop org.cups.cupsd
sudo launchctl start org.cups.cupsd

# Check logs
tail -f /var/log/cups/error_log
```

### Linux
```bash
# Check CUPS status
systemctl status cups

# Restart CUPS
sudo systemctl restart cups

# Check logs
journalctl -u cups -f
```

### Windows
```cmd
REM Check Print Spooler
sc query Spooler

REM Restart Print Spooler
net stop Spooler
net start Spooler

REM Check printer status
wmic printer get name,status
```
