import os
from dotenv import load_dotenv
from flask import Flask, render_template
from models import db
import openai

# ─── Load environment variables from .env ───────
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'fallback-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ─── Configure OpenAI (default provider) ────────
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY not set in environment or .env")

# ─── Landing page ───────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ─── Register blueprints ────────────────────────
from auth_routes    import auth_bp
from store_routes   import store_bp
from product_routes import product_bp
from chat_routes    import chat_bp
from cart_routes    import cart_bp

app.register_blueprint(auth_bp)
app.register_blueprint(store_bp)
app.register_blueprint(product_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(cart_bp)

# ─── Ensure tables exist ────────────────────────
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
