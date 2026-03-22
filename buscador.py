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
TERMOS_BUSCA = ["perfume masculino", "camiseta masculina", "tenis masculino", "relogio masculino"]

def gerar_link(url):
    limpa = url.split('?')[0].split('#')[0]
    return f"{limpa}?matt_tool={MEU_TOOL_ID}&matt_word={MEU_TAG_AFILIADO}"

def monitor():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
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
                                p_old = float(p_tags[0].text.replace('.',''))
                                p_new = float(p_tags[1].text.replace('.',''))
                                
                                titulo = card.select_one('.poly-component__title') or card.select_one('h2')
                                nome = titulo.text.strip()
                                
                                enviar_agora = False
                                motivo = ""

                                # LÓGICA DE DECISÃO MELHORADA
                                if nome not in historico:
                                    # É a primeira vez que vemos o item? Se tiver desconto "De/Por", já manda!
                                    historico[nome] = p_new
                                    if p_new < p_old:
                                        enviar_agora = True
                                        motivo = "🔥 OFERTA ENCONTRADA!"
                                elif p_new < historico[nome]:
                                    # O preço baixou comparado ao que tínhamos guardado
                                    enviar_agora = True
                                    motivo = "📉 PREÇO BAIXOU MAIS!"
                                    historico[nome] = p_new
                                
                                if enviar_agora:
                                    link = gerar_link(card.select_one('a')['href'])
                                    img_tag = card.select_one('img')
                                    foto = img_tag.get('data-src') or img_tag.get('src')
                                    
                                    sacola.append({
                                        'foto': foto, 
                                        'msg': f"{motivo}\n\n✅ {nome}\n\nDe R$ {p_old:.2f} ❌\nPor R$ {p_new:.2f} ✅\n\n🔗 Link: {link}"
                                    })
                        except: continue
                time.sleep(1)
            except: continue

        if sacola:
            print(f"📦 Enviando {len(sacola)} ofertas...", flush=True)
            random.shuffle(sacola)
            for item in sacola:
                requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                             data={"chat_id": CHAT_ID, "photo": item['foto'], "caption": item['msg'], "parse_mode": "HTML"})
                time.sleep(15)
        else:
            print("🔍 Sem mudanças relevantes nesta rodada.", flush=True)

        with open(ARQUIVO_HISTORICO, 'w') as f: json.dump(historico, f, indent=4)
        print("💤 Ciclo finalizado. Aguardando 30 minutos...", flush=True)
        time.sleep(1800)

if __name__ == "__main__":
    Thread(target=run).start()
    monitor()