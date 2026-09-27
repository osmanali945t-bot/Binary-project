import os
import json
import random
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'quotex_ai_pro_ultra_secure_2026_secret_key'

VIP_PASSWORD = "VIP153"
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# TradingView Symbol Mapping
FOREX_PAIRS = {
    'EUR/USD': 'FX:EURUSD', 'GBP/USD': 'FX:GBPUSD', 'USD/JPY': 'FX:USDJPY',
    'AUD/USD': 'FX:AUDUSD', 'USD/CAD': 'FX:USDCAD', 'USD/CHF': 'FX:USDCHF',
    'NZD/USD': 'FX:NZDUSD', 'EUR/GBP': 'FX:EURGBP', 'EUR/JPY': 'FX:EURJPY',
    'GBP/JPY': 'FX:GBPJPY', 'AUD/JPY': 'FX:AUDJPY', 'EUR/AUD': 'FX:EURAUD'
}

def get_tradingview_analysis(symbol, timeframe):
    url = "https://scanner.tradingview.com/forex/scan"
    payload = {
        "symbols": {"tickers": [symbol]},
        "columns": ["close", "EMA200", "RSI", "Recommend.Other", "Recommend.All", "Recommend.MA"]
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                row = data['data'][0]['d']
                return {
                    'close': float(row[0] or 0),
                    'ema200': float(row[1] or 0),
                    'rsi': float(row[2] or 50),
                    'recommendation': float(row[4] or 0)
                }
    except Exception as e:
        print("API Error:", e)
    return None

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template(
        'index.html', 
        pairs=FOREX_PAIRS, 
        is_vip=session.get('is_vip', False),
        username=session.get('username', 'Trader')
    )

@app.route('/login', methods=['GET'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()

    if not name or not email or not phone or not password:
        return jsonify({'status': 'error', 'msg_bn': 'সবগুলো ঘর সঠিকভাবে পূরণ করুন।'})

    users = load_users()
    
    # চেক করা হচ্ছে এই জিমেইল দিয়ে ইতিমধ্যে অ্যাকাউন্ট খোলা আছে কি না
    if email in users:
        return jsonify({'status': 'error', 'msg_bn': 'এই ইমেইল দিয়ে ইতিমধ্যে একটি অ্যাকাউন্ট রেজিস্টার্ড রয়েছে! দয়া করে লগইন করুন।'})

    # ৬ ডিজিটের ভেরিফিকেশন কোড জেনারেট করা
    v_code = str(random.randint(100000, 999999))
    
    users[email] = {
        'name': name, 
        'email': email, 
        'phone': phone,
        'password': password, 
        'verified': False, 
        'verification_code': v_code
    }
    save_users(users)
    
    # টার্মিনাল লগ-এ কোড প্রিন্ট হবে
    print(f"\n[SIGNUP VERIFICATION CODE FOR {email}]: {v_code}\n")

    return jsonify({
        'status': 'success', 
        'email': email,
        'msg_bn': f'রেজিস্ট্রেশন সফল! আপনার ভেরিফিকেশন কোড হলো: {v_code}'
    })

@app.route('/api/verify-code', methods=['POST'])
def api_verify_code():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()

    users = load_users()
    if email not in users:
        return jsonify({'status': 'error', 'msg_bn': 'ইউজার পাওয়া যায়নি।'})

    stored_code = str(users[email].get('verification_code', ''))
    
    if stored_code == code:
        users[email]['verified'] = True
        save_users(users)
        return jsonify({'status': 'success', 'msg_bn': 'ইমেইল সফলভাবে ভেরিফাই হয়েছে! এখন লগইন করুন।'})
    else:
        return jsonify({'status': 'error', 'msg_bn': 'ভুল ভেরিফিকেশন কোড দিয়েছেন!'})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    users = load_users()
    if email not in users:
        return jsonify({'status': 'error', 'msg_bn': 'এই ইমেইল দিয়ে কোনো অ্যাকাউন্ট নেই! প্রথমে সাইন আপ করুন।'})

    user = users[email]
    
    # ইমেইল ভেরিফাইড কি না চেক করা
    if not user.get('verified', False):
        return jsonify({'status': 'error', 'msg_bn': 'আপনার ইমেইলটি এখনো ভেরিফাই করা হয়নি। কোড দিয়ে ভেরিফাই করুন।'})
    
    # ভুল পাসওয়ার্ড চেক করা
    if user['password'] != password:
        return jsonify({'status': 'error', 'msg_bn': 'ভুল পাসওয়ার্ড! সঠিক পাসওয়ার্ড দিয়ে লগইন করুন।'})

    session['logged_in'] = True
    session['username'] = user['name']
    session['email'] = email
    session['is_vip'] = False
    session['lifetime_signal_count'] = 0

    return jsonify({'status': 'success', 'redirect': '/'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/verify-vip', methods=['POST'])
def verify_vip():
    data = request.get_json(silent=True) or {}
    if data.get('vip_pass', '').strip() == VIP_PASSWORD:
        session['is_vip'] = True
        return jsonify({'status': 'success', 'msg_bn': '🎉 অভিনন্দন! VIP অ্যাক্সেস সফলভাবে চালু হয়েছে।'})
    else:
        return jsonify({'status': 'invalid', 'msg_bn': '❌ ভুল VIP পাসওয়ার্ড!'})

@app.route('/admin-panel-secret-xyz')
def admin_panel():
    users = load_users()
    return render_template('admin.html', users=users)

@app.route('/analyze', methods=['POST'])
def analyze():
    if not session.get('logged_in'):
        return jsonify({'status': 'error', 'msg_bn': 'অনুগ্রহ করে প্রথমে লগইন করুন।'})

    is_vip = session.get('is_vip', False)
    lifetime_count = session.get('lifetime_signal_count', 0)

    if not is_vip and lifetime_count >= 5:
        return jsonify({
            'status': 'limit_reached',
            'msg_bn': 'আপনার ফ্রি ৫টি সিগন্যাল লিমিট শেষ! আনলিমিটেড সিগন্যালের জন্য VIP নিন।'
        })

    data = request.get_json(silent=True) or {}
    pair_symbol = data.get('pair')
    timeframe = data.get('timeframe', '5m')

    if not pair_symbol or pair_symbol not in FOREX_PAIRS:
        return jsonify({'status': 'error', 'msg_bn': 'সঠিক কারেন্সি পেয়ার নির্বাচন করুন।'})

    tv_symbol = FOREX_PAIRS[pair_symbol]
    market_data = get_tradingview_analysis(tv_symbol, timeframe)

    if not market_data:
        return jsonify({'status': 'error', 'msg_bn': 'মার্কেট ডেটা ফেচ করতে ত্রুটি হয়েছে।'})

    current_price = round(market_data['close'], 5)
    ema_200 = round(market_data['ema200'], 5)
    rsi = round(market_data['rsi'], 2)
    rec_val = market_data['recommendation']

    is_uptrend = current_price > ema_200
    is_downtrend = current_price < ema_200

    if timeframe == '1m':
        exit_time = "1 - 2 Minutes (Scalp Expiry)"
    elif timeframe == '5m':
        exit_time = "5 Minutes (Standard Binary Expiry)"
    else:
        exit_time = "15 Minutes (Swing Expiry)"

    if rec_val > 0.15 and is_uptrend and rsi < 68:
        signal_title = "STRONG CALL 🟢 (BUY / UP)"
        action_code = "BUY"
        filter_reason = f"Trend: Up, RSI ({rsi}) < 68, Price > EMA200"
        pa_zone = f"Support Reversal: CALL at ~{current_price}"
    elif rec_val < -0.15 and is_downtrend and rsi > 32:
        signal_title = "STRONG PUT 🔴 (SELL / DOWN)"
        action_code = "SELL"
        filter_reason = f"Trend: Down, RSI ({rsi}) > 32, Price < EMA200"
        pa_zone = f"Resistance Rejection: PUT at ~{current_price}"
    else:
        signal_title = "NEUTRAL ⚪ (WAIT)"
        action_code = "NEUTRAL"
        filter_reason = "Consolidation Market"
        pa_zone = "Wait for breakout"
        exit_time = "N/A"

    if not is_vip:
        session['lifetime_signal_count'] = lifetime_count + 1

    remaining = "আনলিমিটেড (VIP Active)" if is_vip else f"{5 - session['lifetime_signal_count']} টি ফ্রি সিগন্যাল বাকি"

    return jsonify({
        'status': 'success',
        'pair': pair_symbol,
        'market': 'Quotex OTC / Forex Market',
        'timeframe': timeframe,
        'exit_time': exit_time,
        'signal_type': signal_title,
        'action_code': action_code,
        'entry_price': current_price,
        'filter_reason': filter_reason,
        'pa_zone': pa_zone,
        'remaining': remaining,
        'msg_bn': 'সিগন্যাল সফলভাবে জেনারেট হয়েছে।'
    })

@app.route('/check-result', methods=['POST'])
def check_result():
    data = request.get_json(silent=True) or {}
    pair_symbol = data.get('pair')
    entry_price = float(data.get('entry_price', 0))
    action_code = data.get('action_code')
    timeframe = data.get('timeframe', '5m')

    if not pair_symbol or pair_symbol not in FOREX_PAIRS:
        return jsonify({'status': 'error', 'msg_bn': 'ইনভ্যালিড পেয়ার'})

    market_data = get_tradingview_analysis(FOREX_PAIRS[pair_symbol], timeframe)
    if not market_data:
        return jsonify({'status': 'error', 'msg_bn': 'রেজাল্ট যাচাই করতে সমস্যা হয়েছে।'})

    exit_price = round(market_data['close'], 5)

    is_win = False
    if action_code == 'BUY':
        is_win = exit_price >= entry_price
    elif action_code == 'SELL':
        is_win = exit_price <= entry_price

    result_text = "WIN 🟢 (প্রফিট / সফল ট্রেড)" if is_win else "LOSS 🔴 (লস / ব্যর্থ ট্রেড)"
    color_code = "#2ea043" if is_win else "#f85149"

    return jsonify({
        'status': 'success',
        'is_win': is_win,
        'result_text': result_text,
        'color_code': color_code,
        'entry_price': entry_price,
        'exit_price': exit_price
    })

if __name__ == '__main__':
    app.run(debug=True)
    
