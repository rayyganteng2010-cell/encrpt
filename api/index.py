from flask import Flask, render_template, request, jsonify, send_file
from cryptography.fernet import Fernet
import base64
import os
import io

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

# --- HELPER: KEY GENERATOR ---
def generate_key():
    return Fernet.generate_key().decode()

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

# ==========================================
# MODE 1: OBFUSCATOR (Runable Scrambled Code)
# ==========================================
@app.route('/api/obfuscate', methods=['POST'])
def obfuscate():
    # Cek apakah user upload file atau input text
    code = ""
    filename = "result"
    lang = request.form.get('lang') # python, javascript, html

    if 'file' in request.files and request.files['file'].filename != '':
        f = request.files['file']
        code = f.read().decode('utf-8', errors='ignore')
        filename = f.filename
    else:
        code = request.form.get('code_text')
        if not code: return jsonify({'error': 'Code kosong!'})

    # Logic Obfuscation
    result_code = ""
    try:
        encoded_bytes = base64.b64encode(code.encode('utf-8'))
        encoded_str = encoded_bytes.decode('utf-8')

        if lang == 'python':
            result_code = f'import base64;exec(base64.b64decode("{encoded_str}"))'
            ext = ".py"
        elif lang == 'javascript':
            result_code = f'eval(atob("{encoded_str}"));'
            ext = ".js"
        elif lang == 'html':
            result_code = f'<script>document.write(atob("{encoded_str}"));</script>'
            ext = ".html"
        else:
            return jsonify({'error': 'Bahasa tidak support!'})

        # Return sebagai file download
        mem = io.BytesIO()
        mem.write(result_code.encode('utf-8'))
        mem.seek(0)
        
        return send_file(
            mem, 
            as_attachment=True, 
            download_name=f"OBFUSCATED_{filename}{ext}", 
            mimetype="text/plain"
        )

    except Exception as e:
        return jsonify({'error': str(e)})


# ==========================================
# MODE 2: VAULT (Encryption Mati / Lock)
# ==========================================
@app.route('/api/vault/lock', methods=['POST'])
def vault_lock():
    key = generate_key()
    f_crypto = Fernet(key.encode())
    
    # 1. Jika Input Text Biasa
    if 'text_data' in request.form and request.form['text_data']:
        text = request.form['text_data']
        enc_text = f_crypto.encrypt(text.encode()).decode()
        return jsonify({'type': 'text', 'result': enc_text, 'key': key})

    # 2. Jika Input File (Foto/Video/Dll)
    if 'file_data' in request.files:
        file = request.files['file_data']
        file_bytes = file.read()
        
        # Limitasi Vercel (PENTING: Vercel punya limit body size 4.5MB)
        if len(file_bytes) > 4 * 1024 * 1024:
            return jsonify({'error': 'File terlalu besar untuk Serverless (Max 4MB).'})

        enc_bytes = f_crypto.encrypt(file_bytes)
        
        mem = io.BytesIO()
        mem.write(enc_bytes)
        mem.seek(0)
        
        return jsonify({
            'type': 'file',
            'filename': file.filename + ".enc",
            'file_b64': base64.b64encode(mem.getvalue()).decode(), # Kirim base64 ke frontend
            'key': key
        })

    return jsonify({'error': 'Tidak ada data!'})

@app.route('/api/vault/unlock', methods=['POST'])
def vault_unlock():
    key = request.form.get('key')
    if not key: return jsonify({'error': 'Mana kuncinya?'})
    
    try:
        f_crypto = Fernet(key.encode())

        # 1. Unlock Text
        if 'text_data' in request.form and request.form['text_data']:
            enc_text = request.form['text_data']
            dec_text = f_crypto.decrypt(enc_text.encode()).decode()
            return jsonify({'type': 'text', 'result': dec_text})

        # 2. Unlock File
        if 'file_data' in request.files:
            file = request.files['file_data']
            file_bytes = file.read()
            dec_bytes = f_crypto.decrypt(file_bytes)
            
            # Hapus ekstensi .enc
            orig_name = file.filename.replace('.enc', '')
            
            return jsonify({
                'type': 'file',
                'filename': "UNLOCKED_" + orig_name,
                'file_b64': base64.b64encode(dec_bytes).decode()
            })
            
    except Exception as e:
        return jsonify({'error': 'Gagal! Key salah atau file rusak.'})
        
    return jsonify({'error': 'Data invalid'})

if __name__ == '__main__':
    app.run(debug=True)
