from requests import get, post
from time import sleep
from datetime import datetime
import traceback

class TextVerifiedAPI:
    def __init__(self, api_key, email):
        "text-verified.com API"
        self.api_key = api_key
        self.email = email
        self.BASE_URL  = f"https://www.textverified.com"
        self.bearer_token = ""
        self.token_expiry_date = ""
        self.sms_delay = 120


    def generate_beraer_token(self):
        post_headers = {"X-API-KEY" : self.api_key, "X-API-USERNAME": self.email}
        try:
            bearer_token_request = post(f"{self.BASE_URL}/api/pub/v2/auth", headers=post_headers)
            bearer_token_json = bearer_token_request.json()
            self.bearer_token = bearer_token_json['token']
            self.token_expiry_date = bearer_token_json['expiresAt']

        except Exception as error:
            print(traceback.format_exc())
            return {'bearer_token' : "Error"}


    def is_bearer_token_expired(self):
        if self.token_expiry_date == "":
            return True
        
        target_date = datetime.fromisoformat(self.token_expiry_date.split('.')[0])
        current_date = datetime.utcnow()

        return current_date > target_date


    def get_balance(self) -> dict:
        if self.is_bearer_token_expired():
            self.generate_beraer_token()

        headers = {"Authorization" : f"Bearer {self.bearer_token}"}
        try:
            balance_req = get(f"{self.BASE_URL}/api/pub/v2/account/me", headers=headers)
            json_output = balance_req.json()
            balance = json_output["currentBalance"]
            return float(balance)
        except Exception as error:
            print(traceback.format_exc())
            return {'balance' : "Error"}


    def create_verification(self):
        if self.is_bearer_token_expired():
            self.generate_beraer_token()

        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        service_name = "telegram"
        json_data = {
            "serviceName": service_name,
            "capability": "sms"
        }


        stock_available = False
        while stock_available == False:
            r = post(f"{self.BASE_URL}/api/pub/v2/verifications", headers=headers, json=json_data)
            data = r.json()

            if "errorDescription" in data:
                if data['errorDescription'] == "Out of stock or unavailable.":
                    print("OUT OF STOCK... Waiting 15 seconds.")
                    sleep(15)
                    continue
            
            stock_available = True
            break


        r.raise_for_status()

        data = r.json()
        verification_details_href = data.get("href")
        print(data)
        return verification_details_href


    def get_verification_details(self, href):
        if self.is_bearer_token_expired():
            self.generate_beraer_token()
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        r = get(href, headers=headers)
        r.raise_for_status()
        data = r.json()
        print(data)
        return data


    def check_code(self, sms_href):
        if self.is_bearer_token_expired():
            self.generate_beraer_token()

        headers = {"Authorization" : f"Bearer {self.bearer_token}"}
        result = get(sms_href, headers=headers).json()
        return result
        

    def cancel_verification(self, cancel_href):
        if self.is_bearer_token_expired():
            self.generate_beraer_token()
        headers = {"Authorization" : f"Bearer {self.bearer_token}"}
        result = post(cancel_href, headers=headers)
        print(f"Cancel Result: {result}")


    def report_verification(self, report_href):
        if self.is_bearer_token_expired():
            self.generate_beraer_token()

        headers = {"Authorization" : f"Bearer {self.bearer_token}"}
        result = post(report_href, headers=headers)
        print(f"Report Result: {result.content}")


def Get_Textverified_Number(textverified:TextVerifiedAPI):

    balance = textverified.get_balance()
    if balance < 1:
        print("LOW BALANCE")
        return None

    try:
        verification_href = textverified.create_verification()
    except Exception as error:
        print(f"Error while creating verification: {error}")

    verification_details = textverified.get_verification_details(verification_href)

    number = verification_details['number']
    verification_id = verification_details['id']
    sms_link = verification_details['sms']['href']
    cancel_link = verification_details['cancel']['link']['href']
    report_link = verification_details['report']['link']['href']
    verification_state = verification_details['state']

    return {
        "number": number,
        "verification_id" : verification_id,
        "sms_link" : sms_link,
        "cancel_link" : cancel_link,
        "report_link" : report_link
    }