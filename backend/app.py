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

    device.last_seen = datetime.utcnow()
    db.session.commit()

    return {"status": "ok"}


@app.route('/api/devices', methods=['GET'])
def list_devices():
    devices = Device.query.all()
    result = []
    
    for d in devices:
        status = d.status()
        if status == "ONLINE":
            d.last_seen = datetime.now()
        
        result.append({
            "cliente": d.cliente,
            "serial": d.serial,
            "ip": d.ip,
            "status": status,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None
        })
    
    db.session.commit()
    return jsonify(result)


@app.route('/api/secullum/sync', methods=['POST'])
def sync_from_secullum():
    try:
        equipamentos = secullum.get_equipamentos()
        
        synced = 0
        for equip in equipamentos:
            equip_id = equip.get("Id")
            descricao = equip.get("Descricao", "Sem nome")
            ip = equip.get("EnderecoIP", "")
            
            device = Device.query.filter_by(secullum_id=equip_id).first()
            
            if not device:
                device = Device(
                    cliente=descricao,
                    serial=str(equip_id),
                    ip=ip or "0.0.0.0",
                    secullum_id=equip_id
                )
                db.session.add(device)
                synced += 1
            else:
                device.cliente = descricao
                if ip:
                    device.ip = ip
        
        db.session.commit()
        
        return jsonify({
            "status": "ok",
            "total_equipamentos": len(equipamentos),
            "novos_sincronizados": synced
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


if __name__ == '__main__':
    app.run(debug=True)
