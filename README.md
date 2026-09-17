# 🗂️ File Organizer

A Python tool that automatically organizes files in any folder into categorized subfolders based on their file type — available both as a **command-line tool** and a **graphical (Tkinter) app**.

## ✨ Features

- **Preview Mode (Dry Run)** — See exactly which files will move where, before anything actually happens
- **Smart Categorization** — Automatically sorts files into: Images, Documents, Videos, Music, Archives, Programs, and Code
- **File Type Summary** — View a breakdown of how many files (and total size) exist per category
- **Subfolder Support** — Optionally scan and organize files inside subfolders too
- **Undo Last Organize** — Safely reverse the most recent organize action using a session-based log
- **Safe by Design** — Never overwrites files; automatically renames duplicates (e.g. `photo_1.jpg`)
- **Two Interfaces** — A command-line version and a Tkinter GUI version with buttons and folder picker

## 🖥️ Screenshots

*(Add a screenshot of the GUI here, e.g. `![GUI Screenshot](screenshot.png)`)*

## 🛠️ Built With

- **Python 3**
- `os` — file and folder operations
- `shutil` — moving files
- `csv` — logging move history for undo support
- `tkinter` — graphical user interface

## 📁 Project Structure

```
file-organizer-python/
├── file_organizer.py          # Command-line version
├── file_organizer_gui.py      # GUI version (Tkinter)
└── README.md
```

## 🚀 How to Run

### Command-Line Version
```bash
python file_organizer.py
```
Follow the on-screen menu to preview, organize, view a summary, or undo the last action.

### GUI Version
```bash
python file_organizer_gui.py
```
1. Click **Browse** to select a folder
2. (Optional) Check **Include subfolders**
3. Click **Preview**, **Organize Now**, **Show Summary**, or **Undo Last Organize**

No extra installation needed — both `tkinter` and all other libraries used come built-in with Python.

## 📌 How It Works

1. The tool scans the selected folder for files
2. Each file's extension is matched against a category map (e.g. `.jpg` → Images, `.pdf` → Documents)
3. Files are moved into subfolders named after their category
4. Every move is logged (with a timestamped session ID) so it can be undone later
5. If a file with the same name already exists in the destination, it's automatically renamed instead of overwritten

## 🔮 Possible Future Improvements

- Custom user-defined categories via a config file
- Scheduled/automatic organizing (e.g. run daily)
- Support for organizing by date instead of type

## 📄 License

This project is open source and free to use for learning purposes.
