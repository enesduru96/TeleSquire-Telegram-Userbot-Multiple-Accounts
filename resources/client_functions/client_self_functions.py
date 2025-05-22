import time
import random
import asyncio
from os import remove
from pathlib import Path
from re import findall

from sqlite3 import OperationalError, DatabaseError


from telethon import functions
from telethon import TelegramClient
from telethon.tl.types import Authorization
from telethon.tl.types import InputPeerUser
from telethon.tl.types import UserFull
from telethon.tl.types import InputPhoto, InputPrivacyValueDisallowAll, InputPrivacyKeyStatusTimestamp, InputPrivacyKeyChatInvite, InputPrivacyValueAllowAll

from telethon.tl.functions.messages import StartBotRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest, GetPasswordRequest, SetPrivacyRequest, GetAuthorizationsRequest, ResetPasswordRequest

import telethon.errors.rpcerrorlist as errorList

from resources.file_handler import FileHandler
from resources.proxy_handler import ProxyHandler
from resources.database_functions.database_handler import DatabaseHandler
from resources.client_functions._client_connection_handler import ConnectionHandler
from resources.database_functions.base_data_classes import SessionCheckResult, ClientInformation
from resources._utils import get_random_2fa, print_yellow, print_red, print_blue, print_magenta, print_green


from resources._loggers import client_logger
from resources.__dependencies import GLOBAL_DEPENDENCIES

class ClientSelfHandler:
    def __init__(self, phone_number, client:TelegramClient):
        self.phone_number = phone_number
        self.client = client
        self.DatabaseHandler:DatabaseHandler = GLOBAL_DEPENDENCIES.database_handler
        self.FileHandler:FileHandler = GLOBAL_DEPENDENCIES.file_handler
        self.ProxyHandler:ProxyHandler = GLOBAL_DEPENDENCIES.proxy_handler
        self.ConnectionHandler = ConnectionHandler(self.phone_number, self.client)

    async def ban_check(self, already_connected=False):
        if already_connected == False:
            if not await self.ConnectionHandler.connect_to_session():
                return SessionCheckResult(status="ERROR", phone_number=self.phone_number, error="None")

        try:
            me = await self.client.get_me()

            if not me:
                client_logger.warning(f"[{self.phone_number}] - BANNED")
                if self.client.is_connected(): await self.client.disconnect()
                await asyncio.sleep(1)
                await self.FileHandler.move_to_banned(self.phone_number)
                client_logger.warning(f"[{self.phone_number}] - BANNED")
                return SessionCheckResult(status="BANNED", phone_number=self.phone_number)

            username = me.username if me.username else None
            return SessionCheckResult(status="ONLINE", phone_number=self.phone_number, username=username)

        except (errorList.AuthKeyDuplicatedError, OperationalError, errorList.AuthKeyUnregisteredError, errorList.UserDeactivatedBanError) as specific_error:
            client_logger.error(f"[{self.phone_number}] - Error on 'ban_check':\n{error}", exc_info=True)
            if self.client.is_connected(): await self.client.disconnect()
            if specific_error.__class__.__name__.upper() == "AUTHKEYDUPLICATEDERROR":
                await self.FileHandler.move_to_duplicated(self.phone_number)
            elif specific_error.__class__.__name__.upper() == "USERDEACTIVATEDBANERROR":
                if self.client.is_connected(): await self.client.disconnect()
                await asyncio.sleep(1)
                await self.FileHandler.move_to_banned(self.phone_number)
                return SessionCheckResult(status="BANNED", phone_number=self.phone_number)
            return SessionCheckResult(status=specific_error.__class__.__name__.upper(), phone_number=self.phone_number)
        except DatabaseError as error:
            client_logger.error(f"[{self.phone_number}] - DATABASEERROR - Error on 'ban_check':\n{error}", exc_info=True)
            return SessionCheckResult(status="DATABASEERROR", phone_number=self.phone_number, error=str(error))
        except ValueError:
            client_logger.error(f"[{self.phone_number}] - VALUE ERROR - Error on 'ban_check':\n{error}", exc_info=True)
            if self.client.is_connected(): await self.client.disconnect()
            await self.FileHandler.move_to_banned(self.phone_number)
            return SessionCheckResult(status="BANNED", phone_number=self.phone_number)
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'ban_check':\n{error}", exc_info=True)
            return SessionCheckResult(status="ERROR", phone_number=self.phone_number, error=str(error))
        finally:
            pass
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()

    async def spambot_complain(self, already_connected=False):
        if already_connected == False:
            if not await self.ConnectionHandler.connect_to_session():
                return
        
        try:
            complaints = [line.replace("\n","").replace('"','') for line in open("data/complaints.txt","r",encoding="utf-8").readlines()]
            
            message_to_send = random.choice(complaints)

            session_info = await self.DatabaseHandler.get_session_info(self.phone_number)
            spambot_id = 178220800
            spambot_access_hash = int(session_info.spambot_access_hash)

            bot_peer = InputPeerUser(spambot_id, spambot_access_hash)
            result = await self.client(StartBotRequest(
                bot         = bot_peer,
                peer        = bot_peer,
                start_param = "SpamCheck"
            ))
            
            await asyncio.sleep(random.randrange(2, 7))
            messages  = await self.client.get_messages(bot_peer, 1)
            last_message      = messages[0]
            last_message_text = last_message.message
            print_blue(f"[{self.phone_number}] -> 1 -> {last_message_text[:30]}")
            if ("harsh response" in last_message_text and "some actions" in last_message_text):
                try:
                    await last_message.click(3)
                except:
                    print(last_message)
                    x = int(input("input button index: "))
                    await last_message.click(x)
            elif("harsh response" in last_message_text and "some phone numbers" in last_message_text):
                try:
                    await last_message.click(0)
                except:
                    print(last_message)
                    x = int(input("input button index: "))
                    await last_message.click(x)
            
            elif "free as a bird" in last_message_text.lower():
                print(f"{self.phone_number} -- Already good news")
                return "clear"

            else:
                print_blue(f"[{self.phone_number}] -> Unexpected answer: {last_message_text}")
                return "error"
            

            await asyncio.sleep(random.randrange(2, 7))
            messages  = await self.client.get_messages(bot_peer, 1)
            last_message      = messages[0]
            last_message_text = last_message.message
            print_blue(f"[{self.phone_number}] -> 2 -> {last_message_text[:30]}")
            if "submit a complaint" in last_message_text:
                await last_message.click(0)


            await asyncio.sleep(random.randrange(2, 7))
            messages  = await self.client.get_messages(bot_peer, 1)
            last_message      = messages[0]
            last_message_text = last_message.message
            print_blue(f"[{self.phone_number}] -> 3 -> {last_message_text[:30]}")
            if "please confirm" in last_message_text.lower():
                await last_message.click(0)
            elif "already" in last_message_text.lower():
                return "waiting"
            else:
                print(last_message)
                x = int(input("input button index: "))
                await last_message.click(x)

            await asyncio.sleep(random.randrange(2, 7))
            messages  = await self.client.get_messages(bot_peer, 1)
            last_message      = messages[0]
            last_message_text = last_message.message
            print_blue(f"[{self.phone_number}] -> 4 -> {last_message_text[:30]}")

            if "what went wrong" in last_message_text.lower():
                await self.client.send_message(bot_peer, message_to_send)
            
            await asyncio.sleep(1)
            messages  = await self.client.get_messages(bot_peer, 1)
            last_message      = messages[0]
            last_message_text = last_message.message
            print_blue(f"[{self.phone_number}] -> 5 -> {last_message_text[:30]}")

            if "this was a mistake, all limitations will be lifted" in last_message_text.lower():
                
                print_green(f"[{self.phone_number}] - Complaint Sent")
                return "sent"

        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'spambot_complain':\n{error}", exc_info=False)
            return "error"
        finally:
            pass
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()

    async def login_create_session_manual(self):
        print(f"Phone: {self.phone_number}\n    This is a one-time login process.\n    After you successfully login, your session will be saved as a file and you will not have to login again.")
        session = f"sessions/active/{self.phone_number}.session"
        if not self.client.is_connected():
            try:
                await self.client.connect()
            except Exception as error:
                client_logger.error(f"[{self.phone_number}] - connection error: {error} trying again.")
                if not await self.retry_connection():
                    client_logger.error(f"[{self.phone_number}] - Error on 'login_and_create_session':\n{error}", exc_info=True)
                    try: remove(f"sessions/active/{self.phone_number}.session")
                    except: pass
                    return

        if not await self.client.is_user_authorized():
            try:
                await self.client.send_code_request(self.phone_number)
            except Exception as error:
                client_logger.error(f"[{self.phone_number}] - Error on send code request 'login_and_create_session':\n{error}", exc_info=True)
                return

            try:
                verificationCode = input(f'\n    {self.phone_number} - Login Code: ')
                if verificationCode == "":
                    print(f"    Login Code Cannot Be Empty!")
                    await self.login_create_session_manual()

                await self.client.sign_in(self.phone_number, verificationCode)
                if self.client.is_connected(): await self.client.disconnect()
            except errorList.SessionPasswordNeededError:
                get_passwd = await self.client(GetPasswordRequest())
                two_fa_input = str(input(f'\n    Two-Factor Authentication Password (hint:{get_passwd.hint}): '))
                try:
                    await self.client.sign_in(password=two_fa_input)
                    await self.FileHandler.update_2fa_json(two_fa_input, self.phone_number)
                    if self.client.is_connected(): await self.client.disconnect()
                    client_logger.success(f"[{self.phone_number}] - Successfully created session: {self.phone_number} | {two_fa_input}")
                except Exception as error:
                    if self.client.is_connected(): await self.client.disconnect()
                    remove(f"sessions/active/{self.phone_number}.session")
                    client_logger.error(f"[{self.phone_number}] - Wrong 2FA while creating session")
                    return
            except Exception as error:
                client_logger.error(f"[{self.phone_number}] - Error on 'login_and_create_session':\n{error}", exc_info=True)
                if self.client.is_connected(): await self.client.disconnect()
                return

    async def send_login_request(self):
        session = f"sessions/active/{self.phone_number}.session"
        if not self.client.is_connected():
            try:
                await self.client.connect()
            except Exception as error:
                client_logger.error(f"[{self.phone_number}] - connection error: {error} trying again.")
                if not await self.retry_connection():
                    client_logger.error(f"[{self.phone_number}] - Error while connecting on 'send_login_request':\n{error}", exc_info=True)
                    try: remove(f"sessions/active/{self.phone_number}.session")
                    except: pass
                    return

        print(f"New Client Connected: {self.client.api_id}, {self.client._proxy}")

        if not await self.client.is_user_authorized():
            try:
                await self.client.send_code_request(self.phone_number)
                return self.client
            except Exception as error:
                client_logger.error(f"[{self.phone_number}] - Error on send code request 'send_login_request':\n{error}", exc_info=True)
                return

    async def sign_in_with_code(self, verification_code, two_fa_input, client:TelegramClient, register_time):
        try:
            await client.sign_in(self.phone_number, verification_code)
            if client.is_connected(): await client.disconnect()
        except errorList.SessionPasswordNeededError:
            try:
                await client.sign_in(password=two_fa_input)
                await self.FileHandler.update_2fa_json(two_fa_input, self.phone_number)
                await self.FileHandler.update_register_time_json(register_time, self.phone_number)
                if client.is_connected(): await client.disconnect()
                print_green(f"[{self.phone_number}] - Successfully created session: {self.phone_number} | {two_fa_input}")
            except Exception as error:
                client_logger.error(f"[{self.phone_number}] - Error on 'sign_in_with_code':\n{error}", exc_info=True)
                print(f"    Wrong 2FA Password! Re-run the script to Try Again.")
                if client.is_connected(): await client.disconnect()
                remove(f"sessions/active/{self.phone_number}.session")

                return
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'sign_in_with_code':\n{error}", exc_info=True)
            if client.is_connected(): await client.disconnect()
            return

    async def get_login_code(self, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return
            
            extract_code = lambda message: findall(r'\d+', message)[0]
            
            last_messages = await self.client.get_messages(777000, 1)
            print(last_messages)

            if len(last_messages) == 0:
                return "Please Request Your Login Code For This Number First!!!"

            last_message  = last_messages[0]

            try:
                return extract_code(last_message.message)
            except (AttributeError, IndexError):
                return last_message.message
            
        except Exception as error:
            client_logger.error(f"[{self.phone_number}]- Error on 'get_client_info':\n{error}", exc_info=True)
            return None
        finally:
            pass
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()

    async def get_client_info(self, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return
                
            me = await self.client.get_me()
            
            full_user:UserFull = await self.client(GetFullUserRequest(me))
            my_bio = full_user.full_user.about

            authCall = await self.client(GetAuthorizationsRequest())
            activeSessions = authCall.authorizations
            for item in activeSessions:
                auth_item:Authorization = item
                if auth_item.current:
                    creation_date = auth_item.date_created
            
            bot_access_hash = 0
            try:
                spambot_input_entity = await self.client.get_input_entity("spambot")
                bot_access_hash = spambot_input_entity.access_hash
            except Exception as e:
                print(f"Error resolving SpamBot for {self.phone_number}: {e}")

            try:
                if me.photo:
                    photo_folder = Path("_files/profile_pictures")
                    profile_photo_path = photo_folder / f"{me.id}.jpg"
                    profile_photo_path = profile_photo_path.as_posix()
                    photo_path = await self.client.download_profile_photo(me, file=profile_photo_path)
                else:
                    photo_path = None

            except errorList.PhotoCropSizeSmallError:
                print(f"Profile photo for {self.phone_number} is too small to download.")
            except Exception as e:
                print(f"Error downloading profile photo for {self.phone_number}: {e}")

            current_time = int(time.time())

            client_information = ClientInformation(
                number=me.phone,
                entity_id=me.id,
                first_name=me.first_name,
                last_name=me.last_name,
                username=me.username,
                session_creation_date=creation_date.strftime("%d/%m/%Y %H:%M:%S"),
                profile_photo=photo_path,
                bio=my_bio,
                spambot_access_hash=bot_access_hash,
                last_checked=current_time
            )

            return client_information
        
        except Exception as error:
            client_logger.error(f"[{self.phone_number}]- Error on 'get_client_info':\n{error}", exc_info=True)
            return None

        finally:
            pass
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()

    async def terminate_other_sessions(self, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return
                
            authCall = await self.client(GetAuthorizationsRequest())
            activeSessions = authCall.authorizations
            for item in activeSessions:
                auth_item:Authorization = item

            sessionCount  = len(activeSessions)

            if sessionCount <= 1:
                print_green(f"{self.phone_number} »» Clear. No other sessions found.")
                return True
        
            reset_auth_call = await self.client(functions.auth.ResetAuthorizationsRequest())
            if reset_auth_call:
                print_blue(f"[{self.phone_number}] - {sessionCount - 1} other sessions serminated.")
                return True
        except errorList.FreshResetAuthorisationForbiddenError:
                print_red(f"[{self.phone_number}] - {sessionCount - 1} sessions semaining. This session is fresh, it needs to wait 24 hours.")
                return False
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'terminate_other_sessions':\n{error}", exc_info=False)
            return False
        finally:
            pass
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()
    

    async def change_two_fa(self, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return
            
            current_twofa = await self.FileHandler.get_session_twofa(self.phone_number)
            new_twofa = get_random_2fa()
            result = await self.client.edit_2fa(current_twofa, new_password=new_twofa)
            if result:
                await self.FileHandler.update_2fa_json(new_twofa, self.phone_number)
                print_green(f"[{self.phone_number}] - 2FA Updated")
                return result
            else:
                client_logger.warning(f"[{self.phone_number}] - Couldn't update 2FA")
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'change_photo':\n{error}", exc_info=True)
        finally:
            pass
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()

    async def reset_two_fa(self, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return
            
            result = await self.client(ResetPasswordRequest())
            print_green(f"[{self.phone_number}] - {result}")

        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'change_photo':\n{error}", exc_info=True)
        finally:
            pass
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()

    async def set_privacy_invite(self, allow:bool, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return
            
            if allow: new_rule = [InputPrivacyValueAllowAll()]
            else: new_rule = [InputPrivacyValueDisallowAll()]
            await self.client(SetPrivacyRequest(key = InputPrivacyKeyChatInvite(), rules = new_rule))
            print_green(f"[{self.phone_number}] - Invite disallowed")
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'change_photo':\n{error}", exc_info=True)
        finally:
            pass
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()

    async def set_privacy_last_seen(self, allow:bool, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return
            
            if allow: new_rule = [InputPrivacyValueAllowAll()]
            else: new_rule = [InputPrivacyValueDisallowAll()]
            await self.client(SetPrivacyRequest(key = InputPrivacyKeyStatusTimestamp(), rules = new_rule))
            print_green(f"[{self.phone_number}] - Last seen disallowed")
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'change_photo':\n{error}", exc_info=True)
        finally:
            pass
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()

    async def change_profile_info(self, change_basic:bool, change_username:bool, change_picture:bool, already_connected=False):
        try:
            if already_connected == False:
                if not await self.ConnectionHandler.connect_to_session():
                    return
            
            original_info = await self.DatabaseHandler.get_session_info(self.phone_number)
            if not original_info:
                return {"number" : self.phone_number}
            
            first_name = await self.FileHandler.create_first_name()
            last_name  = await self.FileHandler.create_last_name()
            about        = await self.FileHandler.create_about()
            username       = await self.FileHandler.create_username()
            new_picture = await self.FileHandler.create_profile_picture()


            info_changed = False
            username_changed = False
            pfp_changed = False

            if change_basic:
                try:
                    await self.client(UpdateProfileRequest(
                        first_name = first_name,
                        last_name  = last_name,
                        about      = about,
                    ))
                    info_changed = True
                except errorList.AboutTooLongError:
                    await self.client(UpdateProfileRequest(
                        first_name = first_name,
                        last_name  = last_name,
                        about      = await self.FileHandler.create_about(),
                    ))
                    info_changed = True


            await asyncio.sleep(4)
            
            if change_username:
                try: 
                    await self.client(UpdateUsernameRequest(username))
                    username_changed = True
                except errorList.UsernameOccupiedError:
                    username  = await self.FileHandler.create_username()
                    await self.client(UpdateUsernameRequest(username))
                    username_changed = True
                except errorList.UsernameInvalidError:
                    username  = await self.FileHandler.create_username()
                    await self.client(UpdateUsernameRequest(username))
                    username_changed = True
                except Exception as error:
                    client_logger.error(f"[{self.phone_number}]- Error on 'change_username':\n{error}", exc_info=True)
        
            await asyncio.sleep(4)

            if info_changed:
                original_info.first_name = first_name
                original_info.last_name = last_name
                original_info.bio = about

            if username_changed:
                original_info.username = username

            if not change_picture:
                print_green(f"[{self.phone_number}] - info changed: {info_changed} - username_changed: {username_changed} - pfp changed: {pfp_changed}")
                return original_info

        
            uploaded_photos = await self.client.get_profile_photos('me')

            for photo in uploaded_photos:
                await self.client(DeletePhotosRequest(
                    id = [InputPhoto(
                        id             = photo.id,
                        access_hash    = photo.access_hash,
                        file_reference = photo.file_reference
                    )]
                ))
            photo_up = False
            while not photo_up:
                await asyncio.sleep(2)
                try:
                    if new_picture != None:
                        file_upload = await self.client.upload_file(new_picture)
                        photo_result = await self.client(UploadProfilePhotoRequest(file=file_upload))
                        photo_up = True
                        pfp_changed = True
                        original_info.profile_photo = new_picture
                        print_green(f"[{self.phone_number}] - info changed: {info_changed} - username_changed: {username_changed} - pfp changed: {pfp_changed}")
                        return original_info
                    else:
                        break
                except errorList.ImageProcessFailedError as error:
                    client_logger.error(f"[{self.phone_number}] - ImageProcessFailedError on 'change_photo':\n{error}", exc_info=True)
                    remove(photo)
                    continue
                except Exception as error:
                    client_logger.error(f"[{self.phone_number}] - Error on 'change_photo':\n{error}", exc_info=True)


            return f"[{self.phone_number}] - info changed: {info_changed} - username_changed: {username_changed} - pfp changed: {pfp_changed}"
        except errorList.FloodWaitError:
            return f"[{self.phone_number}] - FloodWaitError"
        except errorList.UserDeactivatedBanError:
            return f"[{self.phone_number}] - BANNED"
        except Exception as error:
            client_logger.error(f"[{self.phone_number}] - Error on 'change_photo':\n{error}", exc_info=True)
            return ""
        
        finally:
            pass
            if already_connected == False:
                await self.ConnectionHandler.disconnect_from_session()
