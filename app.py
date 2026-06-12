import os
import threading
import time
import requests as req
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "changeme-secret-key-123")

BASE_API = "https://admin.otpservice.xyz/stubs/handler_api.php"

TIMEOUT = 15


def api_get(params):
    try:
        r = req.get(BASE_API, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        text = r.text.strip()
        try:
            return r.json()
        except Exception:
            return {"_raw": text}
    except req.exceptions.Timeout:
        return {"error": "TIMEOUT", "message": "Request timed out"}
    except req.exceptions.RequestException as e:
        return {"error": "REQUEST_FAILED", "message": str(e)}


@app.route("/ping")
def ping():
    return "ok", 200


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/balance")
def get_balance():
    api_key = request.args.get("api_key", "")
    if not api_key:
        return jsonify({"error": "NO_KEY", "message": "API key required"}), 400
    result = api_get({"action": "getBalance", "api_key": api_key})
    return jsonify(result)


@app.route("/api/services")
def get_services():
    api_key = request.args.get("api_key", "")
    if not api_key:
        return jsonify({"error": "NO_KEY", "message": "API key required"}), 400
    result = api_get({"action": "getServices", "api_key": api_key})
    return jsonify(result)


@app.route("/api/countries")
def get_countries():
    api_key = request.args.get("api_key", "")
    if not api_key:
        return jsonify({"error": "NO_KEY", "message": "API key required"}), 400
    result = api_get({"action": "getCountries", "api_key": api_key})
    return jsonify(result)


@app.route("/api/buy", methods=["POST"])
def buy_number():
    data = request.get_json(force=True) or {}
    api_key = data.get("api_key", "")
    service = data.get("service", "")
    country = data.get("country", "")
    max_price = data.get("max_price", "")

    if not api_key:
        return jsonify({"error": "NO_KEY", "message": "API key required"}), 400
    if not service:
        return jsonify({"error": "NO_SERVICE", "message": "Service required"}), 400

    params = {"action": "getNumber", "api_key": api_key, "service": service}
    if country:
        params["country"] = country
    if max_price:
        params["maxPrice"] = max_price

    result = api_get(params)
    return jsonify(result)


@app.route("/api/otp", methods=["POST"])
def get_otp():
    data = request.get_json(force=True) or {}
    api_key = data.get("api_key", "")
    transaction_id = data.get("transaction_id", "")

    if not api_key:
        return jsonify({"error": "NO_KEY", "message": "API key required"}), 400
    if not transaction_id:
        return jsonify({"error": "NO_TXN", "message": "Transaction ID required"}), 400

    params = {"action": "getOtp", "api_key": api_key, "transactionId": transaction_id}
    result = api_get(params)
    return jsonify(result)


@app.route("/api/cancel", methods=["POST"])
def cancel_number():
    data = request.get_json(force=True) or {}
    api_key = data.get("api_key", "")
    transaction_id = data.get("transaction_id", "")

    if not api_key:
        return jsonify({"error": "NO_KEY", "message": "API key required"}), 400
    if not transaction_id:
        return jsonify({"error": "NO_TXN", "message": "Transaction ID required"}), 400

    params = {
        "action": "cancelNumber",
        "api_key": api_key,
        "transactionId": transaction_id,
    }
    result = api_get(params)
    return jsonify(result)


@app.route("/api/rebuy", methods=["POST"])
def rebuy_number():
    data = request.get_json(force=True) or {}
    api_key = data.get("api_key", "")
    transaction_id = data.get("transaction_id", "")

    if not api_key:
        return jsonify({"error": "NO_KEY", "message": "API key required"}), 400
    if not transaction_id:
        return jsonify({"error": "NO_TXN", "message": "Transaction ID required"}), 400

    params = {
        "action": "setStatus",
        "api_key": api_key,
        "transactionId": transaction_id,
        "status": "3",
    }
    result = api_get(params)
    return jsonify(result)


@app.route("/api/history")
def get_history():
    api_key = request.args.get("api_key", "")
    if not api_key:
        return jsonify({"error": "NO_KEY", "message": "API key required"}), 400
    result = api_get({"action": "getHistory", "api_key": api_key})
    return jsonify(result)


def keepalive_ping():
    while True:
        time.sleep(240)
        app_url = os.environ.get("APP_URL", "")
        if app_url:
            try:
                req.get(f"{app_url.rstrip('/')}/ping", timeout=10)
            except Exception:
                pass


ping_thread = threading.Thread(target=keepalive_ping, daemon=True)
ping_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
