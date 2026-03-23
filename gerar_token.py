import requests

# Suas credenciais oficiais
APP_ID = "1338353570016376"
CLIENT_SECRET = "aB5Oo52uktBbTwVVATP4tRyzoreymwgT"
REDIRECT_URI = "https://www.google.com" # Deve ser IGUAL ao que está no dashboard

# O código que você acabou de me passar
CODE = "TG-69c1bdbac904c8000152dc6d-3279577120"

def trocar_codigo_por_token():
    url = "https://api.mercadolibre.com/oauth/token"
    
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded'
    }
    
    payload = {
        'grant_type': 'authorization_code',
        'client_id': APP_ID,
        'client_secret': CLIENT_SECRET,
        'code': CODE,
        'redirect_uri': REDIRECT_URI
    }

    print("🚀 Trocando código por Access Token...")
    response = requests.post(url, data=payload, headers=headers)
    
    if response.status_code == 200:
        dados = response.json()
        print("\n✅ SUCESSO TOTAL!")
        print(f"ACCESS_TOKEN: {dados['access_token']}")
        print(f"REFRESH_TOKEN: {dados['refresh_token']}")
        print(f"EXPIRA EM: {dados['expires_in']} segundos (6 horas)")
        print("\n👉 COPIE E GUARDE ESSES DOIS TOKENS!")
    else:
        print(f"❌ Erro {response.status_code}: {response.text}")

if __name__ == "__main__":
    trocar_codigo_por_token()