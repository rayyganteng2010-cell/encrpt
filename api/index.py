from flask import Flask, render_template, request, jsonify, send_file
from cryptography.fernet import Fernet
import base64
import os
import io

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

# --- HELPER ---
def generate_key():
    return Fernet.generate_key().decode()

@app.route('/')
def home():
    return render_template('index.html')

# ==========================================
# MODE 1: OBFUSCATOR (UTF-8 SAFE & EMOJI SUPPORT)
# ==========================================
@app.route('/api/obfuscate', methods=['POST'])
def obfuscate():
    code = ""
    filename = "result"
    lang = request.form.get('lang') 

    # 1. Handle Input (File / Text)
    if 'file' in request.files and request.files['file'].filename != '':
        f = request.files['file']
        # Pakai utf-8 dan ignore error biar emoji ga bikin crash
        code = f.read().decode('utf-8', errors='ignore') 
        filename = f.filename
    else:
        code = request.form.get('code_text')
        if not code: return jsonify({'error': 'Code kosong!'})

    # 2. Logic Obfuscation (ANTI-GARBLED TEXT)
    try:
        # Encode script asli ke Base64 UTF-8
        encoded_bytes = base64.b64encode(code.encode('utf-8'))
        encoded_str = encoded_bytes.decode('utf-8')
        
        result_code = ""
        ext = ".txt"

        if lang == 'python':
            # Python support utf-8 native, aman
            result_code = f'# Encrypted by RayCrypto\nimport base64\nexec(base64.b64decode("{encoded_str}").decode("utf-8"))'
            ext = ".py"
            
        elif lang == 'javascript':
            # JS butuh decodeURIComponent(escape(...)) buat handle Emoji/UTF-8
            result_code = f"""
// Encrypted by RayCrypto
var _0x = "{encoded_str}";
var _0xDec = function(str) {{
    return decodeURIComponent(escape(window.atob(str)));
}};
eval(_0xDec(_0x));
"""
            ext = ".js"

        elif lang == 'html':
            # HTML Paling rawan error encoding. Kita pake wrapper script UTF-8 safe.
            result_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Protected Page</title>
</head>
<body>
<script type="text/javascript">
    var _0x = "{encoded_str}";
    function _utf8_decode(str) {{
        return decodeURIComponent(escape(window.atob(str)));
    }}
    document.write(_utf8_decode(_0x));
</script>
</body>
</html>"""
            ext = ".html"
            
        else:
            return jsonify({'error': 'Bahasa tidak support!'})

        # Kirim File
        mem = io.BytesIO()
        mem.write(result_code.encode('utf-8')) # Pastikan output file formatnya UTF-8
        mem.seek(0)
        
        return send_file(
            mem, 
            as_attachment=True, 
            download_name=f"ENC_{filename}{ext}", 
            mimetype="text/plain"
        )

    except Exception as e:
        return jsonify({'error': str(e)})


# ==========================================
# MODE 2: VAULT (SAMA SEPERTI SEBELUMNYA)
# ==========================================
@app.route('/api/vault/lock', methods=['POST'])
def vault_lock():
    key = generate_key()
    f_crypto = Fernet(key.encode())
    
    if 'text_data' in request.form and request.form['text_data']:
        text = request.form['text_data']
        # Encode text input ke bytes utf-8 dulu sebelum encrypt
        enc_text = f_crypto.encrypt(text.encode('utf-8')).decode('utf-8')
        return jsonify({'type': 'text', 'result': enc_text, 'key': key})

    if 'file_data' in request.files:
        file = request.files['file_data']
        file_bytes = file.read()
        
        if len(file_bytes) > 4 * 1024 * 1024:
            return jsonify({'error': 'File max 4MB!'})

        enc_bytes = f_crypto.encrypt(file_bytes)
        mem = io.BytesIO()
        mem.write(enc_bytes)
        mem.seek(0)
        
        return jsonify({
            'type': 'file',
            'filename': file.filename + ".enc",
            'file_b64': base64.b64encode(mem.getvalue()).decode('utf-8'),
            'key': key
        })

    return jsonify({'error': 'Data kosong!'})

@app.route('/api/vault/unlock', methods=['POST'])
def vault_unlock():
    key = request.form.get('key')
    if not key: return jsonify({'error': 'Butuh Key!'})
    
    try:
        f_crypto = Fernet(key.encode())

        if 'text_data' in request.form and request.form['text_data']:
            enc_text = request.form['text_data']
            dec_text = f_crypto.decrypt(enc_text.encode('utf-8')).decode('utf-8')
            return jsonify({'type': 'text', 'result': dec_text})

        if 'file_data' in request.files:
            file = request.files['file_data']
            file_bytes = file.read()
            dec_bytes = f_crypto.decrypt(file_bytes)
            orig_name = file.filename.replace('.enc', '')
            
            return jsonify({
                'type': 'file',
                'filename': "OPEN_" + orig_name,
                'file_b64': base64.b64encode(dec_bytes).decode('utf-8')
            })
            
    except Exception as e:
        return jsonify({'error': 'Gagal! Key salah atau file rusak.'})
        
    return jsonify({'error': 'Data invalid'})

if __name__ == '__main__':
    app.run(debug=True)
