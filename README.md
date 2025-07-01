# Sx Photo Album

A beautiful, modern web photo album for your local images.  
Automatically indexes your images from common folders and provides a stunning, searchable, and gallery-style interface.

---

## ✨ Features

- **Automatic image discovery** from your Pictures, Desktop, Downloads, and more
- **Sleek, dark-mode UI** with glassmorphism and responsive design
- **Fast search** and album navigation
- **Fullscreen modal viewer** with keyboard shortcuts
- **Rebuild index** button for instant refresh
- **Responsive design** for desktop and mobile

---

## 🚀 Quickstart

### 1. Clone the repository

```bash
git clone https://github.com/CelsiaSolaraStarflare/Photo-Album.git
cd Sx\ Photo\ Album
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

The app will be available at [http://localhost:5120](http://localhost:5120)

---

## 🖥️ Usage

- **Browse albums**: Select from the dropdown
- **Search**: Use the search bar to filter images by name
- **View fullscreen**: Click any image
- **Keyboard shortcuts**:
  - `Cmd/Ctrl + K`: Focus search
  - `Cmd/Ctrl + R`: Rebuild index
  - `Escape`: Close modal

---

## 🛠️ Scripts

For convenience, you can use the following script to set up and run the app:

### `run.sh`

```bash
#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Make it executable:

```bash
chmod +x run.sh
```

Then run:

```bash
./run.sh
```

---

## 📸 Future Features

- Favorites, tags, and virtual albums
- Slideshow mode
- EXIF metadata viewer
- Download/share options
- Trash/restore functionality

---

## 📝 License

MIT License

---

## 🙏 Credits

Developed with Flask and ❤️. 