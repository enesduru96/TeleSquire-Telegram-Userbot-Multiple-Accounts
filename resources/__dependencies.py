from resources.database_functions.database_handler import DatabaseHandler
from resources.random_device_handler import RandomDeviceHandler
from resources.proxy_handler import ProxyHandler
from resources.file_handler import FileHandler

class DependencyContainer:
    def __init__(self):
        self._database_handler = None
        self._device_handler = None
        self._proxy_handler = None
        self._file_handler = None

    async def initialize(self):
        self._database_handler = await DatabaseHandler.create()
        self._device_handler = RandomDeviceHandler(self._database_handler)
        self._proxy_handler = ProxyHandler(self._database_handler)
        self._file_handler = FileHandler(proxy_handler=self._proxy_handler, device_handler=self._device_handler)

    @property
    def database_handler(self):
        if not self._database_handler:
            raise RuntimeError("DependencyContainer is not initialized yet.")
        return self._database_handler

    @property
    def proxy_handler(self):
        if not self._proxy_handler:
            raise RuntimeError("DependencyContainer is not initialized yet.")
        return self._proxy_handler

    @property
    def device_handler(self):
        if not self._device_handler:
            raise RuntimeError("DependencyContainer is not initialized yet.")
        return self._device_handler

    @property
    def file_handler(self):
        if not self._file_handler:
            raise RuntimeError("DependencyContainer is not initialized yet.")
        return self._file_handler


GLOBAL_DEPENDENCIES = DependencyContainer()