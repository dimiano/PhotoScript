Instructions:
0) Enter the following commands into Command Prompt (after changing the filepaths as required)
1) cd C:\Users\XYZ\Pictures\Python_Script
2) python photo_organizer.py


Key Features:

Source and Destinations

Reads from: C:\Users\XYZ\Pictures\Input_Script
Writes to: C:\Users\XYZ\Pictures\Photos


File Support

Handles multiple image formats (jpg, jpeg, png, gif, tiff)

File Filtering

Automatically skips files with "edited" in filename (case-insensitive)
Checks for duplicates using MD5 hash
Preserves existing files (won't overwrite)


Date Extraction (in priority order)

First tries EXIF DateTimeOriginal
Then tries EXIF CreateDate
Then tries EXIF FileModifyDate
Looks for dates in directory names
Looks for dates in filenames


File Organization

Creates YYYY/MM folder structure
Names files as: YYYY-MM-DD_HH-MM_###.ext
Example: 2015-01-21_16-52_001.jpg


Basic Error Handling

Checks if paths exist
Verifies ExifTool is available
Creates directories if needed
Basic error messages for common issues


Progress Reporting

Shows which file is being processed
Reports successful copies
Indicates when files are skipped
