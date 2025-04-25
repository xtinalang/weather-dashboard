from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    response = {
        "error": e.name,
        "description": e.description,
        "status_code": e.code
    }
    return jsonify(response), e.code

@app.route("/example")
def example():
    abort(404)  # Just to trigger an error for demo

if __name__ == "__main__":
    app.run(debug=True)