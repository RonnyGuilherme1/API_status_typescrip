import requests

CONTROLID_IP = "192.168.50.234"
CONTROLID_STATUS_URL = f"http://{CONTROLID_IP}/api/status"

API_SERVER = "http://localhost:5000/api/heartbeat"
SERIAL = "CID-TESTE-001"

def check_device():
    try:
        r = requests.get(CONTROLID_STATUS_URL, timeout=3)
        if r.status_code == 200:
            requests.post(API_SERVER, json={"serial": SERIAL}, timeout=3)
    except:
        pass

if __name__ == "__main__":
    check_device()
