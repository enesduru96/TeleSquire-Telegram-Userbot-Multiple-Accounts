import asyncio, random
from telethon import TelegramClient
from telethon.tl.types import InputPeerUser

from telethon.tl.functions.messages import StartBotRequest

from resources.proxy_handler import ProxyHandler
from resources.file_handler import FileHandler
from resources.database_functions.database_handler import DatabaseHandler
from resources.client_functions._client_connection_handler import ConnectionHandler

from resources.database_functions.base_data_classes import TelegramUserInformation, TelegramUserAccessInformation
from resources.database_functions.base_db_models import IndexedUserAccess
from resources._utils import print_blue, print_magenta, print_green, print_red, print_yellow


from resources._loggers import client_logger
from resources.__dependencies import GLOBAL_DEPENDENCIES

class ClientUserHandler:
    def __init__(self, phone_number, client:TelegramClient):
        self.phone_number = phone_number
        self.client = client
        self.DatabaseHandler:DatabaseHandler = GLOBAL_DEPENDENCIES.database_handler
        self.FileHandler:FileHandler = GLOBAL_DEPENDENCIES.file_handler
        self.ProxyHandler:ProxyHandler = GLOBAL_DEPENDENCIES.proxy_handler
        self.ConnectionHandler = ConnectionHandler(self.phone_number, self.client)

    async def start_bot_request(self, target_bot, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return False
            
            await asyncio.sleep(random.uniform(1, 15))
            user_db_info = None
            user_access:IndexedUserAccess = await self.DatabaseHandler.get_cached_user_access(self.phone_number, target_bot)
            if not user_access:
                input_entity = await self.client.get_input_entity(target_bot)
                target_peer = await self.client.get_entity(input_entity)
                bot_id = target_peer.id
                bot_access_hash = target_peer.access_hash

                user_db_info = TelegramUserInformation(
                    entity_id=bot_id,
                    first_name=target_peer.first_name,
                    last_name=target_peer.last_name,
                    username=target_peer.username,
                    about="",
                    last_status="",
                    is_premium=target_peer.premium,
                    is_bot=target_peer.bot
                )

                user_access_info = TelegramUserAccessInformation(
                    entity_id=bot_id,
                    access_hash=bot_access_hash,
                    indexer_id= await self.DatabaseHandler.get_session_entity_id(self.phone_number),
                    indexer_phone= self.phone_number
                )
                await self.DatabaseHandler.cache_new_user_access(user_access_info)

                final_peer = InputPeerUser(user_id=bot_id, access_hash=bot_access_hash)
            else:
                final_peer = InputPeerUser(user_id=user_access.entity_id, access_hash=int(user_access.access_hash))

                result = await self.client.get_entity(final_peer)
                user_db_info = TelegramUserInformation(
                    entity_id=result.id,
                    first_name=result.first_name,
                    last_name=result.last_name,
                    username=result.username,
                    about="",
                    last_status="",
                    is_premium=result.premium,
                    is_bot=result.bot
                )
            

            result = await self.client(StartBotRequest(bot=final_peer, peer=final_peer, start_param="start"))
            print(f"{str(result)[:30]}")

            return user_db_info

        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'start_bot_request':\n{error}", exc_info=True)
            return False

        finally:
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()
            pass

