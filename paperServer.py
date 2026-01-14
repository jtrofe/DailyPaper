#=================================#
# Imports for creating the server #
#=================================#
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import json

# Replacement for cgi.parse_header
# it's stupid but recommended https://peps.python.org/pep-0594/#cgi
from email.message import Message

#================================#
# Imports for managing the files #
#================================#
from paper import CreatePaperHTML

#==================#
# Global variables #
#==================#
hostName = '0.0.0.0'
serverPort = 8080

class PaperServer(BaseHTTPRequestHandler):
    def send404(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'404 - Not Found')
    
    def sendHTML(self, html):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(html, 'utf-8'))
    
    def do_GET(self):
        print(self.path)
        
        if self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-Type', 'image/x-icon')
            self.send_header('Content-Length', 0)
            self.end_headers()
            return
        elif self.path == '/':
            html = CreatePaperHTML()
            self.sendHTML(html)
        else:
            print(f'    Loading file {self.path[1:]}')
            with open(self.path[1:], 'rb') as f:
                self.send_response(200)
                #self.send_header('Content-type', 'text/html')
                #self.end_headers()
                self.wfile.write(f.read())
    
    def do_POST(self):
        # TODO maybe in the future? Maybe allow other strips to be added this way?
        # Probably not. Comics.json is easy enough to edit
        pass

if __name__ == '__main__':
    webServer = HTTPServer((hostName, serverPort), PaperServer) 
    ip = socket.gethostbyname(socket.gethostname())
    link = f'http://{ip}:{serverPort}'
    print(f'Started: {link}')
    
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print('Server stopped.')