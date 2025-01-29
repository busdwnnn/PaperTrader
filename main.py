from flask import Flask, jsonify, request, session
from models import User, Trade, Portfolio, LimitOrder
from database import db_session, init_db
from datetime import datetime
import yfinance as yf
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET'])
def test():
    return jsonify({"message": "Server is running!"})

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == data['username']) | 
            (User.email == data['email'])
        ).first()
        if existing_user:
            return jsonify({"error": "Username or email already exists"}), 409

        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            balance=100000.00
        )
        db_session.add(user)
        db_session.commit()
        return jsonify({"message": "User registered successfully", "user_id": user.id})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            session['user_id'] = user.id
            return jsonify({"message": "Login successful", "user_id": user.id})
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/limit-order', methods=['POST'])
@login_required
def place_limit_order():
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        order = LimitOrder(
            user_id=user_id,
            symbol=data['symbol'],
            quantity=data['quantity'],
            target_price=data['target_price'],
            order_type=data['order_type'],  # 'buy' or 'sell'
            status='pending'
        )
        
        db_session.add(order)
        db_session.commit()
        
        return jsonify({
            "message": "Limit order placed successfully",
            "order_id": order.id
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/performance/<int:user_id>', methods=['GET'])
@login_required
def get_performance(user_id):
    try:
        if session['user_id'] != user_id:
            return jsonify({"error": "Unauthorized"}), 403
            
        trades = Trade.query.filter_by(user_id=user_id).all()
        performance = {
            "total_trades": len(trades),
            "profitable_trades": 0,
            "total_profit_loss": 0
        }
        
        for trade in trades:
            if trade.trade_type == 'sell':
                # Calculate profit/loss for completed trades
                buy_trade = Trade.query.filter_by(
                    user_id=user_id,
                    symbol=trade.symbol,
                    trade_type='buy'
                ).first()
                
                if buy_trade:
                    profit = (trade.price - buy_trade.price) * trade.quantity
                    performance['total_profit_loss'] += profit
                    if profit > 0:
                        performance['profitable_trades'] += 1
        
        return jsonify(performance)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trade', methods=['POST'])
def execute_trade():
    data = request.get_json()
    user_id = data['user_id']
    symbol = data['symbol']
    quantity = data['quantity']
    trade_type = data['trade_type']  # 'buy' or 'sell'
    
    # Get real-time price using yfinance
    ticker = yf.Ticker(symbol)
    current_price = ticker.info['regularMarketPrice']
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    total_cost = current_price * quantity
    
    if trade_type == 'buy':
        if user.balance < total_cost:
            return jsonify({"error": "Insufficient funds"}), 400
        user.balance -= total_cost
    else:  # sell
        portfolio = Portfolio.query.filter_by(user_id=user_id, symbol=symbol).first()
        if not portfolio or portfolio.quantity < quantity:
            return jsonify({"error": "Insufficient shares"}), 400
        user.balance += total_cost
        portfolio.quantity -= quantity
    
    trade = Trade(
        user_id=user_id,
        symbol=symbol,
        quantity=quantity,
        price=current_price,
        trade_type=trade_type,
        timestamp=datetime.utcnow()
    )
    
    db_session.add(trade)
    db_session.commit()
    
    return jsonify({
        "message": "Trade executed successfully",
        "trade_id": trade.id,
        "price": current_price,
        "total_cost": total_cost
    })

@app.route('/portfolio/<int:user_id>', methods=['GET'])
def get_portfolio(user_id):
    portfolio = Portfolio.query.filter_by(user_id=user_id).all()
    result = []
    
    for position in portfolio:
        ticker = yf.Ticker(position.symbol)
        current_price = ticker.info['regularMarketPrice']
        market_value = current_price * position.quantity
        
        result.append({
            "symbol": position.symbol,
            "quantity": position.quantity,
            "current_price": current_price,
            "market_value": market_value
        })
    
    return jsonify({"portfolio": result})

if __name__ == '__main__':
    init_db()
    app.run(debug=False) 
