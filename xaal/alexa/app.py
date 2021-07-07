from gevent import monkey; monkey.patch_all()


from xaal.lib import tools,Engine,Device,helpers
from xaal.monitor import Monitor

from bottle import default_app,debug,get,post,request,response,redirect,static_file

import json
import os
import platform
import logging

from gevent import Greenlet
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

from treatment import treatment

# dev-type that don't appear in results
BLACK_LIST=['cli.experimental',]

PACKAGE_NAME = "xaal.alexa"
logger = logging.getLogger(PACKAGE_NAME)

# we use this global variable to share data with greenlet
monitor = None


def monitor_filter(msg):
    """ Filter incomming messages. Return False if you don't want to use this device"""
    if msg.dev_type in BLACK_LIST:
        return False
    return True


def setup_xaal():
    """ setup xAAL Engine & Device. And start it in a Greenlet"""
    global monitor 
    engine = Engine()
    cfg = tools.load_cfg(PACKAGE_NAME)
    if not cfg:
        logger.info("No config file found, building a new one")
        cfg = tools.new_cfg(PACKAGE_NAME)
        cfg['config']['db_server'] = ''
        cfg.write()
    dev            = Device("hmi.basic")
    dev.address    = tools.get_uuid(cfg['config']['addr'])
    dev.vendor_id  = "IHSEV"
    dev.product_id = "REST API"
    dev.version    = 0.1
    dev.info       = "%s@%s" % (PACKAGE_NAME,platform.node())

    engine.add_device(dev)
    db_server = tools.get_uuid(cfg['config'].get('db_server',None))
    if not db_server:
        logger.info('Please set a db_server in your config file')
    monitor = Monitor(dev,filter_func=monitor_filter,db_server=db_server)
    engine.start()        
    green_let = Greenlet(xaal_loop, engine)
    green_let.start()


def xaal_loop(engine):
    """ xAAL Engine Loop Greenlet"""
    while 1:
        engine.loop()

@post('/json')
def receive_json():
    #print(json.dumps(request.json, indent=4, sort_keys=True))
    res = treatment(monitor, request.json)
    res = json.dumps(res, indent=4)    
    response.headers['Content-Type'] = 'application/json'
    return res

def run():
    """ start the xAAL stack & launch the HTTP stuff"""
    helpers.set_console_title(PACKAGE_NAME)
    helpers.setup_console_logger(level=logging.INFO)
    setup_xaal()
    app = default_app()
    debug(True)
    port = 8081
    logger.info("HTTP Server running on port : %d" % port)
    server = WSGIServer(("", port), app, handler_class=WebSocketHandler)
    server.serve_forever()

def main():
    try:
        run()
    except KeyboardInterrupt:
        print("Bye Bye...")
    
    
    
if __name__ == '__main__':
    main()
