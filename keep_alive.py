#!/usr/bin/env python3
"""
Keep Alive Script for Telegram Bot Deployment on Render
This script creates a simple web server to keep the bot alive and handle webhook if needed
"""

import os
import threading
import time
import logging
from flask import Flask, request, jsonify
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Get the port from environment variable or default to 10000
PORT = int(os.environ.get('PORT', 10000))

# Global variable to track bot status
bot_status = {
    "status": "running",
    "start_time": time.time(),
    "uptime": 0
}

@app.route('/')
def home():
    """Root endpoint showing bot status"""
    bot_status["uptime"] = time.time() - bot_status["start_time"]
    return jsonify({
        "message": "🤖 Pokemon Auction Bot is running!",
        "status": bot_status["status"],
        "uptime_seconds": round(bot_status["uptime"], 2),
        "uptime_minutes": round(bot_status["uptime"] / 60, 2),
        "uptime_hours": round(bot_status["uptime"] / 3600, 2)
    })

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    bot_status["uptime"] = time.time() - bot_status["start_time"]
    return jsonify({
        "status": "healthy",
        "bot_status": bot_status["status"],
        "uptime": round(bot_status["uptime"], 2),
        "timestamp": time.time()
    })

@app.route('/status')
def status():
    """Status endpoint showing detailed bot information"""
    bot_status["uptime"] = time.time() - bot_status["start_time"]
    return jsonify(bot_status)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for Telegram (if using webhook instead of polling)"""
    # If you decide to use webhooks instead of polling in the future
    # You can implement the webhook handler here
    return jsonify({"status": "webhook_received"})

@app.route('/restart', methods=['POST'])
def restart():
    """Endpoint to restart the bot (admin only)"""
    # You can add authentication here if needed
    return jsonify({"status": "restart_initiated"})

def run_flask_app():
    """Run the Flask app"""
    try:
        logger.info(f"Starting Flask server on port {PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Flask app error: {e}")

def start_keep_alive():
    """Start the keep-alive server in a separate thread"""
    try:
        flask_thread = threading.Thread(target=run_flask_app, daemon=True)
        flask_thread.start()
        logger.info("Keep-alive server started successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {e}")
        return False

def ping_self():
    """Periodically ping the own server to keep it alive"""
    try:
        render_app_url = os.environ.get('RENDER_EXTERNAL_URL')
        if render_app_url:
            response = requests.get(f"{render_app_url}/health", timeout=10)
            logger.info(f"Self-ping successful: {response.status_code}")
        else:
            logger.info("Self-ping: No external URL set, skipping")
    except Exception as e:
        logger.warning(f"Self-ping failed: {e}")

def start_ping_loop(interval_minutes=10):
    """Start a loop to periodically ping the server"""
    def ping_loop():
        while True:
            time.sleep(interval_minutes * 60)
            ping_self()
    
    ping_thread = threading.Thread(target=ping_loop, daemon=True)
    ping_thread.start()
    logger.info(f"Self-ping loop started with {interval_minutes} minute interval")

if __name__ == '__main__':
    logger.info("Starting keep-alive server...")
    start_keep_alive()
    
    # Start self-ping loop if running on Render
    if os.environ.get('RENDER'):
        start_ping_loop(interval_minutes=10)
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Keep-alive server stopped by user")