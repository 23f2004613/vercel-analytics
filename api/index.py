import json
import os
import numpy as np
from http.server import BaseHTTPRequestHandler

# Load data once at startup
DATA_PATH = os.path.join(os.path.dirname(__file__), 'q-vercel-latency.json')


with open(DATA_PATH) as f:
    DATA = json.load(f)

class handler(BaseHTTPRequestHandler):
    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            
            target_regions = body.get('regions', [])
            threshold = body.get('threshold_ms', 180)

            response_data = {}
            
            for region in target_regions:
                # Filter rows for this region
                rows = [d for d in DATA if d['region'] == region]
                
                if not rows:
                    continue

                # Extract columns
                latencies = [r['latency_ms'] for r in rows]
                uptimes = [r['uptime_pct'] for r in rows]

                # Calculate metrics
                response_data[region] = {
                    "avg_latency": float(np.mean(latencies)),
                    "p95_latency": float(np.percentile(latencies, 95)),
                    "avg_uptime": float(np.mean(uptimes)),
                    "breaches": sum(1 for l in latencies if l > threshold)
                }

            # Send response
            response_json = json.dumps(response_data).encode('utf-8')
            self.send_response(200)
            self._cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response_json)

        except Exception as e:
            self.send_response(500)
            self._cors_headers()
            self.end_headers()
            self.wfile.write(str(e).encode())
