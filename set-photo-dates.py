import os
import re
import sys
import datetime
import time
import pywintypes
import win32file
import win32con

def update_file_timestamps():
    root_folder = r'c:\Photos'
    
    if not os.path.isdir(root_folder):
        print("Error: The provided path is not a valid directory.")
        sys.exit(1)
    
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff', '.raw', '.cr2', '.nef', '.heic', '.nrw'} # Supported image extensions
    VIDEO_EXTENSIONS = {'.mp4', '.3gp', '.mov', '.avi'} # Supported video extensions
    ALL_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS # All supported extensions

    # Pattern examples:
    # - 2025-05-26 at 13.10.43.jpg
    # - 2024-12-20 At 11.27.27_8d769920.jpg
    # - 20240922_113907.jpg
    # The regex accepts year/month/day with optional separators, allows an optional
    # separator or the word 'At' between date and time, and accepts contiguous
    # or separated HH.MM.SS / HH-MM-SS / HH:MM:SS formats.
    pattern = re.compile(
        r'(?P<year>\d{4})[.\-]?(?P<month>\d{2})[.\-]?(?P<day>\d{2})'
        r'(?:[ _\.\-]?(?:[aA]t)?[ _\.\-]?)?'
        r'(?P<hour>\d{2})[.\-:]?(?P<minute>\d{2})[.\-:]?(?P<second>\d{2})'
    )

    skipped_files = []

    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            # if not filename.lower().endswith(".jpg"):
            if not os.path.splitext(filename)[1].lower() in ALL_EXTENSIONS:
                skipped_files.append(file_path)
                continue

            match = pattern.search(filename)
            if not match:
                skipped_files.append(file_path)
                continue

            try:
                # year, month, day, hour, minute, second = map(int, match.groups())
                year = int(match.group("year"))
                month = int(match.group("month"))
                day = int(match.group("day"))
                hour = int(match.group("hour"))
                minute = int(match.group("minute"))
                second = int(match.group("second"))

                file_datetime = datetime.datetime(year, month, day, hour, minute, second)
                timestamp = time.mktime(file_datetime.timetuple())

                # Update modified and accessed times
                os.utime(file_path, (timestamp, timestamp))

                handle = win32file.CreateFile(
                    file_path,
                    win32con.GENERIC_WRITE,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                    None,
                    win32con.OPEN_EXISTING,
                    win32con.FILE_ATTRIBUTE_NORMAL,
                    None
                )
                win32file.SetFileTime(handle, pywintypes.Time(timestamp), None, None)  # type: ignore

                print(f"✅ Updated: {file_path} -> {file_datetime}")

            except Exception as e:
                print(f"⚠️ Error processing {filename}: {e}")
                skipped_files.append(os.path.join(dirpath, filename))

    # Log skipped files (if any)
    if skipped_files:
        log_path = os.path.join(root_folder, "skipped_files.log")
        with open(log_path, "a", encoding="utf-8") as log_file:
            for f in skipped_files:
                log_file.write(f"{f}\n")
        print(f"\n📄 Skipped files logged to: {log_path}")

if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print("Usage: python update_timestamps.py <folder_path>")
    #     sys.exit(1)

    # target_folder = sys.argv[1]

    update_file_timestamps()
