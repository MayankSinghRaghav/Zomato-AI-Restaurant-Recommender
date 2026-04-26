import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_utils import load_and_prepare_data
from phase2.engine import generate_candidates
from phase4.groq_recommender import get_groq_recommendations


class RecommendHandler(BaseHTTPRequestHandler):
    _df = None

    @classmethod
    def _get_df(cls):
        if cls._df is None:
            cls._df, _ = load_and_prepare_data(sample_limit=5000)
        return cls._df

    def _send_json(self, body: dict, status_code: int = 200) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return
        self._send_json({"error": "Not found"}, status_code=404)

    def do_POST(self):
        if self.path != "/recommend":
            self._send_json({"error": "Not found"}, status_code=404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        payload = json.loads(raw.decode("utf-8"))

        user_input = {
            "location": payload.get("location", ""),
            "budget": int(payload.get("budget", 2000)),
            "minimum_rating": float(payload.get("minimum_rating", 4.0)),
            "cuisine": payload.get("cuisine", ""),
            "additional_preference": payload.get("additional_preference", ""),
        }
        top_k = int(payload.get("top_k", 5))

        df = self._get_df()
        candidates = generate_candidates(df=df, user_input=user_input, limit=40)
        result = get_groq_recommendations(user_input=user_input, candidates=candidates, top_k=top_k)
        self._send_json(result)


def main() -> None:
    server = HTTPServer(("0.0.0.0", 8080), RecommendHandler)
    print("Backend listening at http://127.0.0.1:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()
