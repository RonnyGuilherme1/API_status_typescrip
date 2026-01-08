from database import db
from datetime import datetime

class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(120), nullable=False)
    serial = db.Column(db.String(60), unique=True, nullable=False)
    ip = db.Column(db.String(50), nullable=False)

    # Última comunicação válida (Secullum ou Heartbeat)
    last_seen = db.Column(db.DateTime, nullable=True)

    # ID do equipamento no Secullum
    secullum_id = db.Column(db.Integer, unique=True, nullable=True)

    def to_dict(self):
        """
        Serializa o dispositivo para JSON.
        O status é calculado no backend (app.py),
        nunca aqui.
        """
        return {
            "id": self.id,
            "cliente": self.cliente,
            "serial": self.serial,
            "ip": self.ip,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "secullum_id": self.secullum_id
        }

    def __repr__(self):
        return f"<Device {self.serial}>"
