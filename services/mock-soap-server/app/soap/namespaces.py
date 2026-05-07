import xml.etree.ElementTree as ET


SOAP_ENV_NS = "http://schemas.xmlsoap.org/soap/envelope/"
COMPLIANCE_NS = "http://gov.example/regulatory/compliance"

ET.register_namespace("soapenv", SOAP_ENV_NS)
ET.register_namespace("com", COMPLIANCE_NS)


def qualified(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
