from sqlalchemy import func, asc, select
from sqlalchemy.exc import SQLAlchemyError
from resources.database_functions.base_db_models import Proxy, ProxyOrder, FilteredProxy, ProxyUseCounter
from resources._config import Config
import os
import python_socks

from resources.database_functions.database_handler import DatabaseHandler

from asyncio import Lock
proxy_lock = Lock()

class ProxyHandler:
    def __init__(self, database_handler:DatabaseHandler):
        config = Config()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.proxy_file = os.path.join(self.data_dir, "proxy_list.txt")
        self.database_handler = database_handler

    async def get_formatted_proxy(self, proxyString):
        try:
            proxi_part = proxyString.split(':')
            return (
                python_socks.ProxyType.SOCKS5,
                proxi_part[0],      # ip
                int(proxi_part[1]), # port
                True,
                proxi_part[2],      # username
                proxi_part[3]       # password
            )
        except Exception as error:
            print(f"Error on 'get_formatted_proxy':\n{error}")

    async def get_next_proxy(self, phone_number):
        async with self.database_handler.SessionMaker() as session:
            async with proxy_lock:
                try:
                    # Phone prefix-country mapping
                    country_data = {
                        "Indonesia": "62",
                        "South Africa": "27",
                        "United States": "1",
                        "Myanmar": "95",
                    }
                    target_country = next((k for k, v in country_data.items() if phone_number.startswith(v)), None)

                    if not target_country:
                        print("Phone number does not match any country prefix.")
                        return None

                    # Check unused proxies
                    unused_proxies = await session.execute(
                        select(FilteredProxy).outerjoin(
                            ProxyUseCounter, FilteredProxy.proxy == ProxyUseCounter.proxy
                        ).filter(FilteredProxy.geolocation == target_country, ProxyUseCounter.proxy == None)
                    )
                    unused_proxies = unused_proxies.scalars().all()

                    if unused_proxies:
                        selected_proxy = unused_proxies[0]
                        await self.update_proxy_use_counter(selected_proxy.proxy)
                        return selected_proxy.proxy

                    # Check least used proxy
                    least_used_proxy = await session.execute(
                        select(FilteredProxy, ProxyUseCounter.used_times).outerjoin(
                            ProxyUseCounter, FilteredProxy.proxy == ProxyUseCounter.proxy
                        ).filter(FilteredProxy.geolocation == target_country).order_by(
                            asc(ProxyUseCounter.used_times)
                        )
                    )
                    least_used_proxy = least_used_proxy.first()

                    if not least_used_proxy:
                        print(f"No proxies available for geolocation: {target_country}.")
                        return None

                    proxy, _ = least_used_proxy
                    await self.update_proxy_use_counter(proxy.proxy)
                    return proxy.proxy
                except SQLAlchemyError as e:
                    print(f"Database error: {e}")
                    return None

    async def update_proxy_use_counter(self, proxy):
        async with self.database_handler.SessionMaker() as session:
            try:
                proxy_counter = await session.execute(
                    select(ProxyUseCounter).filter_by(proxy=proxy)
                )
                proxy_counter = proxy_counter.scalars().first()

                if proxy_counter:
                    proxy_counter.used_times += 1
                else:
                    session.add(ProxyUseCounter(proxy=proxy, used_times=1))

                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"Error updating proxy use counter: {e}")


    async def reset_proxy_counters(self):
        async with self.database_handler.SessionMaker() as session:
            try:
                await session.execute("UPDATE proxy_use_counter SET used_times = 0")
                await session.commit()
                print("All proxy counters reset to 0.")
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"Error resetting proxy counters: {e}")


    async def add_proxies_from_file(self):
        async with self.database_handler.SessionMaker() as session:
            async with session.begin():
                try:

                    with open(self.proxy_file, 'r', encoding='utf-8') as f:
                        lines = f.read().splitlines()

                    for line in lines:
                        parts = line.strip().split(':')
                        if len(parts) >= 2:
                            ip_address = parts[0]
                            port = int(parts[1])
                            username = parts[2] if len(parts) > 2 else None
                            password = parts[3] if len(parts) > 3 else None

                            existing_proxy = await session.execute(
                                select(Proxy).filter_by(proxy_address=ip_address, port=port)
                            )
                            if not existing_proxy.scalars().first():
                                new_proxy = Proxy(
                                    proxy_address=ip_address,
                                    port=port,
                                    username=username,
                                    password=password
                                )
                                session.add(new_proxy)
                                print(f"Added new proxy: {ip_address}:{port}")
                except Exception as e:
                    print(f"Error adding proxies from file: {e}")