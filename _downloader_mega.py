import subprocess
import re
import os
import traceback
import os
import zipfile
import rarfile
import json

download_dir = '_downloads'
links_file = '_downloads/_download_links.txt'
target_dir = 'sessions/_seller_sessions'
os.makedirs(download_dir, exist_ok=True)

mega_link_pattern = re.compile(r'(https://mega.nz/[^\s]+)')
mega_get_path = r"path\\to\\mega\\mega-get.bat"

key_mapping = {
    "session_file": "session",
    "app_id": "api_id",
    "app_hash": "api_hash",
    "sdk": "system_version",
    "twoFA": "2fa"
}

key_values = {
    "proxy": ""
}

def rename_keys_in_json(file_path, key_map):
    with open(file_path, 'r') as file:
        data = json.load(file)

    for old_key, new_key in key_map.items():
        if old_key in data:
            data[new_key] = data.pop(old_key)

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Keys updated: {file_path}")

def update_key_values_in_json(file_path, key_val_map):
    with open(file_path, 'r') as file:
        data = json.load(file)

    for key, new_value in key_val_map.items():
        if key in data:
            data[key] = new_value

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Values updated: {file_path}")

def remove_null_values(data):
    return {k: v for k, v in data.items() if v is not None}


def download_file_sync(mega_get_path, file_url, download_dir):
    print(f"Downloading: {file_url}")
    try:
        result = subprocess.run(
            [mega_get_path, file_url, download_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(f"Downloaded: {file_url} -> {download_dir}")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error while downloading: {e.stderr.strip()}")

def process_archive(archive_ref, base_name):
    for member in archive_ref.namelist():
        if member.endswith(f"{base_name}.json") or member.endswith(f"{base_name}.session"):
            file_name = os.path.basename(member)
            file_name = file_name.replace("+", "")
            extract_path = os.path.join(target_dir, file_name)
            with archive_ref.open(member) as source, open(extract_path, "wb") as target:
                target.write(source.read())
            print(f"Extracted: {file_name}")


def main(links_file, mega_get_path, download_dir):
    with open(links_file, 'r') as file:
        for line in file:
            match = mega_link_pattern.search(line)
            if match:
                file_url = match.group(1)
                download_file_sync(mega_get_path, file_url, download_dir)

    for file_name in os.listdir(download_dir):
        if file_name.endswith(('.zip', '.rar')):
            archive_path = os.path.join(download_dir, file_name)
            base_name = os.path.splitext(file_name)[0]

            if file_name.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as archive_ref:
                    process_archive(archive_ref, base_name)

            elif file_name.endswith('.rar'):
                with rarfile.RarFile(archive_path, 'r') as archive_ref:
                    process_archive(archive_ref, base_name)

    for file_name in os.listdir(download_dir):
        if file_name.endswith('.json'):
            json_path = os.path.join(download_dir, file_name)
            
            rename_keys_in_json(json_path, key_mapping)
            
            update_key_values_in_json(json_path, key_values)
            
            with open(json_path, 'r') as file:
                data = json.load(file)
            data = remove_null_values(data)

            with open(json_path, 'w') as file:
                json.dump(data, file, indent=4)
            print(f"Null values removed: {json_path}")


if __name__ == "__main__":
    main(links_file, mega_get_path, download_dir)
