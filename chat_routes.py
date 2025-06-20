import os
import re
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash,
    jsonify, abort
)
from models import db, User, Product, ChatSession, Message
from model_adapters import call_model

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat/<int:product_id>')
def chat_page(product_id):
    if 'user_id' not in session:
        flash("Please log in to negotiate.", "warning")
        return redirect(url_for('auth.login'))

    user    = User.query.get_or_404(session['user_id'])
    product = Product.query.get_or_404(product_id)

    # Find or create active ChatSession
    cs = ChatSession.query.filter_by(
        user_id=user.id,
        product_id=product.id,
        active=True
    ).first()

    if not cs:
        # 1) Create session and add to DB
        cs = ChatSession(
            user_id=user.id,
            product_id=product.id,
            current_price=product.price
        )
        db.session.add(cs)
        # 2) Flush so that cs.id is assigned before we create the welcome message
        db.session.flush()

        # Initial greeting
        greeting = (
            f"Hello! I’m here to help you with **{product.name}**. "
            f"Our list price is **${product.price:.2f}**—let me know any questions or what price you have in mind!"
        )
        # Use session_id now that cs.id is available
        db.session.add(
            Message(session_id=cs.id, role='assistant', content=greeting)
        )
        db.session.commit()

    # Load full chat history
    messages = (
        Message.query
               .filter_by(session_id=cs.id)
               .order_by(Message.timestamp)
               .all()
    )

    return render_template(
        'chat.html',
        product=product,
        messages=messages,
        chat_session=cs,
        current_price=cs.current_price
    )


@chat_bp.route('/chat/<int:session_id>/send', methods=['POST'])
def chat_send(session_id):
    if 'user_id' not in session:
        return jsonify({'message': "⚠️ Please log in first."}), 401

    cs = ChatSession.query.get_or_404(session_id)
    if cs.user_id != session['user_id']:
        return jsonify({'message': "⚠️ Invalid session."}), 403
    if not cs.active:
        return jsonify({'message': "💬 This chat has ended."}), 400

    data      = request.get_json() or {}
    user_text = data.get('message', '').strip()
    if not user_text:
        return jsonify({'message': ''})

    # 1) Save user's message
    db.session.add(
        Message(session_id=cs.id, role='user', content=user_text)
    )
    db.session.flush()

    # 2) If admin has taken over, just return current price
    if cs.handed_to_human:
        db.session.commit()
        return jsonify({
            'message': None,
            'price':   f"{cs.current_price:.2f}"
        })

    product     = cs.product
    floor_price = round(product.price - product.max_discount, 2)

    # 3) If at floor price already, inform politely
    if cs.current_price <= floor_price:
        floor_msg = (
            f"I'm truly sorry, but **${floor_price:.2f}** is the best price for **{product.name}**. "
            "Please click Add to Cart if you’d like to proceed."
        )
        db.session.add(
            Message(session_id=cs.id, role='assistant', content=floor_msg)
        )
        cs.current_price = floor_price
        db.session.commit()
        return jsonify({
            'message': floor_msg,
            'price':   f"{cs.current_price:.2f}"
        })

    # 4) Detect discount request
    asked_discount = bool(
        re.search(r'\b(discount|lower|cheaper|price|deal)\b',
                  user_text, re.IGNORECASE)
    )

    # 5) Info mode (no discount)
    if not asked_discount:
        system_prompt = (
            "You’re a friendly sales assistant. "
            "Answer product questions warmly—and do NOT offer a discount unless explicitly asked.\n\n"
            f"Product: {product.name}\n"
            f"Description: {product.description}\n"
            f"Current Price: ${cs.current_price:.2f}\n"
        )
        convo = [{"role": "system", "content": system_prompt}]
        for m in Message.query.filter_by(session_id=cs.id).order_by(Message.timestamp):
            role = 'assistant' if m.role in ('assistant','admin') else 'user'
            convo.append({"role": role, "content": m.content})
        convo.append({"role": "user", "content": user_text})

        provider = os.getenv("MODEL_PROVIDER", "openai")
        try:
            prompt_text = "\n".join(m["content"] for m in convo)
            bot_text    = call_model(provider, prompt_text)
        except Exception:
            bot_text = "⚠️ Sorry, something went wrong. Please try again shortly."

        db.session.add(
            Message(session_id=cs.id, role='assistant', content=bot_text)
        )
        db.session.commit()
        return jsonify({'message': bot_text})

    # 6) Negotiation mode
    system_prompt = (
        "You’re a warm, human‐like sales assistant negotiating step by step.\n\n"
        f"Product: {product.name}\n"
        f"Description: {product.description}\n"
        f"Current Price: ${cs.current_price:.2f}\n"
        f"Floor Price: ${floor_price:.2f}\n\n"
        "GUIDELINES:\n"
        "1. First offer: small (~5%) off current price, above floor.\n"
        "2. Phrase naturally: “I can meet you at $X.XX—does that work for you?”\n"
        "3. If pressed again, step down until floor.\n"
        "4. At floor: “I’m sorry, but $<floor> is the best I can do.”\n"
        "5. If admin override appears, use that price silently.\n"
        "6. Keep it warm and natural.\n"
    )
    convo = [{"role": "system", "content": system_prompt}]
    for m in Message.query.filter_by(session_id=cs.id).order_by(Message.timestamp):
        role = 'assistant' if m.role in ('assistant','admin') else 'user'
        convo.append({"role": role, "content": m.content})
    convo.append({"role": "user", "content": user_text})

    provider = os.getenv("MODEL_PROVIDER", "openai")
    try:
        prompt_text = "\n".join(m["content"] for m in convo)
        bot_text    = call_model(provider, prompt_text)
    except Exception:
        bot_text = "⚠️ Error reaching the model—please try again."

    db.session.add(
        Message(session_id=cs.id, role='assistant', content=bot_text)
    )

    # Clamp any price offered in the AI text
    match = re.search(r'\$([0-9]+(?:\.[0-9]{1,2})?)', bot_text)
    if match:
        offered = float(match.group(1))
        cs.current_price = round(
            max(floor_price, min(offered, cs.current_price)), 2
        )

    db.session.commit()
    return jsonify({
        'message': bot_text,
        'price':   f"{cs.current_price:.2f}"
    })


@chat_bp.route('/chat/<int:session_id>/messages')
def chat_messages(session_id):
    cs = ChatSession.query.get_or_404(session_id)
    if session.get('user_id') != cs.user_id:
        return jsonify({'error': 'unauthorized'}), 403

    # Apply any admin override in transcript
    msgs = Message.query.filter_by(session_id=cs.id).order_by(Message.timestamp).all()
    overridden = False
    for m in msgs:
        if m.role == 'admin':
            mo = re.search(r'\$([0-9]+(?:\.[0-9]{1,2})?)', m.content)
            if mo:
                cs.current_price = round(float(mo.group(1)), 2)
                overridden = True
    if overridden:
        db.session.commit()

    # Only show user + assistant messages to the customer
    visible = [
        {'role': m.role, 'content': m.content}
        for m in msgs if m.role != 'admin'
    ]

    return jsonify({
        'messages': visible,
        'price':    f"{cs.current_price:.2f}"
    })
