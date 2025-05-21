import json, asyncio, random
from telethon import TelegramClient

from telethon.tl.types import ChatInvite, ChatInvitePeek, ChatInviteAlready, MessageService, ReactionEmoji
from telethon.tl.types import InputPeerChannel

from telethon.tl.functions.messages import ImportChatInviteRequest, GetMessagesViewsRequest, CheckChatInviteRequest, SendReactionRequest
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest

from resources.proxy_handler import ProxyHandler
from resources.file_handler import FileHandler
from resources.database_functions.database_handler import DatabaseHandler
from resources.client_functions._client_connection_handler import ConnectionHandler

from resources.database_functions.base_data_classes import ChannelInformation, ChannelAccessInformation
from resources.database_functions.base_db_models import IndexedChannelAccess
from resources._utils import print_blue, print_magenta, print_green, print_red, print_yellow

from datetime import datetime


# available_reactions = ["❤", "🔥", "👍", "👏", "🎉", "💯", "🤩", "😍", "🏆"]
# available_reactions = ["❤", "🔥", "👍", "👏", "🎉", "💯"]
available_reactions = ["❤", "🔥"]


from resources._loggers import client_logger
from resources.__dependencies import GLOBAL_DEPENDENCIES

class ClientChannelHandler:
    def __init__(self, phone_number, client:TelegramClient):
        self.phone_number = phone_number
        self.client = client
        self.DatabaseHandler:DatabaseHandler = GLOBAL_DEPENDENCIES.database_handler
        self.FileHandler:FileHandler = GLOBAL_DEPENDENCIES.file_handler
        self.ProxyHandler:ProxyHandler = GLOBAL_DEPENDENCIES.proxy_handler
        self.ConnectionHandler = ConnectionHandler(self.phone_number, self.client)


    def pretty_print(self,data):
        print(json.dumps(data, indent=4, ensure_ascii=False, default=self.custom_serializer))

    def custom_serializer(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return obj.hex()
        return str(obj)


    async def print_channel_info(self, channel_username, already_connected=False):
        if already_connected == False:
            if not await self.ConnectionHandler.connect_to_session():
                return
        

        is_broadcast_channel = False

        full_channel = await self.client(GetFullChannelRequest(channel_username))


        if hasattr(full_channel, "full_chat") and full_channel.full_chat:
            full_chat = full_channel.full_chat
            print("Full Chat Information Available")
        else:
            print("Full Chat Information Not Available")
            full_chat = None


        if hasattr(full_channel, "chats") and full_channel.chats:
            chats = full_channel.chats
            print("Chats Information Available")
        else:
            print("Chats Information Not Available")
            chats = []


        if not full_chat:
            print("PROBLEM, NO FULL CHAT!")
            full_channel_dict = full_channel.to_dict()
            with open("problem_full_channel_output.json", "w", encoding="utf-8") as f:
                json.dump(full_channel_dict, f, indent=4, ensure_ascii=False, default=self.custom_serializer)
            return
        

        channel_id = full_chat.id
        about = full_chat.about
        member_count = full_chat.participants_count


        await self.FileHandler.pickle_save_full_channel(self.phone_number, channel_id, full_channel)


        if full_chat and hasattr(full_chat, "linked_chat_id") and full_chat.linked_chat_id:
            linked_chat_id = full_chat.linked_chat_id
            print(f"Linked Chat ID: {linked_chat_id}")


        if len(full_channel.chats) == 0:
            main_chat = full_channel.chats[0]
            channel_access_hash = main_chat.access_hash

            if main_chat.broadcast:
                is_broadcast_channel = True


        elif len(full_channel.chats) > 1:
            main_chat = full_channel.chats[0]
            channel_access_hash = main_chat.access_hash

            if main_chat.broadcast:
                is_broadcast_channel = True

            linked_chat = full_channel.chats[1]
            linked_chat_access_hash = linked_chat.access_hash


            linked_chat_entity = await self.client(GetFullChannelRequest(InputPeerChannel(linked_chat_id, linked_chat_access_hash)))
            full_linked_channel_dict = linked_chat_entity.to_dict()
            with open("linked_channel_output.json", "w", encoding="utf-8") as f:
                json.dump(full_linked_channel_dict, f, indent=4, ensure_ascii=False, default=self.custom_serializer)


    async def join_and_cache_private_channel(self, channel_link, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return
            
            channel_username = None
            channel_title = None
            channel_about = ""
            is_broadcast = False
            is_megagroup = False

            invite_link = channel_link.split("/")[-1:][0].replace("+","")
            check_invite = await self.client(CheckChatInviteRequest(invite_link))

            if isinstance(check_invite, ChatInvite) or isinstance(check_invite, ChatInvitePeek):
                channel_title = check_invite.title
                is_broadcast = check_invite.broadcast
                is_megagroup = check_invite.megagroup
                channel_about = check_invite.about
                request_needed = check_invite.request_needed

                import_result = await self.client(ImportChatInviteRequest(invite_link))

                if hasattr(import_result, 'chats') and import_result.chats:
                    channel_id = import_result.chats[0].id
                    channel_access_hash = import_result.chats[0].access_hash
                    has_link = import_result.chats[0].has_link

            elif isinstance(check_invite, ChatInviteAlready):
                channel_title = check_invite.chat.title
                is_broadcast = check_invite.chat.broadcast
                is_megagroup = check_invite.chat.megagroup
                channel_id = check_invite.chat.id
                channel_access_hash = check_invite.chat.access_hash
                request_needed = False


            full_channel = await self.client(GetFullChannelRequest(InputPeerChannel(channel_id, channel_access_hash)))
            full_chat = full_channel.full_chat

            channel_about = full_chat.about
            can_view_participants = full_chat.can_view_participants
            participants_count = full_chat.participants_count
            linked_chat_id = full_chat.linked_chat_id
            slow_time = full_chat.slowmode_seconds

            if len(full_channel.chats) > 0:
                slow_mode = full_channel.chats[0].slowmode_enabled
                channel_username = full_channel.chats[0].username
                if hasattr(full_channel.chats[0], "usernames"):
                    channel_username = full_channel.chats[0].usernames[0]["username"]


            channel_info = ChannelInformation(
                entity_id=channel_id,
                username=channel_username,
                title=channel_title,
                about=channel_about,
                is_broadcast=is_broadcast,
                is_megagroup=is_megagroup,
                linked_chat_id=linked_chat_id,
                can_view_participants=can_view_participants,
                participant_count=participants_count,
                slow_mode=slow_mode,
                slow_time=slow_time,
                request_needed=request_needed,
                is_private=True,
                invite_link=channel_link

            )

            channel_access_info = ChannelAccessInformation(
                entity_id=channel_id,
                access_hash=channel_access_hash,
                indexer_id=await self.DatabaseHandler.get_session_entity_id(self.phone_number),
                indexer_phone= self.phone_number,
                has_joined=True
            )
            await self.DatabaseHandler.cache_new_channel_access(channel_access_info)

            return channel_info
        
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'cache_private_channel':\n{error}", exc_info=True)
            return False

        finally:
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()
            pass


    async def join_and_cache_public_channel(self, channel_username, already_connected=False):
        try:
            await asyncio.sleep(random.randint(10, 30))
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return False

            channel_entity = await self.client.get_entity(channel_username)
            if not channel_entity.broadcast and not channel_entity.megagroup:
                print_magenta(f"{channel_username} is Not a group or channel!")
                return False

            try:
                await self.client(JoinChannelRequest(channel_entity))
                print_green(f"[{self.phone_number}] - Joined: {channel_username}")
            except Exception as error:
                client_logger.error(f"[{self.phone_number}] - Failed to join channel {channel_username}: {error}", exc_info=False)
        

            channel_id = channel_entity.id
            channel_access_hash = channel_entity.access_hash
            channel_title = channel_entity.title
            is_broadcast = channel_entity.broadcast
            is_megagroup = channel_entity.megagroup

            full_channel = await self.client(GetFullChannelRequest(InputPeerChannel(channel_id, channel_access_hash)))
            full_chat = full_channel.full_chat

            channel_about = full_chat.about
            can_view_participants = full_chat.can_view_participants
            participants_count = full_chat.participants_count
            linked_chat_id = full_chat.linked_chat_id
            slow_time = full_chat.slowmode_seconds

            if len(full_channel.chats) > 0:
                slow_mode = full_channel.chats[0].slowmode_enabled
                channel_username = full_channel.chats[0].username

            channel_info = ChannelInformation(
                entity_id=channel_id,
                username=channel_username,
                title=channel_title,
                about=channel_about,
                is_broadcast=is_broadcast,
                is_megagroup=is_megagroup,
                linked_chat_id=linked_chat_id,
                can_view_participants=can_view_participants,
                participant_count=participants_count,
                slow_mode=slow_mode,
                slow_time=slow_time,
                request_needed=False,
                is_private=False,
                invite_link=None
            )

            channel_access_info = ChannelAccessInformation(
                entity_id=channel_id,
                access_hash=channel_access_hash,
                indexer_id= await self.DatabaseHandler.get_session_entity_id(self.phone_number),
                indexer_phone= self.phone_number,
                has_joined=True
            )
            await self.DatabaseHandler.cache_new_channel_access(channel_access_info)


            await self.FileHandler.pickle_save_full_channel(self.phone_number, channel_id, full_channel)

            return channel_info

        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'join_and_cache_public_channel':\n{error}", exc_info=True)
            return False

        finally:
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()
            pass


    async def send_view_and_reaction(self, channel_link, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return False
            
            channel_access:IndexedChannelAccess = await self.DatabaseHandler.get_cached_channel_access(self.phone_number, channel_link)
            if not channel_access:
                print_red(f"[{self.phone_number}] - Has no access. Trying to join...")
                join_result = await self.join_and_cache_public_channel(channel_link)
                if not join_result:
                    return False
                channel_access:IndexedChannelAccess = await self.DatabaseHandler.get_cached_channel_access(self.phone_number, channel_link)
                if not channel_access:
                    print_red(f"[{self.phone_number}] - Has no access. Returning.")
                    return False
                
            channel_id = int(channel_access.entity_id)
            access_hash = int(channel_access.access_hash)


            target_channel_entity = InputPeerChannel(channel_id, access_hash)

            messages = self.client.iter_messages(target_channel_entity, limit=10, wait_time=4)
            async for message in messages:
                if not isinstance(message, MessageService):
                    increment_result = await self.client(GetMessagesViewsRequest(peer=target_channel_entity, id=[message.id], increment=True))
                    await asyncio.sleep(random.uniform(4,9))
                    reaction_to_send = random.choice(available_reactions)
                    reaction = ReactionEmoji(emoticon=reaction_to_send)
                    reaction_result = await self.client(SendReactionRequest(peer=target_channel_entity, msg_id=message.id, reaction=[reaction]))
                    await asyncio.sleep(random.uniform(4,9))

                    print_blue(f"[{self.phone_number}] - Increment: Done - Reaction: {reaction_to_send}")
            
            return True
            
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'send_view_and_reaction':\n{error}", exc_info=True)
            return False

        finally:
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()
            pass
