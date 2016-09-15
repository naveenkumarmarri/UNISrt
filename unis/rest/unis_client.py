import json
import re
import requests
import websocket

from concurrent.futures import ThreadPoolExecutor

from unis.runtime.settings import MIME, get_logger

class UnisError(Exception):
    pass

class UnisClient(object):
    def __init__(self, url, **kwargs):
        self.log = get_logger()
        re_str = 'http[s]?://(?P<host>[^:/]+)(?::(?P<port>[0-9]{1,5}))$'
        if not re.compile(re_str).match(url):
            raise ValueError("unis url is malformed")
        
        self._url = url
        self._verify = kwargs.get("verify", False)
        self._ssl = kwargs.get("cert", None)
        self._executor = ThreadPoolExecutor(max_workers=12)
        self._sockets = []
    
    def shutdown(self):
        self.log.info("Removing sockets")
        for socket in self._sockets:
            socket.close()
        self._executor.shutdown()
    
    def getResources(self):
        headers = { 'content-type': 'application/perfsonar+json',
                    'accept': MIME['PSJSON'] }
        self.log.debug("resources <url={u} headers={h}>".format(u = self._url, h = headers))
        return self._check_response(requests.get(self._url, verify = self._verify, cert = self._ssl))
        
    def get(self, url, limit = None, **kwargs):
        args = self._get_conn_args(url)
        args["url"] = self._build_query(args, limit = limit, **kwargs)
        self.log.debug("get <url={u} headers={h}>".format(u = args["url"], h = args["headers"]))
        return self._check_response(requests.get(args["url"], verify = self._verify, cert = self._ssl))
    
    def post(self, url, data):
        args = self._get_conn_args(url)
        if isinstance(data, dict):
            data = json.dumps(data)
        
        self.log.debug("post <url={u} headers={h}  data={d}>".format(u = args["url"], 
                                                                     h = args["headers"], 
                                                                     d = data))
        return self._check_response(requests.post(args["url"], data = data, 
                                                  verify = self._verify, cert = self._ssl))
    
    def subscribe(self, collection, callback):
        return self._executor.submit(self._subscribe, collection, callback)
    def _subscribe(self, collection, callback):
        kwargs = {}
        if self._ssl:
            kwargs["ca_certs"] = self._ssl[0]
            
        re_str = 'http[s]?://(?P<host>[^:/]+)(?::(?P<port>[0-9]{1,4}))$'
        matches = re.match(re_str, self._url)
        url = "ws{s}://{h}:{p}/subscribe/{c}".format(s = "s" if "ca_certs" in kwargs else "", 
                                                     h = matches.group("host"), 
                                                     p = matches.group("port"), 
                                                     c = collection)
        def on_message(ws, message):
            self.log.debug("ws-message <url={u} msg={m}>".format(u = url, m = message))
            callback(message)
        ws = websocket.WebSocketApp(url, on_message = on_message,
                                    on_error = lambda ws, error: self.log.error("ws-error <url={u} error={e}>".format(u = url, e = error)),
                                    on_open  = lambda ws: self.log.debug("ws-connect <url={u}>".format(u = url)), 
                                    on_close = lambda ws: self.log.debug("ws-close <url={u}>".format(u = url)))
        self._sockets.append(ws)
        ws.run_forever(sslopt=kwargs)
        
    def _build_query(self, args, **kwargs):
        if kwargs:
            q = ""
            for k,v in kwargs.items():
                if v:
                    q += "{k}={v}&".format(k = k, v = v)
                
            return "{b}?{q}".format(b = args["url"], q = q[0:-1])
        return args["url"]
    
    def _get_conn_args(self, url):
        re_str = "{full}|{rel}|{name}".format(full = 'http[s]?://(?P<host>[^:/]+)(?::(?P<port>[0-9]{1,4}))?/(?P<col1>[a-zA-Z]+)(?:/(?P<uid1>[^/]+))?$',
                                              rel  = '#/(?P<col2>[a-zA-Z]+)(?:/(?P<uid2>[^/]+))?$',
                                              name = '(?P<col3>[a-zA-Z]+)$')
        matches = re.compile(re_str).match(url)
        collection = matches.group("col1") or matches.group("col2") or matches.group("col3")
        uid = matches.group("uid1") or matches.group("uid2")
        return { "collection": collection,
                 "url": "{u}/{c}{i}".format(u = self._url, c = collection, i = "/" + uid if uid else ""),
                 "headers": { 'content-type': 'application/perfsonar+json',
                              'accept': MIME['PSJSON'] } }
    
    def _check_response(self, r):
        self.log.debug("unis-response <code={c}>".format(c = r.status_code))
        if 200 <= r.status_code <= 299:
            try:
                return r.json()
            except:
                return r.status_code
        elif 400 <= r.status_code <= 499:
            raise Exception("Error from unis server [bad request] - {t} [{exp}]".format(exp = r.status_code, t = r.text))
        else:
            raise Exception("Error from unis server - {t} [{exp}]".format(exp = r.status_code, t = r.text))
