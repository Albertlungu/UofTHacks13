"""
Simple API server to provide generated images to the 3D frontend.
"""

import os
from pathlib import Path

from flask import Flask, jsonify, send_file
from flask_cors import CORS
from loguru import logger

app = Flask(__name__)
CORS(app)  # Allow frontend to access

# Get project root (2 levels up from src/api/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
IMAGE_DIR = PROJECT_ROOT / "data" / "generated_images"


@app.route("/api/images/recent", methods=["GET"])
def get_recent_images():
    """Get list of recent generated images."""
    try:
        if not IMAGE_DIR.exists():
            return jsonify({"images": []})

        images = sorted(
            IMAGE_DIR.glob("memory_*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Return image filenames (frontend will fetch them individually)
        image_list = [
            {
                "filename": img.name,
                "url": f"/api/images/file/{img.name}",
                "timestamp": img.stat().st_mtime
            }
            for img in images[:50]  # Last 50 images
        ]

        return jsonify({"images": image_list})

    except Exception as e:
        logger.error(f"Error fetching images: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/images/file/<filename>", methods=["GET"])
def get_image_file(filename):
    """Serve a specific image file."""
    try:
        # Security: only allow memory_*.png files
        if not filename.startswith("memory_") or not filename.endswith(".png"):
            return jsonify({"error": "Invalid filename"}), 400

        filepath = IMAGE_DIR / filename

        if not filepath.exists():
            return jsonify({"error": "Image not found"}), 404

        return send_file(filepath, mimetype="image/png")

    except Exception as e:
        logger.error(f"Error serving image: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/images/count", methods=["GET"])
def get_image_count():
    """Get count of generated images."""
    try:
        if not IMAGE_DIR.exists():
            return jsonify({"count": 0})

        count = len(list(IMAGE_DIR.glob("memory_*.png")))
        return jsonify({"count": count})

    except Exception as e:
        logger.error(f"Error counting images: {e}")
        return jsonify({"error": str(e)}), 500


def run_server(host="0.0.0.0", port=5002):
    """Run the image server."""
    logger.info(f"Starting image server on {host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_server()
