"""
File Organizer (GUI Version - Tkinter)
--------------------------------------------------------------
A graphical version of the File Organizer. Lets the user pick a
folder, preview changes, organize files into category subfolders,
view a summary, and undo the last organize action — all from a
simple window instead of the command line.
"""

import os
import csv
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
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
# Core logic (same rules as the command-line version)
# ---------------------------------------------------------------

def get_category(extension):
    """Return the category name for a given file extension."""
    extension = extension.lower()
    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category
    return "Others"


def get_unique_path(destination_folder, filename):
    """Generate a non-conflicting file path in the destination folder."""
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
    """Return a list of full file paths inside folder_path."""
    files_found = []

    if include_subfolders:
        for root, dirnames, filenames in os.walk(folder_path):
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


def build_summary_lines(files):
    """Return a list of formatted text lines summarizing file counts/sizes by category."""
    if not files:
        return ["No files found in this folder."]

    summary = {}
    for file_path in files:
        _, extension = os.path.splitext(file_path)
        category = get_category(extension) if extension else "Others"
        size = os.path.getsize(file_path)
        if category not in summary:
            summary[category] = [0, 0]
        summary[category][0] += 1
        summary[category][1] += size

    lines = ["--- File Type Summary ---", f"{'Category':<12}{'Files':<8}{'Size':<10}", "-" * 30]
    total_files = 0
    total_size = 0
    for category, (count, size) in sorted(summary.items()):
        lines.append(f"{category:<12}{count:<8}{format_size(size):<10}")
        total_files += count
        total_size += size
    lines.append("-" * 30)
    lines.append(f"{'Total':<12}{total_files:<8}{format_size(total_size):<10}")
    return lines


# ---------------------------------------------------------------
# GUI Application
# ---------------------------------------------------------------

class FileOrganizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Organizer")
        self.geometry("700x520")
        self.minsize(600, 450)

        self.folder_path = tk.StringVar()
        self.include_subfolders = tk.BooleanVar(value=False)

        self._build_widgets()

    def _build_widgets(self):
        padding = {"padx": 10, "pady": 6}

        # --- Folder selection row ---
        folder_frame = ttk.Frame(self)
        folder_frame.pack(fill="x", **padding)

        ttk.Label(folder_frame, text="Folder:").pack(side="left")
        entry = ttk.Entry(folder_frame, textvariable=self.folder_path)
        entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(folder_frame, text="Browse...", command=self.browse_folder).pack(side="left")

        # --- Options row ---
        options_frame = ttk.Frame(self)
        options_frame.pack(fill="x", **padding)
        ttk.Checkbutton(
            options_frame, text="Include subfolders", variable=self.include_subfolders
        ).pack(side="left")

        # --- Action buttons row ---
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill="x", **padding)

        ttk.Button(buttons_frame, text="Preview", command=self.preview).pack(side="left", padx=4)
        ttk.Button(buttons_frame, text="Organize Now", command=self.organize).pack(side="left", padx=4)
        ttk.Button(buttons_frame, text="Show Summary", command=self.show_summary).pack(side="left", padx=4)
        ttk.Button(buttons_frame, text="Undo Last Organize", command=self.undo).pack(side="left", padx=4)
        ttk.Button(buttons_frame, text="Clear Log", command=self.clear_output).pack(side="left", padx=4)

        # --- Output text area ---
        output_frame = ttk.Frame(self)
        output_frame.pack(fill="both", expand=True, **padding)

        self.output_box = scrolledtext.ScrolledText(output_frame, wrap="word", font=("Consolas", 10))
        self.output_box.pack(fill="both", expand=True)
        self.output_box.configure(state="disabled")

    # -----------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------

    def log(self, message=""):
        """Append a line of text to the output box."""
        self.output_box.configure(state="normal")
        self.output_box.insert("end", message + "\n")
        self.output_box.see("end")
        self.output_box.configure(state="disabled")

    def clear_output(self):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.configure(state="disabled")

    def browse_folder(self):
        selected = filedialog.askdirectory()
        if selected:
            self.folder_path.set(selected)

    def get_valid_folder(self):
        folder = self.folder_path.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Invalid Folder", "Please choose a valid folder first.")
            return None
        return folder

    # -----------------------------------------------------------
    # Actions
    # -----------------------------------------------------------

    def preview(self):
        folder = self.get_valid_folder()
        if not folder:
            return

        files = scan_files(folder, self.include_subfolders.get())
        self.clear_output()
        self.log("--- DRY RUN (Preview Only) ---\n")

        if not files:
            self.log("No files found to organize in this folder.")
            return

        for file_path in files:
            filename = os.path.basename(file_path)
            _, extension = os.path.splitext(filename)
            category = get_category(extension) if extension else "Others"
            self.log(f"  {filename}  -->  {category}/")

        self.log("")
        for line in build_summary_lines(files):
            self.log(line)

        self.log(f"\n(Preview only — {len(files)} file(s) would be affected.)")

    def organize(self):
        folder = self.get_valid_folder()
        if not folder:
            return

        files = scan_files(folder, self.include_subfolders.get())
        if not files:
            messagebox.showinfo("Nothing to do", "No files found to organize in this folder.")
            return

        confirmed = messagebox.askyesno(
            "Confirm Organize",
            f"This will move {len(files)} file(s) into category folders inside:\n{folder}\n\nContinue?",
        )
        if not confirmed:
            return

        self.clear_output()
        self.log("--- Organizing Files ---\n")

        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = ensure_log_file(folder)
        log_rows = []
        moved_count = 0

        for file_path in files:
            filename = os.path.basename(file_path)
            _, extension = os.path.splitext(filename)
            category = get_category(extension) if extension else "Others"
            category_folder = os.path.join(folder, category)

            if not os.path.exists(category_folder):
                os.makedirs(category_folder)

            destination_path = get_unique_path(category_folder, filename)
            shutil.move(file_path, destination_path)

            moved_count += 1
            log_rows.append(
                [session_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), file_path, destination_path]
            )
            self.log(f"  ✅ Moved: {filename}  -->  {category}/")

        with open(log_path, mode="a", newline="") as log_file:
            writer = csv.writer(log_file)
            writer.writerows(log_rows)

        self.log(f"\n✅ Done! {moved_count} file(s) organized.")
        self.log(f"📝 Log saved to: {log_path}  (session: {session_id})")

    def show_summary(self):
        folder = self.get_valid_folder()
        if not folder:
            return

        files = scan_files(folder, self.include_subfolders.get())
        self.clear_output()
        for line in build_summary_lines(files):
            self.log(line)

    def undo(self):
        folder = self.get_valid_folder()
        if not folder:
            return

        log_path = os.path.join(folder, LOG_FILE)
        if not os.path.exists(log_path):
            messagebox.showinfo("Nothing to undo", "No log file found — nothing to undo.")
            return

        with open(log_path, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            all_rows = list(reader)

        if not all_rows:
            messagebox.showinfo("Nothing to undo", "Log file is empty — nothing to undo.")
            return

        last_session_id = all_rows[-1]["session_id"]
        session_rows = [row for row in all_rows if row["session_id"] == last_session_id]
        remaining_rows = [row for row in all_rows if row["session_id"] != last_session_id]

        confirmed = messagebox.askyesno(
            "Confirm Undo",
            f"Move {len(session_rows)} file(s) from session {last_session_id} back to their original locations?",
        )
        if not confirmed:
            return

        self.clear_output()
        self.log(f"--- Undo Session: {last_session_id} ({len(session_rows)} file(s)) ---\n")

        restored_count = 0
        for row in session_rows:
            original_path = row["original_path"]
            destination_path = row["destination_path"]

            if not os.path.exists(destination_path):
                self.log(f"  ⚠️  Skipped (file not found): {os.path.basename(destination_path)}")
                continue

            original_folder = os.path.dirname(original_path)
            if not os.path.exists(original_folder):
                os.makedirs(original_folder)

            if os.path.exists(original_path):
                original_path = get_unique_path(original_folder, os.path.basename(original_path))

            shutil.move(destination_path, original_path)
            restored_count += 1
            self.log(f"  ↩️  Restored: {os.path.basename(original_path)}")

        with open(log_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(LOG_HEADERS)
            for row in remaining_rows:
                writer.writerow(
                    [row["session_id"], row["timestamp"], row["original_path"], row["destination_path"]]
                )

        self.log(f"\n✅ Undo complete. {restored_count} file(s) restored.")


if __name__ == "__main__":
    app = FileOrganizerApp()
    app.mainloop()
