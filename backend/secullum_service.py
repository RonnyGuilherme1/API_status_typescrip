import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()


class SecullumService:
    AUTH_URL = "https://autenticador.secullum.com.br/Token"
    BANCOS_URL = "https://autenticador.secullum.com.br/ContasSecullumExterno/ListarBancos/"
    API_URL = "https://pontowebintegracaoexterna.secullum.com.br/IntegracaoExterna"

    def __init__(self):
        self.username = os.getenv("SECULLUM_USER")
        self.password = os.getenv("SECULLUM_PASSWORD")

        self.access_token = None
        self.expires_at = None
        self.banco_id = None

    # ---------- AUTH ----------
    def authenticate(self):
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": "3"
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(self.AUTH_URL, data=data, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Erro na autenticação Secullum: {response.text}")

        payload = response.json()

        self.access_token = payload.get("access_token")
        expires_in = payload.get("expires_in", 3600)

        # margem de segurança
        self.expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

    def _token_expirado(self):
        return not self.expires_at or datetime.now() >= self.expires_at

    # ---------- HELPERS ----------
    def _get_headers(self):
        if not self.access_token or self._token_expirado():
            self.authenticate()

        if not self.banco_id:
            raise Exception("Banco Secullum não selecionado")

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept-Language": "pt-BR",
            "secullumidbancoselecionado": str(self.banco_id)
        }

    # ---------- API ----------
    def get_bancos(self):
        if not self.access_token or self._token_expirado():
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        r = requests.get(self.BANCOS_URL, headers=headers)

        if r.status_code != 200:
            raise Exception("Erro ao listar bancos")

        return r.json()

    def set_banco(self, banco_id):
        self.banco_id = banco_id

    def get_equipamentos(self):
        url = f"{self.API_URL}/Equipamentos"
        r = requests.get(url, headers=self._get_headers())

        if r.status_code != 200:
            raise Exception(f"Erro ao buscar equipamentos: {r.text}")

        return r.json()

    def get_fonte_dados(self, equipamento_id, dias=1):
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=dias)

        params = {
            "dataInicio": data_inicio.strftime("%Y-%m-%d"),
            "dataFim": data_fim.strftime("%Y-%m-%d"),
            "equipamentoId": equipamento_id
        }

        url = f"{self.API_URL}/FonteDados"
        r = requests.get(url, headers=self._get_headers(), params=params)

        if r.status_code != 200:
            raise Exception(f"Erro ao buscar fonte de dados: {r.text}")

        return r.json()

    def verificar_status_equipamento(self, equipamento_id):
        eventos = self.get_fonte_dados(equipamento_id, dias=1)
        timestamps = []

        for e in eventos:
            try:
                dt = datetime.strptime(
                    f"{e.get('Data')} {e.get('Hora')}",
                    "%Y-%m-%d %H:%M"
                )
                timestamps.append(dt)
            except:
                pass

        return max(timestamps) if timestamps else None


secullum = SecullumService()
