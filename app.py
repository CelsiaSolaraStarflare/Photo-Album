from flask import Flask, render_template, request, send_file, abort, jsonify
import os
import json
import platform
import concurrent.futures
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import hashlib
from pathlib import Path

app = Flask(__name__)
# Disable all logging
logging.basicConfig(level=logging.CRITICAL)
app.logger.setLevel(logging.CRITICAL)

# Disable Werkzeug logging
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.CRITICAL)

# Index file to store image locations
INDEX_FILE = 'image_index.json'
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

def get_common_image_paths():
    """Get common image directory paths based on the operating system"""
    system = platform.system().lower()
    home = Path.home()
    
    common_paths = []
    
    if system == "darwin":  # macOS
        common_paths = [
            home / "Pictures",
            home / "Desktop",
            home / "Downloads",
            home / "Documents",
            Path("/Users/Shared"),
            home / "Library" / "Application Support" / "Capture One",
            home / "Library" / "Application Support" / "Adobe" / "Lightroom",
        ]
    elif system == "windows":
        common_paths = [
            home / "Pictures",
            home / "Desktop", 
            home / "Downloads",
            home / "Documents",
            home / "OneDrive" / "Pictures",
            Path("C:/Users/Public/Pictures"),
        ]
    else:  # Linux
        common_paths = [
            home / "Pictures",
            home / "Desktop",
            home / "Downloads", 
            home / "Documents",
            Path("/usr/share/pixmaps"),
        ]
    
    # Add current directory and basis folder if they exist
    current_dir = Path(".")
    common_paths.extend([
        current_dir / "basis",
        current_dir / "images",
        current_dir / "photos",
    ])
    
    # Filter out paths that don't exist
    return [path for path in common_paths if path.exists() and path.is_dir()]

def scan_for_images(directory_path, max_depth=3, current_depth=0):
    """Recursively scan directory for images with depth limit"""
    images = []
    
    if current_depth >= max_depth:
        return images
        
    try:
        for item in directory_path.iterdir():
            if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                # Create a unique identifier for the image
                file_stat = item.stat()
                image_info = {
                    'path': str(item.absolute()),
                    'name': item.name,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'album': str(item.parent.name),
                    'full_album_path': str(item.parent.absolute())
                }
                images.append(image_info)
            elif item.is_dir() and not item.name.startswith('.'):
                # Recursively scan subdirectories
                images.extend(scan_for_images(item, max_depth, current_depth + 1))
    except (PermissionError, OSError):
        # Skip directories we can't access
        pass
    
    return images

def build_image_index():
    """Build or rebuild the image index"""
    print("Building image index...")
    all_images = []
    
    common_paths = get_common_image_paths()
    print(f"Scanning {len(common_paths)} directories...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(scan_for_images, path) for path in common_paths]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                images = future.result()
                all_images.extend(images)
            except Exception as e:
                print(f"Error scanning directory: {e}")
    
    # Organize images by album
    albums = {}
    for image in all_images:
        album_name = image['album']
        if album_name not in albums:
            albums[album_name] = {
                'name': album_name,
                'path': image['full_album_path'],
                'images': []
            }
        albums[album_name]['images'].append(image)
    
    # Save index to file
    index_data = {
        'last_updated': datetime.now().isoformat(),
        'total_images': len(all_images),
        'albums': albums
    }
    
    with open(INDEX_FILE, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"Index built: {len(all_images)} images in {len(albums)} albums")
    return index_data

def load_image_index():
    """Load the image index from file"""
    try:
        with open(INDEX_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return build_image_index()

def get_image_hash(image_path):
    """Generate a hash for the image path for secure access"""
    return hashlib.md5(image_path.encode()).hexdigest()

@app.route('/')
def index():
    # Get the search query and album from the request
    q = request.args.get('q', '').strip()
    album = request.args.get('album')
    
    index_data = load_image_index()
    albums = list(index_data['albums'].keys())
    
    # Default album to the first one if not specified
    if not album and albums:
        album = albums[0]

    images = []
    if album and album in index_data['albums']:
        album_data = index_data['albums'][album]
        images = album_data['images']
        
        # Filter images by search query
        if q:
            images = [img for img in images if q.lower() in img['name'].lower()]
        
        # Add hash for secure image serving
        for img in images:
            img['hash'] = get_image_hash(img['path'])

    return render_template('index.html', 
                         images=images, 
                         albums=albums, 
                         current_album=album,
                         search_query=q,
                         total_images=index_data.get('total_images', 0),
                         last_updated=index_data.get('last_updated'))

@app.route('/image/<string:image_hash>')
def get_image(image_hash):
    """Serve image by hash for security"""
    index_data = load_image_index()
    
    # Find image by hash
    for album_name, album_data in index_data['albums'].items():
        for image in album_data['images']:
            if get_image_hash(image['path']) == image_hash:
                image_path = image['path']
                if os.path.exists(image_path):
                    return send_file(image_path)
                else:
                    abort(404)
    
    abort(404)

@app.route('/rebuild-index')
def rebuild_index():
    """API endpoint to rebuild the image index"""
    try:
        index_data = build_image_index()
        return jsonify({
            'success': True,
            'total_images': index_data['total_images'],
            'total_albums': len(index_data['albums']),
            'last_updated': index_data['last_updated']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/albums')
def get_albums():
    """API endpoint to get all albums"""
    index_data = load_image_index()
    albums_info = []
    
    for album_name, album_data in index_data['albums'].items():
        albums_info.append({
            'name': album_name,
            'path': album_data['path'],
            'image_count': len(album_data['images'])
        })
    
    return jsonify(albums_info)

if __name__ == '__main__':
    # Build initial index if it doesn't exist
    if not os.path.exists(INDEX_FILE):
        build_image_index()
    
    print("Starting Sx Photo Album...")
    print("Access the application at: http://localhost:5120")
    app.run(host='0.0.0.0', port=5120, debug=False)
