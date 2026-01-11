from flask import Flask, render_template, request, jsonify
import base64
import os

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)

# --- ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/obfuscate', methods=['POST'])
def obfuscate_code():
    data = request.json
    code = data.get('code', '')
    lang = data.get('lang', '') # python, javascript, atau html

    if not code:
        return jsonify({'error': 'Code kosong bro!'})

    try:
        result_code = ""
        
        # --- LOGIC 1: PYTHON OBFUSCATOR ---
        if lang == 'python':
            # Encode code asli ke Base64
            encoded_bytes = base64.b64encode(code.encode('utf-8'))
            encoded_str = encoded_bytes.decode('utf-8')
            
            # Bungkus dalam exec() biar tetep jalan pas di-run
            # Kita tambah layer sampah variable biar keliatan pusing
            result_code = f"""
import base64
_0x123 = "{encoded_str}"
exec(base64.b64decode(_0x123))
"""
        
        # --- LOGIC 2: JAVASCRIPT OBFUSCATOR ---
        elif lang == 'javascript':
            # Encode ke Base64
            encoded_bytes = base64.b64encode(code.encode('utf-8'))
            encoded_str = encoded_bytes.decode('utf-8')
            
            # Bungkus dalam eval(atob())
            result_code = f"""
var _0xenc = "{encoded_str}";
eval(atob(_0xenc));
"""

        # --- LOGIC 3: HTML OBFUSCATOR ---
        elif lang == 'html':
            # HTML Encrypt biasa dipake buat sembunyiin source code (View Page Source)
            # Kita encode isinya, lalu render pake JS document.write
            encoded_bytes = base64.b64encode(code.encode('utf-8'))
            encoded_str = encoded_bytes.decode('utf-8')
            
            result_code = f"""
<!DOCTYPE html>
<html>
<head><title>Protected Page</title></head>
<body>
<script type="text/javascript">
document.write(atob("{encoded_str}"));
</script>
</body>
</html>
"""
        else:
            return jsonify({'error': 'Bahasa tidak didukung!'})

        return jsonify({'result': result_code})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
