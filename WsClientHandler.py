
import tornado.websocket


import logging
logger = logging.getLogger(__name__)


import Configberry

configberry = Configberry.Configberry()




def hello(fbserver):
    print("asaposkaokspoap skpoaksoak soka posko p")
    logger.info("estoy en el connext WS")
    return True


def connectWs(fbserver):
    print("aiosjoajs s apos11201920912001922")
    logger.info("estoy en el connext WS")
    if configberry.config.has_option('SERVIDOR', "socketio_server"):
        ws_server = configberry.config.get('SERVIDOR', "socketio_server")
        conn = yield tornado.websocket.websocket_connect(ws_server)
        while True:
            msg = yield conn.read_message()
            if msg is None: break
            
            # Do something with msg
            logger.info("llego mensaje desde WEFB %s" % msg)

    else:
        raise Exception("Dno hay socket io server configurado")



class WsServerHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, ref_object):
        priont("inicializando servidor WS para conexxion desde otro paxaprinter")
        self.fbApp = ref_object
        self.fbApp.clientsFb = []

    def open(self):
        priont("OPEN Coneccion de fiscalberry server")
        self.fbApp.clientsFb.append(self)
        logger.info('WSFbHandler Connection WSFbHandler Established')
        print(self)


    def on_message(self, message):
        priont("MENSAJE Coneccion de fiscalberry server")
        logger.info('WSFbHandler message received WSFbHandler %s' % message)
        self.write_message(message)

    def on_close(self):
        priont("CLOSE Coneccion de fiscalberry server")
        self.fbApp.clientsFb.remove(self)
        logger.info('WSFbHandler connection closed WSFbHandler')

    def check_origin(self, origin):
        return True

