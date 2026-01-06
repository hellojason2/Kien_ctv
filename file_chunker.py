import os
import sys
import shutil
import math

CHUNK_SIZE = 45 * 1024 * 1024  # 45 MB to be safe (under 50MB limit)

def split_file(file_path):
    """Splits a file into chunks."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    file_size = os.path.getsize(file_path)
    print(f"Processing '{file_path}' (Size: {file_size / (1024*1024):.2f} MB)")

    # Create a directory for the parts
    base_dir = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    parts_dir = os.path.join(base_dir, f"{filename}_parts")

    if os.path.exists(parts_dir):
        print(f"Warning: Directory '{parts_dir}' already exists. Cleaning up...")
        shutil.rmtree(parts_dir)
    
    os.makedirs(parts_dir)

    part_num = 0
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            
            part_filename = f"{filename}.part{part_num:03d}"
            part_path = os.path.join(parts_dir, part_filename)
            
            with open(part_path, 'wb') as part_file:
                part_file.write(chunk)
            
            print(f"Created part: {part_filename} ({len(chunk) / (1024*1024):.2f} MB)")
            part_num += 1

    print(f"Successfully split '{file_path}' into {part_num} parts in '{parts_dir}'.")

def join_files(file_path):
    """Joins chunks back into the original file."""
    base_dir = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    parts_dir = os.path.join(base_dir, f"{filename}_parts")

    if not os.path.exists(parts_dir):
        print(f"Error: Parts directory '{parts_dir}' not found.")
        return

    # Get all part files, sorted
    parts = sorted([f for f in os.listdir(parts_dir) if f.startswith(filename) and '.part' in f])
    
    if not parts:
        print(f"Error: No parts found in '{parts_dir}'.")
        return

    print(f"Found {len(parts)} parts. Reassembling to '{file_path}'...")

    # Backup original file if it exists
    if os.path.exists(file_path):
        backup_path = file_path + ".bak"
        print(f"Backing up existing file to '{backup_path}'...")
        shutil.move(file_path, backup_path)

    with open(file_path, 'wb') as output_file:
        for part_name in parts:
            part_path = os.path.join(parts_dir, part_name)
            print(f"Reading {part_name}...")
            with open(part_path, 'rb') as part_file:
                shutil.copyfileobj(part_file, output_file)

    print(f"Successfully reassembled '{file_path}'.")

def main():
    if len(sys.argv) < 3:
        print("Usage: python file_chunker.py <split|join> <file_path>")
        return

    action = sys.argv[1].lower()
    file_path = sys.argv[2]

    if action == 'split':
        split_file(file_path)
    elif action == 'join':
        join_files(file_path)
    else:
        print("Invalid action. Use 'split' or 'join'.")

if __name__ == "__main__":
    main()
