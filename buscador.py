import os
import cloudscraper
from bs4 import BeautifulSoup
import time, json, requests, random, re, urllib.parse
from flask import Flask
from threading import Thread

# TENTA IMPORTAR O CONFIG (LOCAL). SE NÃO EXISTIR (NO RENDER), PEGA DAS VARIÁVEIS DE AMBIENTE
try:
    from config import TOKEN_TELEGRAM, CHAT_ID, MEU_TAG_AFILIADO, MEU_TOOL_ID
except ImportError:
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    CHAT_ID = os.getenv("CHAT_ID")
    MEU_TAG_AFILIADO = os.getenv("MEU_TAG_AFILIADO")
    MEU_TOOL_ID = os.getenv("MEU_TOOL_ID")

# Importando o seu encurtador TinyURL
from encurtador import encurtar_link

# Configuração do Flask para o Render não derrubar o bot
app = Flask('')
@app.route('/')
def home(): return "DescontoMEN está vivo!"
def run(): app.run(host='0.0.0.0', port=8080)

ARQUIVO_HISTORICO = "historico_precos.json"
TERMOS_BUSCA = ["perfume masculino", "camiseta masculina", "tenis masculino", "relogio masculino"]

# --- FUNÇÕES DE APOIO ---

def limpar_titulo(titulo):
    """Remove ruídos de SEO e mantém o essencial"""
    t = re.sub(r'(?i)rel[oó]gio\w*', 'Relógio', titulo)
    t = re.sub(r'(?i)t[eê]nis\w*', 'Tênis', t)
    t = re.sub(r'(?i)perfum\w*', 'Perfume', t)
    
    for sep in [r' - ', r' \| ', r' \/ ', r' \(', r' \.', r' \d+mm', r' \d+ml']:
        t = re.split(sep, t)[0]
        
    # Gatilhos extras de limpeza
    gatilhos = ["original", "frete", "unissex", "masculino", "envio", "pronta", "promo"]
    for g in gatilhos:
        match = re.search(f"(?i)\\b{g}.*", t)
        if match: t = t[:match.start()]
        
    palavras = t.split()
    return " ".join(palavras[:6]).strip().title()

def melhorar_foto_ml(url_foto):
    """Converte miniatura em Foto HD (1000x1000)"""
    return url_foto.replace("-I.jpg", "-O.jpg") if "-I.jpg" in url_foto else url_foto

def obter_chamada(nome):
    """Gera frases de impacto baseadas na categoria"""
    n = nome.lower()
    perfume = ["CHEIRINHO DE RICO! 🔥", "PRESENÇA QUE MARCA! 🔥", "FIXAÇÃO BRABA! 🔥"]
    moda = ["ESTILO NO PRECINHO! 🔥", "BÁSICA DE RESPEITO! 🔥", "PEÇA CORINGA! 🔥"]
    geral = ["TÁ BARATO DEMAIS! 🔥", "PREÇO DE BUG! 🔥", "CORRE QUE ACABA! 🔥"]
    
    if "perfume" in n: return random.choice(perfume)
    if any(x in n for x in ["camiseta", "tenis", "roupa"]): return random.choice(moda)
    return random.choice(geral)

def gerar_link_longo(url):
    """Extrai o link real e injeta sua tag de afiliado"""
    try:
        if "click1.mercadolivre" in url and "u=" in url:
            url = urllib.parse.unquote(url.split("u=")[1].split("&")[0])
        url_puro = url.split('#')[0].split('?')[0]
        return f"{url_puro}?matt_tool={MEU_TOOL_ID}&matt_word={MEU_TAG_AFILIADO}"
    except: return url

# --- LOOP PRINCIPAL ---

def monitor():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    historico = json.load(open(ARQUIVO_HISTORICO, 'r')) if os.path.exists(ARQUIVO_HISTORICO) else {}

    print("🚀 DescontoMEN v32.0 Online e Protegido!", flush=True)

    while True:
        sacola_geral = []
        for termo in TERMOS_BUSCA:
            url_busca = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
            ofertas_cat = []
            try:
                res = scraper.get(url_busca, timeout=20)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    cards = soup.select('.poly-card') or soup.select('.ui-search-result__wrapper')
                    
                    for card in cards:
                        try:
                            # Filtro de Avaliação (QA de Qualidade)
                            r_tag = card.select_one('.poly-reviews__rating') or card.select_one('.ui-search-reviews__rating-number')
                            rating = float(r_tag.text.replace(',', '.')) if r_tag else 0
                            if rating > 0 and rating < (4.7 if "perfume" in termo.lower() else 4.6): continue

                            p_tags = card.select('.andes-money-amount__fraction')
                            if len(p_tags) >= 2:
                                p_old = float(p_tags[0].text.replace('.',''))
                                p_new = float(p_tags[1].text.replace('.',''))
                                nome_limpo = limpar_titulo((card.select_one('.poly-component__title') or card.select_one('h2')).text)
                                
                                # Lógica de Histórico e Queda de Preço
                                if nome_limpo not in historico or p_new < historico[nome_limpo]:
                                    historico[nome_limpo] = p_new
                                    if p_new < p_old:
                                        link_curto = encurtar_link(gerar_link_longo(card.select_one('a')['href']))
                                        foto_hd = melhorar_foto_ml(card.select_one('img').get('data-src') or card.select_one('img').get('src'))
                                        
                                        # Matemática do Desconto
                                        desconto = int(100 - ((p_new * 100) / p_old))
                                        economia = p_old - p_new
                                        
                                        msg = (f"<b>{obter_chamada(nome_limpo)}</b>\n\n"
                                               f"📦 {nome_limpo}\n\n"
                                               f"❌ <s>De: R$ {p_old:.2f}</s>\n"
                                               f"✅ <b>Por: R$ {p_new:.2f}</b>\n\n"
                                               f"📉 <b>Economia de {desconto}% (R$ {economia:.2f})</b>")
                                        
                                        markup = {"inline_keyboard": [[{"text": "🛒 VER OFERTA NO ML", "url": link_curto}]]}
                                        ofertas_cat.append({'foto': foto_hd, 'msg': msg, 'markup': markup})
                        except: continue
                random.shuffle(ofertas_cat)
                sacola_geral.extend(ofertas_cat[:3]) # Pega as 3 melhores de cada termo
            except: continue

        if sacola_geral:
            random.shuffle(sacola_geral)
            for item in sacola_geral:
                requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                             json={"chat_id": CHAT_ID, "photo": item['foto'], "caption": item['msg'], "parse_mode": "HTML", "reply_markup": item['markup']})
                time.sleep(30) # Delay para evitar block do Telegram

        json.dump(historico, open(ARQUIVO_HISTORICO, 'w'), indent=4)
        time.sleep(1800) # Espera 30 min para a próxima varredura

if __name__ == "__main__":
    Thread(target=run).start()
    monitor()