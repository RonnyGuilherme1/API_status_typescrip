from database import db
from datetime import datetime
import subprocess
import platform

class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(120), nullable=False)
    serial = db.Column(db.String(60), unique=True, nullable=False)
    ip = db.Column(db.String(50), nullable=False)
    last_seen = db.Column(db.DateTime)
    secullum_id = db.Column(db.Integer, unique=True, nullable=True)

    def ping_device(self):
        param = "-n" if platform.system().lower() == "windows" else "-c"
        try:
            result = subprocess.run(
                ["ping", param, "1", "-w", "1000", self.ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False

    def status(self):
        if self.ping_device():
            return "ONLINE"
        
        if not self.last_seen:
            return "OFFLINE"

        diff = (datetime.now() - self.last_seen).total_seconds()

        if diff <= 300:
            return "INSTAVEL"
        return "OFFLINE"
