import json
import os
import time
import requests
import hashlib

class TempMailAPI:
    BASE_URL = "https://privatix-temp-mail-v1.p.rapidapi.com/request/"
    HEADERS = {
        "X-RapidAPI-Host": "privatix-temp-mail-v1.p.rapidapi.com",
        "X-RapidAPI-Key": "api_key",
    }

    def __init__(self):
        self.email = self.generate_temp_email()

    def get_domains(self):
        response = requests.get(f"{self.BASE_URL}domains/", headers=self.HEADERS)
        if response.status_code == 200:
            domains = response.json()
            print("Available Domains:", domains)
            return domains
        else:
            raise Exception("Failed to retrieve domains list")

    def generate_temp_email(self):
        domains = self.get_domains()
        if domains:
            local_part = "temp" + str(hashlib.md5().hexdigest()[:6])
            email = f"{local_part}@{domains[0]}"  # İlk domaini kullanıyoruz
            print(f"Generated temp email: {email}")
            return email
        else:
            raise Exception("No domains available to create email")

    def get_email_address(self):
        return self.email

    def check_inbox(self):
        email_md5 = hashlib.md5(self.email.encode()).hexdigest()
        response = requests.get(f"{self.BASE_URL}mail/id/{email_md5}/", headers=self.HEADERS)
        
        if response.status_code == 200:
            inbox = response.json()
            if inbox:
                print(f"Found {len(inbox)} message(s) in inbox.")
                return inbox
            else:
                print("No messages in inbox.")
                return None
        else:
            raise Exception("Failed to retrieve inbox")

    def get_email_content(self, message_id):
        email_md5 = hashlib.md5(self.email.encode()).hexdigest()
        response = requests.get(f"{self.BASE_URL}mail/id/{email_md5}/{message_id}/", headers=self.HEADERS)
        
        if response.status_code == 200:
            content = response.json()
            print("Email Content:", content['mail_text'])
            return content
        else:
            raise Exception("Failed to retrieve email content")


# Example use
# if __name__ == "__main__":
#     temp_mail = TempMailAPI()
#     print("Temporary Email Address:", temp_mail.get_email_address())

#     # Gelen kutusunu kontrol et
#     inbox = temp_mail.check_inbox()
#     if inbox:
#         for message in inbox:
#             print("From:", message['mail_from'], "Subject:", message['mail_subject'])
#             content = temp_mail.get_email_content(message['mail_id'])
#             print("Content:", content['mail_text'])