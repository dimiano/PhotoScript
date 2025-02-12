import os
import shutil
import subprocess
import re
from datetime import datetime
from dateutil import parser
import json

# Configuration
SOURCE_DIR = r"C:\Photo_and_video_to_sort"
BASE_DIR = r"C:\Photo_and_video_sorted"
DEST_DIR = BASE_DIR
FILE = ""
EXIFTOOL_PATH = r"exiftool-13.12\exiftool.exe"

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff', '.raw', '.cr2', '.nef', '.heic', '.nrw'} # Supported image extensions
VIDEO_EXTENSIONS = {'.mp4', '.3gp', '.mov', '.avi'} # Supported video extensions
ALL_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS # All supported extensions

# Replace depending on file types: Photo or Video
FILE_EXTENSIONS = ALL_EXTENSIONS

if FILE_EXTENSIONS == ALL_EXTENSIONS:
    FILE_TYPE = 'All'
else:
    FILE_TYPE = "Photo" if FILE_EXTENSIONS == IMAGE_EXTENSIONS else "Video"
    DEST_DIR = f"{BASE_DIR}\\{FILE_TYPE}"

# Format the log file name (e.g., "2025-01-16_15-30-45.log")
file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
FILE = f"{BASE_DIR}\\{FILE_TYPE}_{file_name}" # Log file path (set empty to disable logging)

# Date patterns for filename and directory matching
DATE_PATTERNS = [
    r'(\d{4})[_.-](\d{2})[_.-](\d{2})',     # YYYY-MM-DD or YYYY_MM_DD or YYYY.MM.DD
    r'(\d{4})(\d{2})(\d{2})[ _-](\d{2})(\d{2})(\d{2})', # YYYYMMDD_HHmmss or YYYYMMDD HHmmss or YYYYMMDD-HHmmss
    r'(\d{4})(\d{2})(\d{2})',               # YYYYMMDD
    r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})'  # Month DD, YYYY
]

def log(message: str, mode='a', console=True):
    if console:
        print(message)
    if FILE:
        try:
            with open(FILE, mode, encoding="utf-8") as f:
                f.write(f"{message}\n")
        except Exception as e:
            print(f"Error writing file '{FILE}': {e}")

log(f"Photo Organizer Log: {file_name}", 'w', console=False) # Create log file

def parse_exif_date(date_str):
    """Parse EXIF date string in format 'YYYY:MM:DD HH:MM:SS'"""
    try:
        # Split into date and time parts
        if not date_str or ':' not in date_str:
            return None
            
        # Handle timezone if present
        if '-' in date_str:
            date_str = date_str.split('-')[0]
            
        # Replace EXIF date separator ':' with standard '-' for dates
        parts = date_str.strip().split(' ')
        if len(parts) >= 1:
            date_part = parts[0].replace(':', '-')
            if len(parts) > 1:
                time_part = parts[1]
                formatted_date = f"{date_part} {time_part}"
            else:
                formatted_date = date_part
                
            return parser.parse(formatted_date)
    except Exception as e:
        log(f"Error parsing EXIF date '{date_str}': {e}")
    return None

def get_exif_date(file_path):
    """Extract date from EXIF data using ExifTool."""
    try:
        log(f"Trying to read EXIF data from: {file_path}", console=False)
        result = subprocess.run(
            [EXIFTOOL_PATH, '-json', '-DateTimeOriginal', '-CreateDate', '-FileModifyDate', file_path],
            capture_output=True, text=True, encoding='utf-8'
        )
        
        if result.stdout:
            data = json.loads(result.stdout)
            if data:
                # log("exif data found:")
                # log(json.dumps(data[0], indent=2))
                
                # Try DateTimeOriginal first
                if 'DateTimeOriginal' in data[0]:
                    date = parse_exif_date(data[0]['DateTimeOriginal'])
                    if date:
                        log(f"Using EXIF DateTimeOriginal: {date}", console=False)
                        return date
                
                # Try CreateDate next
                if 'CreateDate' in data[0]:
                    date = parse_exif_date(data[0]['CreateDate'])
                    if date:
                        log(f"Using EXIF CreateDate: {date}", console=False)
                        return date
                
                # Try FileModifyDate as last resort
                if 'FileModifyDate' in data[0]:
                    date = parse_exif_date(data[0]['FileModifyDate'])
                    if date:
                        log(f"Using EXIF FileModifyDate: {date}", console=False)
                        return date
        
        if result.stderr:
            log(f"Subprocess error: {result.stderr}")

        log("No valid EXIF date found")
    except Exception as e:
        log(f"Error reading EXIF data: {e}")
    return None

def extract_date_from_string(text):
    """Extract date from a string using various patterns."""
    log(f"Trying to extract date from text: '{text}'", console=False)
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            try:
                if len(match.groups()) == 3:
                    if match.group(1).isalpha():
                        # Handle "Month DD, YYYY" format
                        date = parser.parse(text)
                        log(f"Found date using 'Month DD, YYYY' pattern: {date}", console=False)
                        return date
                    else:
                        # Handle numeric formats
                        year, month, day = match.groups()
                        date = datetime(int(year), int(month), int(day))
                        log(f"Found date using 'YYYYMMDD' pattern: {date}", console=False)
                        return date
                if len(match.groups()) == 6:
                    # Handle numeric formats
                    year, month, day, hour, min, sec = match.groups()
                    date = datetime(int(year), int(month), int(day), int(hour), int(min), int(sec))
                    log(f"Found date using 'YYYYMMDD_HHmmss' pattern: {date}", console=False)
                    return date
            except ValueError as e:
                log(f"Error parsing date: {e}")
                continue

    log("No date found in text")
    return None

def get_photo_date(file_path):
    """Determine photo date using multiple methods in priority order."""
    log(f"\nProcessing file: '{file_path}'", console=False)
    
    # 1. Try EXIF data
    # log("Attempting to get EXIF date...")
    date = get_exif_date(file_path)
    if date:
        # log(f"Successfully got date from EXIF: {date}", console=False)
        return date

    # 2. Try filename
    # log("Attempting to get date from filename...")
    file_name = os.path.basename(file_path)
    date = extract_date_from_string(file_name)
    if date:
        log(f"Successfully got date from filename: {date}", console=False)
        return date

    # 1. Try directory name
    # log("Attempting to get date from directory name...")
    dir_name = os.path.dirname(file_path)
    date = extract_date_from_string(dir_name)
    if date:
        log(f"Successfully got date from directory: {date}", console=False)
        return date

    log("WARNING: Could not determine date from any source!")
    return None

def get_file_hash(file_path):
    """Calculate MD5 hash of a file."""
    import hashlib
    with open(file_path, 'rb') as f:
        md5_hash = hashlib.md5()
        while chunk := f.read(8192):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def process_photos():
    """Main function to process all photos."""
    # Dictionary to keep track of counters for each day
    day_counters = {}
    
    # Keep track of processed files to avoid duplicates
    processed_hashes = set()
    COUNT = 0
    # First, get hashes of all existing files in destination
    log("\nScanning existing files in destination...\n")
    for root, _, files in os.walk(DEST_DIR):
        for filename in files:
            if os.path.splitext(filename)[1].lower() in FILE_EXTENSIONS:
                file_path = os.path.join(root, filename)
                COUNT += 1
                try:
                    file_hash = get_file_hash(file_path)
                    processed_hashes.add(file_hash)
                    log(f"Found {COUNT} existing file: '{filename}'", console=False)
                except Exception as e:
                    log(f"Error processing existing file '{file_path}': {e}")
    
    COUNT = 0
    # Process all files recursively from source
    log(f"\nProcessing all files from '{SOURCE_DIR}' into '{DEST_DIR}'...\n")
    for root, _, files in os.walk(SOURCE_DIR):
        for filename in files:
            if os.path.splitext(filename)[1].lower() in FILE_EXTENSIONS:
                file_path = os.path.join(root, filename)
                COUNT += 1
                
                # Check if file is unique
                try:
                    file_hash = get_file_hash(file_path)
                    if file_hash in processed_hashes:
                        log(f"Skipping {COUNT} duplicate file: '{file_path}'")
                        continue
                    processed_hashes.add(file_hash)
                except Exception as e:
                    log(f"Error checking {COUNT} file hash '{file_path}': {e}")
                    continue

                # Get photo date
                photo_date = get_photo_date(file_path)
                if not photo_date:
                    log(f"Skipping {COUNT} '{file_path}' - Could not determine date")
                    continue

                # Create destination directory structure
                year_month = f"{photo_date.year:04d}\\{photo_date.month:02d}"
                target_dir = os.path.join(DEST_DIR, year_month)
                os.makedirs(target_dir, exist_ok=True)

                # Generate new filename
                # Use the date as the key for the counter
                date_key = f"{photo_date.year}{photo_date.month:02d}{photo_date.day:02d}"
                day_counters[date_key] = day_counters.get(date_key, 0) + 1
                counter = day_counters[date_key]
                
                extension = os.path.splitext(filename)[1].lower()
                
                # Format the new filename with date and time using the requested format:
                # YYYY-MM-DD_HH-MM_###.ext
                new_filename = (
                    f"{photo_date.year:04d}-{photo_date.month:02d}-{photo_date.day:02d}_"
                    f"{photo_date.hour:02d}-{photo_date.minute:02d}_"
                    f"{counter:03d}{extension}"
                )
                
                target_path = os.path.join(target_dir, new_filename)

                # Check if target file already exists
                if os.path.exists(target_path):
                    log(f"Skipping {COUNT} '{file_path}' - Target file already exists: '{target_path}'")
                    continue

                # Copy the file
                try:
                    shutil.copy2(file_path, target_path)
                    log(f"Successfully copied ({COUNT}): '{file_path}' -> '{target_path}'", console=False)
                except Exception as e:
                    log(f"Error copying {COUNT} '{file_path}': {e}")

    log(f"\nProcessed {COUNT} files.")

def verify_paths():
    """Verify all paths exist and are accessible."""
    errors = []
    
    # Check destination directory exists
    log(f"\nChecking destination directory: {DEST_DIR}")
    if not os.path.exists(DEST_DIR):
        try:
            os.makedirs(DEST_DIR)
            log("Starting photo organization...", 'w', console=False)
            log("\nCreated destination directory")
        except Exception as e:
            errors.append(f"Cannot create destination directory {DEST_DIR}: {e}")
    else:
        log("Destination directory exists")
    
    # Check ExifTool
    log(f"\nChecking ExifTool at: {EXIFTOOL_PATH}")
    if not os.path.exists(EXIFTOOL_PATH):
        errors.append(f"ExifTool not found at {EXIFTOOL_PATH}")
    else:
        log("ExifTool found successfully")
    
    # Check source directory
    log(f"\nChecking source directory: {SOURCE_DIR}")
    if not os.path.exists(SOURCE_DIR):
        errors.append(f"Source directory not found: {SOURCE_DIR}")
    else:
        log("Source directory found successfully")
    
    return errors

def format_timedelta(td):
    # Convert seconds to hours, minutes, and remaining seconds
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    microseconds = str(td.microseconds)[:2]

    return f"{hours:02}:{minutes:02}:{seconds:02}.{microseconds}"

if __name__ == "__main__":
    start_time = datetime.now()
    log(f"Starting photo organization at {start_time} ...", 'w')

    errors = verify_paths()

    if errors:
        log("\nError(s) found:")
        for error in errors:
            log(f"- {error}")
        log("\nPlease correct these errors and run the script again.")
        exit(1)

    process_photos()
    
    end_time = datetime.now()
    execution_time = format_timedelta(end_time - start_time)
    
    log(f"\nPhoto organization completed at {end_time} (time: {execution_time})!\n")
