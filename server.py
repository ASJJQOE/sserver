from flask import Flask, request, Response, jsonify
import queue

app = Flask(__name__)

# Diccionario para gestionar múltiples celulares de forma independiente
dispositivos = {}

def obtener_o_crear(device_id):
    if device_id not in dispositivos:
        dispositivos[device_id] = {
            "cmd_queue": queue.Queue(maxsize=1),
            "video_queue": queue.Queue(maxsize=1)
        }
    return dispositivos[device_id]

@app.route('/list_devices', methods=['GET'])
def list_devices():
    """Nueva ruta para que el PC vea quién está conectado"""
    return jsonify(list(dispositivos.keys()))

@app.route('/send_cmd/<device_id>', methods=['POST'])
def send_cmd(device_id):
    data = request.get_json()
    disp = obtener_o_crear(device_id)
    if not disp["cmd_queue"].full():
        disp["cmd_queue"].put(data['cmd'])
    return jsonify({"status": "Enviado"})

@app.route('/get_cmd/<device_id>', methods=['GET'])
def get_cmd(device_id):
    disp = obtener_o_crear(device_id)
    try:
        return disp["cmd_queue"].get(timeout=0.1)
    except:
        return ""

@app.route('/upload_frame/<device_id>', methods=['POST'])
def upload_frame(device_id):
    disp = obtener_o_crear(device_id)
    if not disp["video_queue"].full():
        disp["video_queue"].put(request.data)
    else:
        disp["video_queue"].get()
        disp["video_queue"].put(request.data)
    return "OK"

@app.route('/stream/<device_id>')
def stream(device_id):
    disp = obtener_o_crear(device_id)
    def generate():
        while True:
            frame = disp["video_queue"].get()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)