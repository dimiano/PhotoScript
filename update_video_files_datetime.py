# Update Windows file timestamps for video files from their embedded QuickTime metadata.

import os
import shutil
import subprocess
import re
from datetime import datetime
from dateutil import parser
import json


# Configuration
BASE_DIR = r"C:\Videos"
LOG_FILE = ""
EXIFTOOL_PATH = r"exiftool-13.59\exiftool.exe"

FILE_EXTENSIONS = {'.mp4', '.3gp', '.mov', '.avi', '.mts'} # Supported video extensions
FILE_TYPE = "Video_datetime"

# Format the log file name (e.g., "2025-01-16_15-30-45.log")
file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
LOG_FILE = os.path.join(BASE_DIR, f"{FILE_TYPE}_{file_name}") # Log file path (set empty to disable logging)

if not os.path.isabs(EXIFTOOL_PATH):
    EXIFTOOL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXIFTOOL_PATH)


def log(message, level="info"):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    except Exception:
        pass

    entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{level.upper()}] {message}"

    if LOG_FILE:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as handle:
                handle.write(entry + "\n")
        except Exception:
            pass

    if level in {"warning", "error"}:
        print(entry)


def parse_quicktime_date(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    cleaned = text.replace("T", " ")
    cleaned = re.sub(r"^(\d{4}):(\d{2}):(\d{2})", r"\1-\2-\3", cleaned)
    cleaned = cleaned.replace("Z", "+00:00")

    try:
        return parser.parse(cleaned)
    except Exception:
        return None


def get_quicktime_dates(file_path):
    found_dates = []

    try:
        result = subprocess.run(
            [EXIFTOOL_PATH, "-j", "-CreateDate", "-TrackCreateDate", "-MediaCreateDate", file_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        if result.returncode != 0 and result.stderr.strip():
            log(f"ExifTool returned an error for {file_path}: {result.stderr.strip()}", "error")
            return found_dates

        if not result.stdout.strip():
            log(f"No EXIF metadata returned for {file_path}", "warning")
            return found_dates

        data = json.loads(result.stdout)
        if not data:
            log(f"No metadata records found for {file_path}", "warning")
            return found_dates

        metadata = data[0]
        tags = ["CreateDate", "TrackCreateDate", "MediaCreateDate"]

        for tag in tags:
            raw_value = metadata.get(tag)
            if raw_value is None:
                continue

            parsed = parse_quicktime_date(raw_value)
            if parsed is None:
                log(f"Could not parse {tag} value '{raw_value}' for {file_path}", "warning")
                continue

            # log(f"Found {tag}: {raw_value} -> {parsed.isoformat()}")
            found_dates.append(parsed)

    except FileNotFoundError:
        log(f"ExifTool not found at {EXIFTOOL_PATH}", "error")
    except json.JSONDecodeError as exc:
        log(f"Failed to decode exiftool JSON for {file_path}: {exc}", "error")
    except Exception as exc:
        log(f"Unexpected error reading QuickTime metadata from {file_path}: {exc}", "error")

    return found_dates


def set_windows_file_datetime(file_path, target_dt):
    if os.name != "nt":
        os.utime(file_path, (target_dt.timestamp(), target_dt.timestamp()))
        return

    safe_path = file_path.replace("'", "''")
    safe_dt = target_dt.isoformat()

    powershell_command = (
        f"$item = Get-Item -LiteralPath '{safe_path}'; "
        f"$target = [DateTimeOffset]::Parse('{safe_dt}', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeLocal); "
        f"$item.CreationTimeUtc = $target.UtcDateTime; "
        f"$item.LastWriteTimeUtc = $target.UtcDateTime;"
    )

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell_command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "PowerShell failed to set file dates.")


def process_video_files():
    total_files = 0
    updated_files = 0
    skipped_files = 0

    def handle_walk_error(error):
        log(f"Could not access folder '{error.filename}': {error}", "warning")

    for root, _, files in os.walk(BASE_DIR, onerror=handle_walk_error):
        for filename in files:
            extension = os.path.splitext(filename)[1].lower()
            if extension not in FILE_EXTENSIONS:
                continue

            file_path = os.path.join(root, filename)
            total_files += 1
            log(f"\nProcessing file {total_files}: {file_path}")
            print(f"Processing file {total_files}: {file_path}")

            try:
                dates = get_quicktime_dates(file_path)
                if not dates:
                    log(f"Warning: no usable QuickTime metadata found in {file_path}", "warning")
                    skipped_files += 1
                    continue

                oldest = min(dates)
                log(f"Oldest QuickTime date for {file_path}: {oldest.isoformat()}")

                set_windows_file_datetime(file_path, oldest)
                log(f"Updated file timestamps for {file_path} to {oldest.isoformat()}")
                updated_files += 1

            except Exception as exc:
                log(f"Error updating timestamps for {file_path}: {exc}", "error")
                skipped_files += 1

    log(f"Completed. Total matching files: {total_files}; Updated: {updated_files}; Skipped: {skipped_files}")


def verify_setup():
    if not os.path.exists(BASE_DIR):
        log(f"Base directory does not exist: {BASE_DIR}", "error")
        return False

    if not os.path.exists(EXIFTOOL_PATH):
        log(f"ExifTool not found at {EXIFTOOL_PATH}", "error")
        return False

    log(f"Base directory: {BASE_DIR}")
    log(f"ExifTool path: {EXIFTOOL_PATH}")
    return True


if __name__ == "__main__":
    log(f"Starting QuickTime timestamp update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")

    if not verify_setup():
        raise SystemExit(1)

    process_video_files()
