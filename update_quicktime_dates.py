"""Set QuickTime date tags for one file."""

import os
import subprocess
from datetime import datetime


# Configuration
FILE_PATH = r"C:\Videos\Video.3gp"
NEW_DATE_TIME = "2012:09:10 13:31:46"

LOG_FILE = ""
EXIFTOOL_PATH = r"exiftool-13.59\exiftool.exe"

FILE_TYPE = "Video_datetime"

QUICKTIME_TAGS = (
    "CreateDate",
    "ModifyDate",
    "TrackCreateDate",
    "TrackModifyDate",
    "MediaCreateDate",
    "MediaModifyDate",
)


file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
if not LOG_FILE:
    LOG_FILE = os.path.join(os.path.dirname(FILE_PATH), f"{FILE_TYPE}_{file_name}")

if not os.path.isabs(EXIFTOOL_PATH):
    EXIFTOOL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXIFTOOL_PATH)


def log(message="", level="info"):
    """Write a message to the configured log and show warnings/errors."""
    if message:
        prefix = f"[{level.upper()}] " if level != "info" else ""
        entry = f"{datetime.now():%Y-%m-%d %H:%M:%S} {prefix}{message}"
    else:
        entry = ""

    if LOG_FILE:
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, "a", encoding="utf-8") as handle:
                handle.write(entry + "\n")
        except OSError as exc:
            print(f"[WARNING] Could not write log file: {exc}")

    if level in {"warning", "error"}:
        print(entry)


def validate_configuration():
    """Validate the target file, ExifTool, and requested date."""
    date_formats = ("%Y-%m-%d %H:%M:%S", "%Y:%m:%d %H:%M:%S")
    if not any(
        _matches_date_format(NEW_DATE_TIME, date_format)
        for date_format in date_formats
    ):
        raise ValueError(
            "NEW_DATE_TIME must use YYYY-MM-DD HH:MM:SS or YYYY:MM:DD HH:MM:SS"
        )

    if not os.path.isfile(FILE_PATH):
        raise FileNotFoundError(f"Target file does not exist: {FILE_PATH}")
    if not os.path.isfile(EXIFTOOL_PATH):
        raise FileNotFoundError(f"ExifTool not found at: {EXIFTOOL_PATH}")


def _matches_date_format(value, date_format):
    try:
        datetime.strptime(value, date_format)
    except ValueError:
        return False
    return True


def update_quicktime_dates(file_path):
    """Set every configured QuickTime date tag in one ExifTool operation."""
    assignments = [f"-QuickTime:{tag}={NEW_DATE_TIME}" for tag in QUICKTIME_TAGS]
    command = [EXIFTOOL_PATH, "-overwrite_original", *assignments, file_path]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "unknown ExifTool error"
        raise RuntimeError(details)


if __name__ == "__main__":
    try:
        validate_configuration()
    except (FileNotFoundError, ValueError) as exc:
        log(str(exc), "error")
        raise SystemExit(1)

    log(f"Starting QuickTime date update for {FILE_PATH}")
    log(f"Target date/time: {NEW_DATE_TIME}")
    try:
        update_quicktime_dates(FILE_PATH)
        log(f"Updated {FILE_PATH} -> {NEW_DATE_TIME}")
        print(f"Updated: {FILE_PATH}")
    except (OSError, RuntimeError) as exc:
        log(f"Failed to update {FILE_PATH}: {exc}", "error")
        raise SystemExit(1)
