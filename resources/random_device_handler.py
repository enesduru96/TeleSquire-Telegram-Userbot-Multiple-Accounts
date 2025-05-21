import json
import random
from resources._config import Config
from resources.database_functions.base_db_models import SystemVersion, Device, AppVersion, RandomDeviceOrder
from sqlalchemy import select

from resources.database_functions.database_handler import DatabaseHandler

new_devices = ['FA506QM-HN008TS', 'K413EA-EB313WS', 'G512LV-AZ224TS', 'B5EEK-069IN', 'GL504GM-ES152T', 'GV301QE-K6153TS', 
               'UX482EG-KA711TS', 'CP713-2W', 'G713QM-K4215TS', 'G532LWS-HF091T', 'FA506QM-HN008TS', 'GU603ZX-K8024WS', 
               '15-ec1073dx', 'G512LI-HN096T', 'FA566QM-HN087TS', '15ITL05', 'GZ301VV-MU014WS', 'G513RM-HF272WS', 
               'G713RM-LL167WS', 'GA401IU-HA246TS', 'G513IC-HN025W', 'FA706ICB-HX061W', 'FX506HM-HN016T', 'G513IH-HN084TS', 
               'G513QM-HF315TS', '16ARH7H', 'FA506QM-HN008TS', 'Mach-W19B', 'UX482EG-KA521WS', 'FA566IV-HN413T', 
               'G532LV-AZ090TS', 'G512LU-HN263TS', 'FX566HE-HN048T', 'G713QM-K4215TS', 'FA506QM-HN008TS', 'G531GU-ES016T', 
               'G512LU-HN263TS', '15ITL05', 'G512LI-HN059T', 'G513QE-HN166TS', 'GZ301ZE-LD064WS', '15-dk', 
               'UP5401ZA-KN711WS', 'GA401QH-HZ080TS', 'G713IC-HX056T', 'GX550LWS-HF130TS', 'FA506IC-HN075W', 
               'G513QR-HQ218TS', 'GU603ZM-K8035WS', 'GA401IU-HA246TS', 'GV301QH-K5485TS', 'UP3404VA-KN543WS', 
               'G513IH-HN084TS', 'G814JI-N6097WS', 'G513QM-HF315TS', 'GZ301VIC-MU004WS', 'G513IH-HN084TS', 
               'G533QS-HQ102TS', 'PGP1TVC-43M1I', '2SJ7AH9H-UQEY1', 'C2UYS-7QWSO', 'HF9L54QB-N1AT1']

from asyncio import Lock
device_lock = Lock()

class RandomDeviceHandler:
    def __init__(self, database_handler:DatabaseHandler):
        self.config_handler = Config()
        self.database_handler = database_handler

    async def update_random_device_list(self):
        async with self.database_handler.SessionMaker() as session:
            async with session.begin():
                try:
                    with open('data/random_device.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    system_versions = data['pc']['system_versions']
                    devices = data['pc']['devices']
                    app_version_str = data['pc']['app_version']

                    # Devices
                    existing_devices = await session.execute(select(Device.name))
                    existing_device_names = {device[0] for device in existing_devices}
                    for device_name in devices:
                        if device_name not in existing_device_names:
                            session.add(Device(name=device_name))
                            print(f"Device Added: {device_name}")

                    # System Versions
                    existing_system_versions = await session.execute(select(SystemVersion.name))
                    existing_system_version_names = {sv[0] for sv in existing_system_versions}
                    for sv_name in system_versions:
                        if sv_name not in existing_system_version_names:
                            session.add(SystemVersion(name=sv_name))
                            print(f"System Version Added: {sv_name}")

                    # App Version
                    existing_app_versions = await session.execute(select(AppVersion.version))
                    existing_app_version_names = {app_ver[0] for app_ver in existing_app_versions}
                    if app_version_str not in existing_app_version_names:
                        session.add(AppVersion(version=app_version_str))
                        print(f"App Version Added: {app_version_str}")

                    # Random Device Order
                    random_device_order = RandomDeviceOrder(
                        main_order=data['main_order'],
                        system_versions_order=data['pc']['system_versions_order'],
                        devices_order=data['pc']['devices_order'],
                        app_version_id=1
                    )
                    existing_device_orders = await session.execute(select(RandomDeviceOrder.main_order))
                    existing_device_order_names = {ro[0] for ro in existing_device_orders}
                    if random_device_order.main_order not in existing_device_order_names:
                        session.add(random_device_order)
                        print(f"Device Order Added: {random_device_order}")
                except Exception as e:
                    print("An error occurred:", e)
            
    async def add_new_devices(self):
        async with self.database_handler.SessionMaker() as session:
            async with session.begin():
                try:
                    existing_devices = await session.execute(select(Device.name))
                    existing_device_names = {device[0] for device in existing_devices}

                    for device_name in new_devices:
                        if device_name not in existing_device_names:
                            session.add(Device(name=device_name))
                            print(f"Device Added: {device_name}")
                except Exception as e:
                    print("An error occurred:", e)
            
    async def update_orders_pc(self):
        async with self.database_handler.SessionMaker() as session:
            async with session.begin():
                try:
                    order = await session.execute(select(RandomDeviceOrder))
                    order = order.scalar()

                    total_system_versions = await session.execute(select(SystemVersion))
                    total_system_versions_count = len(total_system_versions.scalars().all())

                    total_devices = await session.execute(select(Device))
                    total_devices_count = len(total_devices.scalars().all())

                    order.system_versions_order = (order.system_versions_order + 1) % total_system_versions_count
                    order.devices_order = (order.devices_order + 1) % total_devices_count
                except Exception as e:
                    print("An error occurred:", e)

    async def get_device_info_and_api(self):
        async with self.database_handler.SessionMaker() as session:
            async with device_lock:
                try:
                    order = await session.execute(select(RandomDeviceOrder))
                    order = order.scalar()
                    system_version = await session.execute(
                        select(SystemVersion.name).order_by(SystemVersion.id).offset(order.system_versions_order)
                    )
                    system_version = system_version.scalar()
                    device = await session.execute(
                        select(Device.name).order_by(Device.id).offset(order.devices_order)
                    )
                    device = device.scalar()
                    app_version = await session.execute(
                        select(AppVersion.version).filter_by(id=order.app_version_id)
                    )
                    app_version = app_version.scalar()

                    await self.update_orders_pc()

                    api_id = self.config_handler.api_id
                    api_hash = self.config_handler.api_hash

                    return device, system_version, app_version, api_id, api_hash
                
                except Exception as e:
                    print("An error occurred:", e)
                    return None

