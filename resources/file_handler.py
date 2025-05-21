import asyncio, os
import logging
import random
import json
import string
import pickle
from aiofiles import open as aio_open
from aiofiles.os import rename as aio_rename, remove as aio_remove, wrap as aio_wrap
from os import listdir

from resources.proxy_handler import ProxyHandler
from resources.random_device_handler import RandomDeviceHandler

from resources._loggers import client_logger

class FileHandler:
    def __init__(self, proxy_handler=None, device_handler=None):
        self.ProxyHandler:ProxyHandler = proxy_handler
        self.DeviceHandler:RandomDeviceHandler = device_handler
        self.sessions_dir = "sessions/active"
        self.banned_dir = "sessions/banned"
        self.duplicated_dir = "sessions/duplicated"
        self.spam_dir = "sessions/spam"
        self.people_data_dir = "data/people"
        self.initialize_resources()

    def _load_file_lines(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                return content.splitlines()
        except Exception as e:
            client_logger.error(f"Error loading file {file_path}: {e}")
            return []

    def initialize_resources(self):
        try:
            self.first_names = self._load_file_lines(f"{self.people_data_dir}/first_names.txt")
            self.last_names = self._load_file_lines(f"{self.people_data_dir}/last_names.txt")
            self.abouts = self._load_file_lines(f"{self.people_data_dir}/abouts.txt")
            self.usernames = self._load_file_lines(f"{self.people_data_dir}/usernames.txt")

            profile_pictures_dir = "_files/profile_pictures"
            files = os.listdir(profile_pictures_dir)

            self.profile_pictures = [
                f"{profile_pictures_dir}/{photo}"
                for photo in files
                if photo.endswith(".jpg") or photo.endswith(".jpeg")
            ]
        except Exception as e:
            client_logger.error(f"Error initializing resources: {e}")

    async def _random_string(self, length: int = 12) -> str:
        return ''.join(random.choices(string.ascii_lowercase, k=length))

    async def create_first_name(self):
        return random.choice(self.first_names) if self.first_names else await self._random_string()

    async def create_last_name(self):
        return random.choice(self.last_names) if self.last_names else await self._random_string()

    async def create_about(self):
        return random.choice(self.abouts) if self.abouts else await self._random_string()

    async def create_username(self):
        base_username = random.choice(self.usernames) if self.usernames else await self._random_string()
        return f"{random.choice(string.ascii_letters)}{random.choice(string.ascii_letters)}{base_username}{random.randint(0, 999)}"

    async def create_profile_picture(self):
        return random.choice(self.profile_pictures) if self.profile_pictures else None

    async def move_session(self, destination_dir: str, phone_number:str):
        try:
            await aio_rename(f"{self.sessions_dir}/{phone_number}.session", f"{destination_dir}/{phone_number}.session")
            await aio_rename(f"{self.sessions_dir}/{phone_number}.json", f"{destination_dir}/{phone_number}.json")
        except Exception as error:
            client_logger.error(f"[{phone_number}] - Error moving session to '{destination_dir}':\n{error}", exc_info=True)

    async def move_to_banned(self, phone_number):
        await self.move_session(self.banned_dir, phone_number)

    async def move_to_duplicated(self, phone_number):
        await self.move_session(self.duplicated_dir, phone_number)

    async def move_to_spam(self, phone_number):
        await self.move_session(self.spam_dir, phone_number)

    async def check_json(self, phone_number):
        json_path = f"{self.sessions_dir}/{phone_number}.json"
        try:
            if await aio_wrap(os.path.isfile)(json_path):
                async with aio_open(json_path, 'r', encoding="utf-8") as json_file:
                    session_json = json.loads(await json_file.read())
            else:
                device_model, system_version, app_version, api_id, api_hash = await self.DeviceHandler.get_device_info_and_api()
                new_proxy = await self.ProxyHandler.get_next_proxy(phone_number)
                session_json = {
                    "session": phone_number,
                    "api_id": api_id,
                    "api_hash": api_hash,
                    "device": device_model,
                    "system_version": system_version,
                    "app_version": app_version,
                    "lang_code": "en",
                    "system_lang": "en-us",
                    "2fa": None,
                    "proxy": new_proxy
                }
                async with aio_open(json_path, 'w', encoding="utf-8") as json_file:
                    await json_file.write(json.dumps(session_json))
            return session_json
        except Exception as error:
            client_logger.error(f"Error checking JSON for {phone_number}: {error}", exc_info=True)
            return None

    async def update_json_field(self, field, value, phone_number):
        json_path = f"{self.sessions_dir}/{phone_number}.json"
        try:
            async with aio_open(json_path, 'r+', encoding="utf-8") as json_file:
                session_json = json.loads(await json_file.read())
                session_json[field] = value
                await json_file.seek(0)
                await json_file.write(json.dumps(session_json, indent=4))
                await json_file.truncate()
                return True
        except Exception as error:
            client_logger.error(f"[{phone_number}] - Error updating '{field}' in JSON:\n{error}", exc_info=True)
            return False

    async def update_json_field_seller(self, field, value, phone_number):
        json_path = f"sessions/_seller_sessions/{phone_number}.json"
        try:
            async with aio_open(json_path, 'r+', encoding="utf-8") as json_file:
                session_json = json.loads(await json_file.read())
                session_json[field] = value
                await json_file.seek(0)
                await json_file.write(json.dumps(session_json, indent=4))
                await json_file.truncate()
                return True
        except Exception as error:
            client_logger.error(f"[{phone_number}] - Error updating '{field}' in JSON:\n{error}", exc_info=True)
            return False

    async def update_2fa_json(self, new_password, phone_number):
        await self.update_json_field('2fa', new_password, phone_number)

    async def get_session_twofa(self, phone_number):
        data = await self.check_json(phone_number)
        return data.get('2fa') or data.get('twoFA')
    
    async def update_register_time_json(self, new_register_time, phone_number):
        await self.update_json_field('register_time', new_register_time, phone_number)

    async def update_proxy_json(self, new_proxy, phone_number):
        await self.update_json_field('proxy', new_proxy, phone_number)


    def get_session_list(self) -> list:
        return [file.replace('.session', '').replace("+","") for file in listdir("sessions/active/.") if file.endswith(".session")]


    def get_seller_session_list(self) -> list:
        return [file.replace('.session', '').replace("+","") for file in listdir("sessions/_seller_sessions/.") if file.endswith(".session")]


    async def pickle_load_full_channel(self, phone_number, channel_id):
        file_path = f"sessions/__cache/{phone_number}/{channel_id}.pkl"

        if os.path.exists(file_path):
            async with aio_open(file_path, "rb") as file:
                content = await file.read()
                return pickle.loads(content)
        else:
            print(f"Pickle cache not found: {file_path}")
            return None

    async def pickle_save_full_channel(self, phone_number, channel_id, full_channel):
        file_path = f"sessions/__cache/{phone_number}/{channel_id}.pkl"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        async with aio_open(file_path, "wb") as file:
            await file.write(pickle.dumps(full_channel))