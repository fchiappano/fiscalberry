#!/usr/bin/env python
# coding=utf-8

from multiprocessing import freeze_support
import argparse
import _thread

from FiscalberryApp import FiscalberryApp


def init_server():
	
	fbserver = FiscalberryApp()

	try:
		_thread.start_new_thread( fbserver.discover, ("Thread-1", 2, ) )
		_thread.start_new_thread( fbserver.ws_socketio, ("Thread-2", 4, ) )
		_thread.start_new_thread( fbserver.start, ("Thread-3", 4, ) )
	except:
		print( "Error: unable to start thread")
	


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

