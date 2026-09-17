"""
File Organizer (Advanced Version)
--------------------------------------------------------------
Automatically organizes files in a folder into categorized
subfolders (Images, Documents, Videos, Music, Archives, etc.)
based on their file extension.

Features:
- Preview (dry run) mode
- File type summary (count + size per category)
- Optional subfolder scanning
- Undo last organize action
"""

import os
import csv
import shutil
from datetime import datetime

# Map of category -> list of file extensions
CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".heic"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".xls", ".ppt", ".pptx", ".csv"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm"],
    "Music": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Programs": [".exe", ".msi", ".apk", ".sh", ".bat"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".json", ".xml"],
}
CATEGORY_FOLDER_NAMES = list(CATEGORIES.keys()) + ["Others"]

LOG_FILE = "file_organizer_log.csv"
LOG_HEADERS = ["session_id", "timestamp", "original_path", "destination_path"]


# ---------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------

def get_category(extension):
    """Return the category name for a given file extension."""
    extension = extension.lower()
    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category
    return "Others"


def get_unique_path(destination_folder, filename):
    """
    If a file with the same name already exists in the destination,
    generate a new unique name instead of overwriting it.
    """
    base_name, extension = os.path.splitext(filename)
    destination_path = os.path.join(destination_folder, filename)
    counter = 1

    while os.path.exists(destination_path):
        new_filename = f"{base_name}_{counter}{extension}"
        destination_path = os.path.join(destination_folder, new_filename)
        counter += 1

    return destination_path


def format_size(size_bytes):
    """Convert a size in bytes to a human-readable string (KB/MB/GB)."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def scan_files(folder_path, include_subfolders):
    """
    Return a list of full file paths inside folder_path.
    Skips the log file and any folder created by this tool
    (Images, Documents, etc.) to avoid re-processing already
    organized files when scanning subfolders.
    """
    files_found = []

    if include_subfolders:
        for root, dirnames, filenames in os.walk(folder_path):
            # Don't descend into folders that this tool itself created
            dirnames[:] = [d for d in dirnames if d not in CATEGORY_FOLDER_NAMES]

            for filename in filenames:
                if filename == LOG_FILE or filename.startswith("."):
                    continue
                files_found.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(folder_path):
            full_path = os.path.join(folder_path, filename)
            if os.path.isfile(full_path) and filename != LOG_FILE and not filename.startswith("."):
                files_found.append(full_path)

    return files_found


def ensure_log_file(folder_path):
    """Create the log file with headers if it doesn't already exist."""
    log_path = os.path.join(folder_path, LOG_FILE)
    if not os.path.exists(log_path):
        with open(log_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(LOG_HEADERS)
    return log_path


# ---------------------------------------------------------------
# Core features
# ---------------------------------------------------------------

def show_summary(files):
    """Print a count and total size of files, grouped by category."""
    if not files:
        print("\nNo files found in this folder.")
        return

    summary = {}  # category -> [count, total_size]

    for file_path in files:
        _, extension = os.path.splitext(file_path)
        category = get_category(extension) if extension else "Others"
        size = os.path.getsize(file_path)

        if category not in summary:
            summary[category] = [0, 0]
        summary[category][0] += 1
        summary[category][1] += size

    print("\n--- File Type Summary ---")
    print(f"{'Category':<12}{'Files':<8}{'Size':<10}")
    print("-" * 30)

    total_files = 0
    total_size = 0
    for category, (count, size) in sorted(summary.items()):
        print(f"{category:<12}{count:<8}{format_size(size):<10}")
        total_files += count
        total_size += size

    print("-" * 30)
    print(f"{'Total':<12}{total_files:<8}{format_size(total_size):<10}")


def organize_folder(folder_path, dry_run, include_subfolders):
    """
    Scan the given folder (and optionally subfolders) and move each
    file into a category subfolder based on its extension.

    If dry_run is True, only a preview is shown and no files are moved.
    """
    if not os.path.isdir(folder_path):
        print(f"❌ Error: '{folder_path}' is not a valid folder.")
        return

    files = scan_files(folder_path, include_subfolders)

    if not files:
        print("\nNo files found to organize in this folder.")
        return

    print(f"\n{'--- DRY RUN (Preview Only) ---' if dry_run else '--- Organizing Files ---'}\n")

    if dry_run:
        for file_path in files:
            filename = os.path.basename(file_path)
            _, extension = os.path.splitext(filename)
            category = get_category(extension) if extension else "Others"
            print(f"  {filename}  -->  {category}/")

        show_summary(files)
        print(f"\n(Preview only — {len(files)} file(s) would be affected. Run again without dry-run to actually move them.)")
        return

    # Actual organizing (not a dry run)
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = ensure_log_file(folder_path)
    log_rows = []
    moved_count = 0

    for file_path in files:
        filename = os.path.basename(file_path)
        _, extension = os.path.splitext(filename)
        category = get_category(extension) if extension else "Others"
        category_folder = os.path.join(folder_path, category)

        if not os.path.exists(category_folder):
            os.makedirs(category_folder)

        destination_path = get_unique_path(category_folder, filename)
        shutil.move(file_path, destination_path)

        moved_count += 1
        log_rows.append([session_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file_path, destination_path])
        print(f"  ✅ Moved: {filename}  -->  {category}/")

    with open(log_path, mode="a", newline="") as log_file:
        writer = csv.writer(log_file)
        writer.writerows(log_rows)

    print(f"\n✅ Done! {moved_count} file(s) organized.")
    print(f"📝 Log saved to: {log_path}  (session: {session_id})")


def undo_last_organize(folder_path):
    """
    Move files from the most recent organize session back to their
    original locations, using the log file as a reference.
    """
    log_path = os.path.join(folder_path, LOG_FILE)

    if not os.path.exists(log_path):
        print("\nNo log file found — nothing to undo.")
        return

    with open(log_path, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        all_rows = list(reader)

    if not all_rows:
        print("\nLog file is empty — nothing to undo.")
        return

    last_session_id = all_rows[-1]["session_id"]
    session_rows = [row for row in all_rows if row["session_id"] == last_session_id]
    remaining_rows = [row for row in all_rows if row["session_id"] != last_session_id]

    print(f"\n--- Undo Session: {last_session_id} ({len(session_rows)} file(s)) ---")
    confirm = input("Move these files back to their original locations? (y/n): ").strip().lower()

    if confirm != "y":
        print("Cancelled.")
        return

    restored_count = 0
    for row in session_rows:
        original_path = row["original_path"]
        destination_path = row["destination_path"]

        if not os.path.exists(destination_path):
            print(f"  ⚠️  Skipped (file not found): {os.path.basename(destination_path)}")
            continue

        original_folder = os.path.dirname(original_path)
        if not os.path.exists(original_folder):
            os.makedirs(original_folder)

        # Avoid overwriting if something already exists at the original path
        if os.path.exists(original_path):
            original_path = get_unique_path(original_folder, os.path.basename(original_path))

        shutil.move(destination_path, original_path)
        restored_count += 1
        print(f"  ↩️  Restored: {os.path.basename(original_path)}")

    # Rewrite the log file without the undone session's rows
    with open(log_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(LOG_HEADERS)
        for row in remaining_rows:
            writer.writerow([row["session_id"], row["timestamp"], row["original_path"], row["destination_path"]])

    print(f"\n✅ Undo complete. {restored_count} file(s) restored.")


# ---------------------------------------------------------------
# Menu / entry point
# ---------------------------------------------------------------

def ask_include_subfolders():
    """Ask the user whether subfolders should be scanned too."""
    choice = input("Include subfolders too? (y/n): ").strip().lower()
    return choice == "y"


def main_menu():
    """Display the main menu and handle user input."""
    print("===== File Organizer =====")
    folder_path = input("\nEnter the full folder path to organize: ").strip().strip('"')

    if not folder_path or not os.path.isdir(folder_path):
        print("❌ Invalid folder path. Exiting.")
        return

    while True:
        print("\n1. Preview only (Dry Run - no files will be moved)")
        print("2. Organize Now (files will actually be moved)")
        print("3. Show File Type Summary")
        print("4. Undo Last Organize")
        print("5. Exit")

        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            include_subfolders = ask_include_subfolders()
            organize_folder(folder_path, dry_run=True, include_subfolders=include_subfolders)
        elif choice == "2":
            include_subfolders = ask_include_subfolders()
            confirm = input("⚠️  This will move files in the folder. Continue? (y/n): ").strip().lower()
            if confirm == "y":
                organize_folder(folder_path, dry_run=False, include_subfolders=include_subfolders)
            else:
                print("Cancelled.")
        elif choice == "3":
            include_subfolders = ask_include_subfolders()
            files = scan_files(folder_path, include_subfolders)
            show_summary(files)
        elif choice == "4":
            undo_last_organize(folder_path)
        elif choice == "5":
            print("\nExiting. Goodbye! 👋")
            break
        else:
            print("⚠️  Invalid option, please try again.")


if __name__ == "__main__":
    main_menu()
