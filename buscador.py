import cloudscraper
from bs4 import BeautifulSoup
import time, json, requests, os, random
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online!"
def run(): app.run(host='0.0.0.0', port=8080)

# --- CONFIGURAÇÕES ---
TOKEN_TELEGRAM = "8610297805:AAHq2rzzImn9WEfOPdRrz4y_xM83MQ1qx6w"
CHAT_ID = "2050785699"
MEU_TAG_AFILIADO = "gd20260319125059"
MEU_TOOL_ID = "64029233"
ARQUIVO_HISTORICO = "historico_precos.json"
TERMOS_BUSCA = ["perfume masculino", "camiseta masculina", "tenis masculino", "relogio masculino"]

def gerar_link(url):
    limpa = url.split('?')[0].split('#')[0]
    return f"{limpa}?matt_tool={MEU_TOOL_ID}&matt_word={MEU_TAG_AFILIADO}"

def obter_chamada_impacto(nome):
    """Gera aquelas frases que chamam a atenção no topo da mensagem"""
    n = nome.lower()
    if "perfume" in n:
        return random.choice(["CHEIRINHO DE SUCESSO! 🔥", "PRESENÇA MARCANTE! 🔥", "PREÇO DE OUTRO MUNDO! 🔥", "TÁ DADO ESSE PERFUME! 🔥"])
    if "camiseta" in n or "camisa" in n:
        return random.choice(["ESTILO NO PRECINHO! 🔥", "BÁSICA DE RESPEITO! 🔥", "TÁ DADA ESSA PEÇA! 🔥", "PRA RENOVAR O GUARDA-ROUPA! 🔥"])
    if "tênis" in n or "tenis" in n:
        return random.choice(["PISANTE NOVO NO PÉ! 🔥", "CONFORTO E ESTILO! 🔥", "TÁ DADO ESSE TÊNIS! 🔥", "OPORTUNIDADE ÚNICA! 🔥"])
    return random.choice(["TÁ DADO DEMAIS! 🔥", "OFERTA DO DIA! 🔥", "CORRE QUE ACABA! 🔥"])

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
                                
                                deve_enviar = False
                                if nome not in historico:
                                    historico[nome] = p_new
                                    if p_new < p_old: deve_enviar = True
                                elif p_new < historico[nome]:
                                    historico[nome] = p_new
                                    deve_enviar = True
                                
                                if deve_enviar:
                                    link = gerar_link(card.select_one('a')['href'])
                                    img_tag = card.select_one('img')
                                    foto = img_tag.get('data-src') or img_tag.get('src')
                                    chamada = obter_chamada_impacto(nome)
                                    
                                    # --- O SEU NOVO FORMATO AQUI ---
                                    msg = (f"<b>{chamada}</b>\n\n"
                                           f"✅ {nome}\n\n"
                                           f"De R$ {p_old:.2f} ❌\n"
                                           f"Por R$ {p_new:.2f} ✅\n\n"
                                           f"🔗 Link: {link}")
                                    
                                    sacola.append({'foto': foto, 'msg': msg})
                        except: continue
                time.sleep(2)
            except: continue

        if sacola:
            print(f"📦 Enviando {len(sacola)} ofertas no novo formato...", flush=True)
            random.shuffle(sacola)
            for item in sacola:
                requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                             data={"chat_id": CHAT_ID, "photo": item['foto'], "caption": item['msg'], "parse_mode": "HTML"})
                time.sleep(15)
        else:
            print("🔍 Sem novidades nesta rodada.", flush=True)

        with open(ARQUIVO_HISTORICO, 'w') as f: json.dump(historico, f, indent=4)
        print("💤 Ciclo finalizado. Dormindo 30 min...", flush=True)
        time.sleep(1800)

if __name__ == "__main__":
    Thread(target=run).start()
    monitor()