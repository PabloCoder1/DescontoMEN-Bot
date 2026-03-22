import cloudscraper
from bs4 import BeautifulSoup
import time, json, requests, os, random
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online!"
def run(): app.run(host='0.0.0.0', port=8080)

TOKEN_TELEGRAM = "8610297805:AAHq2rzzImn9WEfOPdRrz4y_xM83MQ1qx6w"
CHAT_ID = "2050785699"
MEU_TAG_AFILIADO = "gd20260319125059"
MEU_TOOL_ID = "64029233"
ARQUIVO_HISTORICO = "historico_precos.json"
TERMOS_BUSCA = ["perfume masculino", "camiseta masculina ribana", "tenis nike masculino", "relogio masculino"]

def gerar_link(url):
    limpa = url.split('?')[0].split('#')[0]
    return f"{limpa}?matt_tool={MEU_TOOL_ID}&matt_word={MEU_TAG_AFILIADO}"

def monitor():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    # Carrega histórico
    if os.path.exists(ARQUIVO_HISTORICO):
        with open(ARQUIVO_HISTORICO, 'r') as f: historico = json.load(f)
    else: historico = {}

    print("💰 DescontoMEN Online e Vigiando!", flush=True)

    while True:
        agora = time.strftime('%H:%M:%S')
        print(f"⏰ {agora} - Iniciando varredura...", flush=True)
        sacola = []
        
        for termo in TERMOS_BUSCA:
            url = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
            try:
                res = scraper.get(url, timeout=20)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    cards = soup.select('.poly-card') or soup.select('.ui-search-result__wrapper')
                    
                    for card in cards:
                        try:
                            p_tags = card.select('.andes-money-amount__fraction')
                            if len(p_tags) >= 2:
                                p_new = float(p_tags[1].text.replace('.',''))
                                titulo = card.select_one('.poly-component__title') or card.select_one('h2')
                                nome = titulo.text.strip()
                                
                                if nome not in historico:
                                    historico[nome] = p_new
                                elif p_new < historico[nome]:
                                    link = gerar_link(card.select_one('a')['href'])
                                    foto = (card.select_one('img').get('data-src') or card.select_one('img').get('src'))
                                    sacola.append({
                                        'foto': foto, 
                                        'msg': f"🔥 <b>PREÇO BAIXOU!</b>\n\n✅ {nome}\n\nDe R$ {historico[nome]:.2f} ❌\nPor R$ {p_new:.2f} ✅\n\n🔗 Link: {link}"
                                    })
                                    historico[nome] = p_new
                        except: continue
                else:
                    print(f"⚠️ Erro no ML ({termo}): Status {res.status_code}", flush=True)
            except Exception as e:
                print(f"❌ Falha de conexão: {e}", flush=True)
            time.sleep(2)

        if sacola:
            print(f"📦 Enviando {len(sacola)} ofertas misturadas...", flush=True)
            random.shuffle(sacola)
            for item in sacola:
                requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                             data={"chat_id": CHAT_ID, "photo": item['foto'], "caption": item['msg'], "parse_mode": "HTML"})
                time.sleep(15)
        else:
            print("🔍 Nada novo com preço menor nesta rodada.", flush=True)

        with open(ARQUIVO_HISTORICO, 'w') as f: json.dump(historico, f, indent=4)
        print("💤 Ciclo finalizado. Aguardando 30 minutos...", flush=True)
        time.sleep(1800)

if __name__ == "__main__":
    Thread(target=run).start()
    monitor()