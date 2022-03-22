# -*- coding: iso-8859-1 -*-
import string
import types
import json
from Comandos.ComandoFiscalInterface import ComandoFiscalInterface
from ComandoInterface import formatText, ComandoException
from Drivers.FiscalPrinterDriver import PrinterException
import logging

logger = logging.getLogger(__name__)


class FiscalPrinterError(Exception):
    pass


class EpsonPanamaComandos(ComandoFiscalInterface):
    # el traductor puede ser: TraductorFiscal o TraductorReceipt
    # path al modulo de traductor que este comando necesita
    traductorModule = "Traductores.TraductorFiscalPanama"

    _currentDocument = None
    _currentDocumentType = None

    DEFAULT_DRIVER = "Epson"

    DEBUG = True

    CMD_OPEN_FISCAL_RECEIPT     = 0x40    
    CMD_PRINT_TEXT_IN_FISCAL    = 0x41
    CMD_PRINT_LINE_ITEM         = (0x42, 0x62)
    CMD_PRINT_SUBTOTAL          = (0x43, 0x63)
    CMD_ADD_PAYMENT             = (0x44, 0x64)
    CMD_CLOSE_FISCAL_RECEIPT    = (0x45, 0x65)

    CMD_DAILY_CLOSE             = 0x39

    CMD_STATUS_REQUEST          = 0x2a

    CMD_PRINT_AUDITORIA         = 0x3b

    CMD_OPEN_DRAWER             = 0x7b

    CMD_SET_HEADER_TRAILER      = 0x5d

    CMD_OPEN_NON_FISCAL_RECEIPT = 0x48
    CMD_PRINT_NON_FISCAL_TEXT   = 0x49
    CMD_CLOSE_NON_FISCAL_RECEIPT = 0x4a

    CURRENT_DOC_TICKET = 1
    CURRENT_DOC_BILL_TICKET = 2
    CURRENT_DOC_CREDIT_TICKET = 4
    CURRENT_DOC_NON_FISCAL = 3

    models = [
        "tickeadoras", 
        "epsonlx300+", 
        "tm-220-af", 
        "tm-t900fa"
        ]

    
    def start(self):
        pass

    def close(self):
        pass

    def _sendCommand(self, commandNumber, parameters, skipStatusErrors=False):
        print("_sendCommand", commandNumber, parameters)
        try:
            logger.debug("sendCommand: SEND|0x%x|%s|%s" % (commandNumber,
                                                                       skipStatusErrors and "T" or "F",
                                                                       str(parameters)))
            return self.conector.sendCommand(commandNumber, parameters, skipStatusErrors)
        except PrinterException as e:
            logger.exception("PrinterException: %s" % str(e))
            raise ComandoException("Error de la impresora fiscal: " + str(e))

    def openNonFiscalReceipt(self):
        status = self._sendCommand(self.CMD_OPEN_NON_FISCAL_RECEIPT, [])
        self._currentDocument = self.CURRENT_DOC_NON_FISCAL
        self._currentDocumentType = None
        return status

    def printNonFiscalText(self, text):
        return self._sendCommand(self.CMD_PRINT_NON_FISCAL_TEXT, [formatText(text[:40] or " ")])

    ADDRESS_SIZE = 30

    def setHeader(self, header=None):
        "Establecer encabezados"
        if not header:
            header = []
        line = 3
        for text in (header + [chr(0x7f)] * 3)[:3]:  # Agrego chr(0x7f) (DEL) al final para limpiar las
            # líneas no utilizadas
            self._setHeaderTrailer(line, text)
            line += 1

    def _setHeaderTrailer(self, line, text):
        self._sendCommand(self.CMD_SET_HEADER_TRAILER, (str(line), text))

    def setTrailer(self, trailer = None):
        "Establecer pie"
        if not trailer:
            trailer = []
        line = 11
        for text in (trailer + [chr(0x7f)] * 9)[:9]:
            self._setHeaderTrailer(line, text)
            line += 1

    def _getCommandIndex(self):
        if self._currentDocument == self.CURRENT_DOC_TICKET:
            return 0
        elif self._currentDocument in (self.CURRENT_DOC_BILL_TICKET, self.CURRENT_DOC_CREDIT_TICKET):
            return 1
        elif self._currentDocument == self.CURRENT_DOC_NON_FISCAL:
            return 2

    def openTicket(self, params):
        self._sendCommand(self.CMD_OPEN_FISCAL_RECEIPT, params)    #   params == Array con [Razón Social, RUC] o [vacio]
        self._currentDocument = self.CURRENT_DOC_TICKET

    def closeDocument(self):
        if self._currentDocument == self.CURRENT_DOC_TICKET:
            reply = self._sendCommand(self.CMD_CLOSE_FISCAL_RECEIPT[self._getCommandIndex()], ["T"])
            return reply[2]
        
        if self._currentDocument in (self.CURRENT_DOC_NON_FISCAL,):
            return self._sendCommand(self.CMD_CLOSE_NON_FISCAL_RECEIPT, ["T"], True)

        raise NotImplementedError

    def cancelDocument(self):
        if self._currentDocument in (self.CURRENT_DOC_TICKET, self.CURRENT_DOC_BILL_TICKET,
                                     self.CURRENT_DOC_CREDIT_TICKET):
            status = self._sendCommand(self.CMD_ADD_PAYMENT[self._getCommandIndex()], ["Cancelar", "0", 'C'])
            return status
        if self._currentDocument in (self.CURRENT_DOC_NON_FISCAL,):
            self.printNonFiscalText("CANCELADO")
            return self.closeDocument()
        #Esto es por si alguna razon un printTicket quedo sin completarse. Ya que si no, no hay manera de cancelar el documento abierto
        self.cancelAnyDocument()
        return []
        #raise NotImplementedError 

    def __addItemPiceUnitStr(self, price):
        return "%0.4f" % price

    def __addItemParams(self, description, quantityStr, priceUnitStr, ivaStr, sign, productCode):
        return [formatText(description[-1][:20]),
                                   quantityStr, priceUnitStr, ivaStr, sign, productCode]

    def addItem(self, description, quantity, price, iva, itemNegative=False, discount=0, discountDescription='',
                discountNegative=True, productCode=""):
        if type(description) in types.StringTypes:
            description = [description]
        if itemNegative:
            sign = 'm'
        else:
            sign = 'M'

        quantityStr = str(int(quantity * 1000))        
                
        priceUnitStr = self.__addItemPiceUnitStr(price)

        ivaStr = str(int(iva * 100))
        extraparams = self._currentDocument in (self.CURRENT_DOC_BILL_TICKET,
                                                self.CURRENT_DOC_CREDIT_TICKET) and ["", "", ""] or []
        if self._getCommandIndex() == 0:
            for d in description[:-1]:
                self._sendCommand(self.CMD_PRINT_TEXT_IN_FISCAL,
                                  [formatText(d)[:20]])

        params = self.__addItemParams(description, quantityStr, priceUnitStr, ivaStr, sign, productCode)
        logger.info("Imprimiendo item ...................")
        logger.info(self)
        reply = self._sendCommand(self.CMD_PRINT_LINE_ITEM[self._getCommandIndex()],params + extraparams)

        if discount:
            discountStr = str(int(discount * 100))
            self._sendCommand(self.CMD_PRINT_LINE_ITEM[self._getCommandIndex()],
                              [formatText(discountDescription[:20]), "1000",
                               discountStr, ivaStr, 'm', "0", "0"] + extraparams)
        return reply

    def addPayment(self, description, payment, code):
        paymentStr = str(int(payment * 100))
        if code == "":
            code ='1'
        status = self._sendCommand(self.CMD_ADD_PAYMENT[self._getCommandIndex()],
                                   [formatText(description)[:20], paymentStr, 'T', code])
        return status

    
    # def addAdditional(self, description, amount, iva, negative=False):
    #     """Agrega un adicional a la FC.
    #         @param description  Descripción
    #         @param amount       Importe (sin iva en FC A, sino con IVA)
    #         @param iva          Porcentaje de Iva
    #         @param negative True->Descuento, False->Recargo"""
    #     if negative:
    #         if not description:
    #             description = "Descuento"
    #         sign = 'm'
    #     else:
    #         if not description:
    #             description = "Recargo"
    #         sign = 'M'

    #     quantityStr = "1000"
    #     bultosStr = "0"
    #     priceUnit = amount
    #     if self._currentDocumentType != 'A':
    #         # enviar con el iva incluido
    #         priceUnitStr = str(int(round(priceUnit * 100, 0)))
    #     else:
    #         # enviar sin el iva (factura A)
    #         priceUnitStr = str(int(round((priceUnit / ((100 + iva) / 100)) * 100, 0)))
    #     ivaStr = str(int(iva * 100))
    #     extraparams = self._currentDocument in (self.CURRENT_DOC_BILL_TICKET,
    #                                             self.CURRENT_DOC_CREDIT_TICKET) and ["", "", ""] or []
    #     reply = self._sendCommand(self.CMD_PRINT_LINE_ITEM[self._getCommandIndex()],
    #                               [formatText(description[:20]),
    #                                quantityStr, priceUnitStr, ivaStr, sign, bultosStr, "0"] + extraparams)
    #     return reply

    def dailyClose(self, type):
        reply = self._sendCommand(self.CMD_DAILY_CLOSE, [type, "P"])
        print(reply)
        return reply[2:]

    def getLastNumber(self, letter):
        reply = self._sendCommand(self.CMD_STATUS_REQUEST, ["A"], True)
        if len(reply) < 3:
            # La respuesta no es válida. Vuelvo a hacer el pedido y si hay algún error que se reporte como excepción
            reply = self._sendCommand(self.CMD_STATUS_REQUEST, ["A"], False)
        if letter == "A":
            return int(reply[6])
        else:
            return int(reply[4])

    def getStatus(self):
        reply = self._sendCommand(self.CMD_STATUS_REQUEST, [], False)
        return reply

    def getLastCreditNoteNumber(self, letter):
        reply = self._sendCommand(self.CMD_STATUS_REQUEST, ["A"], True)
        if len(reply) < 3:
            # La respuesta no es válida. Vuelvo a hacer el pedido y si hay algún error que se reporte como excepción
            reply = self._sendCommand(self.CMD_STATUS_REQUEST, ["A"], False)
        if letter == "A":
            return int(reply[10])
        else:
            return int(reply[11])

    def cancelAnyDocument(self):
        try:
            self._sendCommand(self.CMD_ADD_PAYMENT[0], ["Cancelar", "0", 'C'])
            return True
        except:
            pass
        try:
            self._sendCommand(self.CMD_ADD_PAYMENT[1], ["Cancelar", "0", 'C'])
            return True
        except:
            pass
        try:
            self._sendCommand(self.CMD_CLOSE_NON_FISCAL_RECEIPT, ["T"])
            return True
        except:
            pass
        return False

    def getWarnings(self):
        ret = []
        reply = self._sendCommand(self.CMD_STATUS_REQUEST, ["N"], True)
        printerStatus = reply[0]
        x = int(printerStatus, 16)
        if ((1 << 4) & x) == (1 << 4):
            ret.append("Poco papel para la cinta de auditoria")
        if ((1 << 5) & x) == (1 << 5):
            ret.append("Poco papel para comprobantes o tickets")
        return ret

    def imprimirAuditoria(self, desde, hasta):
        #desde & Hasta = Nros de Zeta o fechas, ambos pueden ser usados como intervalos de tiempo.
        #la 'D' significa que quiero que imprima un reporte detallado.
        reply = self._sendCommand(self.CMD_PRINT_AUDITORIA, [desde, hasta, 'D'])
        return reply

    def openDrawer(self):
        reply = self._sendCommand(self.CMD_OPEN_DRAWER, [])
        return reply

    def __del__(self):
        try:
            self.close()
        except:
            pass