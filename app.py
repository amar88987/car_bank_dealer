from flask import Flask, jsonify, request, render_template
import requests
from config import PORT, BANK_API_URL
from database import initialize_database, get_cars, get_customers, create_financing_request, get_financing_requests

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html", bank_api_url=BANK_API_URL)

@app.get("/api/cars")
def cars():
    data = get_cars()
    return jsonify(success=True, count=len(data), cars=data)

@app.get("/api/customers")
def customers():
    data = get_customers()
    return jsonify(success=True, count=len(data), customers=data)

@app.get("/api/financing-requests")
def financing_requests():
    data = get_financing_requests()
    return jsonify(success=True, count=len(data), requests=data)

@app.get("/api/bank-health")
def bank_health():
    try:
        response = requests.get(f"{BANK_API_URL}/api/health", timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.RequestException as exc:
        return jsonify(success=False, status="offline", error=str(exc)), 502

@app.post("/api/finance")
def finance():
    data = request.get_json(silent=True) or {}
    required = ["customer_id", "car_id", "amount", "months"]
    missing = [f for f in required if data.get(f) in (None, "")]
    if missing:
        return jsonify(success=False, message="Missing required fields", fields=missing), 400

    try:
        customer_id = int(data["customer_id"])
        car_id = int(data["car_id"])
        amount = float(data["amount"])
        months = int(data["months"])
    except (ValueError, TypeError):
        return jsonify(success=False, message="Invalid numeric values"), 400

    car = next((c for c in get_cars() if c["id"] == car_id), None)
    customer = next((c for c in get_customers() if c["id"] == customer_id), None)
    if not car:
        return jsonify(success=False, message="Car not found"), 404
    if not customer:
        return jsonify(success=False, message="Customer not found"), 404

    payload = {
        "customer_id": customer_id,
        "car_id": car_id,
        "car_name": f'{car["brand"]} {car["model"]} {car["year"]}',
        "amount": amount,
        "months": months
    }

    try:
        response = requests.post(f"{BANK_API_URL}/api/loans", json=payload, timeout=20)
        bank_data = response.json()
    except requests.RequestException as exc:
        return jsonify(success=False, message="Could not connect to Bank API", error=str(exc)), 502

    loan = bank_data.get("loan") or {}
    status = loan.get("status", "Rejected" if response.status_code >= 400 else "Pending")
    loan_id = loan.get("id")

    request_id = create_financing_request(
        customer_id, car_id, amount, months, loan_id, status,
        bank_data.get("message", "")
    )

    return jsonify(
        success=bank_data.get("success", False),
        message=bank_data.get("message", "Bank response received"),
        financing_request_id=request_id,
        bank_response=bank_data
    ), response.status_code

if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=PORT)
