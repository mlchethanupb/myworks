import http.server
import socketserver

PORT = 4840
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("131.234.28.250", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
