from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from datetime import datetime, timedelta
import random
import qrcode
import io
import base64

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clipboard.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class Clipboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(4), unique=True, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def cleanup():
        expiration_time = datetime.utcnow() - timedelta(minutes=15)
        Clipboard.query.filter(Clipboard.created_at < expiration_time).delete()
        db.session.commit()

def generate_code():
    while True:
        code = f"{random.randint(1000, 9999)}"
        if not Clipboard.query.filter_by(code=code).first():
            return code

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["POST"])
def create():
    data = request.json
    if "text" not in data or not data["text"].strip():
        return jsonify({"error": "Текст не может быть пустым"}), 400

    Clipboard.cleanup()
    code = generate_code()
    new_entry = Clipboard(code=code, text=data["text"])
    db.session.add(new_entry)
    db.session.commit()

    socketio.emit("new_text", {"code": code, "text": data["text"]})  # Уведомление через WebSocket
    return jsonify({"code": code})

@app.route("/get/<code>", methods=["GET"])
def get_text(code):
    Clipboard.cleanup()
    entry = Clipboard.query.filter_by(code=code).first()
    if not entry:
        return jsonify({"error": "Код не найден или срок хранения истёк"}), 404
    return jsonify({"text": entry.text})

@app.route("/delete", methods=["POST"])
def delete():
    db.session.query(Clipboard).delete()
    db.session.commit()
    socketio.emit("clear_texts")  # Уведомление через WebSocket
    return jsonify({"message": "Все записи удалены"})

@app.route("/stats", methods=["GET"])
def stats():
    count = Clipboard.query.count()
    return jsonify({"count": count})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, host="0.0.0.0", port=5005, debug=True, allow_unsafe_werkzeug=True)

