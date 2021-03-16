# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solutions
#    Copyright (C) 2011-2021 https://OmniaSolutions.website
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 15 Mar 2021

@author: mboscolo
'''
import os
import logging
import glob
import zipfile
import tempfile
import ftplib
import datetime
import hashlib
import ssl
import socket

IPDV_TEMPLATE_FILE = """
        <file>
            <docid>{DOCID}</docid>
            <filename>{FILENAME}</filename>
            <mimetype>{MIMETYPE}</mimetype>
            <closingDate>{CLOSING_DATE}</closingDate>
            <hash algorithm="SHA-256">
                <value>{HASH}</value>
            </hash>
            <metadata>
                <mandatory>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>dataDocumentoTributario</name>
                        <value>{DATA_DOCUMENTO_TRIBUTARIA}</value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>oggettodocumento</name>
                        <value>fatturapa</value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>dataDocumento</name>
                        <value>{DATA_DOCUMENTO}</value>
                    </singlemetadata>
                    <complexmetadata namespace="conservazione.doc" name="soggettotributario" namespaceNode="conservazione.soggetti" nodeName="soggetto">
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>codicefiscale</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>cognome</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>denominazione</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>nome</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>partitaiva</name>
                            <value></value>
                        </singlemetadata>
                    </complexmetadata>
                    <complexmetadata namespace="conservazione.doc" name="destinatario" namespaceNode="conservazione.soggetti" nodeName="soggetto">
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>codicefiscale</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>cognome</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>denominazione</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>nome</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>partitaiva</name>
                            <value></value>
                        </singlemetadata>
                    </complexmetadata>
                    <complexmetadata namespace="conservazione.doc" name="soggettoproduttore" namespaceNode="conservazione.soggetti" nodeName="soggetto">
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>codicefiscale</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>cognome</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>denominazione</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>nome</name>
                            <value></value>
                        </singlemetadata>
                        <singlemetadata>
                            <namespace>conservazione.soggetti</namespace>
                            <name>partitaiva</name>
                            <value></value>
                        </singlemetadata>
                    </complexmetadata>
                </mandatory>
                <extrainfos>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>idDocumentoOriginale</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>pid</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>idFascicolo</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>idOrigine</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>tipologia</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.nostoredExt</namespace>
                        <name>externalCode</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>codiceTipologia</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>tipoNotifica</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>numeroFattura</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>soggettoImposta</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>ddt</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>notaAccredito</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>progressivo</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>sezionale</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>nomeSezionale</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>applicativoProduzione</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>idSistemaVersante</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>condizioniAccesso</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>esito</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>livelloRiservatezza</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>cfTitolareFirma</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>allegato1</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>allegato2</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>note1</name>
                        <value></value>
                    </singlemetadata>
                    <singlemetadata>
                        <namespace>conservazione.doc</namespace>
                        <name>note2</name>
                        <value></value>
                    </singlemetadata>
                </extrainfos>
            </metadata>
        </file>
"""

IPDV_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<PDV>
    <pdvid>{PDVID}</pdvid>
    <docClass namespace="conservazione.doc">1__fatturaPA</docClass>
    <files>
    {FILE}
    </files>
</PDV>"""

def sha256_64(file_name):
    sha256_hash = hashlib.sha256()
    with open(file_name,"rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.digest().encode('base64').strip()

def generatePDVFile(pdv_name, xmlFile):
    xml_file_name = os.path.basename(xmlFile)
    d = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    newValue = {'DOCID':"ID_%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%s%f"),
                'FILENAME': xml_file_name,
                'MIMETYPE': 'text/xml',
                'CLOSING_DATE': d, #@yyyy-mm-ddThh:mm:ss.sssZ@
                'HASH': sha256_64(xmlFile), # md5(xmlFile),
                'DATA_DOCUMENTO_TRIBUTARIA': d,
                'DATA_DOCUMENTO': d,#2021-03-13T08:02:00.000Z
                }
    return IPDV_TEMPLATE_FILE.format(**newValue)

def generatePDV(base_file, pdv_name, files):
    pdv_file_name = os.path.join(base_file, "IPDV-%s.xml" % pdv_name)
    newValue = {'PDVID': pdv_name,
                'FILE': files}
    newIpdv = IPDV_TEMPLATE.format(**newValue) 
    with open(pdv_file_name, 'wb') as f:
        f.write(newIpdv)
    return pdv_file_name

FTPTLS_OBJ = ftplib.FTP_TLS

# Class to manage implicit FTP over TLS connections, with passive transfer mode
# - Important note:
#   If you connect to a VSFTPD server, check that the vsftpd.conf file contains
#   the property require_ssl_reuse=NO
class FTPTLS(FTPTLS_OBJ):
    host = "127.0.0.1"
    port = 990
    user = "anonymous"
    timeout = 60
    logLevel = 0

    # Init both this and super
    def __init__(self, host=None, user=None, passwd=None, acct=None, keyfile=None, certfile=None, context=None, timeout=60):        
        try:
            FTPTLS_OBJ.__init__(self, host, user, passwd, acct, keyfile, certfile, context, timeout)
        except Exception as ex:
            logging.warning('Cannot make FTPTLS_OBJ init due to error %r' % (ex))
            FTPTLS_OBJ.__init__(self, host, user, passwd, acct, timeout)
        self.codice_fiscale='' 

    # Custom function: Open a new FTPS session (both connection & login)
    def openSession(self, host="127.0.0.1", port=990, user="anonymous", password=None, timeout=60):
        self.user = user
        # connect()
        ret = self.connect(host, port, timeout)
        # prot_p(): Set up secure data connection.
        try:
            ret = self.prot_p()
            if (self.logLevel > 1): self._log("INFO - FTPS prot_p() done: " + ret)
        except Exception as e:
            if (self.logLevel > 0): self._log("ERROR - FTPS prot_p() failed - " + str(e))
            raise e
        # login()
        try:
            ret = self.login(user=user, passwd=password)
            if (self.logLevel > 1): self._log("INFO - FTPS login() done: " + ret)
        except Exception as e:
            if (self.logLevel > 0): self._log("ERROR - FTPS login() failed - " + str(e))
            raise e
        if (self.logLevel > 1): self._log("INFO - FTPS session successfully opened")

    # Override function
    def connect(self, host="127.0.0.1", port=990, timeout=60):
        self.host = host
        self.port = port
        self.timeout = timeout
        try:
            self.sock = socket.create_connection((self.host, self.port), self.timeout)
            self.af = self.sock.family
            self.sock = ssl.wrap_socket(self.sock, self.keyfile, self.certfile)
            self.file = self.sock.makefile('r')
            self.welcome = self.getresp()
            if (self.logLevel > 1): self._log("INFO - FTPS connect() done: " + self.welcome)
        except Exception as e:
            if (self.logLevel > 0): self._log("ERROR - FTPS connect() failed - " + str(e))
            raise e
        return self.welcome

    # Override function
    def makepasv(self):
        host, port = FTPTLS_OBJ.makepasv(self)
        # Change the host back to the original IP that was used for the connection
        host = socket.gethostbyname(self.host)
        return host, port

    # Custom function: Close the session
    def closeSession(self):
        try:
            self.close()
            if (self.logLevel > 1): self._log("INFO - FTPS close() done")
        except Exception as e:
            if (self.logLevel > 0): self._log("ERROR - FTPS close() failed - " + str(e))
            raise e
        if (self.logLevel > 1): self._log("INFO - FTPS session successfully closed")

    # Private method for logs
    def _log(self, msg):
        # Be free here on how to implement your own way to redirect logs (e.g: to a console, to a file, etc.)
        print(msg)
    
    def cdTree(self, currentDir):
        if currentDir != "":
            try:
                self.cwd(currentDir)
            except:
                self.cdTree("/".join(currentDir.split("/")[:-1]))
                self.mkd(currentDir)
                self.cwd(currentDir)
                
    def push_to_aruba(self, pdv_name, xml_source):
        logging.info("Push to ftp %s" % xml_source)
        logging.info("Current Directory is %s" % self.pwd())
        to_write = "/%s/%s" % (self.codice_fiscale, pdv_name)
        self.cdTree(to_write)
        self.cwd(to_write)
        with open(xml_source,'rb') as file:                                     # file to send
            self.storbinary('STOR %s' % os.path.basename(xml_source), file)     # send the file
            
            
            
            
            