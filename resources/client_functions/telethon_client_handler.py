from re import search
from dataclasses import dataclass

from resources.random_device_handler import RandomDeviceHandler
from resources.proxy_handler import ProxyHandler
from resources.client_functions.client_self_functions import ClientSelfHandler
from resources.client_functions.client_channel_functions import ClientChannelHandler
from resources.client_functions.client_user_functions import ClientUserHandler
from resources.file_handler import FileHandler
from resources.database_functions.database_handler import DatabaseHandler
from telethon import TelegramClient

from resources.__dependencies import GLOBAL_DEPENDENCIES

from resources._loggers import client_logger
import asyncio, selectors


re_until_date = lambda spam_message : search(r"(\d\d? [a-zA-z]+ \d{4}, \d{2}:\d{2} UTC)", spam_message)


@dataclass
class SessionCheckResult:
    status: str
    phone_number: str
    username: str = None
    error: str = None
    until_date: str = None

class MyClient:
    def __init__(self, phone_number):
        self.client = None
        self.SelfFunctions = None
        self.ChannelFunctions = None
        self.UserFunctions = None
        self.phone_number = phone_number
        self.DatabaseHandler:DatabaseHandler = GLOBAL_DEPENDENCIES.database_handler
        self.ProxyHandler:ProxyHandler = GLOBAL_DEPENDENCIES.proxy_handler
        self.FileHandler:FileHandler = GLOBAL_DEPENDENCIES.file_handler
        self.DeviceHandler:RandomDeviceHandler = GLOBAL_DEPENDENCIES.device_handler

    async def async_init(self):
        self.client = await self.get_telegram_client()
        self.SelfFunctions = ClientSelfHandler(self.phone_number, self.client)
        self.ChannelFunctions = ClientChannelHandler(self.phone_number, self.client)
        self.UserFunctions = ClientUserHandler(self.phone_number, self.client)
        return self

    @classmethod
    async def create(cls, phone_number):
        instance = cls(phone_number)
        return await instance.async_init()
    

    async def get_telegram_client(self):
        try:

            session_json = await self.FileHandler.check_json(self.phone_number)
            device_model = session_json['device']
            system_version = session_json.get('system_version') or session_json.get('sdk')
            app_version = session_json['app_version']
            api_id = session_json.get('api_id') or session_json.get('app_id')
            api_hash = session_json.get('api_hash') or session_json.get('app_hash')
            lang_code = session_json.get('lang_code') or 'en'
            system_lang = session_json.get("system_lang") or session_json.get("system_lang_code") or "en-us"
            proxies = await self.ProxyHandler.get_formatted_proxy(session_json["proxy"]) if 'proxy' in session_json else None

            session_loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
            client = TelegramClient(
                f"sessions/active/{self.phone_number}.session", api_id, api_hash,
                proxy=proxies, connection_retries=3, loop=session_loop, device_model=device_model,
                system_version=system_version, app_version=app_version, lang_code=lang_code, system_lang_code=system_lang)

            return client
        except Exception as error:
            client_logger.error(f"Error on 'get_telegram_client':\n{error}", exc_info=True)
            return None

    async def ban_check(self):
        return await self.SelfFunctions.ban_check()

    async def spambot_complain(self):
        return await self.SelfFunctions.spambot_complain()

    async def login_create_session_manual(self):
        return await self.SelfFunctions.login_create_session_manual()

    async def send_login_request(self):
        return await self.SelfFunctions.send_login_request()

    async def get_login_code(self):
        return await self.SelfFunctions.get_login_code()

    async def sign_in_with_code(self, verification_code, two_fa_input, client:TelegramClient, register_time=None):
        return await self.SelfFunctions.sign_in_with_code(verification_code, two_fa_input, client, register_time)

    async def terminate_other_sessions(self):
        return await self.SelfFunctions.terminate_other_sessions()
    
    async def get_client_info(self):
        return await self.SelfFunctions.get_client_info()
    
    async def change_profile_info(self, change_basic, change_username, change_pfp):
        return await self.SelfFunctions.change_profile_info(change_basic, change_username, change_pfp)
    
    async def change_two_fa(self):
        return await self.SelfFunctions.change_two_fa()
    
    async def reset_two_fa(self):
        return await self.SelfFunctions.reset_two_fa()

    async def set_privacy_invite(self, allow:bool=True):
        return await self.SelfFunctions.set_privacy_invite(allow)

    async def set_privacy_last_seen(self, allow:bool=True):
        return await self.SelfFunctions.set_privacy_last_seen(allow)


    async def print_channel_info(self, channel_username):
        return await self.ChannelFunctions.print_channel_info(channel_username)


    async def join_and_cache_public_channel(self, channel_username):
        return await self.ChannelFunctions.join_and_cache_public_channel(channel_username)

    async def join_and_cache_private_channel(self, channel_link):
        return await self.ChannelFunctions.join_and_cache_private_channel(channel_link)
    

    async def send_view_and_reaction(self, channel_link):
        return await self.ChannelFunctions.send_view_and_reaction(channel_link)



    async def start_bot_request(self, target_bot):
        return await self.UserFunctions.start_bot_request(target_bot)