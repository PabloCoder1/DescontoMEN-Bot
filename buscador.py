import os, cloudscraper, time, json, requests, random, re, urllib.parse
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from threading import Thread

# --- 1. CONFIGURAÇÃO DE SEGURANÇA ---
try:
    from config import (
        TOKEN_TELEGRAM, CHAT_ID, MEU_TAG_AFILIADO, MEU_TOOL_ID, 
        GATILHOS_DE_CORTE, CHAMADAS, TERMOS_PESQUISA,
        MIN_DESCONTO, MIN_RATING
    )
except ImportError:
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    CHAT_ID = os.getenv("CHAT_ID")
    MEU_TAG_AFILIADO = os.getenv("MEU_TAG_AFILIADO")
    MEU_TOOL_ID = os.getenv("MEU_TOOL_ID")
    GATILHOS_DE_CORTE = ["original", "frete"]
    CHAMADAS = {"geral": ["OFERTA INSANA! 🔥"]}
    TERMOS_PESQUISA = ["perfume masculino"]
    MIN_DESCONTO = 15
    MIN_RATING = 4.7

try:
    from encurtador import encurtar_link
except ImportError:
    def encurtar_link(url): return url

# --- 2. STATUS ---
stats = {"status": "Online", "ofertas_enviadas_hoje": 0, "ultima_varredura": "Nunca"}
app = Flask('')

@app.route('/')
def home():
    return f"<h1>DescontoMEN v32.9</h1><p>Varrendo {len(TERMOS_PESQUISA)} termos | Meta: 20 posts/ciclo</p>"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 3. TRATAMENTO ---

def limpar_titulo(titulo):
    t = re.sub(r'(?i)rel[oó]gio\w*', 'Relógio', titulo)
    t = re.sub(r'(?i)t[eê]nis\w*', 'Tênis', t)
    t = re.sub(r'(?i)perfum\w*', 'Perfume', t)
    for sep in [r' - ', r' \| ', r' \/ ', r' \(', r' \.', r' \d+mm', r' \d+ml']:
        t = re.split(sep, t)[0]
    for g in GATILHOS_DE_CORTE:
        match = re.search(f"(?i)\\b{g}\\b.*", t)
        if match: t = t[:match.start()]
    return " ".join(t.split()[:6]).strip().title()

def melhorar_foto_ml(url_foto):
    return url_foto.replace("-I.jpg", "-O.jpg") if "-I.jpg" in url_foto else url_foto

def obter_chamada(nome):
    n = nome.lower()
    cat = "perfume" if "perfume" in n else "tenis" if "tenis" in n else "roupa" if any(x in n for x in ["camiseta", "roupa", "calça", "jeans"]) else "geral"
    return random.choice(CHAMADAS.get(cat, CHAMADAS["geral"]))

def gerar_link_longo(url):
    try:
        if "click1.mercadolivre" in url and "u=" in url:
            url = urllib.parse.unquote(url.split("u=")[1].split("&")[0])
        return f"{url.split('#')[0].split('?')[0]}?matt_tool={MEU_TOOL_ID}&matt_word={MEU_TAG_AFILIADO}"
    except: return url

# --- 4. MOTOR DE ALTA PERFORMANCE ---

def monitor():
    global stats
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    
    while True:
        historico = json.load(open("historico_precos.json", 'r')) if os.path.exists("historico_precos.json") else {}
        stats["status"] = "Iniciando Varredura Massiva..."
        stats["ultima_varredura"] = time.strftime('%H:%M:%S')
        
        sacola_geral = []
        
        # Embaralha os termos para que cada ciclo comece por marcas diferentes
        termos_ciclo = TERMOS_PESQUISA[:]
        random.shuffle(termos_ciclo)

        print(f"📡 Scan v32.9: Analisando {len(termos_ciclo)} categorias...", flush=True)

        for termo in termos_ciclo:
            try:
                res = scraper.get(f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}", timeout=15)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    cards = soup.select('.poly-card') or soup.select('.ui-search-result__wrapper')
                    
                    # LIMITADOR DE PERFORMANCE: Analisar apenas os 5 primeiros de cada termo
                    for card in cards[:5]:
                        try:
                            # Avaliação
                            r_tag = card.select_one('.poly-reviews__rating') or card.select_one('.ui-search-reviews__rating-number')
                            rating = float(r_tag.text.replace(',', '.')) if r_tag else 0
                            if rating > 0 and rating < MIN_RATING: continue

                            # Preços
                            p_tags = card.select('.andes-money-amount__fraction')
                            p_old, p_new = 0, 0
                            if len(p_tags) >= 2:
                                p_old, p_new = float(p_tags[0].text.replace('.','')), float(p_tags[1].text.replace('.',''))
                            else:
                                p_old_tag = card.select_one('.andes-money-amount--previous .andes-money-amount__fraction')
                                if p_old_tag:
                                    p_old, p_new = float(p_old_tag.text.replace('.','')), float(p_tags[0].text.replace('.',''))

                            if p_old > 0 and p_new < p_old:
                                desc = int(100 - ((p_new * 100) / p_old))
                                if desc < MIN_DESCONTO: continue

                                nome_limpo = limpar_titulo((card.select_one('.poly-component__title') or card.select_one('h2')).text)
                                
                                if nome_limpo not in historico or p_new < (historico[nome_limpo] - 1):
                                    historico[nome_limpo] = p_new
                                    link = encurtar_link(gerar_link_longo(card.select_one('a')['href']))
                                    foto = melhorar_foto_ml(card.select_one('img').get('data-src') or card.select_one('img').get('src'))
                                    
                                    msg = (f"<b>{obter_chamada(nome_limpo)}</b>\n\n"
                                           f"📦 {nome_limpo}\n\n"
                                           f"❌ <s>De: R$ {p_old:.2f}</s>\n"
                                           f"✅ <b>Por: R$ {p_new:.2f}</b>\n\n"
                                           f"📉 <b>Economia de {desc}%</b>")
                                    
                                    markup = {"inline_keyboard": [[{"text": "🛒 VER OFERTA NO ML", "url": link}]]}
                                    sacola_geral.append({'foto': foto, 'msg': msg, 'markup': markup})
                        except: continue
                # Pequeno delay para não ser bloqueado pelo ML
                time.sleep(1)
            except: continue

        # --- ENVIO DAS 20 MELHORES ---
        if sacola_geral:
            print(f"💎 Varredura Completa: {len(sacola_geral)} ofertas de ELITE encontradas.", flush=True)
            random.shuffle(sacola_geral)
            
            # Aumentado para 20 itens
            for item in sacola_geral[:20]:
                try:
                    requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                                 json={"chat_id": CHAT_ID, "photo": item['foto'], "caption": item['msg'], "parse_mode": "HTML", "reply_markup": item['markup']}, timeout=15)
                    stats["ofertas_enviadas_hoje"] += 1
                    # Delay de 15s entre posts para o Telegram não marcar como spam
                    time.sleep(15)
                except: continue

        json.dump(historico, open("historico_precos.json", 'w'), indent=4)
        stats["status"] = "Dormindo (Aguardando próxima volta)"
        print("😴 Ciclo de volume finalizado. Dormindo 10 min...", flush=True)
        time.sleep(600)

def self_ping():
    url = f"http://localhost:{os.environ.get('PORT', 10000)}" 
    while True:
        try: requests.get(url, timeout=10)
        except: pass
        time.sleep(600)

if __name__ == "__main__":
    Thread(target=run).start()
    Thread(target=self_ping).start()
    monitor()