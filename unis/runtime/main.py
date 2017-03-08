import atexit
import configparser
import copy
import signal
import sys

from unis.services import RuntimeService
from unis.runtime import settings
from unis.runtime.oal import ObjectLayer
from unis.utils.pubsub import Events

class RuntimeMeta(type):
    instances = {}
    def __call__(cls, *args, **kwargs):
        try:
            url = kwargs.get('url', args[0] if len(args) else None)
        except IndexError:
            raise AttributeError("Runtime constructor must contain url as first argument")
        if url not in cls.instances:
            cls.instances[url] = super(RuntimeMeta, cls).__call__(*args, **kwargs)
        return cls.instances[url]

class Runtime(object):
    @property
    def settings(self):
        if not hasattr(self, "_settings"):
            class DefaultDict(dict):
                def get(self, k, default=None):
                    val = super(DefaultDict, self).get(k, default)
                    return val or default
            
            self._settings = DefaultDict(copy.deepcopy(settings.DEFAULT_CONFIG))
            if settings.CONFIGFILE:
                tmpConfig = configparser.RawConfigParser(allow_no_value=True)
                tmpConfig.read(settings.CONFIGFILE)
                
                for section in tmpConfig.sections():
                    if not section in self._settings:
                        self._settings[section] = {}
                    
                    for key, setting in tmpConfig.items(section):
                        if setting == "true":
                            self._settings[section][key] = True
                        elif setting == "false":
                            self._settings[section][key] = False
                        else:
                            self._settings[section][key] = setting
                        
        return self._settings
    
    def __init__(self, url=None, defer_update=False, subscribe=True, auto_sync=True, inline=False):
        self.log = settings.get_logger()
        self.log.info("Starting Unis network Runtime Environment...")
        
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        atexit.register(self.shutdown)
        
        self._services = []
        self.settings["defer_update"] = defer_update
        self.settings["subscribe"] = subscribe
        self.settings["auto_sync"] = auto_sync
        self.settings["inline"] = inline
        if url:
            self.settings["unis"]["url"] = url
        self._oal = ObjectLayer(runtime=self, **self.settings["unis"])
        
        for service in self.settings["services"]:
            self.addService(service)
        
    def __getattr__(self, n):
        if "_oal" in self.__dict__:
            return getattr(self.__dict__["_oal"], n)
        else:
            raise AttributeError("_oal not found in Runtime")
        
    @property
    def collections(self):
        return self._oal._cache.values()
        
    def find(self, href):
        return self._oal.find(href)
    
    def insert(self, resource, commit=False):
        result = self._oal.insert(resource)
        if commit:
            resource.commit()
        return result
    
    def addService(self, service):
        instance = service
        if isinstance(service, type):
            instance = service()
        if not isinstance(instance, RuntimeService):
            raise ValueError("Service must by of type RuntimeService")
        instance.attach(self)
    
    def shutdown(self, sig=None, frame=None):
        self.log.info("Tearing down connection to UNIS...")
        if getattr(self, "_oal", None):
            self._oal.shutdown()
            self._oal = None
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        self.log.info("Teardown complete.")
        if sig:
            sys.exit(130)
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.shutdown()
