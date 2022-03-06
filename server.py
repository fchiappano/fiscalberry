#!/usr/bin/env python
# coding=utf-8

from multiprocessing import freeze_support
import argparse
import multiprocessing

from FiscalberryApp import FiscalberryApp

def init_server():
	
	fbserver = FiscalberryApp()
	fbserver.discover()
	fbserver.start()

	
def init_server_sio(isServer):

	fbserver = FiscalberryApp()
	sioserver = multiprocessing.Process(target=fbserver.startSocketIO, args={isServer},name="SocketIO")
	sioserver.start()
	fbserver.start()
	sioserver.terminate()


def send_discover():
	fbserver = FiscalberryApp()
	# lanzar discover a URL de servidor configurado con datos del config actual
	fbserver.discover()


if __name__ == "__main__":
	freeze_support()
	
	parser = argparse.ArgumentParser(description='Servidor websockets para impresión fiscal y ESCP')
	parser.add_argument('--discover', 
							help='envia a la URL información de este servicio.', 
							action='store_true')
	parser.add_argument('--sio',
							help='Inicia son SocketIO como cliente',
							action='store_true')
	parser.add_argument('--sio_server',
							help='Inicia son SocketIO como server',
							action='store_true')
	args = parser.parse_args()

	if args.discover:
		send_discover()
		exit()
	elif args.sio:
		init_server_sio(False)
	elif args.sio_server:
		init_server_sio(True)
	else:
		init_server()
	
