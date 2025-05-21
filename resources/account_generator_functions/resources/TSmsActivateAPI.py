from requests import get
from time import sleep
class SmsActivateAPI(object):
    countries = {'russia': 0, 'ukraine': 1, 'kazakhstan': 2, 'china': 3, 'philippines': 4, 'myanmar': 5, 'indonesia': 6, 'malaysia': 7, 'kenya': 8, 'tanzania': 9, 'vietnam': 10, 'kyrgyzstan': 11, 'usa (virtual)': 12, 'israel': 13, 'hongkong': 14, 'poland': 15, 'england': 16, 'dcongo': 18, 'nigeria': 19, 'macao': 20, 'egypt': 21, 'india': 22, 'ireland': 23, 'cambodia': 24, 'laos': 25, 'haiti': 26, 'ivory': 27, 'gambia': 28, 'serbia': 29, 'yemen': 30, 'southafrica': 31, 'romania': 32, 'colombia': 33, 'estonia': 34, 'canada': 36, 'morocco': 37, 'ghana': 38, 'argentina': 39, 'uzbekistan': 40, 'cameroon': 41, 'chad': 42, 'germany': 43, 'lithuania': 44, 'croatia': 45, 'sweden': 46, 'iraq': 47, 'netherlands': 48, 'latvia': 49, 'austria': 50, 'belarus': 51, 'thailand': 52, 'saudiarabia': 53, 'mexico': 54, 'taiwan': 55, 'spain': 56, 'algeria': 58, 'slovenia': 59, 'bangladesh': 60, 'senegal': 61, 'turkey': 62, 'czech': 63, 'srilanka': 64, 'peru': 65, 'pakistan': 66, 'newzealand': 67, 'guinea': 68, 'mali': 69, 'venezuela': 70, 'ethiopia': 71, 'mongolia': 72, 'brazil': 73, 'afghanistan': 74, 'uganda': 75, 'angola': 76, 'cyprus': 77, 'france': 78, 'papua': 79, 'mozambique': 80, 'nepal': 81, 'belgium': 82, 'bulgaria': 83, 'hungary': 84, 'moldova': 85, 'italy': 86, 'paraguay': 87, 'honduras': 88, 'tunisia': 89, 'nicaragua': 90, 'timorleste': 91, 'bolivia': 92, 'costarica': 93, 'guatemala': 94, 'uae': 95, 'zimbabwe': 96, 'puertorico': 97, 'togo': 99, 'kuwait': 100, 'salvador': 101, 'libyan': 102, 'jamaica': 103, 'trinidad': 104, 'ecuador': 105, 'swaziland': 106, 'oman': 107, 'bosnia': 108, 'dominican': 109, 'qatar': 111, 'panama': 112, 'mauritania': 114, 'sierraleone': 115, 'jordan': 116, 'portugal': 117, 'barbados': 118, 'burundi': 119, 'benin': 120, 'brunei': 121, 'bahamas': 122, 'botswana': 123, 'belize': 124, 'caf': 125, 'dominica': 126, 'grenada': 127, 'georgia': 128, 'greece': 129, 'guineabissau': 130, 'guyana': 131, 'iceland': 132, 'comoros': 133, 'saintkitts': 134, 'liberia': 135, 'lesotho': 136, 'malawi': 137, 'namibia': 138, 'niger': 139, 'rwanda': 140, 'slovakia': 141, 'suriname': 142, 'tajikistan': 143, 'monaco': 144, 'bahrain': 145, 'reunion': 146, 'zambia': 147, 'armenia': 148, 'somalia': 149, 'congo': 150, 'chile': 151, 'furkinafaso': 152, 'lebanon': 153, 'gabon': 154, 'albania': 155, 'uruguay': 156, 'mauritius': 157, 'bhutan': 158, 'maldives': 159, 'guadeloupe': 160, 'turkmenistan': 161, 'frenchguiana': 162, 'finland': 163, 'saintlucia': 164, 'luxembourg': 165, 'saintvincentgrenadines': 166, 'equatorialguinea': 167, 'djibouti': 168, 'antiguabarbuda': 169, 'caymanislands': 170, 'montenegro': 171, 'denmark': 172, 'switzerland': 173, 'norway': 174, 'australia': 175, 'eritrea': 176, 'southsudan': 177, 'saotomeandprincipe': 178, 'aruba': 179, 'montserrat': 180, 'anguilla': 181, 'japan': 182, 'northmacedonia': 183, 'seychelles': 184, 'newcaledonia': 185, 'capeverde': 186, 'usa': 187, 'southkorea': 190}

    def __init__(self):
        self.api_key = "sms_activate_api_key"
        self.source  = f"https://sms-activate.org/stubs/handler_api.php?api_key={self.api_key}&"
        self.ruble_limit = 30
        self.country = "indonesia"
        self.sms_delay = 120

    def get_balance(self) -> dict:
        balance_req = get(f"{self.source}action=getBalance")
        try:
            key, value  = balance_req.text.split(":")
        except Exception:
            print(f"    {balance_req.text}")
        return {'balance': float(value)}

    def fetch_code(self, _id:int):
        request = get(f"{self.source}&action=getStatus&id={_id}")
        return request.text

    def cancel_order(self, _id:int):
        return get(f"{self.source}&action=setStatus&status=8&id={_id}")

    def ban_order(self, _id:int):
        return get(f"{self.source}&action=setStatus&status=8&id={_id}")

    def finish_order(self, _id:int):
        return get(f"{self.source}&action=setStatus&status=6&id={_id}")

    @property
    def _get_country_list(self) -> list:
        return list(SmsActivateAPI.countries.keys())

    def _get_country_id(self, country:str) -> int:
        return SmsActivateAPI.countries[country]

    def _get_price(self, country_id:int, servis:str='tg'):
        price = get(f"{self.source}action=getPrices&service={servis}&country={country_id}").json()[str(country_id)][servis]
        return {
            'price' : price['cost'],
            'count' : price['count'],
        }

    def get_service(self, country:str, service:str='tg') -> dict:
        _country = country.lower()
        if _country not in self._get_country_list:
            raise ValueError(f"{country} Not in ;\n\n{self._get_country_list}")

        country_id = self._get_country_id(_country)
        data       = self._get_price(country_id, service)
        return {
            "country" : _country,
            "id"      : country_id,
            "price"   : data['price'],
            "count"   : data['count']
        }

    def get_number(self, country_id:int, service:str='tg'):
        order_req = get(f"{self.source}action=getNumber&service={service}&country={country_id}")

        try:
            key, _id, phone = order_req.text.split(':')
            status = get(f"{self.source}&action=setStatus&status=1&id={_id}").text
            if status == 'ACCESS_READY':
                return {
                    "success"  : True,
                    "order_id" : _id,
                    "phone"    : f"+{phone}"
                }
            else:
                self.cancel_order(_id=_id)
                return {
                    "success" : False
                }
        except ValueError:
            return {
                "success" : False
            }

    def buy_number(self):
        my_money = self.get_balance()['balance']
        if not my_money:
            input("OUT OF MONEY... PRESS ENTER.")
        if my_money < self.ruble_limit:
            input("OUT OF MONEY... PRESS ENTER.")

        while True:
            service = self.get_service(self.country)

            if service['price'] > self.ruble_limit:
                print(f"    [Expensive] {service['country']} | {service['price']} Rub.")
                continue

            if service['count'] == 0:
                print(f"    [No Number] {service['country']} | {service['price']} Rub.")
                continue

            buy = self.get_number(service['id'])

            if buy['success']:
                return {
                    "id"      : int(buy['order_id']),
                    "operator": "Sms-Activate",
                    "phone"   : buy['phone'],
                    "country" : service['country'],
                    "price"   : service['price']
                }


def Fetch_SmsActivate_Code(number_id:int,phone_number):
    phone_sms_code = None

    time_out = 120
    while not phone_sms_code:
        sms_act_api = SmsActivateAPI()
        sms_code = sms_act_api.fetch_code(number_id)
        if (sms_code != 'STATUS_WAIT_CODE') and sms_code.split(':')[0] == 'STATUS_OK':
            sms_act_api.finish_order(number_id)
            return sms_code.split(':')[1]

        sleep(3)
        time_out -= 3
        print(f"    {phone_number} > Waiting for SMS: {time_out} \r ", end="")
        if time_out <= 0:
            return None

def Get_SmsActivate_Number(sms_activate:SmsActivateAPI):
    phone_sms_act_api = None

    while not phone_sms_act_api:
        sleep(1)
        phone_number = sms_activate.buy_number()
        if phone_number:
            return phone_number


def Fetch_SmsActivate_Code(number_id:int, phone_number, sms_activate:SmsActivateAPI):
    phone_sms_code = None

    time_out = 120
    while not phone_sms_code:
        sms_code = sms_activate.fetch_code(number_id)
        if (sms_code != 'STATUS_WAIT_CODE') and sms_code.split(':')[0] == 'STATUS_OK':
            sms_activate.finish_order(number_id)
            return sms_code.split(':')[1]

        sleep(3)
        time_out -= 3
        print(f"    {phone_number} > Waiting for SMS: {time_out} \r", end="")
        if time_out <= 0:
            return None