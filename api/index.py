import json
import os
import numpy as np
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    
    def _cors_headers(self):
        # This guarantees the headers are identical for GET, POST, and OPTIONS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        # If the bot sends a GET request to check the URL, give it the CORS headers
        self.send_response(200)
        self._cors_headers()
        self.end_headers()
        self.wfile.write(b"Endpoint is active")

    def do_POST(self):
        try:
            # 1. Load data
            DATA_PATH = os.path.join(os.path.dirname(__file__), 'q-vercel-latency.json')
            with open(DATA_PATH) as f:
                DATA = json.load(f)

            # 2. Parse request
            content_length = int(self.headers.get('Content-Length', 0))
            body_string = self.rfile.read(content_length).decode('utf-8')
            
            # Failsafe if the bot sends an empty POST body
            if not body_string:
                body = {}
            else:
                body = json.loads(body_string)
            
            target_regions = body.get('regions', [])
            threshold = body.get('threshold_ms', 180)

            # 3. Calculate metrics
            response_data = {}
            for region in target_regions:
                rows = [d for d in DATA if d.get('region') == region]
                if not rows:
                    continue

                latencies = [r['latency_ms'] for r in rows]
                uptimes = [r['uptime_pct'] for r in rows]

                response_data[region] = {
                    "avg_latency": float(np.mean(latencies)),
                    "p95_latency": float(np.percentile(latencies, 95)),
                    "avg_uptime": float(np.mean(uptimes)),
                    "breaches": sum(1 for l in latencies if l > threshold)
                }

            # 4. Send response
            response_json = json.dumps(response_data).encode('utf-8')
            self.send_response(200)
            self._cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response_json)

        except Exception as e:
            # Even if it crashes, return the CORS headers so the bot doesn't get mad
            error_msg = f"PYTHON ERROR: {str(e)}"
            self.send_response(500)
            self._cors_headers()
            self.end_headers()
            self.wfile.write(error_msg.encode('utf-8'))
