import ssl
from celery_connectors.utils import ev


def build_ssl_options(ca_cert="",
                      keyfile="",
                      certfile="",
                      ssl_required="0"):

    use_ca_certs = ev("SSL_CA_CERT", ca_cert)
    use_keyfile = ev("SSL_KEYFILE", keyfile)
    use_certfile = ev("SSL_CERTFILE", certfile)
    use_ssl_required = ev("SSL_REQUIRED", ssl_required) == "1"

    ssl_options = {}
    if use_ca_certs:
        ssl_options["ca_certs"] = use_ca_certs
    if use_keyfile:
        ssl_options["keyfile"] = use_keyfile
    if use_certfile:
        ssl_options["certfile"] = use_certfile
    if use_ssl_required:
        ssl_options["cert_reqs"] = ssl.CERT_REQUIRED

    return ssl_options
# end of build_ssl_options
