import http.server
import socketserver

PORT = 4842
Address_="0.0.0.0"
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer((Address_, PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
