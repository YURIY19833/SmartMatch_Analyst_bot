from flask import Flask, request, jsonify
from predict import predict_match
from run_full_pipeline import main as run_pipeline
import threading
import os

app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def predict():
    data = request.json or {}
    home = data.get('home')
    away = data.get('away')
    if not home or not away:
        return jsonify({'error': 'home and away are required'}), 400
    result = predict_match(home, away)
    return jsonify({'result': result})


@app.route('/run', methods=['POST'])
def run():
    # Run pipeline in background thread to avoid request timeout
    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()
    return jsonify({'status': 'pipeline started'}), 202


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'env': os.environ.get('FOOTBALL_API_KEY') is not None})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
