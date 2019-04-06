import time
from threading import Thread
try:
    import socketserver as SocketServer
    import http.server as SimpleHTTPServer
except ImportError:
    import SocketServer
    import SimpleHTTPServer


ARCHIVE = []


def log_info(info):
    print('-----------------------------------------------------')
    print('                      REQUEST                        ')
    print('-----------------------------------------------------')
    print('METHOD:...........' + info['http_method'])
    print('PATH:.............' + info['path'])
    for header in info['headers']:
        for key, value in header.items():
            print('HEADER:...........' + str(key) + ': ' + str(value))
    print('DATA:.............' + str(info['data']))
    print('-----------------------------------------------------\n')


class PactResponse(object):
    body = None
    headers = []
    status = 500

    def __init__(self, status=None, body=None, headers=None):
        self.body = body or self.body
        self.status = status or self.status
        self.headers = headers or self.headers

    def __str__(self):
        return "STATUS: " + str(self.status) + ", HEADERS: " + str(self.headers) + ", BODY: " + str(self.body)


def ProxyFactory(mock_response=PactResponse()):
    class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
        mock_response = None

        def __init__(self, *args, **kwargs):
            super(Proxy, self).__init__(*args, **kwargs)
            self.mock_response = mock_response

        def do_GET(self):
            data = self.read_request_data(self)
            self.handle_request('GET', data)

        def do_POST(self):
            data = self.read_request_data(self)
            self.handle_request('POST', data)

        def do_PUT(self):
            data = self.read_request_data(self)
            self.handle_request('PUT', data)

        def do_DELETE(self):
            data = self.read_request_data(self)
            self.handle_request('DELETE', data)

        def read_request_data(self, other_self):
            header_value = other_self.headers['Content-Length']
            data_length = int(
                header_value) if header_value is not None else None
            return other_self.rfile.read(data_length) if data_length is not None else None

        def info(self, http_method, data):
            info = {
                'http_method': http_method,
                'path': self.path,
                'data': data,
                'headers': []
            }
            for key, value in self.headers.items():
                info['headers'].append(dict([(key, value)]))
            return info

        def handle_request(self, http_method, data):
            info = self.info(http_method, data)
            ARCHIVE.append(info)
            self.respond()

        def respond(self):
            self.send_response(int(mock_response.status))
            for header in mock_response.headers:
                for key, value in header.items():
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(str(mock_response.body).encode())

    return Proxy


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


class ProxyBox(object):

    def __init__(self, mock_response=PactResponse(), base_url='0.0.0.0', port=1234):
        self.port = port
        self.base_url = base_url
        ProxyClass = ProxyFactory(mock_response)
        self.server = ThreadedTCPServer((self.base_url, self.port), ProxyClass)
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True

    def start(self):
        self.server_thread.start()
        print('PROXY SERVER LISTENING ON http://' +
              self.base_url + ':' + str(self.port))
        print('===================================')

    def shutdown(self):
        print('=====================================================')
        print('                       ARCHIVE                       ')
        print('=====================================================')
        for item in ARCHIVE:
            log_info(item)
        self.server.shutdown()
        self.server.server_close()


box = ProxyBox(PactResponse(
    status=201,
    headers=[{'Content-Type': 'application/json'}, {'X-Spam': 'eggs'}],
    body='{"hallo": "world", "ciao": "mondo", "ni hao": "shie jie"}'
))

box.start()
time.sleep(10)
box.shutdown()
