import hmac
import hashlib
import subprocess
from flask import Flask, request, abort

app = Flask(__name__)

# Set this to your GitHub webhook secret (or leave as empty string if not using secret)
GITHUB_SECRET = "your_github_webhook_secret_141516"

def verify_signature(payload, signature):
    if not GITHUB_SECRET:
        return True  # No secret set, skip verification
    mac = hmac.new(GITHUB_SECRET.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest('sha256=' + mac.hexdigest(), signature)

@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    if GITHUB_SECRET and (signature is None or not verify_signature(request.data, signature)):
        abort(403)
    # Pull latest code from the correct directory
    subprocess.Popen(["git", "pull"], cwd="/home/sbydevapp/joke-bot")
    return "OK", 200

@app.route('/', methods=['GET'])
def github_webhook_get():
    return "Tesing ... ", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)