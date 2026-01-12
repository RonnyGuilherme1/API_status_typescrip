from flask import Flask, jsonify, request
from flask_cors import CORS
from database import db
from models import Device
from datetime import datetime
from secullum_service import secullum
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "controlid.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ---------------- SECULLUM ----------------

@app.route('/api/secullum/banco/<int:banco_id>', methods=['POST'])
def set_secullum_banco(banco_id):
    secullum.set_banco(banco_id)
    return jsonify({"status": "ok", "banco_id": banco_id})


@app.route('/api/secullum/importar', methods=['POST'])
def importar_equipamentos():
    data = request.json or {}
    banco_id = data.get("banco_id")

    if not banco_id:
        return jsonify({"error": "Informe o banco_id"}), 400

    # Seleciona o banco no Secullum
    secullum.set_banco(banco_id)

    equipamentos = secullum.get_equipamentos()
    inseridos = 0

    for e in equipamentos:
        secullum_id = e.get("Id")
        descricao = e.get("Descricao", "Sem nome")
        ip = e.get("EnderecoIP") or "0.0.0.0"

        if Device.query.filter_by(secullum_id=secullum_id).first():
            continue

        device = Device(
            cliente=descricao,
            serial=f"SEC-{secullum_id}",
            ip=ip,
            secullum_id=secullum_id,
            fabricante="secullum"
        )

        db.session.add(device)
        inseridos += 1

    db.session.commit()
    return jsonify({"status": "ok", "importados": inseridos})



# ---------------- DEVICES ----------------

@app.route('/api/devices', methods=['GET'])
def list_devices():
    devices = Device.query.all()
    now = datetime.now()
    result = []

    for d in devices:
        last_seen = d.last_seen

        if d.secullum_id:
            evento = secullum.verificar_status_equipamento(d.secullum_id)
            if evento:
                d.last_seen = evento
                last_seen = evento

        status = "OFFLINE"
        if last_seen:
            diff = (now - last_seen).total_seconds()
            if diff <= 20:
                status = "ONLINE"
            elif diff <= 120:
                status = "INSTAVEL"

        result.append({
            "cliente": d.cliente,
            "serial": d.serial,
            "ip": d.ip,
            "status": status,
            "last_seen": last_seen.isoformat() if last_seen else None
        })

    db.session.commit()
    return jsonify(result)


@app.route('/api/devices/<serial>', methods=['PUT'])
def update_device(serial):
    device = Device.query.filter_by(serial=serial).first()

    if not device:
        return jsonify({"error": "Dispositivo não encontrado"}), 404

    data = request.json or {}

    if "new_serial" in data:
        device.serial = data["new_serial"]

    if "ip" in data:
        device.ip = data["ip"]

    if "fabricante" in data:
        device.fabricante = data["fabricante"]

    db.session.commit()
    return jsonify({"status": "ok"})


@app.route('/api/debug/devices', methods=['GET'])
def debug_devices():
    devices = Device.query.all()
    return jsonify([
        {
            "id": d.id,
            "cliente": d.cliente,
            "serial": d.serial,
            "ip": d.ip,
            "fabricante": d.fabricante,
            "secullum_id": d.secullum_id,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None
        }
        for d in devices
    ])


if __name__ == '__main__':
    app.run(debug=True)
