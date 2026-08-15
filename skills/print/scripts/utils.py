#!/usr/bin/env python3
"""
Print utility functions for cross-platform printing.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Platform constants
PLATFORM_DARWIN = "darwin"
PLATFORM_LINUX = "linux"
PLATFORM_WINDOWS = "windows"

SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}


def detect_platform() -> str:
    """Detect the current operating system."""
    system = sys.platform.lower()
    if system.startswith("darwin"):
        return PLATFORM_DARWIN
    if system.startswith("linux"):
        return PLATFORM_LINUX
    if system.startswith("win"):
        return PLATFORM_WINDOWS
    raise OSError(f"Unsupported platform: {sys.platform}")


def run_command(
    cmd: List[str],
    timeout: int = 30,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command and capture text output."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
    )


def _find_powershell() -> Optional[str]:
    """Locate a PowerShell executable on Windows."""
    for candidate in ("powershell", "pwsh"):
        if shutil.which(candidate):
            return candidate
    return None


def _run_powershell(script: str, timeout: int = 30) -> Optional[subprocess.CompletedProcess[str]]:
    """Run a PowerShell script if PowerShell is available."""
    shell = _find_powershell()
    if not shell:
        return None
    try:
        return run_command(
            [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            timeout=timeout,
        )
    except Exception:
        return None


def _resolve_pdf_to_printer_module() -> Optional[str]:
    """Find a usable pdf-to-printer module path."""
    if not shutil.which("node"):
        return None

    try:
        result = run_command(
            ["node", "-e", "process.stdout.write(require.resolve('pdf-to-printer'))"],
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    if shutil.which("npm"):
        try:
            result = run_command(["npm", "root", "-g"], timeout=10)
            if result.returncode == 0:
                module_path = Path(result.stdout.strip()) / "pdf-to-printer"
                if module_path.exists():
                    return str(module_path)
        except Exception:
            pass

    return None


def get_default_printer() -> Optional[str]:
    """Get the system default printer name."""
    platform = detect_platform()

    if platform == PLATFORM_WINDOWS:
        result = _run_powershell(
            "(Get-CimInstance Win32_Printer | Where-Object {$_.Default -eq $true} | "
            "Select-Object -First 1 -ExpandProperty Name)"
        )
        if result and result.returncode == 0:
            printer_name = result.stdout.strip()
            if printer_name:
                return printer_name

        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows NT\CurrentVersion\Windows",
            ) as key:
                device = winreg.QueryValueEx(key, "Device")[0]
                printer_name = device.split(",")[0]
                return printer_name if printer_name else None
        except Exception:
            return None

    try:
        result = run_command(["lpstat", "-d"])
        if result.returncode == 0:
            parts = result.stdout.strip().split(":", 1)
            if len(parts) > 1:
                return parts[1].strip()
    except Exception:
        pass

    return None


def get_available_printers() -> List[Dict[str, Any]]:
    """Get list of available printers with status and default flag."""
    platform = detect_platform()
    printers: List[Dict[str, Any]] = []

    if platform == PLATFORM_WINDOWS:
        result = _run_powershell(
            "Get-CimInstance Win32_Printer | "
            "Select-Object Name,PrinterStatus,Default | ConvertTo-Json -Compress"
        )
        if result and result.returncode == 0 and result.stdout.strip():
            try:
                parsed = json.loads(result.stdout)
                entries = parsed if isinstance(parsed, list) else [parsed]
                for entry in entries:
                    printers.append(
                        {
                            "name": entry.get("Name"),
                            "status": str(entry.get("PrinterStatus", "unknown")),
                            "default": bool(entry.get("Default")),
                        }
                    )
                return [printer for printer in printers if printer.get("name")]
            except json.JSONDecodeError:
                pass

        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Printers\Connections") as key:
                index = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                        index += 1
                        parts = subkey_name.split(",")
                        if len(parts) >= 4:
                            printers.append(
                                {
                                    "name": ",".join(parts[3:]),
                                    "status": "unknown",
                                    "default": False,
                                }
                            )
                    except OSError:
                        break
        except Exception:
            return []
    else:
        statuses: Dict[str, str] = {}
        try:
            status_result = run_command(["lpstat", "-p"])
            if status_result.returncode == 0:
                for line in status_result.stdout.splitlines():
                    if not line.startswith("printer "):
                        continue
                    _, remainder = line.split("printer ", 1)
                    if " is " in remainder:
                        name, status = remainder.split(" is ", 1)
                        statuses[name.strip()] = f"is {status.strip()}"
                    else:
                        statuses[remainder.strip()] = "unknown"
        except Exception:
            pass

        try:
            names_result = run_command(["lpstat", "-e"])
            if names_result.returncode == 0:
                for line in names_result.stdout.splitlines():
                    name = line.strip()
                    if name:
                        printers.append(
                            {
                                "name": name,
                                "status": statuses.get(name, "unknown"),
                                "default": False,
                            }
                        )
        except Exception:
            pass

    default_printer = get_default_printer()
    for printer in printers:
        printer["default"] = printer.get("name") == default_printer

    return printers


def construct_print_command(
    file_path: str,
    printer: Optional[str] = None,
    copies: int = 1,
    duplex: Optional[str] = None,
    paper: Optional[str] = None,
    orientation: Optional[str] = None,
    pages: Optional[str] = None,
) -> Tuple[List[str], Dict[str, Any]]:
    """Construct platform-specific print command and metadata."""
    platform = detect_platform()
    metadata: Dict[str, Any] = {
        "platform": platform,
        "file": file_path,
        "printer": printer,
        "copies": copies,
        "backend": None,
        "warnings": [],
    }

    if platform == PLATFORM_WINDOWS:
        command, backend_meta = _construct_windows_command(
            file_path, printer, copies, duplex, paper, orientation, pages
        )
        metadata.update(backend_meta)
        return command, metadata

    command = _construct_cups_command(
        file_path, printer, copies, duplex, paper, orientation, pages
    )
    metadata["backend"] = "cups"
    return command, metadata


def _construct_cups_command(
    file_path: str,
    printer: Optional[str],
    copies: int,
    duplex: Optional[str],
    paper: Optional[str],
    orientation: Optional[str],
    pages: Optional[str],
) -> List[str]:
    """Construct a CUPS lp command for macOS/Linux."""
    cmd = ["lp", "-n", str(copies)]

    if printer:
        cmd.extend(["-d", printer])

    if duplex:
        duplex_map = {
            "none": "one-sided",
            "long-edge": "two-sided-long-edge",
            "short-edge": "two-sided-short-edge",
        }
        cups_duplex = duplex_map.get(duplex)
        if cups_duplex:
            cmd.extend(["-o", f"sides={cups_duplex}"])

    if paper:
        cmd.extend(["-o", f"media={paper.lower()}"])

    if orientation == "landscape":
        cmd.extend(["-o", "orientation-requested=4"])

    if pages:
        cmd.extend(["-o", f"page-ranges={pages}"])

    cmd.append(file_path)
    return cmd


def _construct_windows_command(
    file_path: str,
    printer: Optional[str],
    copies: int,
    duplex: Optional[str],
    paper: Optional[str],
    orientation: Optional[str],
    pages: Optional[str],
) -> Tuple[List[str], Dict[str, Any]]:
    """Construct a Windows print command and metadata."""
    if shutil.which("lpr"):
        warnings: List[str] = []
        if duplex:
            warnings.append("Windows lpr backend ignores duplex; printer defaults apply.")
        if paper:
            warnings.append("Windows lpr backend ignores paper size; printer defaults apply.")
        if orientation:
            warnings.append("Windows lpr backend ignores orientation; printer defaults apply.")
        if pages:
            warnings.append("Windows lpr backend ignores page ranges; printer defaults apply.")

        cmd = ["lpr", f"-#{copies}"]
        if printer:
            cmd.extend(["-P", printer])
        cmd.append(file_path)
        return cmd, {"backend": "lpr", "warnings": warnings}

    module_path = _resolve_pdf_to_printer_module()
    if module_path:
        return _construct_pdf_to_printer_command(
            module_path, file_path, printer, copies, duplex, paper, orientation, pages
        )

    return [], {
        "backend": None,
        "warnings": [
            "No Windows print backend found. Enable LPR Port Monitor or install pdf-to-printer.",
        ],
    }


def _construct_pdf_to_printer_command(
    module_path: str,
    file_path: str,
    printer: Optional[str],
    copies: int,
    duplex: Optional[str],
    paper: Optional[str],
    orientation: Optional[str],
    pages: Optional[str],
) -> Tuple[List[str], Dict[str, Any]]:
    """Construct a Node-based pdf-to-printer invocation."""
    options: Dict[str, Any] = {"copies": copies}
    if printer:
        options["printer"] = printer
    if pages:
        options["pages"] = pages
    if orientation:
        options["orientation"] = orientation
    if paper:
        options["paperSize"] = paper
    if duplex:
        duplex_map = {
            "none": "simplex",
            "long-edge": "duplexlong",
            "short-edge": "duplexshort",
        }
        options["side"] = duplex_map.get(duplex, duplex)

    script = (
        "const mod=require(process.argv[1]);"
        "const file=process.argv[2];"
        "const opts=JSON.parse(process.argv[3]);"
        "Promise.resolve(mod.print(file, opts))"
        ".then((job)=>{ if (job) process.stdout.write(String(job)); })"
        ".catch((error)=>{ console.error(error && error.message ? error.message : String(error)); process.exit(1); });"
    )
    cmd = ["node", "-e", script, module_path, file_path, json.dumps(options)]
    return cmd, {"backend": "pdf-to-printer", "warnings": []}


def execute_print_command(cmd: List[str]) -> Dict[str, Any]:
    """Execute print command and normalize the result."""
    if not cmd:
        return {
            "success": False,
            "error_code": "BACKEND_UNAVAILABLE",
            "error_message": "No print command constructed (backend unavailable)",
        }

    try:
        result = run_command(cmd, timeout=60)
        success = result.returncode == 0
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        normalized: Dict[str, Any] = {
            "success": success,
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "error_code": None if success else "PRINT_COMMAND_FAILED",
            "error_message": stderr if not success else None,
            "command": " ".join(cmd),
        }

        job_id = extract_job_id(stdout)
        if job_id:
            normalized["job_id"] = job_id

        return normalized
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error_code": "PRINT_TIMEOUT",
            "error_message": "Print command timed out after 60 seconds",
        }
    except Exception as error:
        return {
            "success": False,
            "error_code": "PRINT_EXECUTION_FAILED",
            "error_message": f"Print execution failed: {error}",
        }


def extract_job_id(stdout: str) -> Optional[str]:
    """Extract a best-effort print job identifier from stdout."""
    if not stdout:
        return None

    if "request id is " in stdout:
        remainder = stdout.split("request id is ", 1)[1]
        return remainder.split(" ", 1)[0].strip()

    return stdout.splitlines()[0].strip() if stdout else None


def check_dependencies() -> Dict[str, bool]:
    """Check whether likely backends and converters are available."""
    platform = detect_platform()
    dependencies: Dict[str, bool] = {}

    if platform == PLATFORM_WINDOWS:
        dependencies["lpr.exe"] = shutil.which("lpr") is not None
        dependencies["node"] = shutil.which("node") is not None
        dependencies["pdf-to-printer"] = _resolve_pdf_to_printer_module() is not None
        dependencies["powershell"] = _find_powershell() is not None
    else:
        dependencies["lp"] = shutil.which("lp") is not None
        dependencies["lpstat"] = shutil.which("lpstat") is not None

    soffice = shutil.which("soffice")
    if not soffice:
        common_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
        ]
        soffice = any(Path(path).exists() for path in common_paths)
    dependencies["LibreOffice"] = bool(soffice)

    return dependencies


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Print utilities")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    subparsers.add_parser("platform", help="Detect platform")
    subparsers.add_parser("default-printer", help="Get default printer")
    subparsers.add_parser("list-printers", help="List available printers")
    subparsers.add_parser("check-deps", help="Check dependencies")

    args = parser.parse_args()

    if args.command == "platform":
        print(detect_platform())
    elif args.command == "default-printer":
        print(get_default_printer() or "")
    elif args.command == "list-printers":
        print(json.dumps(get_available_printers(), indent=2, ensure_ascii=False))
    elif args.command == "check-deps":
        print(json.dumps(check_dependencies(), indent=2, ensure_ascii=False))
    else:
        parser.print_help()
