#!/usr/bin/env python2
# coding=utf-8

from multiprocessing import freeze_support
import argparse
import threading
from WsClientHandler import hello, connectWs

from FiscalberryApp import FiscalberryApp

import logging
logger = logging.getLogger(__name__)



def init_server():
	
	'''
	logger.info("por comenzar el hilo")
	# conectar con main fiscalberry server waiting for ws messages
	t1 = threading.Thread(target=connectWs,args=(None,));
	logger.info("antes de comenzar el hilo")
	t1.start();
	logger.info("comenzo el hilo")

	while t1.is_alive():
		try:
			logger.info("joinea el hilo")
			t1.join(timeout = 0.1)
			logger.info("joineÓ el hilo")
		except IOError:
			pass #Gets thrown when we interrupt the join

	# iniciar tornado server
	'''
	fbserver = FiscalberryApp()

	logger.info("web server start")
	fbserver.start()
	logger.info("web server ya iniciado")

def send_discover():
	fbserver = FiscalberryApp()

	# lanzar discover a URL de servidor configurado con datos del config actual
	fbserver.discover()


if __name__ == "__main__":
	freeze_support()
	
	parser = argparse.ArgumentParser(description='servidor websockets para impresión fiscal y ESCP')
	parser.add_argument('--discover', 
							help='envia a la URL información de este servicio.', 
							action='store_true')
	args = parser.parse_args()

	if args.discover:
		send_discover()
		exit()

	init_server()

