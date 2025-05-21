from requests import get
from time import sleep

class SmsManAPI(object):
    def __init__(self):
        self.api_key = "smsman_api_key"
        self.ruble_limit = 30
        self.sms_delay = 120

        self.application_id = 3

        self.countries = [
            # {"name" : "libya", "code": 297},
            # {"name" : "zambia", "code": 15},
            # {"name" : "jamaica", "code": 230},
            # {"name" : "pakistan", "code": 16},
            # {"name" : "indonesia", "code": 7},
            {"name" : "usa", "code": 5}
        ]
                          

    def get_balance(self) -> dict:
        balance_req = get(f"https://api.sms-man.com/control/get-balance?token={self.api_key}").json()
        try:
            value = balance_req["balance"]
        except Exception:
            print(f"    {balance_req.text}")
        return float(value)


    def fetch_code(self, _id:int):
        try:
            result = get(f"https://api.sms-man.com/control/get-sms?token={self.api_key}&request_id={_id}").json()
            if "sms_code" in result:
                return result["sms_code"]
            elif "error_code" in result:
                if result["error_code"] == "wait_sms":
                    print("Waiting SMS...")
                    return None
                
        except Exception as error:
            print(error)
            return None


    def cancel_order(self, _id:int):
        return get(f"https://api.sms-man.com/control/set-status?token={self.api_key}&request_id={_id}&status=used")

    def ban_order(self, _id:int):
        return get(f"https://api.sms-man.com/control/set-status?token={self.api_key}&request_id={_id}&status=reject")


    def get_number(self, country_data):
        country_id = country_data["code"]
        try:
            order_req = get(f"https://api.sms-man.com/control/get-number?token={self.api_key}&country_id={country_id}&application_id={self.application_id}")
            data = order_req.json()
            if "number" in data:
                return {
                    "number": data["number"],
                    "request_id": data["request_id"]
                }
            else:
                print(f"Error getting number: {data}")
                return None
        except Exception as error:
            print(error)
            return None


    def buy_number(self):
        my_money = self.get_balance()
        if not my_money:
            input("OUT OF MONEY... PRESS ENTER.")
        if my_money < self.ruble_limit:
            input("OUT OF MONEY... PRESS ENTER.")

        i = 0
        while True:
            number = self.get_number(self.countries[i])
            print(f"NUMBER RESULT: {number}")

            if number:
                return number
            if not number:
                i = (i + 1) % len(self.countries)
                sleep(1)
                continue
            return number



def Fetch_SMSMAN_Code(number_id:int,phone_number, api:SmsManAPI):
    phone_sms_code = None

    time_out = 120
    while not phone_sms_code:
        sms_code = api.fetch_code(number_id)
        if sms_code:
            return sms_code

        sleep(3)
        time_out -= 3
        print(f"    {phone_number} > Waiting for SMS: {time_out} \r ", end="")
        if time_out <= 0:
            return None


def Get_SMSMAN_Number(api:SmsManAPI):
    number = None

    while not number:
        sleep(1)
        phone_number = api.buy_number()
        if phone_number:
            return phone_number