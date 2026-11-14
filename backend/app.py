from flask import Flask, jsonify, request
from dotenv import load_dotenv
try:
    from backend.services import data_store, chat_service
except ModuleNotFoundError:
    # Supports running as: python backend/app.py
    from services import data_store, chat_service

load_dotenv()

app = Flask(__name__)

@app.get("/api/health")
def health():
    return jsonify({"ok": True})

@app.get("/api/cities")
def cities():
    return jsonify(data_store.get_cities_master())

@app.get("/api/foreign-born")
def foreign_born():
    city      = request.args.get("city")
    city_type = request.args.get("city_type")
    return jsonify(data_store.get_foreign_born(city=city, city_type=city_type))

@app.get("/api/country-of-origin")
def country_of_origin():
    city = request.args.get("city")
    return jsonify(data_store.get_country_of_origin(city=city))

@app.get("/api/education")
def education():
    city = request.args.get("city")
    return jsonify(data_store.get_education(city=city))

@app.get("/api/homeownership")
def homeownership():
    city = request.args.get("city")
    return jsonify(data_store.get_homeownership(city=city))

@app.get("/api/employment-income")
def employment_income():
    city = request.args.get("city")
    return jsonify(data_store.get_employment_income(city=city))

@app.get("/api/poverty")
def poverty():
    city = request.args.get("city")
    return jsonify(data_store.get_poverty(city=city))

@app.get("/api/median-income")
def median_income():
    city = request.args.get("city")
    return jsonify(data_store.get_median_income(city=city))

@app.get("/api/map-stats")
def map_stats():
    return jsonify(data_store.get_map_stats())

@app.get("/api/time-series")
def time_series():
    city   = request.args.get("city")
    metric = request.args.get("metric", "fb_pct")
    return jsonify(data_store.get_time_series(city=city, metric=metric))


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True)

    # Validate request body
    if not isinstance(payload, dict):
        return jsonify({
            "error": "Expected a JSON object"
        }), 400

    message = payload.get("message")

    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "error": "Message must be a non-empty string"
        }), 400

    message = message.strip()

    if len(message) > 2000:
        return jsonify({
            "error": "Message exceeds 2000 characters"
        }), 400

    try:
        result = chat_service.chat(message)

        if (
            not isinstance(result, dict)
            or not isinstance(result.get("answer"), str)
        ):
            raise ValueError("Invalid chat service response")

        return jsonify(result), 200

    except Exception as exc:
        app.logger.error(
            "Chat request failed (%s)",
            type(exc).__name__
        )

        return jsonify({
            "error": "Chat service temporarily unavailable"
        }), 500
    


if __name__ == "__main__":
    import os

    port = int(os.getenv("PORT", "3000"))

    app.run(
        host="127.0.0.1",
        port=port,
        debug=False,
    )
