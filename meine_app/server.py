from http.server import SimpleHTTPRequestHandler, HTTPServer
import socket
import os
from datetime import datetime

class IPv6HTTPServer(HTTPServer):
    address_family = socket.AF_INET6

class UploadHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        file_data = self.rfile.read(content_length)
        
        # 1. Generiere einen Zeitstempel (z.B. 20260527_175512)
        zeitstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 2. Erstelle den neuen, einzigartigen Dateinamen
        datei_name = f"verbindungs_{zeitstempel}.mp3"
        
        # Pfad für deine App
        ziel_ordner = "/var/www/walki-talki/meine_app/media"
        ziel_datei = os.path.join(ziel_ordner, datei_name)
        
        # 3. Speichert die neue MP3-Datei ab
        with open(ziel_datei, "wb") as f:
            f.write(file_data)
            
        print(f"\n[INFO] --> Neue Datei erfolgreich gespeichert:")
        print(f"         {ziel_datei}")
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MP3 erfolgreich als neue Datei gespeichert!")

# Server starten auf Port 8000
server = IPv6HTTPServer(('::', 8000), UploadHandler)
print("==========================================================")
print("Server laeuft unter /var/www/walki-talki/meine_app/")
print("Speichert jede Aufnahme als NEUE Datei mit Zeitstempel ab.")
print("==========================================================")
server.serve_forever()
