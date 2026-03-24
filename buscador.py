import os
import cloudscraper
from bs4 import BeautifulSoup
import time, json, requests, random, re, urllib.parse
from flask import Flask, jsonify
from threading import Thread

# --- 1. CONFIGURAÇÃO DE SEGURANÇA (HÍBRIDA) ---
try:
    from config import TOKEN_TELEGRAM, CHAT_ID, MEU_TAG_AFILIADO, MEU_TOOL_ID
except ImportError:
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    CHAT_ID = os.getenv("CHAT_ID")
    MEU_TAG_AFILIADO = os.getenv("MEU_TAG_AFILIADO")
    MEU_TOOL_ID = os.getenv("MEU_TOOL_ID")

# Tenta importar o encurtador, se falhar, usa o link original
try:
    from encurtador import encurtar_link
except ImportError:
    def encurtar_link(url): return url

# --- 2. MONITORAMENTO E STATUS ---
stats = {
    "status": "Online",
    "ofertas_enviadas_hoje": 0,
    "ultima_varredura": "Nunca"
}

app = Flask('')

@app.route('/')
def home():
    return f"<h1>DescontoMEN-Bot v32.5</h1><p>Status: {stats['status']}</p><p>Ofertas: {stats['ofertas_enviadas_hoje']}</p>"

@app.route('/status')
def get_status():
    return jsonify(stats)

def run():
    # AJUSTE PARA O RENDER: Pega a porta do sistema ou usa 10000 por padrão
    port = int(os.environ.get("PORT", 10000))
    print(f"📡 Flask iniciado na porta {port}")
    app.run(host='0.0.0.0', port=port)

# --- 3. FUNÇÕES DE TRATAMENTO ---

def limpar_titulo(titulo):
    t = re.sub(r'(?i)rel[oó]gio\w*', 'Relógio', titulo)
    t = re.sub(r'(?i)t[eê]nis\w*', 'Tênis', t)
    t = re.sub(r'(?i)perfum\w*', 'Perfume', t)
    for sep in [r' - ', r' \| ', r' \/ ', r' \(', r' \.', r' \d+mm', r' \d+ml']:
        t = re.split(sep, t)[0]
    gatilhos = ["original", "frete", "unissex", "masculino", "envio", "pronta", "promo", "lacrado"]
    for g in gatilhos:
        match = re.search(f"(?i)\\b{g}.*", t)
        if match: t = t[:match.start()]
    return " ".join(t.split()[:6]).strip().title()

def melhorar_foto_ml(url_foto):
    return url_foto.replace("-I.jpg", "-O.jpg") if "-I.jpg" in url_foto else url_foto

def obter_chamada(nome):
    n = nome.lower()
    if "perfume" in n: return random.choice(["CHEIRINHO DE RICO! 🔥", "PRESENÇA MARCANTE! 🔥"])
    return random.choice(["ESTILO NO PRECINHO! 🔥", "TÁ BARATO DEMAIS! 🔥"])

def gerar_link_longo(url):
    try:
        if "click1.mercadolivre" in url and "u=" in url:
            url = urllib.parse.unquote(url.split("u=")[1].split("&")[0])
        url_puro = url.split('#')[0].split('?')[0]
        return f"{url_puro}?matt_tool={MEU_TOOL_ID}&matt_word={MEU_TAG_AFILIADO}"
    except: return url

# --- 4. MOTOR DE MONITORAMENTO ---

def monitor():
    global stats
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    print("🚀 Bot de Nuvem Iniciado!", flush=True)

    while True:
        historico = json.load(open("historico_precos.json", 'r')) if os.path.exists("historico_precos.json") else {}
        stats["status"] = "Varrendo..."
        stats["ultima_varredura"] = time.strftime('%H:%M:%S')
        
        sacola_geral = []
        for termo in ["perfume masculino", "camiseta masculina", "tenis masculino", "relogio masculino"]:
            try:
                res = scraper.get(f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}", timeout=20)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    cards = soup.select('.poly-card') or soup.select('.ui-search-result__wrapper')
                    
                    for card in cards:
                        p_tags = card.select('.andes-money-amount__fraction')
                        if len(p_tags) < 2: continue 

                        p_old = float(p_tags[0].text.replace('.',''))
                        p_new = float(p_tags[1].text.replace('.',''))
                        
                        # Filtro de Avaliação
                        r_tag = card.select_one('.poly-reviews__rating') or card.select_one('.ui-search-reviews__rating-number')
                        rating = float(r_tag.text.replace(',', '.')) if r_tag else 0
                        if rating > 0 and rating < 4.0: continue

                        nome_limpo = limpar_titulo((card.select_one('.poly-component__title') or card.select_one('h2')).text)
                        
                        if p_new < p_old:
                            if nome_limpo not in historico or p_new < (historico[nome_limpo] - 1):
                                historico[nome_limpo] = p_new
                                link = encurtar_link(gerar_link_longo(card.select_one('a')['href']))
                                foto = melhorar_foto_ml(card.select_one('img').get('data-src') or card.select_one('img').get('src'))
                                desc = int(100 - ((p_new * 100) / p_old))
                                msg = f"<b>{obter_chamada(nome_limpo)}</b>\n\n📦 {nome_limpo}\n\n❌ <s>De: R$ {p_old:.2f}</s>\n✅ <b>Por: R$ {p_new:.2f}</b>\n\n📉 <b>Economia de {desc}%</b>"
                                markup = {"inline_keyboard": [[{"text": "🛒 VER OFERTA NO ML", "url": link}]]}
                                sacola_geral.append({'foto': foto, 'msg': msg, 'markup': markup})
            except: continue

        if sacola_geral:
            random.shuffle(sacola_geral)
            for item in sacola_geral[:10]:
                requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                             json={"chat_id": CHAT_ID, "photo": item['foto'], "caption": item['msg'], "parse_mode": "HTML", "reply_markup": item['markup']})
                stats["ofertas_enviadas_hoje"] += 1
                time.sleep(15)

        json.dump(historico, open("historico_precos.json", 'w'), indent=4)
        stats["status"] = "Dormindo"
        time.sleep(600)

def self_ping():
    # URL genérica para não dar erro se mudar o nome do app
    url = "http://localhost:10000" 
    while True:
        try: requests.get(url, timeout=10)
        except: pass
        time.sleep(600)

if __name__ == "__main__":
    Thread(target=run).start()
    Thread(target=self_ping).start()
    monitor()