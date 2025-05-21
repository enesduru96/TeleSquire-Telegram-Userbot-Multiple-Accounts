import json
import os
import time
import requests
import random

class TempMail:
    BASE_URL = "https://www.1secmail.com/api/v1/"

    def __init__(self, email=None):
        if email:
            self.email = email
        else:
            self.email = self.generate_temp_email()

    def generate_temp_email(self):
        domains = [
            "@rteet.com",
            "@rteet.com",
            "@rteet.com",
            "@rteet.com"
        ]
        random_domain = random.choice(domains)

        response = requests.get(f"{self.BASE_URL}?action=genRandomMailbox&count=1")
        if response.status_code == 200:
            local_part = response.json()[0].split("@")[0]
            email = f"{local_part}{random_domain}"
            print(f"Generated temp email: {email}")
            return email
        else:
            raise Exception("Failed to generate temp email")

    def get_email_address(self):
        return self.email

    def save_email(self, email, number, filename="emails.json"):
        new_entry = {"number": number, "email": email}

        if os.path.exists(filename):
            with open(filename, "r") as file:
                data = json.load(file)
        else:
            data = []

        data.append(new_entry)

        with open(filename, "w") as file:
            json.dump(data, file, indent=4)

        print(f"Email {email} saved with number {number}.")

    def check_inbox(self):
        username, domain = self.email.split('@')
        response = requests.get(f"{self.BASE_URL}?action=getMessages&login={username}&domain={domain}")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Failed to retrieve inbox")

    def get_email_content(self, message_id):
        username, domain = self.email.split('@')
        response = requests.get(f"{self.BASE_URL}?action=readMessage&login={username}&domain={domain}&id={message_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Failed to retrieve email content")

    def monitor_inbox_return_code(self, retries=10, delay=10):
        print("Checking inbox...")
        for _ in range(retries):
            inbox = self.check_inbox()
            
            if inbox:
                print(f"Found {len(inbox)} message(s) in inbox:")
                for message in inbox:
                    print(f"From: {message['from']}, Subject: {message['subject']}, Date: {message['date']}")
                    email_content = self.get_email_content(message['id'])
                    print(f"Content: {email_content['textBody']}")

                    email_text = email_content['textBody']
                    lines = email_text.splitlines()
                    for line in lines:
                        if "Your code is" in line:
                            code = line.split("Your code is:")[1].split(".")[0].strip()
                            return code
                return None
            else:
                print(f"No messages yet, checking again in {delay} seconds...")
                time.sleep(delay)
        print("No messages received after multiple attempts.")