import http.server
import socketserver

PORT = 80

class server(http.server.SimpleHTTPRequestHandler):
    # Override the default log print flooding stdout
    def log_message(self, format, *args):
        pass

with socketserver.TCPServer(("", PORT), server) as httpd:
    httpd.serve_forever()

