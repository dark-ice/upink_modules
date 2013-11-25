import xmlrpclib

__author__ = 'andrey'


class CookieTransport(xmlrpclib.Transport):
    '''
    Adds to request all cookies from previous request
    '''
    def __init__(self, api_key='6be7bf92c3e2508e328efdcdfb0d1b59'):
        xmlrpclib.Transport.__init__(self)
        self.cookie = None
        self.api_key = api_key

    def single_request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request

        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)

        try:
            self.send_request(h, handler, request_body)
            self.send_host(h, host)
            self.send_user_agent(h)

            if not self.api_key is None:
                h.putheader("Cookie", "api_key=%s" % self.api_key)

            self.send_user_agent(h)
            self.send_content(h, request_body)

            self.verbose = verbose
            response = h.getresponse(buffering=True)
            return self.parse_response(response)

        except xmlrpclib.Fault:
            raise

        except Exception:
            # All unexpected errors leave connection in
            # a strange state, so we clear it.
            self.close()
            raise

proxy = xmlrpclib.ServerProxy("http://allpositions.ru:80/api/", transport=CookieTransport(), encoding='UTF-8')
print proxy.system.listMethods()
print proxy.get_project(10779)