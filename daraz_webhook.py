import ngrok
import winsound
import threading
from flask import Flask, request, jsonify


def beep():
    winsound.Beep(440, 1000)


# Initialize Flask app
app = Flask(__name__)


# Route to handle POST request
@app.route("/webhook", methods=['POST'])
def webhook():
    # Capture the JSON data from the POST request
    threading.Thread(target=beep).start()
    response = request.json
    for key in response:
        print(key, ":", response[key])

    # Respond to the POST request
    return jsonify({"status": "success", "data_received": response}), 200


if __name__ == '__main__':
    # Step 1: Start an ngrok tunnel programmatically
    ngrok.set_auth_token("2nG1wUHYHDiVyxLYA6H9pYgJhVo_862eNbJeyksyjbrBCC5Z1")  # Optional, if you need authentication
    public_url = ngrok.connect(5000, hostname="tapir-willing-ultimately.ngrok-free.app")  # This exposes port 5000
    print(f"ngrok tunnel available at: {public_url.url()}")

    # Step 2: Start the Flask app
    app.run(port=5000)
