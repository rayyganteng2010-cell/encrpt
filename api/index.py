from flask import Flask, render_template, request, jsonify
from cryptography.fernet import Fernet
import qrcode
import io
import base64
import os

# Konfigurasi Path Template untuk Vercel Environment
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

# --- KONFIGURASI ---
MAX_QR_CHARS = 1000  # Batas karakter aman untuk QR Code

# --- HELPER FUNCTIONS ---
def generate_key():
    return Fernet.generate_key().decode()

def encrypt_bytes(data_bytes, key):
    f = Fernet(key.encode())
    return f.encrypt(data_bytes)

def decrypt_bytes(data_bytes, key):
    f = Fernet(key.encode())
    return f.decrypt(data_bytes)

def generate_qr(text_data):
    # Logika Smart QR: Kalau kepanjangan, return None (biar gak error/pecah)
    if len(text_data) > MAX_QR_CHARS:
        return None
        
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(text_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

# 1. API UNTUK TEKS / KODE (JS, PY, HTML)
@app.route('/api/text/encrypt', methods=['POST'])
def text_encrypt():
    data = request.json
    text = data.get('text', '')
    
    if not text: return jsonify({'error': 'Teks kosong!'})

    try:
        key = generate_key()
        encrypted_bytes = encrypt_bytes(text.encode(), key)
        encrypted_str = encrypted_bytes.decode()
        
        # Cek apakah QR Code memungkinkan
        qr_image = generate_qr(encrypted_str)
        qr_status = "ok" if qr_image else "too_long"
        
        return jsonify({
            'result': encrypted_str,
            'key': key,
            'qr': qr_image,
            'qr_status': qr_status
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/text/decrypt', methods=['POST'])
def text_decrypt():
    data = request.json
    text = data.get('text', '')
    key = data.get('key', '')
    
    try:
        decrypted_bytes = decrypt_bytes(text.encode(), key)
        return jsonify({'result': decrypted_bytes.decode()})
    except:
        return jsonify({'result': '❌ Gagal! Key salah atau data rusak.'})

# 2. API UNTUK FILE (Upload)
@app.route('/api/file/encrypt', methods=['POST'])
def file_encrypt():
    if 'file' not in request.files: return jsonify({'error': 'No file'})
    
    try:
        file = request.files['file']
        file_data = file.read()
        key = generate_key()
        
        encrypted_data = encrypt_bytes(file_data, key)
        
        return jsonify({
            'filename': file.filename + ".enc",
            'file_data': base64.b64encode(encrypted_data).decode(),
            'key': key
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/file/decrypt', methods=['POST'])
def file_decrypt():
    if 'file' not in request.files: return jsonify({'error': 'No file'})
    
    try:
        file = request.files['file']
        key = request.form.get('key')
        file_data = file.read()
        
        decrypted_data = decrypt_bytes(file_data, key)
        orig_name = file.filename.replace('.enc', '')
        
        return jsonify({
            'filename': "UNLOCKED_" + orig_name,
            'file_data': base64.b64encode(decrypted_data).decode()
        })
    except:
        return jsonify({'error': 'Gagal Dekripsi! Key salah atau file rusak.'})

# Penting untuk local testing, Vercel akan ignore ini
if __name__ == '__main__':
    app.run(debug=True)
