import os
import sys

##################################################################
# UNISrt Configuration
##################################################################
CONFIGFILE = None

STANDALONE_DEFAULTS = {
    "properties": {
        "configurations": {
            "unis_url": "http://localhost:8888",
            "ms_url": "http://localhost:8888",
            "use_ssl": False,
            "ssl_cert": "client.pem",
            "ssl_key": "client.key",
            "ssl_cafile": None
            }
        },
    "resources": [
#        "domains",
#        "nodes",
#        "ports",
#        "ipports",
#        "links",
#        "services",
#        "measurements",
#        "paths",
        "exnodes",
        "extents"
        ],
    }

UNISRT_ROOT = os.path.dirname(os.path.abspath(__file__)) + os.sep
sys.path.append(os.path.dirname(os.path.dirname(UNISRT_ROOT)))

##################################################################
# Schema definitions and locations
##################################################################
SCHEMA_HOST        = 'unis.crest.iu.edu'
SCHEMAS_LOCAL      = False

JSON_SCHEMAS_ROOT  = os.path.join(UNISRT_ROOT, "schemas")
SCHEMA_CACHE_DIR   = os.path.join(JSON_SCHEMAS_ROOT, ".cache")

JSON_SCHEMA_SCHEMA = "http://json-schema.org/draft-04/schema#"
JSON_SCHEMA_HYPER  = "http://json-schema.org/draft-04/hyper-schema#"
JSON_SCHEMA_LINKS  = "http://json-schema.org/draft-04/links#"

_schema = "http://{host}/schema/{directory}/{name}"
SCHEMAS = {
    'manifest':        _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "manifest#"),
    'lifetime':        _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "lifetime#"),
    'networkresource': _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "networkresource#"),
    'node':            _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "node#"),
    'domain':          _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "domain#"),
    'port':            _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "port#"),
    'link':            _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "link#"),
    'path':            _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "path#"),
    'network':         _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "network#"),
    'topology':        _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "topology#"),
    'service':         _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "service#"),
    'metadata':        _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "metadata#"),
    'data':            _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "data#"),
    'datum':           _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "datum#"),
    'measurement':     _schema.format(host = SCHEMA_HOST, directory = "20160630", name = "measurement#"),
    'exnode':          _schema.format(host = SCHEMA_HOST, directory = "exnode/6", name = "exnode#"),
    'extent':          _schema.format(host = SCHEMA_HOST, directory = "exnode/6", name = "extent#"),
}

MIME = {
    'HTML': 'text/html',
    'JSON': 'application/json',
    'PLAIN': 'text/plain',
    'SSE': 'text/event-stream',
    'PSJSON': 'application/perfsonar+json',
    'PSBSON': 'application/perfsonar+bson',
    'PSXML': 'application/perfsonar+xml',
    }

##################################################################
# Logging configuration
##################################################################
import logging
from netlogger import nllog

DEBUG = False
TRACE = False

NETLOGGER_NAMESPACE = "unisrt"

def config_logger():
    """Configures netlogger"""
    nllog.PROJECT_NAMESPACE = NETLOGGER_NAMESPACE
    #logging.setLoggerClass(nllog.PrettyBPLogger)
    logging.setLoggerClass(nllog.BPLogger)
    log = logging.getLogger(nllog.PROJECT_NAMESPACE)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)
    # set level
    if TRACE:
        log_level = (logging.WARN, logging.INFO, logging.DEBUG,
                     nllog.TRACE)[3]
    elif DEBUG:
        log_level = (logging.WARN, logging.INFO, logging.DEBUG,
                     nllog.TRACE)[2]

    else:
        log_level = (logging.WARN, logging.INFO, logging.DEBUG,
                     nllog.TRACE)[1]
    log.setLevel(log_level)

def get_logger(namespace=NETLOGGER_NAMESPACE):
    """Return logger object"""
    # Test if netlogger is initialized
    if nllog.PROJECT_NAMESPACE != NETLOGGER_NAMESPACE:
        config_logger()
    return nllog.get_logger(namespace)

