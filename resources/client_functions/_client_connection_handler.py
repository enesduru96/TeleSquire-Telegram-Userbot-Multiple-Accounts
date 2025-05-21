import time, asyncio, logging
from telethon import TelegramClient
from python_socks._errors import ProxyError
from resources._utils import print_red
from resources._loggers import client_logger
from resources.__dependencies import GLOBAL_DEPENDENCIES

class ConnectionHandler:
    def __init__(self, phone_number, client:TelegramClient):
        self.phone_number = phone_number
        self.client = client
        self.FileHandler = GLOBAL_DEPENDENCIES.file_handler
        self.DatabaseHandler = GLOBAL_DEPENDENCIES.database_handler

    async def connect_to_session(self):
        try:
            if not self.client.is_connected():
                try:
                    await self.client.connect()
                except ProxyError as error:
                    print_red(f"[{self.phone_number}] - Proxy error: {error}")
                    retry_success = await self.retry_connection()
                    if not retry_success:
                        await self.disconnect_from_session()
                        client_logger.warning(f"[{self.phone_number}] - connect_to_session retry error, returning.")
                        return False
                    
                except Exception as error:
                    client_logger.error(f"[{self.phone_number}] - Error on 'connect_to_session - get_me':\n{error}", exc_info=True)

                    retry_success = await self.retry_connection()
                    if not retry_success:
                        await self.disconnect_from_session()
                        client_logger.warning(f"[{self.phone_number}] - connect_to_session retry error, returning.")
                        return False

            should_check_ban = await self.DatabaseHandler.check_session_last_checked(self.phone_number)
            if should_check_ban:
                try:
                    me = await self.client.get_me()
                    if not me:
                        client_logger.warning(f"[{self.phone_number}] - connect_to_session/get_me - BANNED")
                        await self.disconnect_from_session()
                        await self.FileHandler.move_to_banned(self.phone_number)
                        return False
                    
                    current_time = int(time.time())
                    await self.DatabaseHandler.update_session_last_checked(self.phone_number, current_time)
                except Exception as error:
                    client_logger.error(f"[{self.phone_number}] - Error on 'connect_to_session - get_me':\n{error}", exc_info=True)
                    await self.disconnect_from_session()
                    return False

            return True
        except Exception as error:
            await self.disconnect_from_session()
            client_logger.error(f"[{self.phone_number}] - Error on 'connect_to_session':\n{error}", exc_info=True)
            return False   

    async def disconnect_from_session(self):
        try:
            if self.client.is_connected():
                await self.client.disconnect()
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'disconnect_from_session':\n{error}", exc_info=True)

    async def retry_connection(self):
        try:
            await self.client.connect()
            client_logger.info(f"[{self.phone_number}] - Reconnected successfully.")
            return True
        except ProxyError as error:
            print_red(f"[{self.phone_number}] - Retry Failed: {error}")
            return False
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Connection retry failed: {error}", exc_info=True)
            return False