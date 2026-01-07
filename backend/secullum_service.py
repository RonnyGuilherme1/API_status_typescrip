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
    
    def get_bancos(self):
        if not self.access_token:
            self.authenticate()
        return self.bancos
    
    def set_banco(self, banco_id):
        self.banco_id = str(banco_id)
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept-Language": "pt-BR",
            "secullumidbancoselecionado": self.banco_id
        }
    
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
    
    def get_ultimo_evento_por_equipamento(self):
        eventos = self.get_fonte_dados(dias=7)
        
        ultimo_por_equip = {}
        for evento in eventos:
            equip_id = evento.get("EquipamentoId")
            data = evento.get("Data")
            hora = evento.get("Hora", "00:00")
            
            if equip_id:
                timestamp = f"{data} {hora}"
                if equip_id not in ultimo_por_equip or timestamp > ultimo_por_equip[equip_id]:
                    ultimo_por_equip[equip_id] = timestamp
        
        return ultimo_por_equip


secullum = SecullumService()
