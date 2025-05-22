import asyncio
import json
import os


devices = {
    "Honor": [
        "BVL-AN16",
        "BVL-AN00",
        "PGT-AN10",
        "PGT-AN00",
        "HPB-AN00",
        "OXF-AN10",
        "OXF-AN00"
    ],
    "Xiaomi": [
        "23116PN5BC",
        "23127PN0CC",
        "2304FPN6DG",
        "2210132C",
        "2211133C",
        "2203121C",
        "MI 9"
    ],
    "Redmi": [
        "23113RKC6C",
        "2311DRK48C",
        "22127RK46C",
        "23078RKD5C",
        "22081212C"
    ],
    "OPPO": [
        "PJJ110",
        "PJH110",
        "PHW110",
        "PHM110",
        "PHY110",
        "PHZ110",
        "PGEM10",
        "PGFM10",
    ],
    "vivo": [
        "V2329A",
        "V237A",
        "V2218A",
        "V2217A",
        "V2324A",
        "V239A",
        "V2266A",
        "V2229A",
        "V2242A",
        "V2241A",
        "V2339A",
        "V2338A"
    ],
    "Samsung": [
        "SM-X810N",
        "SM-X910N",
        "SM-X710N",
        "SM-S9280",
        "SM-S9260",
        "SM-S9210",
        "SM-S9180",
        "SM-S9160",
        "SM-S9110",
        "SM-N9860",
        "SM-N9810"
    ],
    "OnePlus": [
        "PJD110",
        "PHB110",
        "NE2210",
        "HD1910",
        "HD1900",
        "GM1910",
        "GM1900"
    ],
    "ROG": [
        "ASUS_AI2401_A",
        "ROG Phone 7 Ultimate",
        "ASUS_AI2205_A",
        "ASUS AI2201_B"
    ],
    "Google Phone": [
        "G576D",
        "GFE4J",
        "G82U8"
    ],
    "SONY": [
        "XQ-BE42",
        "XQ-AQ52",
        "SO-41B",
        "SO-02L",
        "SOV44"
    ],
    "AQUOS": [
        "A208SH",
        "SH-M24",
        "SHG07"
    ]
}

STATE_FILE = "data/emulator_device_progress.json"
PROXY_ORDER_FILE = "data/emulator_proxy_order.json"
PROXY_LIST_FILE = "data/emulator_my_proxies.txt"

class DeviceManager:
    def __init__(self, emulator_index, device_serial):
        self.emulator_index = emulator_index
        self.device_serial = device_serial
        self.devices = devices
        self.state_file = STATE_FILE
        self.progress = self.load_progress()

        self.proxy_order_file = PROXY_ORDER_FILE
        self.proxy_list_file = PROXY_LIST_FILE
        self.proxy_order = self.load_proxy_order()
        self.proxies = self.load_proxies()

    def load_progress(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as file:
                return json.load(file)
        else:
            return {"current_manufacturer": "Honor", "current_model_index": 0}

    def save_progress(self, manufacturer, model_index):
        with open(self.state_file, "w") as file:
            json.dump({"current_manufacturer": manufacturer, "current_model_index": model_index}, file)

    async def run_command(self, cmd):
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return stdout.decode().strip(), stderr.decode().strip()

    async def get_device_identity(self):
        print(f"Fetching device identity for {self.device_serial}...\n")
        manufacturer, _ = await self.run_command(f"adb -s {self.device_serial} shell getprop ro.product.manufacturer")
        model, _ = await self.run_command(f"adb -s {self.device_serial} shell getprop ro.product.model")
        imei, _ = await self.run_command(f"adb -s {self.device_serial} shell service call iphonesubinfo 1")
        androidid, _ = await self.run_command(f"adb -s {self.device_serial} shell settings get secure android_id")
        mac, _ = await self.run_command(f"adb -s {self.device_serial} shell cat /sys/class/net/wlan0/address")

        print(f"Manufacturer: {manufacturer}")
        print(f"Model: {model}")
        print(f"IMEI: {imei}")
        print(f"Android ID: {androidid}")
        print(f"MAC Address: {mac}")
        print("-" * 50)

    async def modify_device_identity(self, manufacturer, model):
        print(f"Setting manufacturer: {manufacturer}, model: {model}")
        cmd = (
            f"ldconsole modify --index {self.emulator_index} "
            f"--manufacturer {manufacturer} --model {model} "
            f"--imei auto --imsi auto --simserial auto --androidid auto --mac auto"
        )
        stdout, stderr = await self.run_command(cmd)
        if stderr:
            print(f"Failed to modify identity: {stderr}")
        else:
            print(f"Identity modified successfully!")
        print("-" * 50)

    async def restart_emulator(self):
        print(f"Restarting emulator {self.emulator_index}...\n")
        await self.run_command(f"ldconsole reboot --index {self.emulator_index}")
        await asyncio.sleep(15)
        print("Emulator restarted successfully.")
        print("-" * 50)

    async def process_single_device(self):
        current_manufacturer = self.progress["current_manufacturer"]
        current_model_index = self.progress["current_model_index"]

        manufacturers = list(self.devices.keys())
        manufacturer = manufacturers[manufacturers.index(current_manufacturer)]
        model = self.devices[manufacturer][current_model_index]

        print("Current Device Information:")
        await self.get_device_identity()

        await self.change_proxy()

        await self.modify_device_identity(manufacturer, model)

        await self.restart_emulator()

        print("Updated Device Information:")
        await self.get_device_identity()

        if current_model_index + 1 < len(self.devices[manufacturer]):
            self.save_progress(manufacturer, current_model_index + 1)
        else:
            next_manufacturer_index = manufacturers.index(current_manufacturer) + 1
            if next_manufacturer_index < len(manufacturers):
                self.save_progress(manufacturers[next_manufacturer_index], 0)
            else:
                print("All devices processed. Restarting from the beginning.")
                self.save_progress("Honor", 0)

    def load_proxy_order(self):
        if os.path.exists(self.proxy_order_file):
            with open(self.proxy_order_file, "r") as file:
                return json.load(file)
        else:
            return {"current_order": 0}

    def save_proxy_order(self, order):
        with open(self.proxy_order_file, "w") as file:
            json.dump({"current_order": order}, file)

    def load_proxies(self):
        if os.path.exists(self.proxy_list_file):
            with open(self.proxy_list_file, "r") as file:
                return [line.strip() for line in file if line.strip()]
        else:
            print(f"Proxy list file {self.proxy_list_file} not found!")
            return []

    async def change_proxy(self):
        if not self.proxies:
            print("No proxies loaded. Cannot change proxy!")
            return

        current_order = self.proxy_order["current_order"]
        proxy = self.proxies[current_order]
        print(f"Setting proxy: {proxy}")

        cmd = f"adb -s {self.device_serial} shell settings put global http_proxy {proxy}"
        stdout, stderr = await self.run_command(cmd)
        if stderr:
            print(f"Failed to set proxy: {stderr}")
        else:
            print(f"Proxy set successfully: {proxy}")

        next_order = (current_order + 1) % len(self.proxies)
        self.save_proxy_order(next_order)