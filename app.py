from flask import Flask, request, jsonify, send_from_directory
from urllib.parse import urlparse
import yt_dlp
import os
import re

app = Flask(__name__)

DOWNLOAD_DIR = "/tmp/kyy-downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ALLOWED_DOMAINS = [
    "tiktok.com",
    "instagram.com",
    "youtube.com",
    "youtu.be"
]

@app.after_request
def cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/")
def home():
    return jsonify({
        "name": "KYY Downloader API",
        "status": "online",
        "version": "1.0"
    })

@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url.startswith(("https://", "http://")):
        return jsonify({"error": "URL tidak valid"}), 400

    host = (urlparse(url).hostname or "").lower()

    if not any(
        host == domain or host.endswith("." + domain)
        for domain in ALLOWED_DOMAINS
    ):
        return jsonify({"error": "Platform tidak didukung"}), 400

    try:
        options = {
            "format": "best[ext=mp4]/best",
            "outtmpl": DOWNLOAD_DIR + "/%(id)s.%(ext)s",
            "noplaylist": True,
            "max_filesize": 200 * 1024 * 1024,
            "quiet": True
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        if not os.path.isfile(filepath):
            base = os.path.splitext(filepath)[0]
            for ext in [".mp4", ".mkv", ".webm"]:
                if os.path.isfile(base + ext):
                    filepath = base + ext
                    break

        if not os.path.isfile(filepath):
            return jsonify({"error": "File tidak ditemukan"}), 500

        filename = os.path.basename(filepath)

        return jsonify({
            "status": "success",
            "title": info.get("title"),
            "filename": filename,
            "download_url": "/api/file/" + filename
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)[:300]
        }), 500

@app.route("/api/file/<filename>")
def get_file(filename):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", filename):
        return jsonify({"error": "Nama file tidak valid"}), 400

    return send_from_directory(
        DOWNLOAD_DIR,
        filename,
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
