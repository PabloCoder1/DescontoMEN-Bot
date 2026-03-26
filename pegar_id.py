import requests
import urllib3

# Isso aqui serve para tirar aquele aviso chato de "Conexão Insegura" do terminal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://desconto-men-evolution-api.qkyhax.easypanel.host"
KEY = "429683C4C977415CAAFCCE10F7D57E11"
INSTANCE = "desconto-men"

def listar_grupos():
    # Rota correta para a versão v2 da Evolution
    url = f"{URL}/group/fetchAllGroups/{INSTANCE}?getParticipants=false"
    headers = {"apikey": KEY}
    
    try:
        # O pulo do gato: verify=False ignora o erro de certificado SSL
        res = requests.get(url, headers=headers, verify=False) 
        if res.status_code == 200:
            grupos = res.json()
            print("\n📋 LISTA DE GRUPOS ENCONTRADOS:")
            for g in grupos:
                print(f"Nome: {g.get('subject')} | ID: {g.get('id')}")
        else:
            print(f"❌ Erro na API: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"💥 Erro de conexão: {e}")

if __name__ == "__main__":
    listar_grupos()