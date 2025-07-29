from flask import Flask, render_template, request, redirect, session, url_for
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Used for session encryption

DATA_FILE = 'phones.json'

# Load phones from JSON file
def load_phones():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Save phones to JSON file
def save_phones(phones):
    with open(DATA_FILE, 'w') as f:
        json.dump(phones, f, indent=4)

# Calculate prices for platforms X, Y, Z
def calculate_platform_prices(base_price):
    return {
        'X': int(base_price * 0.9),  # 10% fee
        'Y': int(base_price * 0.92 - 2),  # 8% + $2 fee
        'Z': int(base_price * 0.88)  # 12% fee
    }

# Map conditions to platform-specific categories
def map_conditions(condition):
    return {
        'X': {
            'Excellent': 'New',
            'Good': 'Good',
            'Usable': 'Scrap'
        }.get(condition, 'Good'),
        'Y': {
            'Excellent': '3 stars (Excellent)',
            'Good': '2 stars (Good)',
            'Usable': '1 star (Usable)'
        }.get(condition, '2 stars (Good)'),
        'Z': {
            'Excellent': 'New',
            'Good': 'As New',
            'Usable': 'Good'
        }.get(condition, 'As New')
    }

# Show login page and handle login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

# Dashboard view after login
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    phones = load_phones()
    visible_phones = []

    for phone in phones:
        # Prevent out-of-stock from displaying
        if phone['stock'] <= 0:
            continue

        # Ensure prices exist
        if 'prices' not in phone:
            phone['prices'] = calculate_platform_prices(phone['base_price'])

        # Only list phones if they're profitable (price > 0 on all platforms)
        if all(p > 0 for p in phone['prices'].values()):
            phone['condition_mapping'] = map_conditions(phone['condition'])
            visible_phones.append(phone)

    return render_template('dashboard.html', phones=visible_phones)

# Add phone
@app.route('/add', methods=['POST'])
def add():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    phones = load_phones()
    new_phone = {
        'id': len(phones) + 1,
        'brand': request.form['brand'],
        'model': request.form['model'],
        'condition': request.form['condition'],
        'base_price': int(request.form['base_price']),
        'stock': int(request.form['stock'])
    }
    new_phone['prices'] = calculate_platform_prices(new_phone['base_price'])
    phones.append(new_phone)
    save_phones(phones)
    return redirect(url_for('dashboard'))

# Delete phone
@app.route('/delete/<int:phone_id>')
def delete(phone_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    phones = load_phones()
    phones = [phone for phone in phones if phone['id'] != phone_id]
    save_phones(phones)
    return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
