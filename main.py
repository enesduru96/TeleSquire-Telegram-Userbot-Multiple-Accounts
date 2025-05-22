import json, asyncio, os, random, time, traceback

from resources._config import Config
from resources._utils import print_blue, print_magenta, print_green, print_red, print_yellow
from resources.account_generator_functions.acc_generator import AccGenerator, device_configs
from resources.client_functions.telethon_client_handler import MyClient
from resources.client_functions.seller_client_handler import SellerClientHandler

from resources.database_functions.base_data_classes import ClientInformation, ChannelInformation, TelegramUserInformation
from resources.database_functions.base_db_models import SessionDuo, IndexedSession, DialogueFiles
from resources.database_functions.database_handler import DatabaseHandler
from resources.random_device_handler import RandomDeviceHandler
from resources.file_handler import FileHandler
from resources.proxy_handler import ProxyHandler

from resources.__dependencies import GLOBAL_DEPENDENCIES

class MainMenu:
    def __init__(self):
        self.config = Config()
        self.database_url = self.config.get_database_url()
        self.DatabaseHandler = None
        self.DeviceHandler = None
        self.FileHandler = None
        self.ProxyHandler = None

    async def start(self):
        await GLOBAL_DEPENDENCIES.initialize()
        self.DatabaseHandler:DatabaseHandler = GLOBAL_DEPENDENCIES.database_handler
        self.DeviceHandler:RandomDeviceHandler = GLOBAL_DEPENDENCIES.device_handler
        self.FileHandler:FileHandler = GLOBAL_DEPENDENCIES.file_handler
        self.ProxyHandler:ProxyHandler = GLOBAL_DEPENDENCIES.proxy_handler

        await self.DatabaseHandler.create_dialogue_database()
        await self.DeviceHandler.update_random_device_list()
        await self.DeviceHandler.add_new_devices()
        await self.main_menu()



    async def create_session_duos(self):
        dialogue_files = await self.DatabaseHandler.get_least_used_dialogues()

        session_datas = []
        numbers = self.FileHandler.get_session_list()
        for number in numbers:
            session_data:IndexedSession = await self.DatabaseHandler.get_session_info(number)
            if session_data.is_banned == False:
                session_datas.append(session_data)

        random.shuffle(session_datas)


        for i in range(0, len(session_datas) - 1, 2):
            session_1 = session_datas[i]
            session_2 = session_datas[i + 1]

            random_dialogue:DialogueFiles = random.choice(dialogue_files)
            dialogue_files.remove(random_dialogue)
            await self.DatabaseHandler.increment_dialogue_use(random_dialogue.file_name)
            
            duo_entry = SessionDuo(
                session_a_id = session_1.entity_id,
                session_a_phone = session_1.number,
                session_b_id = session_2.entity_id,
                session_b_phone = session_2.number,
                dialogue_filename = random_dialogue.file_name
            )
            await self.DatabaseHandler.update_session_duo(duo_entry)

    async def create_dialogue_tasks(self):
        pass
        # TODO:
        # First make duos both index and add to contacts each other
        # Get my duo: get my id -> check duos list for both a and b, see where I am at, if I'm b, duo is a. If I'm a, duo is b. get their id.
        # Then with the id, get the indexed telegram user by id, so that you can create the InputPeerUser and send the message without resolving username
        # Save the message task as completed
        # Go on


#region MENUS

    async def main_menu(self):
        while True:
            print("\nMain Menu:\n")
            print("[1] - Account Management")
            print("[2] - Proxy and Connection Settings")
            print("[3] - Channel and Group Management")
            print("[4] - User and Bot Interaction")
            print("[5] - JSON and Config Management")
            print("[6] - Warm Up Menu")
            print("[0] - Exit")
            
            choice = input("  » ").strip()
            if choice == "1":
                await self.account_management_menu()
            elif choice == "2":
                await self.proxy_connection_menu()
            elif choice == "3":
                await self.channel_group_management_menu()
            elif choice == "4":
                await self.user_bot_interaction_menu()
            elif choice == "5":
                await self.json_config_menu()
            elif choice == "6":
                await self.warmup_menu()
            elif choice == "0":
                print("Exiting...")
                break
            else:
                print("Invalid input, please try again.")

    async def account_management_menu(self):
        while True:
            os.system('CLS')

            print("\nAccount Management:\n")
            print_yellow("[1] - Generate Accounts")
            print_green("\n[2] - Check Ban (My Accounts)")
            print_green("[3] - Check Ban (Seller Accounts)")
            print_magenta("\n[4] - Complain to Spambot")
            print("\n[5] - Login and Save Account")
            print("[6] - Get Login Code")
            print("[7] - Convert Seller Sessions")
            print("[8] - Save Session Info to DB")
            print_yellow("\n[9] - Bulk Change Profile Info")
            print("\n\n[b] - Back")

            choice = input("  » ").strip()
            if choice == "1":
                await self.generate_accounts()
            elif choice == "2":
                await self.check_ban_my_accounts()
            elif choice == "3":
                await self.check_ban_seller_accounts()
            elif choice == "4":
                await self.spambot_complain()
            elif choice == "5":
                await self.login_and_save_account()
            elif choice == "6":
                await self.get_telegram_login_code()
            elif choice == "7":
                await self.convert_seller_sessions()
            elif choice == "8":
                await self.save_clients_info_to_db()
            elif choice == "9":
                await self.bulk_change_profile_info()
            elif choice == "b":
                break
            else:
                print("Invalid input, please try again.")

    async def proxy_connection_menu(self):
        while True:
            os.system('CLS')

            print("\nProxy and Connection Settings:\n")
            print_blue("[1] - Change Proxies (My Accounts)")
            print_blue("[2] - Change Proxies (Seller Accounts)")
            print_red("\n[3] - Terminate Other Sessions")
            print_green("\n[4] - Change Two-Factor Authentication")
            print_red("\n[7] - Reset Two-Factor Authentication")
            print("\n\n[b] - Back")

            choice = input("  » ").strip()
            if choice == "1":
                await self.change_proxies()
            elif choice == "2":
                await self.change_proxies_seller()
            elif choice == "3":
                await self.terminate_other_sessions()
            elif choice == "4":
                await self.change_twofa()
            elif choice == "7":
                await self.reset_twofa()
            elif choice == "b":
                break
            else:
                print("Invalid input, please try again.")

    async def channel_group_management_menu(self):
        while True:
            os.system('CLS')

            print("\nChannel and Group Management:\n")
            print("[1] - Bulk Join Channel")
            print("[2] - Send View and Reaction")
            print("[3] - Print Channel Info")
            print("[4] - Print Private Channel Info")
            print("\n\n[b] - Back")

            choice = input("  » ").strip()
            if choice == "1":
                await self.bulk_join_channel()
            elif choice == "2":
                await self.send_view_and_reaction()
            elif choice == "3":
                await self.print_channel_info()
            elif choice == "4":
                await self.print_private_channel_info()
            elif choice == "b":
                break
            else:
                print("Invalid input, please try again.")

    async def user_bot_interaction_menu(self):
        while True:
            os.system('CLS')

            print("\nUser and Bot Interaction:\n")
            print("[1] - Start Bot Request")
            print("\n\n[b] - Back")

            choice = input("  » ").strip()
            if choice == "1":
                await self.start_bot_request()
            elif choice == "b":
                break
            else:
                print("Invalid input, please try again.")

    async def json_config_menu(self):
        while True:
            os.system('CLS')

            print("\nJSON and Config Management:\n")
            print("[1] - Fix 'lang_code'")
            print("[2] - Change App Version")
            print("\n\n[b] - Back")

            choice = input("  » ").strip()
            if choice == "1":
                await self.fix_lang_code()
            elif choice == "2":
                await self.change_app_versions()
            elif choice == "b":
                break
            else:
                print("Invalid input, please try again.")

    async def warmup_menu(self):
        while True:
            os.system('CLS')

            print("\nOther Tools:\n")
            print_yellow("[1] - Create Session Duos (random)")
            print_blue("[2] - Create Dialogue Tasks")
            print("\n\n[b] - Back")

            choice = input("  » ").strip()
            if choice == "1":
                await self.create_session_duos()
            if choice == "2":
                await self.create_dialogue_tasks()
            elif choice == "b":
                break
            else:
                print("Invalid input, please try again.")

                    
#endregion


#region MENU 1

    async def generate_accounts(self):
        amount = int(input("How many accounts: "))
        device_index = int(input("Device index: "))
        config = device_configs[device_index]
        acc_generator = AccGenerator(config)

        try:
            for i in range(amount):
                generator_process = await acc_generator.run()
                number = generator_process["number"]
                new_client = await MyClient.create(number)
                new_client_client = await new_client.send_login_request()
                await asyncio.sleep(10)
                login_code = await acc_generator.get_login_code_from_content()
                await new_client.sign_in_with_code(login_code, None, new_client_client, int(time.time()))
                await new_client.change_two_fa()
                await asyncio.sleep(3)
                await new_client.set_privacy_last_seen(False)
                await asyncio.sleep(3)
                await new_client.set_privacy_invite(False)
                await asyncio.sleep(3)
                result = await new_client.change_profile_info(change_basic=True, change_username=True, change_pfp=True)
                if isinstance(result, ClientInformation):
                    await self.DatabaseHandler.save_session_info(result)
                await acc_generator.DeviceManager.process_single_device()

        except Exception as error:
            print(f"Error AccountGen: {error} \n\n Traceback: \n {traceback.format_exc()}")
        
        input("  » ")

    async def check_all_sessions(self, seller_sessions:bool):
        my_phone_numbers = self.FileHandler.get_seller_session_list() if seller_sessions else self.FileHandler.get_session_list()
        if not my_phone_numbers:
            input("""WARNING! No session files found in the sessions folder.
                     Add session files and try again.""")
            return

        print(f"\nChecking Your Accounts for Ban...")

        tasks = [
            asyncio.create_task(
                SellerClientHandler(phone).ban_check() if seller_sessions else (await MyClient.create(phone)).ban_check()
            )
            for phone in my_phone_numbers
        ]

        ban_count = 0
        online_count = 0
        error_count = 0
        spam_count = 0

        for completed_task in asyncio.as_completed(tasks):
            res = await completed_task
            if res.status == "BANNED":
                ban_count += 1
                print_red(f"BANNED » {res.phone_number}")
            elif res.status == "ONLINE":
                online_count += 1
                print_green(f"[{res.phone_number}] - ACTIVE - USERNAME: {res.username}")
            elif res.status == "SPAM":
                spam_count += 1
            elif res.status == "ERROR":
                error_count += 1

        print(f"\nOnline: {online_count}   Banned: {ban_count}   Error: {error_count}   Spam: {spam_count}")
        input("  » ")

    async def check_ban_my_accounts(self):
        print("Checking Ban (my accounts)...")
        await self.check_all_sessions(seller_sessions=False)

    async def check_ban_seller_accounts(self):
        print("Checking Ban (seller accounts)...")
        await self.check_all_sessions(seller_sessions=True)
    
    async def spambot_complain(self):
        session_list = self.FileHandler.get_session_list()

        tasks = [
            asyncio.create_task((await MyClient.create(phone)).spambot_complain())
            for phone in session_list
        ]

        clear_count = 0
        sent_count = 0
        waiting_count = 0
        error_count = 0
        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task

            if result == "clear":
                clear_count += 1
            elif result == "sent":
                sent_count += 1
            elif result == "waiting":
                waiting_count += 1
            elif result == "error":
                error_count += 1
        

        print_green(f"Clear: {clear_count}")
        print_yellow(f"Sent: {sent_count}")
        print_blue(f"Waiting: {waiting_count}")
        print_red(f"Error: {error_count}")

        input("  » ")

    async def login_and_save_account(self):
        print("Logging in and saving account...")
        count = int(input("    How Many Accounts Will You Login To?: "))
        for _ in range(count):
            admin_phone = str(input("\n\n    Phone Number(+xxx): "))
            client_handler = await MyClient.create(admin_phone)
            await client_handler.login_create_session_manual()
        input("    Press ENTER for Main Menu.")
        input("  » ")

    async def get_telegram_login_code(self):
        sessions = self.FileHandler.get_session_list()
        number   = 0
        session_ids = []
        for session in sessions:
            print_green(f'{number} - {session}')
            session_ids.append(session)
            number += 1

        session_index    = input(f"\nPlease Login Telegram, Request Code and Choose Number:")
        selected_session = session_ids[int(session_index)]

        try:
            client = await MyClient.create(selected_session)
            code = await client.get_login_code()
        except Exception as err:
            print(err)
        
        if code == "BANNED":
            print(f"\n{selected_session} is BANNED")

        if len(code) != 5:
            print(f"\n  The Returned Code Was not 5 characters long. Please Make Sure You Requested Login Code and Try Again.")
            return

        print_blue(f"\n --Login Code For {selected_session}--")
        print_green(f"\n    {code}")

        input("  » ")

    async def convert_seller_sessions(self):
        print("Converting seller sessions...")
        session_list = self.FileHandler.get_seller_session_list()
        tasks = [self.handle_convert_session(phone) for phone in session_list]
        for task in asyncio.as_completed(tasks):
            await task
        input("  » ")

    async def handle_convert_session(self, phone):
        new_client = await MyClient.create(phone)
        seller_client = SellerClientHandler(phone)
        seller_twoFA = await seller_client.get_seller_twoFa()
        seller_register_time = await seller_client.get_seller_register_time()
        new_client_client = await new_client.send_login_request()
        await asyncio.sleep(5)
        login_code = await seller_client.get_login_code()
        if login_code != "banned":
            await new_client.sign_in_with_code(login_code, seller_twoFA, new_client_client, seller_register_time)
            await asyncio.sleep(5)
            await new_client.change_two_fa()
            await asyncio.sleep(3)
            await new_client.set_privacy_last_seen(False)
            await asyncio.sleep(3)
            await new_client.set_privacy_invite(False)

    async def save_clients_info_to_db(self):
        print("Getting client information...")
        session_list = self.FileHandler.get_session_list()
        tasks = []

        for phone in session_list:
            if await self.DatabaseHandler.is_session_in_db(phone):
                print(f"Session {phone} already exists in the database. Skipping.")
                continue

            client_task = asyncio.create_task((await MyClient.create(phone)).get_client_info())
            tasks.append(client_task)

        for completed_task in asyncio.as_completed(tasks):
            client_info = await completed_task
            if client_info:
                await self.DatabaseHandler.save_session_info(client_info)
        
        input("  » ")

#endregion


#region MENU 2

    async def bulk_change_profile_info(self):
        def get_user_choice(prompt: str) -> bool:
            return input(prompt) == "y"

        change_basic = get_user_choice("Input 'y' to change basic information: ")
        change_username = get_user_choice("Input 'y' to change usernames: ")
        change_photo = get_user_choice("Input 'y' to change profile pictures: ")

        session_list = self.FileHandler.get_session_list()

        tasks = [
            asyncio.create_task((await MyClient.create(phone)).change_profile_info(change_basic, change_username, change_photo))
            for phone in session_list
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        dict_tasks = []
        for result in results:
            if isinstance(result, ClientInformation):
                dict_tasks.append(
                    asyncio.create_task(self.DatabaseHandler.save_session_info(result))
                )
            elif isinstance(result, dict):
                number = result["number"]
                dict_tasks.append(
                    asyncio.create_task(self.change_profile_dict_result(number, change_basic, change_username, change_photo))
                )
            elif isinstance(result, Exception):
                print(f"Task error: {result}")

        await asyncio.gather(*dict_tasks)

        input("  » ")

    async def change_profile_dict_result(self, number, change_basic, change_username, change_photo):
        client = await MyClient.create(number)
        client_info = await client.get_client_info()
        if client_info:
            save_result = await self.DatabaseHandler.save_session_info(client_info)
            if save_result:
                return await client.change_profile_info(change_basic, change_username, change_photo)
       
    async def terminate_other_sessions(self):
        print("Terminating other sessions...")
        session_list = self.FileHandler.get_session_list()
        tasks = [
            asyncio.create_task((await MyClient.create(phone)).terminate_other_sessions())
            for phone in session_list
        ]
        for completed_task in asyncio.as_completed(tasks):
            await completed_task

        input("  » ")

    async def change_proxies(self):
        session_list = self.FileHandler.get_session_list()
        for phone_number in session_list:
            new_proxy = await self.ProxyHandler.get_next_proxy(phone_number)
            if await self.FileHandler.update_json_field("proxy", new_proxy, phone_number):
                print_green(f"[{phone_number}] > {new_proxy.split(':')[2]}")

        input("  » ")        

    async def change_proxies_seller(self):
        session_list = self.FileHandler.get_seller_session_list()
        for phone_number in session_list:
            new_proxy = await self.ProxyHandler.get_next_proxy(phone_number)
            if await self.FileHandler.update_json_field_seller("proxy", new_proxy, phone_number):
                print_green(f"[{phone_number}] > {new_proxy.split(':')[2]}")

        input("  » ")      

    async def change_twofa(self):
        session_list = self.FileHandler.get_session_list()

        tasks = [
            asyncio.create_task((await MyClient.create(phone)).change_two_fa())
            for phone in session_list
        ]

        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task

        input("  » ")

    async def reset_twofa(self):
        session_list = self.FileHandler.get_session_list()

        tasks = [
            asyncio.create_task((await MyClient.create(phone)).reset_two_fa())
            for phone in session_list
        ]

        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task

        input("  » ")

#endregion


#region MENU 3

    async def bulk_join_channel(self):
        target_channel = input("Target Channel: ")
        session_list = self.FileHandler.get_session_list()
        channel_cached = False
        if "/+" in target_channel:
            tasks = [
                asyncio.create_task((await MyClient.create(phone)).join_and_cache_private_channel(target_channel))
                for phone in session_list
            ]
        else:
            tasks = [
                asyncio.create_task((await MyClient.create(phone)).join_and_cache_public_channel(target_channel))
                for phone in session_list
            ]
        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            if isinstance(result, ChannelInformation):
                if channel_cached == False:
                    await self.DatabaseHandler.cache_new_channel(result)
                    channel_cached = True
                    

        input("  » ")

    async def send_view_and_reaction(self):
        target_channel = "https://t.me/PNUTBoy"
        session_list = self.FileHandler.get_session_list()

        for phone in session_list:
            my_client = await MyClient.create(phone)
            result = await my_client.send_view_and_reaction(target_channel)
            if result:
                print(f"Success for session: {phone}")
            else:
                print(f"Failed for session: {phone}")
            
            delay = random.uniform(2, 30)
            await asyncio.sleep(delay)

        input("  » ")

    async def print_channel_info(self):
        channel_username = input("Channel Username: ")
        session_list = self.FileHandler.get_session_list()
        task = asyncio.create_task((await MyClient.create(session_list[0])).print_channel_info(channel_username))
        result = await task
        input("->>")
    
    async def print_private_channel_info(self):
        channnel_link = "https://t.me/+lt04KT5uedxmOGEx"
        session_list = self.FileHandler.get_session_list()
        task = asyncio.create_task((await MyClient.create(session_list[1])).join_and_cache_private_channel(channnel_link))
        result = await task
        input("->>")

#endregion


#region MENU 4

    async def start_bot_request(self):
        target_bot = input("Target Bot: ")
        session_list = self.FileHandler.get_session_list()
        bot_cached = False
        tasks = [
            asyncio.create_task((await MyClient.create(phone)).start_bot_request(target_bot))
            for phone in session_list
        ]

        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            if isinstance(result, TelegramUserInformation):
                if bot_cached == False:
                    await self.DatabaseHandler.cache_new_user(result)
                    bot_cached = True
                    

        input("  » ")

#endregion


#region MENU 5

    async def fix_lang_code(self):
        lang_code = "en"
        system_lang = "en-us"
        phone_numbers = self.FileHandler.get_session_list()
        for phone in phone_numbers:
            file_path = f"sessions/active/{phone}.json"
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "lang_code" not in data:
                    data["lang_code"] = lang_code
                if ("system_lang" not in data) and ("system_lang_code" not in data):
                    data["system_lang"] = system_lang
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                print(f"{file_path} updated.")
            
            except FileNotFoundError:
                print(f"Error: {file_path} not found.")
            except json.JSONDecodeError:
                print(f"Error: {file_path} JSON format error.")

        input("  » ")

    async def change_app_versions(self):
        new_version = input("Input new version: ")
        phone_numbers = self.FileHandler.get_session_list()
        for phone in phone_numbers:
            file_path = f"sessions/active/{phone}.json"
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["app_version"] = new_version
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                print(f"{file_path} güncellendi.")
            
            except FileNotFoundError:
                print(f"Hata: {file_path} bulunamadı.")
            except json.JSONDecodeError:
                print(f"Hata: {file_path} JSON formatı hatalı.")

        input("  » ")

#endregion






if __name__ == "__main__":
    menu = MainMenu()
    asyncio.run(menu.start())