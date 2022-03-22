# -*- coding: utf-8 -*-
from Traductores.TraductorInterface import TraductorInterface
import math


class TraductorFiscalPanama(TraductorInterface):

    def dailyClose(self, type):
        "Comando X o Z"
        # cancelar y volver a un estado conocido
        self.comando.cancelAnyDocument()

        self.comando.start()
        ret = self.comando.dailyClose(type)
        self.comando.close()
        return ret

    def imprimirAuditoria(self, desde, hasta):
        "Imprimir Auditoria"
        #Solo compatible para Epson 1G y 2G por el momento...

        #desde & hasta parametros que pueden ser números de zetas o fechas en formato ddmmyyyy

        self.comando.start()
        ret = self.comando.imprimirAuditoria(desde, hasta)
        self.comando.close()
        return ret

    def getStatus(self):
        "getStatus"
        self.comando.start()
        ret = self.comando.getStatus()
        self.comando.close()
        return ret

    def setHeader(self, *args):
        "SetHeader"
        self.comando.start()
        ret = self.comando.setHeader(list(args))
        self.comando.close()
        return ret

    def setTrailer(self, *args):
        "SetTrailer"
        self.comando.start()
        ret = self.comando.setTrailer(list(args))
        self.comando.close()
        return ret

    def openDrawer(self, *args):
        "Abrir caja registradora"
        self.comando.start()
        ret = self.comando.openDrawer()
        self.comando.close()
        return ret

    def getLastNumber(self, tipo_cbte):
        "Devuelve el último número de comprobante"
        self.comando.start()
        letra_cbte = tipo_cbte[-1] if len(tipo_cbte) > 1 else None
        ret = self.comando.getLastNumber(letra_cbte)
        self.comando.close()
        return ret

    def cancelDocument(self, *args):
        "Cancelar comprobante en curso"
        self.comando.start()
        self.comando.cancelAnyDocument()
        self.comando.close()

    def printTicket(self, encabezado=None, items=[], pagos=[], addAdditional=None, setHeader=None, setTrailer=None):
        if setHeader:
            self.setHeader(*setHeader)

        if setTrailer:
            self.setTrailer(*setTrailer)
        
        self.comando.start()

        try:

          if encabezado:
              self._abrirComprobante(**encabezado)
          else:
              self._abrirComprobante()

          #if items:
          for item in items:
              self._imprimirItem(**item)
         
          if pagos:
                for pago in pagos:
                    self._imprimirPago(**pago)

        #   if addAdditional:
        #       self.comando.addAdditional(**addAdditional)
          
          rta = self._cerrarComprobante()
          self.comando.close()
          return rta

        except Exception as e:
          self.cancelDocument()
          raise

    def _abrirComprobante(self,
                          nombre_cliente    =   None,       # Razon Social
                          tipo_doc          =   "RUC",      # RUC/CI
                          nro_doc           =   None,       # Nro de RUC/CI
                          referencia        =   None,       # Nro Comprobante original  (ND/NC)
                          nro_registro      =   None,       # Nro registro impresora    (ND/NC)
                          fecha_original    =   None,       # Fecha en formato: AAMMDD  (NC/ND)
                          hora_original     =   None,       # Hora en formato HHMMSS    (NC/ND)
                          tipo_cbte         =   'A',        # A = Factura/Ticket; B = Nota Débito ; D = Nota Crédito (según criterio de manual)
                          **kwargs
                          ):
        "Creo un objeto factura (internamente) e imprime el encabezado"

        # crear la estructura interna
        self.factura = {"encabezado": dict(
                            nombre_cliente   =   nombre_cliente,
                            tipo_doc         =   tipo_doc, 
                            nro_doc          =   nro_doc,
                            referencia       =   referencia,
                            nro_registro     =   nro_registro,
                            fecha_original   =   fecha_original,
                            hora_original    =   hora_original,                                            
                            tipo_cbte        =   tipo_cbte,
                            ),
                        "items": [], 
                        "pagos": []}
        printer = self.comando

        ret = False

        # enviar los comandos de apertura de comprobante fiscal:
        if tipo_cbte == 'A' :
            if (nro_doc and nombre_cliente):
                ret = printer.openTicket([nombre_cliente, nro_doc])
            else:
                ret = printer.openTicket([])

        elif ((tipo_cbte == 'B' or tipo_cbte =='D') and (nombre_cliente and nro_doc and referencia and nro_registro and fecha_original and hora_original)):
            ret = printer.openTicket([nombre_cliente, nro_doc, referencia, nro_registro, fecha_original, hora_original, tipo_cbte])
           
        return ret

    def _imprimirItem(self, ds, qty, importe, alic_iva = 0, itemNegative = False, discount = 0, discountDescription = '',
                      discountNegative=False, productCode=""):
        "Envia un item (descripcion, cantidad, etc.) a una factura"

        if importe < 0:
            importe = math.fabs(importe)
            itemNegative = True

        self.factura["items"].append(dict(
                                            ds              =       ds,
                                            qty             =       qty,
                                            importe         =       importe,
                                            alic_iva        =       alic_iva,
                                            itemNegative    =       itemNegative,
                                            discount        =       discount,
                                            discountDescription=discountDescription,
                                            discountNegative=discountNegative,
                                            productCode     =       productCode))

        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        if discountDescription == '':
            discountDescription = ds

        return self.comando.addItem(ds, float(qty), float(importe), float(alic_iva),
                                    itemNegative, float(discount), discountDescription, discountNegative, productCode)

    def _imprimirPago(self, ds, importe, codigo='1'):
        "Imprime una linea con la forma de pago y monto"
        self.factura["pagos"].append(dict(ds=ds, importe=importe, codigo=codigo))
        return self.comando.addPayment(ds, float(importe), str(codigo))
    
    def _cerrarComprobante(self, *args):
        "Envia el comando para cerrar un comprobante Fiscal"
        return self.comando.closeDocument()
