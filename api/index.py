import json
import os
import numpy as np
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()
        self.wfile.write(b"Endpoint is ready")

    def do_POST(self):
        try:
            # 1. Safely read the body (even if the bot sends an empty request)
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body_string = self.rfile.read(content_length).decode('utf-8')
                body = json.loads(body_string)
            else:
                body = {}

            target_regions = body.get('regions', [])
            threshold = body.get('threshold_ms', 180)

            # 2. Load data
            DATA_PATH = os.path.join(os.path.dirname(__file__), 'q-vercel-latency.json')
            with open(DATA_PATH, 'r') as f:
                DATA = json.load(f)

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

            # 4. Send success response with CORS
            self.send_response(200)
            self.send_cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

        except Exception as e:
            # 5. If the bot sends garbage, DO NOT CRASH. 
            # Return a 400 Bad Request, but STILL attach the CORS headers!
            self.send_response(400)
            self.send_cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
