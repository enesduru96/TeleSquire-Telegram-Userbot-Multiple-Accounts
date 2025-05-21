import re
import os
import traceback
import zipfile
import json
import aiohttp
import asyncio

links_file = '_downloads/_download_links.txt'
download_dir = '_downloads'
os.makedirs(download_dir, exist_ok=True)
zie_link_pattern = re.compile(r'(https://2zie\.com/[^\s]+)')

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

async def download_file(session, url, download_dir):
    try:
        file_name = os.path.basename(url)
        file_path = os.path.join(download_dir, file_name)
        async with session.get(url) as response:
            if response.status == 200:
                with open(file_path, 'wb') as f:
                    f.write(await response.read())
                print(f"Downloaded: {url} -> {file_path}")
            else:
                print(f"Failed to download {url}: HTTP {response.status}")
    except Exception as e:
        print(f"An error occurred while downloading {url}: {e}")
        traceback.print_exc()

async def download_links_concurrently():
    tasks = []
    async with aiohttp.ClientSession() as session:
        with open(links_file, 'r') as file:
            for line in file:
                match = zie_link_pattern.search(line)
                if match:
                    file_url = match.group(1)
                    print(f"Queueing download: {file_url}")
                    tasks.append(download_file(session, file_url, download_dir))

        await asyncio.gather(*tasks)

def extract_files():
    for file_name in os.listdir(download_dir):
        if file_name.endswith('.zip'):
            zip_path = os.path.join(download_dir, file_name)
            
            base_name = file_name.split('_')[0]
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if member.startswith(base_name) and (member.endswith('.session') or member.endswith('.json')):
                        target_path = os.path.join(download_dir, os.path.basename(member))
                        with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                            target.write(source.read())
                        print(f"Extracted: {target_path}")

def process_json_files():
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

async def main():
    print("Starting downloads...")
    await download_links_concurrently()
    print("Download complete. Extracting files...")
    extract_files()
    print("Extraction complete. Processing JSON files...")
    process_json_files()
    print("Processing complete.")

if __name__ == "__main__":
    asyncio.run(main())
