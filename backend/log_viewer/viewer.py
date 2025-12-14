import http.server
import socketserver
import json
import os
import re

PORT = 8080
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'security_logs', 'security.log')

class LogViewerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/logs':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            logs = []
            if os.path.exists(LOG_FILE_PATH):
                with open(LOG_FILE_PATH, 'r') as f:
                    # Read lines in reverse order to show newest first
                    lines = f.readlines()[::-1]
                    for line in lines:
                        # Simple regex to parse standard logging format
                        # 2023-10-27 10:00:00,000 - LEVEL - Message
                        match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.*)', line)
                        if match:
                            logs.append({
                                'timestamp': match.group(1),
                                'level': match.group(2),
                                'message': match.group(3)
                            })
                        else:
                             # Handle unformatted lines or stack traces gracefully
                            logs.append({
                                'timestamp': '',
                                'level': 'UNKNOWN',
                                'message': line.strip()
                            })
            
            self.wfile.write(json.dumps(logs).encode())
        elif self.path == '/':
            self.path = '/index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        else:
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == "__main__":
    # Change directory to the location of this script so index.html is found
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), LogViewerHandler) as httpd:
        print(f"Serving Security Log Viewer at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
