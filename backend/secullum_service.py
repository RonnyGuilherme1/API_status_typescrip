import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()


class SecullumService:
    AUTH_URL = "https://autenticador.secullum.com.br/Token"
    CLAIMS_URL = "https://autenticador.secullum.com.br/ReinvidicacoesToken"
    BANCOS_URL = "https://autenticador.secullum.com.br/ContasSecullumExterno/ListarBancos/"
    API_URL = "https://pontowebintegracaoexterna.secullum.com.br/IntegracaoExterna"

    def __init__(self):
        self.username = os.getenv("SECULLUM_USER")
        self.password = os.getenv("SECULLUM_PASSWORD")
        self.access_token = None
        self.banco_id = None
        self.bancos = []

    # ---------------- AUTH ----------------

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
            raise Exception(f"Erro na autenticação: {response.text}")

        result = response.json()
        self.access_token = result.get("access_token")

        self._get_banco_id()
        return self.access_token

    def _get_banco_id(self):
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.get(self.BANCOS_URL, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Erro ao obter bancos ({response.status_code}): {response.text}")

        all_bancos = response.json()
        self.bancos = [b for b in all_bancos if b.get("clienteId") == "3"]

        if self.bancos:
            self.banco_id = str(self.bancos[0].get("id"))

        return self.banco_id

    # ---------------- HELPERS ----------------

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept-Language": "pt-BR",
            "secullumidbancoselecionado": self.banco_id
        }

    def _parse_secullum_datetime(self, data_str, hora_str=None):
        if not data_str:
            return None

        try:
            if "T" in data_str:
                return datetime.fromisoformat(data_str)

            if hora_str:
                return datetime.strptime(
                    f"{data_str} {hora_str}", "%Y-%m-%d %H:%M"
                )

            return datetime.strptime(data_str, "%Y-%m-%d")

        except Exception as e:
            print(f"Erro ao converter data Secullum: {data_str} {hora_str} -> {e}")
            return None

    # ---------------- API ----------------

    def get_bancos(self):
        if not self.access_token:
            self.authenticate()
        return self.bancos

    def set_banco(self, banco_id):
        self.banco_id = str(banco_id)

    def get_equipamentos(self):
        if not self.access_token:
            self.authenticate()

        url = f"{self.API_URL}/Equipamentos"
        response = requests.get(url, headers=self._get_headers())

        if response.status_code != 200:
            raise Exception(f"Erro ao buscar equipamentos: {response.text}")

        return response.json()

    def get_fonte_dados(self, equipamento_id=None, dias=1):
        if not self.access_token:
            self.authenticate()

        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=dias)

        params = {
            "dataInicio": data_inicio.strftime("%Y-%m-%d"),
            "dataFim": data_fim.strftime("%Y-%m-%d")
        }

        if equipamento_id:
            params["equipamentoId"] = equipamento_id

        url = f"{self.API_URL}/FonteDados"
        response = requests.get(url, headers=self._get_headers(), params=params)

        if response.status_code != 200:
            raise Exception(f"Erro ao buscar fonte de dados: {response.text}")

        return response.json()

    def get_batidas(self, equipamento_id=None, dias=1):
        if not self.access_token:
            self.authenticate()

        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=dias)

        params = {
            "dataInicio": data_inicio.strftime("%Y-%m-%d"),
            "dataFim": data_fim.strftime("%Y-%m-%d")
        }

        if equipamento_id:
            params["equipamentoId"] = equipamento_id

        url = f"{self.API_URL}/Batidas"
        response = requests.get(url, headers=self._get_headers(), params=params)

        if response.status_code != 200:
            raise Exception(f"Erro ao buscar batidas: {response.text}")

        return response.json()

    # ---------------- STATUS ----------------

    def verificar_status_equipamento(self, equipamento_id):
        try:
            eventos = self.get_fonte_dados(equipamento_id=equipamento_id, dias=1)

            timestamps = []

            for e in eventos:
                data = e.get("Data")
                hora = e.get("Hora")

                dt = self._parse_secullum_datetime(data, hora)
                if dt:
                    timestamps.append(dt)

            if not timestamps:
                return None

            return max(timestamps)

        except Exception as e:
            print(f"Erro Secullum {equipamento_id}: {e}")
            return None



secullum = SecullumService()
