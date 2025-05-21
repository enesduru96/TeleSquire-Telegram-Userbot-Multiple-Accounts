import json, asyncio, selectors, os
import python_socks
import re
from shutil import move
from re import search
from dataclasses import dataclass
from sqlite3 import OperationalError, DatabaseError

from telethon import TelegramClient
import telethon.errors.rpcerrorlist as errorList

re_until_date = lambda spam_message : search(r"(\d\d? [a-zA-z]+ \d{4}, \d{2}:\d{2} UTC)", spam_message)

from resources._loggers import client_logger
from resources.__dependencies import GLOBAL_DEPENDENCIES


@dataclass
class SessionCheckResult:
    status: str
    phone_number: str
    username: str = None
    error: str = None
    until_date: str = None

class SellerClientHandler:
    def __init__(self, phone_number, proxy_handler=None, device_handler=None, file_handler=None):
        self.phone_number = phone_number
        self.proxy_handler = proxy_handler or GLOBAL_DEPENDENCIES.proxy_handler
        self.device_handler = device_handler or GLOBAL_DEPENDENCIES.device_handler
        self.file_handler = file_handler or GLOBAL_DEPENDENCIES.file_handler

    #region Session Json Data Related

    def get_formatted_proxy(self, proxyString):
        try:
            proxi_part = proxyString.split(':')
            return (
                python_socks.ProxyType.SOCKS5,
                proxi_part[0],      # ip
                int(proxi_part[1]), # port
                True,
                proxi_part[2], # username
                proxi_part[3]  # password
            )
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'get_formatted_proxy':\n{error}", exc_info=True)


    async def check_session_json(self):
        try:
            file_path = "sessions/_seller_sessions"
            if os.path.isfile(f"{file_path}/{self.phone_number}.json"):
                jsonFile = open(f'{file_path}/{self.phone_number}.json', 'r+', encoding="utf-8")
                sessionJson = json.load(jsonFile)

                device_model_r = sessionJson['device']
                system_version = sessionJson.get('system_version') or sessionJson.get('sdk')
                app_version_r = sessionJson['app_version']
                api_id = sessionJson.get('api_id') or sessionJson.get('app_id')
                api_hash = sessionJson.get('api_hash') or sessionJson.get('app_hash')
                lang_code = sessionJson.get('lang_code') or 'en'
                system_lang_code = sessionJson.get("system_lang") or sessionJson.get("system_lang_code") or "en-us"

                if "proxy" in sessionJson:
                    if not isinstance(sessionJson["proxy"], str):
                        new_proxy = await self.proxy_handler.get_next_proxy(self.phone_number)
                    else:
                        new_proxy = sessionJson["proxy"]

                proxies = new_proxy
                proxy_string = new_proxy

                if "twoFA" in sessionJson:
                    two_factor = sessionJson["twoFA"]
                elif "2fa" in sessionJson:
                    two_factor = sessionJson['2fa']

                with open(f'{file_path}/{self.phone_number}.json', 'r', encoding="utf-8") as f:
                    data = json.load(f)
                data["proxy"] = proxy_string
                with open(f'{file_path}/{self.phone_number}.json', 'w', encoding="utf-8") as f:
                    json.dump(data, f)

            return {
                "device"        : device_model_r,
                "system_version": system_version,
                "app_version"   : app_version_r,
                "api_id"        : api_id,
                "api_hash"      : api_hash,
                "2fa"           : two_factor,
                "proxies"       : proxies,
                'proxy_string'  : proxy_string,
                "lang_code"     : lang_code,
                "system_lang"   : system_lang_code
                }
        except Exception as error:
            client_logger.error(f"Error on 'check_session_json':\n{error}", exc_info=True)

    async def get_seller_client(self):
        try:
            file_path = "sessions/_seller_sessions"
            session_info_list = await self.check_session_json()
            if isinstance(session_info_list, str):
                device_model_r, system_version_r, app_version_r, api_id, api_hash = await self.device_handler.get_device_info_and_api()
                lang_code = "en"
                system_lang = "en-US"
                twoFA = None
                new_proxy = await self.proxy_handler.get_next_proxy(self.phone_number)
                proxies = new_proxy
                proxy_string = new_proxy
                
            else:
                device_model_r = session_info_list["device"]
                system_version_r = session_info_list["system_version"]
                app_version_r = session_info_list["app_version"]
                api_id = session_info_list["api_id"]
                api_hash = session_info_list["api_hash"]
                lang_code = session_info_list["lang_code"]
                system_lang = session_info_list["system_lang"]
                proxies = self.get_formatted_proxy(session_info_list["proxies"]) if session_info_list['proxies'] != None else None
                twoFA = session_info_list['2fa']

                proxy_string = session_info_list["proxies"]

            print(proxies)
            session_loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
            client = TelegramClient(
                f"{file_path}/{self.phone_number}.session", api_id, api_hash,
                proxy=proxies, connection_retries=3, loop=session_loop, device_model=device_model_r,
                system_version=system_version_r, app_version=app_version_r, lang_code=lang_code, system_lang_code=system_lang)

            return client
        except Exception as error:
            client_logger.error(f"Error on 'get_telegram_client':\n{error}", exc_info=True)
            return None
    
    #endregion    

    #region File Move

    def move_to_banned(self):
        try:
            file_path = "sessions/_seller_sessions"
            move(f'{file_path}/{self.phone_number}.session', f'{file_path}/banned/{self.phone_number}.session')
            move(f'{file_path}/{self.phone_number}.json', f'{file_path}/banned/{self.phone_number}.json')
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'move_to_banned':\n{error}", exc_info=True)

    def move_to_duplicated(self):
        try:
            file_path = "sessions/_seller_sessions"
            move(f'{file_path}/{self.phone_number}.session', f'{file_path}/duplicated/{self.phone_number}.session')
            move(f'{file_path}/{self.phone_number}.json', f'{file_path}/duplicated/{self.phone_number}.json')
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'move_to_duplicated':\n{error}", exc_info=True)

    def move_to_spam(self):
        try:
            file_path = "sessions/_seller_sessions"
            move(f'{file_path}/{self.phone_number}.session', f'{file_path}/spam/{self.phone_number}.session')
            move(f'{file_path}/{self.phone_number}.json', f'{file_path}/spam/{self.phone_number}.json')
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'move_to_spam':\n{error}", exc_info=True)


    #endregion

    async def get_seller_twoFa(self):
        file_path = "sessions/_seller_sessions"
        with open(f"{file_path}/{self.phone_number}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if "2fa" in data:
                twoFA = str(data["2fa"])
            elif "twoFA" in data:
                twoFA = str(data["twoFA"])
            return twoFA
    
    async def get_seller_register_time(self):
        file_path = "sessions/_seller_sessions"
        with open(f"{file_path}/{self.phone_number}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if "register_time" in data:
                register_time = str(data["register_time"])
            return register_time

    async def get_login_code(self):
        code_pattern = re.compile(r'(\d{5})')

        try:
            seller_client:TelegramClient = await self.get_seller_client()
            await seller_client.connect()
        except ConnectionError:
            try:
                seller_client:TelegramClient = await self.get_seller_client()
                await seller_client.connect()
            except Exception as error:
                client_logger.error(f"[{self.phone_number}] - Error while connecting on 'get_login_code':\n{error}", exc_info=True)
                return

        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'get_login_code':\n{error}", exc_info=True)
            return

        try:
            async for dialog in seller_client.iter_dialogs():
                if dialog.name == "Telegram":
                    print("Found telegram chat")
                    async for message in seller_client.iter_messages(dialog.id, limit=1):
                        match = code_pattern.search(message.text)
                        if match:
                            verificationCode = match.group(1)
                            print(f"Code: {verificationCode}")
                            await seller_client.disconnect()
                            return verificationCode
        except errorList.UserDeactivatedBanError:
            try:await seller_client.disconnect()
            except:pass
            self.move_to_banned()
            return "banned"


    async def ban_check(self):
        client = await self.get_seller_client()
        try:
            await client.connect()
        except Exception as error:
            client_logger.error(f"[{self.phone_number}]- Error on 'ban_check':\n{error}", exc_info=True)
            print(f"    {self.phone_number} Connection Error, Trying Again...")
            try:
                client = await self.get_seller_client()
                await client.connect()
            except Exception as error:
                client_logger.error(f"[{self.phone_number}] - CONNERR - Error on 'ban_check':\n{error}", exc_info=True)
                return SessionCheckResult(status="CONNERR", phone_number=self.phone_number)
        
        try:
            my_telegram_user = await client.get_me()

            if not my_telegram_user:
                client_logger.warning(f"[{self.phone_number}] - BANNED")
                if client.is_connected(): await client.disconnect()
                self.move_to_banned()
                return SessionCheckResult(status="BANNED", phone_number=self.phone_number)

            username = my_telegram_user.username if my_telegram_user.username else None
            return SessionCheckResult(status="ONLINE", phone_number=self.phone_number, username=username)

        except (errorList.AuthKeyDuplicatedError, OperationalError, errorList.AuthKeyUnregisteredError, errorList.UserDeactivatedBanError) as specific_error:
            client_logger.error(f"[{self.phone_number}] - Error on 'ban_check':\n{error}", exc_info=True)
            if client.is_connected(): await client.disconnect()
            if specific_error.__class__.__name__.upper() == "AUTHKEYDUPLICATEDERROR":
                self.move_to_duplicated()
            elif specific_error.__class__.__name__.upper() == "USERDEACTIVATEDBANERROR":
                self.move_to_banned()
            return SessionCheckResult(status=specific_error.__class__.__name__.upper(), phone_number=self.phone_number)
        except DatabaseError as error:
            client_logger.error(f"[{self.phone_number}] - DATABASEERROR - Error on 'ban_check':\n{error}", exc_info=True)
            return SessionCheckResult(status="DATABASEERROR", phone_number=self.phone_number, error=str(error))
        except ValueError:
            client_logger.error(f"[{self.phone_number}] - VALUE ERROR - Error on 'ban_check':\n{error}", exc_info=True)
            if client.is_connected(): await client.disconnect()
            self.move_to_banned()
            return SessionCheckResult(status="BANNED", phone_number=self.phone_number)
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'ban_check':\n{error}", exc_info=True)
            return SessionCheckResult(status="ERROR", phone_number=self.phone_number, error=str(error))
        finally:
            if client.is_connected():
                await client.disconnect()