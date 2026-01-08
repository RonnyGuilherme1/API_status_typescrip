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


@app.route('/api/devices/test', methods=['POST'])
def create_test_device():
    serial = '0m0200/026370'

    device = Device.query.filter_by(serial=serial).first()
    if device:
        return jsonify({
            "status": "exists",
            "message": "Dispositivo já cadastrado"
        }), 200

    device = Device(
        cliente='Cliente Teste',
        serial=serial,
        ip='192.168.50.234'
    )

    db.session.add(device)
    db.session.commit()

    return jsonify({
        "status": "created",
        "message": "Dispositivo criado com sucesso"
    }), 201


@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    serial = data.get('serial')

    device = Device.query.filter_by(serial=serial).first()
    if not device:
        return {"error": "Device not found"}, 404

    device.last_seen = datetime.now()
    db.session.commit()

    return {"status": "ok"}


@app.route('/api/devices', methods=['GET'])
def list_devices():
    devices = Device.query.all()
    result = []

    now = datetime.now()

    for d in devices:
        last_seen = d.last_seen

        # 🔹 Prioridade 1: Secullum
        if d.secullum_id:
            secullum_event = secullum.verificar_status_equipamento(d.secullum_id)
            if secullum_event:
                last_seen = secullum_event
                d.last_seen = secullum_event

        # 🔹 Define status APENAS pelo last_seen
        status = "OFFLINE"

        if last_seen:
            diff = (now - last_seen).total_seconds()

            if diff <= 20:
                status = "ONLINE"
            elif diff <= 120:
                status = "INSTAVEL"
            else:
                status = "OFFLINE"

        result.append({
            "cliente": d.cliente,
            "serial": d.serial,
            "ip": d.ip,
            "status": status,
            "last_seen": last_seen.isoformat() if last_seen else None
        })

    db.session.commit()
    return jsonify(result)



@app.route('/api/secullum/sync', methods=['POST'])
def sync_from_secullum():
    try:
        equipamentos = secullum.get_equipamentos()
        atualizados = 0

        for equip in equipamentos:
            equip_id = equip.get("Id")
            descricao = equip.get("Descricao", "Sem nome")
            ip = equip.get("EnderecoIP", "")

            device = Device.query.filter_by(secullum_id=equip_id).first()
            if not device:
                continue

            device.cliente = descricao
            if ip:
                device.ip = ip

            atualizados += 1

        db.session.commit()

        return jsonify({
            "status": "ok",
            "equipamentos_no_secullum": len(equipamentos),
            "equipamentos_atualizados_no_banco": atualizados
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/secullum/equipamentos', methods=['GET'])
def get_secullum_equipamentos():
    try:
        equipamentos = secullum.get_equipamentos()
        return jsonify(equipamentos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/secullum/fonte-dados/<int:equip_id>', methods=['GET'])
def get_fonte_dados(equip_id):
    try:
        dados = secullum.get_fonte_dados(equipamento_id=equip_id, dias=7)
        return jsonify(dados)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/secullum/bancos', methods=['GET'])
def get_secullum_bancos():
    try:
        bancos = secullum.get_bancos()
        return jsonify(bancos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/secullum/banco/<int:banco_id>', methods=['POST'])
def set_secullum_banco(banco_id):
    try:
        secullum.set_banco(banco_id)
        return jsonify({"status": "ok", "banco_id": banco_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/devices/<serial>/ip', methods=['PUT'])
def update_device_ip(serial):
    data = request.get_json()
    new_ip = data.get('ip')

    if not new_ip:
        return jsonify({"error": "IP não informado"}), 400

    device = Device.query.filter_by(serial=serial).first()
    if not device:
        return jsonify({"error": "Dispositivo não encontrado"}), 404

    device.ip = new_ip
    db.session.commit()

    return jsonify({
        "status": "ok",
        "serial": serial,
        "ip": new_ip
    })


@app.route('/api/devices/<serial>', methods=['PUT'])
def update_device(serial):
    data = request.get_json()

    device = Device.query.filter_by(serial=serial).first()
    if not device:
        return jsonify({"error": "Dispositivo não encontrado"}), 404

    if 'cliente' in data:
        device.cliente = data['cliente']
    if 'ip' in data:
        device.ip = data['ip']
    if 'new_serial' in data:
        device.serial = data['new_serial']

    db.session.commit()

    return jsonify({
        "status": "ok",
        "device": {
            "cliente": device.cliente,
            "serial": device.serial,
            "ip": device.ip
        }
    })


@app.route('/api/debug/devices', methods=['GET'])
def debug_devices():
    devices = Device.query.all()
    return jsonify([
        {
            "id": d.id,
            "cliente": d.cliente,
            "serial": d.serial,
            "ip": d.ip,
            "secullum_id": d.secullum_id,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None
        }
        for d in devices
    ])


if __name__ == '__main__':
    app.run(debug=True)
