import time, asyncio
from resources.account_generator_functions.resources.AppiumController import AppiumController
from resources.account_generator_functions.resources.TextVerifiedAPI import TextVerifiedAPI, Get_Textverified_Number
from resources.account_generator_functions.resources.TSmsActivateAPI import SmsActivateAPI, Get_SmsActivate_Number, Fetch_SmsActivate_Code
from resources.account_generator_functions.resources.TSmsManAPI import SmsManAPI, Get_SMSMAN_Number, Fetch_SMSMAN_Code
from resources.account_generator_functions.resources.TempMail import TempMail
from resources.account_generator_functions.resources._Utils import get_random_name_surname

from resources.account_generator_functions.resources.device_manager import DeviceManager
from resources.file_handler import FileHandler
device_configs = [
    {"device_serial": "emulator-5554", "system_port": 8204, "index": 0},
    {"device_serial": "emulator-5556", "system_port": 8205, "index": 1},
    {"device_serial": "emulator-5568", "system_port": 8206, "index": 2}
]

class AccGenerator:
    def __init__(self, config):
        self.FileHandler = FileHandler("")
        # self.proxy_setter = ProxySetter()
        self.device_config = config
        self.apk_path = "resources/account_generator_functions/resources/Telegram.apk"
        self.package_name = "org.telegram.messenger.web"
        self.package_activity = "org.telegram.ui.LaunchActivity"
        self.device_serial = self.device_config['device_serial']
        self.system_port = self.device_config['system_port']
        self.device_index = self.device_config['index']
        self.DeviceManager = DeviceManager(self.device_index, self.device_serial)
        self.controller = None

        self.textverified_api_key = "textverified_api_key"
        self.textverified_email = "textverified_email_address"
        self.textverified = TextVerifiedAPI(self.textverified_api_key, self.textverified_email)


        self.smsActivate = SmsActivateAPI()
        self.smsActivate_phone_data = None


        self.smsMAN = SmsManAPI()
        self.smsMAN_phone_data = None


        self.new_number = None
        self.sms_link = None
        self.cancel_href = None
        self.report_href = None

        self.temp_mail = TempMail()
        self.temp_mail_new_address = None

        self.sms_provider = 1

    async def get_login_code_from_content(self):
        return self.controller.get_login_code_from_content_desc()
    

    async def test_check_internal_error(self):
        self.controller = AppiumController(self.package_name, self.package_activity, self.device_serial, self.system_port)
        self.controller.start_driver()
        self.controller.wait_for_activity()
        result = self.controller.internal_error_reset()

    async def test_print_page(self):
        self.controller = AppiumController(self.package_name, self.package_activity, self.device_serial, self.system_port)
        self.controller.start_driver()
        self.controller.wait_for_activity()
        self.controller.print_page_source()

    async def test_cleat_text(self):
        self.controller = AppiumController(self.package_name, self.package_activity, self.device_serial, self.system_port)
        self.controller.start_driver()
        self.controller.wait_for_activity()
        self.controller.clear_text_field()

    async def step_1_reinstall_app(self):
        try:
            await self.DeviceManager.change_proxy()
            await asyncio.sleep(2)

            self.controller = AppiumController(self.package_name, self.package_activity, self.device_serial, self.system_port)
            self.controller.start_driver()
            self.controller.reinstall_app(self.apk_path)
            self.controller.restart_app()
            self.controller.wait_for_activity()
            self.controller.click_text("Start Messaging")
            time.sleep(1)
            self.controller.click_text("Continue")
            time.sleep(1)
            self.controller.click_text("ALLOW")
            time.sleep(1)
            self.controller.click_edit_text()
            return True
        except Exception as error:
            print(f"Step_1_Error: {error}")
            return False
        

    async def step_2_get_number(self):
        try:
            if self.sms_provider == 0:
                phone_data = Get_SmsActivate_Number(self.smsActivate)
                self.smsActivate_phone_data = phone_data
                id = phone_data["id"]
                phone = phone_data["phone"]
                country = phone_data["country"]
                price = phone_data["price"]
                self.new_number = phone
                return True
            elif self.sms_provider == 1:
                number_request = Get_Textverified_Number(self.textverified)
                self.new_number = number_request['number']
                self.sms_link = number_request['sms_link']
                self.cancel_href = number_request['cancel_link']
                self.report_href = number_request['report_link']
                return True
            elif self.sms_provider == 2:
                phone_data = Get_SMSMAN_Number(self.smsMAN)
                self.smsMAN_phone_data = phone_data
                self.new_number = phone_data["number"]
                return True
        except Exception as error:
            print(f"Step_2_Error: {error}")
            return False
        
    
    async def step_3_enter_number_and_check_ban(self):
        try:
            if self.sms_provider == 0:
                self.controller.enter_text(f"{self.new_number}")
            elif self.sms_provider == 1:
                self.controller.enter_text(f"1{self.new_number}")
            elif self.sms_provider == 2:
                self.controller.enter_text(f"{self.new_number}")

            time.sleep(1)
            self.controller.click_with_content_desc("Done")
            time.sleep(1)
            try:
                self.controller.click_text("Yes")
                time.sleep(1)

                self.controller.click_text("Continue")
                time.sleep(1)
                self.controller.click_text("ALLOW")

            except:
                pass

            return True
        except Exception as error:
            print(f"Step_3_Error: {error}")
            return False
    

    async def step_4_check_ban(self):
        try:
            await asyncio.sleep(5)
            if self.controller.number_is_banned_2():
                self.controller.click_text("OK")
                if self.sms_provider == 0:
                    time.sleep(120)
                    self.smsActivate.ban_order(self.smsActivate_phone_data["id"])
                elif self.sms_provider == 1:
                    self.textverified.cancel_verification(self.cancel_href)
                elif self.sms_provider == 2:
                    self.smsMAN.ban_order(self.smsMAN_phone_data["request_id"])
                print("BANNED NUMBER")
                return False
            else:
                return True
        except Exception as error:
            print(f"Step_4_Error: {error}")
            return False
        

    async def step_5_check_has_email(self):
        try:
            if self.controller.has_email_2():
                print("ALREADY REGISTERED")
                if self.sms_provider == 0:
                    time.sleep(120)
                    self.smsActivate.cancel_order(self.smsActivate_phone_data["id"])
                elif self.sms_provider == 1:
                    self.textverified.cancel_verification(self.cancel_href)
                elif self.sms_provider == 2:
                    self.smsMAN.cancel_order(self.smsMAN_phone_data["request_id"])
                return False
            else:
                return True
        except Exception as error:
            print(f"Step_5_Error: {error}")
            return False
    
    async def step_5_1_check_already_registered(self):
        try:
            if self.controller.already_registered_2():
                print("ALREADY REGISTERED")
                if self.sms_provider == 0:
                    time.sleep(120)
                    self.smsActivate.cancel_order(self.smsActivate_phone_data["id"])
                elif self.sms_provider == 1:
                    self.textverified.cancel_verification(self.cancel_href)
                elif self.sms_provider == 2:
                    self.smsMAN.cancel_order(self.smsMAN_phone_data["request_id"])
                return False
            else:
                return True
        except Exception as error:
            print(f"Step_5_1_Error: {error}")
            return False
    
    async def step_5_2_check_if_calling(self):
        try:
            if self.controller.is_calling_to_verify_2():
                print("CALLING, WAIT 120...")
                if self.sms_provider == 0:
                    self.smsActivate.cancel_order(self.smsActivate_phone_data["id"])
                elif self.sms_provider == 1:
                    self.textverified.cancel_verification(self.report_href)
                elif self.sms_provider == 2:
                    self.smsMAN.cancel_order(self.smsMAN_phone_data["request_id"])
                return False
            else:
                return True
        except Exception as error:
            print(f"Step_5_2_Error: {error}")
            return False
        


    async def step_6_check_asking_email(self):
        try:
            if self.controller.is_asking_email():
                print("Asked Email, Cancel...")
                if self.sms_provider == 0:
                    time.sleep(120)
                    self.smsActivate.cancel_order(self.smsActivate_phone_data["id"])
                elif self.sms_provider == 1:
                    self.textverified.cancel_verification(self.cancel_href)
                elif self.sms_provider == 2:
                    self.smsMAN.cancel_order(self.smsMAN_phone_data["request_id"])
                return False
            else:
                return True
        except Exception as error:
            print(f"Step_6_Error: {error}")
            return False

    async def step_6_1_check_internal_error(self):
        try:
            if self.controller.internal_error_reset():
                print("Internal error, change proxy and device info...")
                await self.DeviceManager.process_single_device()
                return False
            else:
                return True
        except Exception as error:
            print(f"Step_6_Error: {error}")
            return False

    async def step_6_1_enter_email_and_monitor(self):
        try:
            time.sleep(1)
            self.controller.enter_text(self.temp_mail_new_address)
            time.sleep(1)
            self.controller.click_with_content_desc("Done")
            email_code_result = self.temp_mail.monitor_inbox_return_code()
            if email_code_result is not None:
                self.controller.enter_text(email_code_result)
            if self.controller.email_not_allowed():
                return self.go_back_get_new_mail()
            else:
                print("Email is good.")
                self.temp_mail.save_email(self.temp_mail_new_address, self.new_number)
                return True
        except Exception as error:
            print(f"Step_6_1_Error: {error}")
            return False


    async def go_back_get_new_mail(self):
        try:
            self.controller.click_text("OK")
            time.sleep(1)
            self.controller.press_back_button()
            time.sleep(1)
            self.temp_mail = TempMail()
            self.temp_mail_new_address = self.temp_mail.get_email_address()
            print(f"Temp email address: {self.temp_mail_new_address}")
            return self.step_6_1_enter_email_and_monitor()
        except Exception as error:
            print(f"go_back_get_new_mail Error: {error}")
            return False


    async def step_7_sms_code(self):
        try:
            if not self.controller.number_is_good():
                if self.sms_provider == 0:
                    time.sleep(120)
                    self.smsActivate.cancel_order(self.smsActivate_phone_data["id"])
                elif self.sms_provider == 1:
                    self.textverified.cancel_verification(self.cancel_href)
                elif self.sms_provider == 2:
                    self.smsMAN.cancel_order(self.smsMAN_phone_data["request_id"])
                return False
            sms_code = "123"
            code_received = False
            while not code_received:
                if self.sms_provider == 0:
                    sms_code = Fetch_SmsActivate_Code(self.smsActivate_phone_data["id"], self.new_number, self.smsActivate)
                    print(f"SMS CODE: {sms_code}")
                    if isinstance(sms_code, str) and len(sms_code) == 5:
                        code_received = True
                    else:
                        self.smsActivate.cancel_order(self.smsActivate_phone_data["id"])
                        return False
                elif self.sms_provider == 1:
                    sms_result = self.textverified.check_code(self.sms_link)
                    sms_code = sms_result['data'][0]['parsedCode']
                    print(f"SMS CODE: {sms_code}")
                    if isinstance(sms_code, str) and len(sms_code) == 5:
                        code_received = True

                elif self.sms_provider == 2:
                    sms_code = Fetch_SMSMAN_Code(self.smsMAN_phone_data["request_id"], self.new_number, self.smsMAN)
                    print(f"SMS CODE: {sms_code}")
                    if isinstance(sms_code, str) and len(sms_code) == 5:
                        code_received = True
                    else:
                        self.smsMAN.cancel_order(self.smsMAN_phone_data["request_id"])
                        return False

            time.sleep(1)
            self.controller.enter_text(sms_code)

            return True
        except Exception as error:
            print(f"Step_7_Error: {error}")
            return False

    async def ready_telegram_user(self):
        try:
            name = await self.FileHandler.create_first_name()
            surname = await self.FileHandler.create_last_name()

            time.sleep(8)
            self.controller.input_name_surname(name, surname)

            time.sleep(1)
            self.controller.click_with_content_desc("Done")

            time.sleep(6)
            self.controller.click_text("Not now")

            time.sleep(1)
            self.controller.click_text("Deny")

            time.sleep(1)
            self.controller.click_text("Deny")

            #Send new session request to the number


            #Click on telegram and print source to get login code, then you are free to go with telethon.


        except:
            pass

    def _print(self):
        self.controller.print_page_source()

    async def run(self):
        state = 1
        while state:
            if state == 1:
                if await self.step_1_reinstall_app():
                    state = 2
                else:
                    print("Step 1 failed, retrying...")

            elif state == 2:
                if await self.step_2_get_number():
                    state = 3
                else:
                    print("Step 2 failed, retrying...")

            elif state == 3:
                result = await self.step_3_enter_number_and_check_ban()
                if isinstance(result, str):
                    print("Failed step 4. Will order new number.")
                else:
                    if result == True:
                        state = 31
                    else:
                        state = 1

            elif state == 31:
                result = await self.step_4_check_ban()
                if result == False:
                    state = 1
                else:
                    state = 5


            elif state == 5:
                print("State 5")
                if await self.step_5_check_has_email():
                    state = 51
                else:
                    print("Step 5 failed, will get new number.")
                    state = 1

            elif state == 51:
                print("State 51")
                if await self.step_5_1_check_already_registered():
                    state = 52
                else:
                    print("Step 5.1 failed, will get new number.")
                    state = 1

            elif state == 52:
                print("State 52")
                if await self.step_5_2_check_if_calling():
                    state = 6
                else:
                    print("Step 5.2 failed, will get new number.")
                    state = 1

            elif state == 6:
                print("State 6")
                if await self.step_6_check_asking_email():
                    state = 61
                else:
                    print("Step 6 failed. will get new number.")
                    state = 1

            elif state == 61:
                print("State 61")
                if await self.step_6_1_check_internal_error():
                    state = 7
                else:
                    state = 1

            elif state == 7:
                print("State 7")
                if await self.step_7_sms_code():
                    state = 8
                else:
                    state = 5

            elif state == 8:
                if await self.ready_telegram_user():
                    return {"number": self.new_number.replace("+","")}
                else:
                    print("Step 8 failed.")
                    input("->>>")
                    state = 1