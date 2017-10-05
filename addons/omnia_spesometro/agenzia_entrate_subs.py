#!/usr/bin/env python

#
# Generated Thu Oct  5 12:05:11 2017 by generateDS.py version 2.28b.
# Python 2.7.9 (default, Jun 29 2016, 13:08:31)  [GCC 4.9.2]
#
# Command line options:
#   ('-o', '/srv/workspace/odooAddons-7/addons/omnia_spesometro/agenzia_entrate.py')
#   ('-s', '/srv/workspace/odooAddons-7/addons/omnia_spesometro/agenzia_entrate_subs.py')
#
# Command line arguments:
#   /srv/workspace/odooAddons-7/addons/omnia_spesometro/agenzia_entrate.xsd
#
# Command line:
#   /usr/local/bin/generateDS.py -o "/srv/workspace/odooAddons-7/addons/omnia_spesometro/agenzia_entrate.py" -s "/srv/workspace/odooAddons-7/addons/omnia_spesometro/agenzia_entrate_subs.py" /srv/workspace/odooAddons-7/addons/omnia_spesometro/agenzia_entrate.xsd
#
# Current working directory (os.getcwd()):
#   omnia_spesometro
#

import sys
from lxml import etree as etree_

import ??? as supermod

def parsexml_(infile, parser=None, **kwargs):
    if parser is None:
        # Use the lxml ElementTree compatible parser so that, e.g.,
        #   we ignore comments.
        parser = etree_.ETCompatXMLParser()
    doc = etree_.parse(infile, parser=parser, **kwargs)
    return doc

#
# Globals
#

ExternalEncoding = 'ascii'

#
# Data representation classes
#


class DatiFatturaTypeSub(supermod.DatiFatturaType):
    def __init__(self, versione=None, DatiFatturaHeader=None, DTE=None, DTR=None, ANN=None, Signature=None):
        super(DatiFatturaTypeSub, self).__init__(versione, DatiFatturaHeader, DTE, DTR, ANN, Signature, )
supermod.DatiFatturaType.subclass = DatiFatturaTypeSub
# end class DatiFatturaTypeSub


class DatiFatturaHeaderTypeSub(supermod.DatiFatturaHeaderType):
    def __init__(self, ProgressivoInvio=None, Dichiarante=None, IdSistema=None):
        super(DatiFatturaHeaderTypeSub, self).__init__(ProgressivoInvio, Dichiarante, IdSistema, )
supermod.DatiFatturaHeaderType.subclass = DatiFatturaHeaderTypeSub
# end class DatiFatturaHeaderTypeSub


class DichiaranteTypeSub(supermod.DichiaranteType):
    def __init__(self, CodiceFiscale=None, Carica=None):
        super(DichiaranteTypeSub, self).__init__(CodiceFiscale, Carica, )
supermod.DichiaranteType.subclass = DichiaranteTypeSub
# end class DichiaranteTypeSub


class DTETypeSub(supermod.DTEType):
    def __init__(self, CedentePrestatoreDTE=None, CessionarioCommittenteDTE=None, Rettifica=None):
        super(DTETypeSub, self).__init__(CedentePrestatoreDTE, CessionarioCommittenteDTE, Rettifica, )
supermod.DTEType.subclass = DTETypeSub
# end class DTETypeSub


class DTRTypeSub(supermod.DTRType):
    def __init__(self, CessionarioCommittenteDTR=None, CedentePrestatoreDTR=None, Rettifica=None):
        super(DTRTypeSub, self).__init__(CessionarioCommittenteDTR, CedentePrestatoreDTR, Rettifica, )
supermod.DTRType.subclass = DTRTypeSub
# end class DTRTypeSub


class ANNTypeSub(supermod.ANNType):
    def __init__(self, IdFile=None, Posizione=None):
        super(ANNTypeSub, self).__init__(IdFile, Posizione, )
supermod.ANNType.subclass = ANNTypeSub
# end class ANNTypeSub


class CedentePrestatoreDTETypeSub(supermod.CedentePrestatoreDTEType):
    def __init__(self, IdentificativiFiscali=None, AltriDatiIdentificativi=None):
        super(CedentePrestatoreDTETypeSub, self).__init__(IdentificativiFiscali, AltriDatiIdentificativi, )
supermod.CedentePrestatoreDTEType.subclass = CedentePrestatoreDTETypeSub
# end class CedentePrestatoreDTETypeSub


class CedentePrestatoreDTRTypeSub(supermod.CedentePrestatoreDTRType):
    def __init__(self, IdentificativiFiscali=None, AltriDatiIdentificativi=None, DatiFatturaBodyDTR=None):
        super(CedentePrestatoreDTRTypeSub, self).__init__(IdentificativiFiscali, AltriDatiIdentificativi, DatiFatturaBodyDTR, )
supermod.CedentePrestatoreDTRType.subclass = CedentePrestatoreDTRTypeSub
# end class CedentePrestatoreDTRTypeSub


class CessionarioCommittenteDTETypeSub(supermod.CessionarioCommittenteDTEType):
    def __init__(self, IdentificativiFiscali=None, AltriDatiIdentificativi=None, DatiFatturaBodyDTE=None):
        super(CessionarioCommittenteDTETypeSub, self).__init__(IdentificativiFiscali, AltriDatiIdentificativi, DatiFatturaBodyDTE, )
supermod.CessionarioCommittenteDTEType.subclass = CessionarioCommittenteDTETypeSub
# end class CessionarioCommittenteDTETypeSub


class CessionarioCommittenteDTRTypeSub(supermod.CessionarioCommittenteDTRType):
    def __init__(self, IdentificativiFiscali=None, AltriDatiIdentificativi=None):
        super(CessionarioCommittenteDTRTypeSub, self).__init__(IdentificativiFiscali, AltriDatiIdentificativi, )
supermod.CessionarioCommittenteDTRType.subclass = CessionarioCommittenteDTRTypeSub
# end class CessionarioCommittenteDTRTypeSub


class DatiFatturaBodyDTETypeSub(supermod.DatiFatturaBodyDTEType):
    def __init__(self, DatiGenerali=None, DatiRiepilogo=None):
        super(DatiFatturaBodyDTETypeSub, self).__init__(DatiGenerali, DatiRiepilogo, )
supermod.DatiFatturaBodyDTEType.subclass = DatiFatturaBodyDTETypeSub
# end class DatiFatturaBodyDTETypeSub


class DatiFatturaBodyDTRTypeSub(supermod.DatiFatturaBodyDTRType):
    def __init__(self, DatiGenerali=None, DatiRiepilogo=None):
        super(DatiFatturaBodyDTRTypeSub, self).__init__(DatiGenerali, DatiRiepilogo, )
supermod.DatiFatturaBodyDTRType.subclass = DatiFatturaBodyDTRTypeSub
# end class DatiFatturaBodyDTRTypeSub


class RettificaTypeSub(supermod.RettificaType):
    def __init__(self, IdFile=None, Posizione=None):
        super(RettificaTypeSub, self).__init__(IdFile, Posizione, )
supermod.RettificaType.subclass = RettificaTypeSub
# end class RettificaTypeSub


class IdentificativiFiscaliTypeSub(supermod.IdentificativiFiscaliType):
    def __init__(self, IdFiscaleIVA=None, CodiceFiscale=None):
        super(IdentificativiFiscaliTypeSub, self).__init__(IdFiscaleIVA, CodiceFiscale, )
supermod.IdentificativiFiscaliType.subclass = IdentificativiFiscaliTypeSub
# end class IdentificativiFiscaliTypeSub


class IdentificativiFiscaliITTypeSub(supermod.IdentificativiFiscaliITType):
    def __init__(self, IdFiscaleIVA=None, CodiceFiscale=None):
        super(IdentificativiFiscaliITTypeSub, self).__init__(IdFiscaleIVA, CodiceFiscale, )
supermod.IdentificativiFiscaliITType.subclass = IdentificativiFiscaliITTypeSub
# end class IdentificativiFiscaliITTypeSub


class IdentificativiFiscaliNoIVATypeSub(supermod.IdentificativiFiscaliNoIVAType):
    def __init__(self, IdFiscaleIVA=None, CodiceFiscale=None):
        super(IdentificativiFiscaliNoIVATypeSub, self).__init__(IdFiscaleIVA, CodiceFiscale, )
supermod.IdentificativiFiscaliNoIVAType.subclass = IdentificativiFiscaliNoIVATypeSub
# end class IdentificativiFiscaliNoIVATypeSub


class AltriDatiIdentificativiNoSedeTypeSub(supermod.AltriDatiIdentificativiNoSedeType):
    def __init__(self, Denominazione=None, Nome=None, Cognome=None, Sede=None, StabileOrganizzazione=None, RappresentanteFiscale=None):
        super(AltriDatiIdentificativiNoSedeTypeSub, self).__init__(Denominazione, Nome, Cognome, Sede, StabileOrganizzazione, RappresentanteFiscale, )
supermod.AltriDatiIdentificativiNoSedeType.subclass = AltriDatiIdentificativiNoSedeTypeSub
# end class AltriDatiIdentificativiNoSedeTypeSub


class AltriDatiIdentificativiNoCAPTypeSub(supermod.AltriDatiIdentificativiNoCAPType):
    def __init__(self, Denominazione=None, Nome=None, Cognome=None, Sede=None, StabileOrganizzazione=None, RappresentanteFiscale=None):
        super(AltriDatiIdentificativiNoCAPTypeSub, self).__init__(Denominazione, Nome, Cognome, Sede, StabileOrganizzazione, RappresentanteFiscale, )
supermod.AltriDatiIdentificativiNoCAPType.subclass = AltriDatiIdentificativiNoCAPTypeSub
# end class AltriDatiIdentificativiNoCAPTypeSub


class IndirizzoNoCAPTypeSub(supermod.IndirizzoNoCAPType):
    def __init__(self, Indirizzo=None, NumeroCivico=None, CAP=None, Comune=None, Provincia=None, Nazione=None):
        super(IndirizzoNoCAPTypeSub, self).__init__(Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione, )
supermod.IndirizzoNoCAPType.subclass = IndirizzoNoCAPTypeSub
# end class IndirizzoNoCAPTypeSub


class IndirizzoTypeSub(supermod.IndirizzoType):
    def __init__(self, Indirizzo=None, NumeroCivico=None, CAP=None, Comune=None, Provincia=None, Nazione=None):
        super(IndirizzoTypeSub, self).__init__(Indirizzo, NumeroCivico, CAP, Comune, Provincia, Nazione, )
supermod.IndirizzoType.subclass = IndirizzoTypeSub
# end class IndirizzoTypeSub


class RappresentanteFiscaleTypeSub(supermod.RappresentanteFiscaleType):
    def __init__(self, IdFiscaleIVA=None, Denominazione=None, Nome=None, Cognome=None):
        super(RappresentanteFiscaleTypeSub, self).__init__(IdFiscaleIVA, Denominazione, Nome, Cognome, )
supermod.RappresentanteFiscaleType.subclass = RappresentanteFiscaleTypeSub
# end class RappresentanteFiscaleTypeSub


class RappresentanteFiscaleITTypeSub(supermod.RappresentanteFiscaleITType):
    def __init__(self, IdFiscaleIVA=None, Denominazione=None, Nome=None, Cognome=None):
        super(RappresentanteFiscaleITTypeSub, self).__init__(IdFiscaleIVA, Denominazione, Nome, Cognome, )
supermod.RappresentanteFiscaleITType.subclass = RappresentanteFiscaleITTypeSub
# end class RappresentanteFiscaleITTypeSub


class DatiGeneraliTypeSub(supermod.DatiGeneraliType):
    def __init__(self, TipoDocumento=None, Data=None, Numero=None):
        super(DatiGeneraliTypeSub, self).__init__(TipoDocumento, Data, Numero, )
supermod.DatiGeneraliType.subclass = DatiGeneraliTypeSub
# end class DatiGeneraliTypeSub


class DatiGeneraliDTRTypeSub(supermod.DatiGeneraliDTRType):
    def __init__(self, TipoDocumento=None, Data=None, Numero=None, DataRegistrazione=None):
        super(DatiGeneraliDTRTypeSub, self).__init__(TipoDocumento, Data, Numero, DataRegistrazione, )
supermod.DatiGeneraliDTRType.subclass = DatiGeneraliDTRTypeSub
# end class DatiGeneraliDTRTypeSub


class DatiRiepilogoTypeSub(supermod.DatiRiepilogoType):
    def __init__(self, ImponibileImporto=None, DatiIVA=None, Natura=None, Detraibile=None, Deducibile=None, EsigibilitaIVA=None):
        super(DatiRiepilogoTypeSub, self).__init__(ImponibileImporto, DatiIVA, Natura, Detraibile, Deducibile, EsigibilitaIVA, )
supermod.DatiRiepilogoType.subclass = DatiRiepilogoTypeSub
# end class DatiRiepilogoTypeSub


class DatiIVATypeSub(supermod.DatiIVAType):
    def __init__(self, Imposta=None, Aliquota=None):
        super(DatiIVATypeSub, self).__init__(Imposta, Aliquota, )
supermod.DatiIVAType.subclass = DatiIVATypeSub
# end class DatiIVATypeSub


class IdFiscaleTypeSub(supermod.IdFiscaleType):
    def __init__(self, IdPaese=None, IdCodice=None):
        super(IdFiscaleTypeSub, self).__init__(IdPaese, IdCodice, )
supermod.IdFiscaleType.subclass = IdFiscaleTypeSub
# end class IdFiscaleTypeSub


class IdFiscaleITTypeSub(supermod.IdFiscaleITType):
    def __init__(self, IdPaese=None, IdCodice=None):
        super(IdFiscaleITTypeSub, self).__init__(IdPaese, IdCodice, )
supermod.IdFiscaleITType.subclass = IdFiscaleITTypeSub
# end class IdFiscaleITTypeSub


class IdFiscaleITIvaTypeSub(supermod.IdFiscaleITIvaType):
    def __init__(self, IdPaese=None, IdCodice=None):
        super(IdFiscaleITIvaTypeSub, self).__init__(IdPaese, IdCodice, )
supermod.IdFiscaleITIvaType.subclass = IdFiscaleITIvaTypeSub
# end class IdFiscaleITIvaTypeSub


class SignatureTypeSub(supermod.SignatureType):
    def __init__(self, Id=None, SignedInfo=None, SignatureValue=None, KeyInfo=None, Object=None):
        super(SignatureTypeSub, self).__init__(Id, SignedInfo, SignatureValue, KeyInfo, Object, )
supermod.SignatureType.subclass = SignatureTypeSub
# end class SignatureTypeSub


class SignatureValueTypeSub(supermod.SignatureValueType):
    def __init__(self, Id=None, valueOf_=None):
        super(SignatureValueTypeSub, self).__init__(Id, valueOf_, )
supermod.SignatureValueType.subclass = SignatureValueTypeSub
# end class SignatureValueTypeSub


class SignedInfoTypeSub(supermod.SignedInfoType):
    def __init__(self, Id=None, CanonicalizationMethod=None, SignatureMethod=None, Reference=None):
        super(SignedInfoTypeSub, self).__init__(Id, CanonicalizationMethod, SignatureMethod, Reference, )
supermod.SignedInfoType.subclass = SignedInfoTypeSub
# end class SignedInfoTypeSub


class CanonicalizationMethodTypeSub(supermod.CanonicalizationMethodType):
    def __init__(self, Algorithm=None, anytypeobjs_=None, valueOf_=None, mixedclass_=None, content_=None):
        super(CanonicalizationMethodTypeSub, self).__init__(Algorithm, anytypeobjs_, valueOf_, mixedclass_, content_, )
supermod.CanonicalizationMethodType.subclass = CanonicalizationMethodTypeSub
# end class CanonicalizationMethodTypeSub


class SignatureMethodTypeSub(supermod.SignatureMethodType):
    def __init__(self, Algorithm=None, HMACOutputLength=None, anytypeobjs_=None, valueOf_=None, mixedclass_=None, content_=None):
        super(SignatureMethodTypeSub, self).__init__(Algorithm, HMACOutputLength, anytypeobjs_, valueOf_, mixedclass_, content_, )
supermod.SignatureMethodType.subclass = SignatureMethodTypeSub
# end class SignatureMethodTypeSub


class ReferenceTypeSub(supermod.ReferenceType):
    def __init__(self, Id=None, URI=None, Type=None, Transforms=None, DigestMethod=None, DigestValue=None):
        super(ReferenceTypeSub, self).__init__(Id, URI, Type, Transforms, DigestMethod, DigestValue, )
supermod.ReferenceType.subclass = ReferenceTypeSub
# end class ReferenceTypeSub


class TransformsTypeSub(supermod.TransformsType):
    def __init__(self, Transform=None):
        super(TransformsTypeSub, self).__init__(Transform, )
supermod.TransformsType.subclass = TransformsTypeSub
# end class TransformsTypeSub


class TransformTypeSub(supermod.TransformType):
    def __init__(self, Algorithm=None, anytypeobjs_=None, XPath=None, valueOf_=None, mixedclass_=None, content_=None):
        super(TransformTypeSub, self).__init__(Algorithm, anytypeobjs_, XPath, valueOf_, mixedclass_, content_, )
supermod.TransformType.subclass = TransformTypeSub
# end class TransformTypeSub


class DigestMethodTypeSub(supermod.DigestMethodType):
    def __init__(self, Algorithm=None, anytypeobjs_=None, valueOf_=None, mixedclass_=None, content_=None):
        super(DigestMethodTypeSub, self).__init__(Algorithm, anytypeobjs_, valueOf_, mixedclass_, content_, )
supermod.DigestMethodType.subclass = DigestMethodTypeSub
# end class DigestMethodTypeSub


class KeyInfoTypeSub(supermod.KeyInfoType):
    def __init__(self, Id=None, KeyName=None, KeyValue=None, RetrievalMethod=None, X509Data=None, PGPData=None, SPKIData=None, MgmtData=None, anytypeobjs_=None, valueOf_=None, mixedclass_=None, content_=None):
        super(KeyInfoTypeSub, self).__init__(Id, KeyName, KeyValue, RetrievalMethod, X509Data, PGPData, SPKIData, MgmtData, anytypeobjs_, valueOf_, mixedclass_, content_, )
supermod.KeyInfoType.subclass = KeyInfoTypeSub
# end class KeyInfoTypeSub


class KeyValueTypeSub(supermod.KeyValueType):
    def __init__(self, DSAKeyValue=None, RSAKeyValue=None, anytypeobjs_=None, valueOf_=None, mixedclass_=None, content_=None):
        super(KeyValueTypeSub, self).__init__(DSAKeyValue, RSAKeyValue, anytypeobjs_, valueOf_, mixedclass_, content_, )
supermod.KeyValueType.subclass = KeyValueTypeSub
# end class KeyValueTypeSub


class RetrievalMethodTypeSub(supermod.RetrievalMethodType):
    def __init__(self, URI=None, Type=None, Transforms=None):
        super(RetrievalMethodTypeSub, self).__init__(URI, Type, Transforms, )
supermod.RetrievalMethodType.subclass = RetrievalMethodTypeSub
# end class RetrievalMethodTypeSub


class X509DataTypeSub(supermod.X509DataType):
    def __init__(self, X509IssuerSerial=None, X509SKI=None, X509SubjectName=None, X509Certificate=None, X509CRL=None, anytypeobjs_=None):
        super(X509DataTypeSub, self).__init__(X509IssuerSerial, X509SKI, X509SubjectName, X509Certificate, X509CRL, anytypeobjs_, )
supermod.X509DataType.subclass = X509DataTypeSub
# end class X509DataTypeSub


class X509IssuerSerialTypeSub(supermod.X509IssuerSerialType):
    def __init__(self, X509IssuerName=None, X509SerialNumber=None):
        super(X509IssuerSerialTypeSub, self).__init__(X509IssuerName, X509SerialNumber, )
supermod.X509IssuerSerialType.subclass = X509IssuerSerialTypeSub
# end class X509IssuerSerialTypeSub


class PGPDataTypeSub(supermod.PGPDataType):
    def __init__(self, PGPKeyID=None, PGPKeyPacket=None, anytypeobjs_=None):
        super(PGPDataTypeSub, self).__init__(PGPKeyID, PGPKeyPacket, anytypeobjs_, )
supermod.PGPDataType.subclass = PGPDataTypeSub
# end class PGPDataTypeSub


class SPKIDataTypeSub(supermod.SPKIDataType):
    def __init__(self, SPKISexp=None, anytypeobjs_=None):
        super(SPKIDataTypeSub, self).__init__(SPKISexp, anytypeobjs_, )
supermod.SPKIDataType.subclass = SPKIDataTypeSub
# end class SPKIDataTypeSub


class ObjectTypeSub(supermod.ObjectType):
    def __init__(self, Id=None, MimeType=None, Encoding=None, anytypeobjs_=None, valueOf_=None, mixedclass_=None, content_=None):
        super(ObjectTypeSub, self).__init__(Id, MimeType, Encoding, anytypeobjs_, valueOf_, mixedclass_, content_, )
supermod.ObjectType.subclass = ObjectTypeSub
# end class ObjectTypeSub


class ManifestTypeSub(supermod.ManifestType):
    def __init__(self, Id=None, Reference=None):
        super(ManifestTypeSub, self).__init__(Id, Reference, )
supermod.ManifestType.subclass = ManifestTypeSub
# end class ManifestTypeSub


class SignaturePropertiesTypeSub(supermod.SignaturePropertiesType):
    def __init__(self, Id=None, SignatureProperty=None):
        super(SignaturePropertiesTypeSub, self).__init__(Id, SignatureProperty, )
supermod.SignaturePropertiesType.subclass = SignaturePropertiesTypeSub
# end class SignaturePropertiesTypeSub


class SignaturePropertyTypeSub(supermod.SignaturePropertyType):
    def __init__(self, Target=None, Id=None, anytypeobjs_=None, valueOf_=None, mixedclass_=None, content_=None):
        super(SignaturePropertyTypeSub, self).__init__(Target, Id, anytypeobjs_, valueOf_, mixedclass_, content_, )
supermod.SignaturePropertyType.subclass = SignaturePropertyTypeSub
# end class SignaturePropertyTypeSub


class DSAKeyValueTypeSub(supermod.DSAKeyValueType):
    def __init__(self, P=None, Q=None, G=None, Y=None, J=None, Seed=None, PgenCounter=None):
        super(DSAKeyValueTypeSub, self).__init__(P, Q, G, Y, J, Seed, PgenCounter, )
supermod.DSAKeyValueType.subclass = DSAKeyValueTypeSub
# end class DSAKeyValueTypeSub


class RSAKeyValueTypeSub(supermod.RSAKeyValueType):
    def __init__(self, Modulus=None, Exponent=None):
        super(RSAKeyValueTypeSub, self).__init__(Modulus, Exponent, )
supermod.RSAKeyValueType.subclass = RSAKeyValueTypeSub
# end class RSAKeyValueTypeSub


def get_root_tag(node):
    tag = supermod.Tag_pattern_.match(node.tag).groups()[-1]
    rootClass = None
    rootClass = supermod.GDSClassesMapping.get(tag)
    if rootClass is None and hasattr(supermod, tag):
        rootClass = getattr(supermod, tag)
    return tag, rootClass


def parse(inFilename, silence=False):
    parser = None
    doc = parsexml_(inFilename, parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'DatiFatturaType'
        rootClass = supermod.DatiFatturaType
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    if not silence:
        sys.stdout.write('<?xml version="1.0" ?>\n')
        rootObj.export(
            sys.stdout, 0, name_=rootTag,
            namespacedef_='',
            pretty_print=True)
    return rootObj


def parseEtree(inFilename, silence=False):
    parser = None
    doc = parsexml_(inFilename, parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'DatiFatturaType'
        rootClass = supermod.DatiFatturaType
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    mapping = {}
    rootElement = rootObj.to_etree(None, name_=rootTag, mapping_=mapping)
    reverse_mapping = rootObj.gds_reverse_node_mapping(mapping)
    if not silence:
        content = etree_.tostring(
            rootElement, pretty_print=True,
            xml_declaration=True, encoding="utf-8")
        sys.stdout.write(content)
        sys.stdout.write('\n')
    return rootObj, rootElement, mapping, reverse_mapping


def parseString(inString, silence=False):
    from StringIO import StringIO
    parser = None
    doc = parsexml_(StringIO(inString), parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'DatiFatturaType'
        rootClass = supermod.DatiFatturaType
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    if not silence:
        sys.stdout.write('<?xml version="1.0" ?>\n')
        rootObj.export(
            sys.stdout, 0, name_=rootTag,
            namespacedef_='')
    return rootObj


def parseLiteral(inFilename, silence=False):
    parser = None
    doc = parsexml_(inFilename, parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'DatiFatturaType'
        rootClass = supermod.DatiFatturaType
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    if not silence:
        sys.stdout.write('#from ??? import *\n\n')
        sys.stdout.write('import ??? as model_\n\n')
        sys.stdout.write('rootObj = model_.rootClass(\n')
        rootObj.exportLiteral(sys.stdout, 0, name_=rootTag)
        sys.stdout.write(')\n')
    return rootObj


USAGE_TEXT = """
Usage: python ???.py <infilename>
"""


def usage():
    print(USAGE_TEXT)
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        usage()
    infilename = args[0]
    parse(infilename)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()
