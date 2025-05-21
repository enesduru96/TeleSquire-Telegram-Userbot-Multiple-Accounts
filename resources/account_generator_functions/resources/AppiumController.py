from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy as By
from appium.options.common import AppiumOptions
from xml.dom.minidom import parseString
import subprocess
import time
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class AppiumController:
    def __init__(self, package_name, package_activity, device_serial, system_port):
        self.package_name = package_name
        self.package_activity = package_activity
        self.device_serial = device_serial
        self.system_port = system_port
        self.driver = None

    def start_driver(self):
        options = AppiumOptions()
        options.platform_name = "Android"
        options.device_name = self.device_serial
        options.automation_name = "UiAutomator2"
        options.app_package = self.package_name
        options.app_activity = self.package_activity
        options.no_reset = True
        options.new_command_timeout = 300
        options.uiautomator2_server_launch_timeout = 60000
        options.system_port = self.system_port

        self.driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
        print(f"Driver started for {self.device_serial} on systemPort {self.system_port}")

    def stop_app(self):
        subprocess.run(["adb", "-s", self.device_serial, "shell", "am", "force-stop", self.package_name], check=True)
        print(f"{self.package_name} app stopped.")

    def start_app(self):
        subprocess.run(["adb", "-s", self.device_serial, "shell", "am", "start", "-n", f"{self.package_name}/{self.package_activity}"], check=True)
        print(f"{self.package_name} app started.")


    def install_app(self, apk_path):
        try:
            subprocess.run(["adb", "-s", self.device_serial, "install", apk_path], check=True)
            print(f"{apk_path} installed.")
        except subprocess.CalledProcessError as e:
            print(f"Couldn't install app: {e}")

    def uninstall_app(self, package_name=None):
        if package_name is None:
            package_name = self.package_name

        try:
            subprocess.run(["adb", "-s", self.device_serial, "uninstall", package_name], check=True)
            print(f"{package_name} uninstalled.")
        except subprocess.CalledProcessError as e:
            print(f"Couldn't uninstall app: {e}")
    
    def reinstall_app(self, apk_path):
        self.uninstall_app()
        time.sleep(5)
        self.install_app(apk_path)
        time.sleep(6)

    def restart_app(self):
        self.stop_app()
        time.sleep(3)
        self.start_app()
        time.sleep(3)
        subprocess.run(["adb", "-s", self.device_serial, "uninstall", "io.appium.uiautomator2.server"], check=True)
        subprocess.run(["adb", "-s", self.device_serial, "uninstall", "io.appium.uiautomator2.server.test"], check=True)
        self.start_driver()


    def press_back_button(self):
        try:
            subprocess.run(["adb", "-s", self.device_serial, "shell", "input", "keyevent", "4"], check=True)
            print("Back button simualted.")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")


    def wait_for_activity(self, timeout=10):
        if self.driver:
            is_activity_open = self.driver.wait_activity(self.package_activity, timeout)
            print(f"Was activity on: {is_activity_open}")
            return is_activity_open
        else:
            print("Couldn't start driver.")
            return False

    def print_page_source(self):
        if self.driver:
            page_source = self.driver.page_source
            pretty_xml = parseString(page_source).toprettyxml(indent="    ")
            print(pretty_xml)

            with open("drony_page_source.xml", "w", encoding="utf-8") as f:
                f.write(pretty_xml)
        else:
            print("Driver didn't start and couldn't get page source.")


    def swipe_to_left(self):
        screen_size = self.driver.get_window_size()
        width = screen_size['width']
        height = screen_size['height']
        
        start_x = width * 0.9 
        end_x = width * 0.1
        y = height * 0.5

        self.driver.swipe(start_x, y, end_x, y, 800)
        time.sleep(2)




    def swipe_to_right(self):
        screen_size = self.driver.get_window_size()
        width = screen_size['width']
        height = screen_size['height']
        
        start_x = width * 0.1
        end_x = width * 0.9
        y = height * 0.5

        self.driver.swipe(start_x, y, end_x, y, 800)
        time.sleep(2)


    def email_not_allowed(self):
        try:
            allowed_text = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, f"//*[@text='An error occurred.\nEMAIL_NOT_ALLOWED']"))
            )
            return True
        except Exception as e:
            print("Email is allowed")
            return False

    def email_not_allowed_2(self):
        try:
            source = self.driver.page_source
            if "An error occurred.\nEMAIL_NOT_ALLOWED" in source:
                return True
            else:
                return False
        except Exception as e:
            return False

    def is_asking_email(self):
        try:
            source = self.driver.page_source
            if "Choose a login email" in source:
                return True
            else:
                return False
        except Exception as e:
            return False

    def has_email_2(self):
        try:
            source = self.driver.page_source
            if "Check Your Email" in source:
                return True
            else:
                return False
        except Exception as e:
            return False

    def already_registered_2(self):
        try:
            source = self.driver.page_source
            if "Check your Telegram messages" in source:
                return True
            else:
                return False
        except Exception as e:
            return False
        

    def is_calling_to_verify_2(self):
        try:
            source = self.driver.page_source
            if "Phone Verification" in source:
                return True
            else:
                return False
        except Exception as e:
            return False


    def number_is_banned_2(self):
        try:
            source = self.driver.page_source
            if "This phone number is banned." in source:
                return True
            else:
                return False
        except Exception as e:
            return False


    def number_is_good(self):
        try:
            email_text = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, f"//*[@text='Enter code']"))
            )
            return True
        except Exception as e:
            return False


    def number_is_good_2(self):
        try:
            source = self.driver.page_source
            if "Enter code" in source:
                return True
            else:
                return False
        except Exception as e:
            return False


    def internal_error_reset(self):
        try:
            source = self.driver.page_source

            if "An internal error" in source:
                print("INTERNAL ERROR")
                return True
            else:
                return False
        except Exception as e:
            return False


    def click_with_content_desc(self, desc):
        try:
            navigate_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[@content-desc='{desc}']"))
            )
            navigate_button.click()
        except Exception as e:
            print("Error clicking with content description:", e)


    def click_text(self, text):
        try:
            wifi_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[@text='{text}']"))
            )
            wifi_element.click()
        except Exception as e:
            print("Error clicking text:", e)
            

    def click_edit_text(self):
        try:
            edit_text_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "android.widget.EditText"))
            )
            edit_text_element.click()
        except Exception as e:
            print("Error clicking EditText:", e)
        

    def enter_text(self, text):
        try:
            edit_text_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "android.widget.EditText"))
            )
            edit_text_element.clear()
            time.sleep(1)
            edit_text_element.clear()
            edit_text_element.send_keys(text)
            print(f"{text} typed.")

        except Exception as e:
            print("Error entering text:", e)


    def input_name_surname(self, name, surname):
        try:
            edit_text_elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "android.widget.EditText"))
            )
            for i, field in enumerate(edit_text_elements):
                if i == 0:
                    field.click()
                    field.send_keys(name)
                elif i == 1:
                    field.click()
                    field.send_keys(surname)

        except Exception as error:
            print("Error filling EditText fields:", error)


    def clear_text_field(self):
        try:
            edit_text_elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "android.widget.EditText"))
            )
            
            for edit_text_element in edit_text_elements:
                edit_text_element.clear()
                time.sleep(0.1)

                if edit_text_element == edit_text_elements[1]:
                    edit_text_element.send_keys(Keys.BACKSPACE)

            print("Cleared text fields")
        
        except Exception as e:
            print("Error clearing text fields:", e)



    def click_telegram_message(self, message_text=None):
        try:
            message_elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup"))
            )
            if not message_elements:
                print("Message not found.")
                return

            if message_text:
                for message_element in message_elements:
                    if message_text in message_element.text:
                        message_element.click()
                        print(f"Clicked on message: {message_text}")
                        return
                print(f"Couldn't find message: {message_text}")
            else:
                message_elements[0].click()
                print("Clicked first message.")
        except Exception as e:
            print(f"Error clicking message: {e}")


    def get_login_code(self):
        try:
            message_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(@text, 'Login code:')]")
                )
            )

            message_text = message_element.get_attribute("text")
            print(f"Found message text: {message_text}")

            match = re.search(r'\b\d{5}\b', message_text)
            if match:
                login_code = match.group(0)
                print(f"Found login code: {login_code}")
                return login_code
            else:
                print("Couldn't find 5 number login code")
                return None
        except Exception as e:
            print(f"Error getting login code: {e}")
            return None



    def get_login_code_from_content_desc(self):
        try:
            message_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@content-desc[contains(., 'Login code')]]")
                )
            )

            content_desc = message_element.get_attribute("content-desc")
            print(f"Content-desc found: {content_desc}")

            match = re.search(r'\b\d{5}\b', content_desc)
            if match:
                login_code = match.group(0)
                print(f"Login code: {login_code}")
                return login_code
            else:
                print("Login code not found.")
                return None
        except Exception as e:
            print(f"Error getting login code: {e}")
            return None


    def quit_driver(self):
        if self.driver:
            self.driver.quit()
            print("Appium connection terminated.")
        else:
            print("Driver is not running.")
