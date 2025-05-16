# Photo Organizer Script

This Python script automatically organizes your photos into a structured folder system based on their date information. It prioritizes EXIF data for date extraction, but also intelligently falls back to directory and filename analysis when EXIF is unavailable.

## Instructions

0. **Verify all files extensions that are present in your Photo/Video folder running next powershell command (not sure hot to do it in python though)**:
    ```pwsh
    Get-ChildItem -Recurse -File | ForEach-Object { $_.Extension } | Sort-Object -Unique
    ```
    it gives you something like next (*I was surprised about old `.3gp` video (Samsung?) and `.nrw` Nikon photo formats. Also notice `.tif` and `.tiff`*):
    ```
    pwsh >
    .3gp
    .avi
    .HEIC
    .jpeg
    .jpg
    .nrw
    .MOV
    .mp4
    .tif
    .tiff
    .zip
    ```
    Thus, you can adjust your `IMAGE_EXTENSIONS` or `VIDEO_EXTENSIONS` filter.

1.  **Open Command Prompt (or Terminal):**
    *   Navigate to the script's location using the `cd` command.
    *   **Important:** Replace `C:\PhotoScript` with the actual path to the directory containing `photo_organizer.py`.

        ```bash
        cd C:\PhotoScript
        ```

2.  **Run the script:**

    ```bash
        python photo_organizer.py
    ```

## Key Features

### Source and Destinations

*   **Reads From:**  `C:\Photo_and_video_to_sort`
*   **Writes To:**  `C:\Photo_and_video_sorted\Photo` or `C:\Photo_and_video_sorted\Video` based on selected file extensions

    **Important:** Be sure to replace these with your actual input and output directories.

### File Support

*   **Handles multiple image formats:** '.jpg', '.jpeg', '.png', '.gif', '.tiff', '.raw', '.cr2', '.nef', '.heic'.
*   **Handles multiple video formats:** '.mp4', '.3gp', '.mov', '.avi'.

### File Filtering

*   **Skips "edited" files:** Automatically skips files that have "edited" (case-insensitive) in their filename.
*   **Duplicate Checking:**  Uses MD5 hash to identify and skip duplicate files.
*   **Preserves Existing Files:** The script will not overwrite any existing files.

### Date Extraction (Priority Order)

The script will extract date information in this order:

1.  **EXIF DateTimeOriginal:**  The preferred EXIF tag.
2.  **EXIF CreateDate:** Used if `DateTimeOriginal` is unavailable.
3.  **EXIF FileModifyDate:**  Used as a last resort if the above EXIF tags aren't found.
4.  **Filename:** Looks for dates embedded in the filename.
5.  **Directory Name:** Looks for dates embedded in the directory name.

### File Organization

*   **YYYY/MM Folder Structure:**  Creates year and month folders to keep your pictures well organized. For example: `2025/05`.
*   **File Naming:**  Renames files using this format:  `YYYY-MM-DD_HH-MM_###.ext`
    *   Example:  `2025-05-21_16-52_001.jpg`
    *  `###` is a counter to ensure uniqueness

### Basic Error Handling

*   **Path Existence:**  Verifies that the specified input and output paths are valid.
*   **ExifTool Availability:** Checks if ExifTool is installed and accessible in the system's PATH.
*   **Directory Creation:**  Creates the output directories if they do not already exist.
*   **Clear Error Messages:** Provides basic error messages for common issues.

### Progress Reporting

*   **Logs** Writes complete log to the destination folder as `FILE_TYPE_%Y-%m-%d_%H-%M-%S.log` like `Photo_2025-01-16_15-30-45.log` or `Video_2025-01-16_15-30-45.log` based on selected file extensions.
*   **File Processing:** Displays the name of the file currently being processed.
*   **Success Messages:** Reports when a file has been successfully copied.
*   **Skipped Messages:** Indicates when files are skipped due to being duplicates or marked "edited."

## Important Notes

*   `exiftool` is available as portable version in the repository.
*   If you prefer another version, ensure that `exiftool` is installed and accessible. You may need to add it to your system's PATH environment variables.
*   Remember to replace the example file paths with your specific source and destination directories in the script.

This script will greatly simplify your photo management by sorting and naming files appropriately. Let me know if you have any further questions.