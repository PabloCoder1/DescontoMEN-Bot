import os
import cloudscraper
from bs4 import BeautifulSoup
import time, json, requests, random, re, urllib.parse
from flask import Flask, jsonify
from threading import Thread

# --- 1. CONFIGURAÇÃO DE SEGURANÇA (HÍBRIDA) ---
# Tenta pegar do config.py (Local), se não existir (Render), pega do sistema
try:
    from config import TOKEN_TELEGRAM, CHAT_ID, MEU_TAG_AFILIADO, MEU_TOOL_ID
except ImportError:
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    CHAT_ID = os.getenv("CHAT_ID")
    MEU_TAG_AFILIADO = os.getenv("MEU_TAG_AFILIADO")
    MEU_TOOL_ID = os.getenv("MEU_TOOL_ID")

from encurtador import encurtar_link

# --- 2. MONITORAMENTO E STATUS (PAINEL DO PABLO) ---
stats = {
    "status": "Iniciando sistema...",
    "ofertas_enviadas_hoje": 0,
    "ultima_varredura": "Nunca",
    "erros_conexao": 0
}

app = Flask('')

@app.route('/')
def home():
    return f"<h1>DescontoMEN-Bot v32.3</h1><p>Status: {stats['status']}</p><p>Ofertas hoje: {stats['ofertas_enviadas_hoje']}</p>"

@app.route('/status')
def get_status():
    return jsonify(stats)

def run():
    app.run(host='0.0.0.0', port=8080)

# --- 3. CONFIGURAÇÕES DO MONITOR ---
ARQUIVO_HISTORICO = "historico_precos.json"
TERMOS_BUSCA = ["perfume masculino", "camiseta masculina", "tenis masculino", "relogio masculino"]

# --- 4. FUNÇÕES DE TRATAMENTO (PRO) ---

def limpar_titulo(titulo):
    t = re.sub(r'(?i)rel[oó]gio\w*', 'Relógio', titulo)
    t = re.sub(r'(?i)t[eê]nis\w*', 'Tênis', t)
    t = re.sub(r'(?i)perfum\w*', 'Perfume', t)
    
    for sep in [r' - ', r' \| ', r' \/ ', r' \(', r' \.', r' \d+mm', r' \d+ml']:
        t = re.split(sep, t)[0]
    
    # Gatilhos de limpeza solicitados
    gatilhos = ["original", "frete", "unissex", "masculino", "envio", "pronta", "promo", "lacrado"]
    for g in gatilhos:
        match = re.search(f"(?i)\\b{g}.*", t)
        if match: t = t[:match.start()]
        
    palavras = t.split()
    return " ".join(palavras[:6]).strip().title()

def melhorar_foto_ml(url_foto):
    """Converte miniatura borrada em Foto HD (1000px)"""
    return url_foto.replace("-I.jpg", "-O.jpg") if "-I.jpg" in url_foto else url_foto

def obter_chamada(nome):
    n = nome.lower()
    perfume = ["CHEIRINHO DE RICO! 🔥", "PRESENÇA QUE MARCA! 🔥", "FIXAÇÃO BRABA! 🔥"]
    moda = ["ESTILO NO PRECINHO! 🔥", "BÁSICA DE RESPEITO! 🔥", "PEÇA CORINGA! 🔥"]
    geral = ["TÁ BARATO DEMAIS! 🔥", "PREÇO DE BUG! 🔥", "CORRE QUE ACABA! 🔥"]
    
    if "perfume" in n: return random.choice(perfume)
    if any(x in n for x in ["camiseta", "tenis", "roupa", "sapato"]): return random.choice(moda)
    return random.choice(geral)

def gerar_link_longo(url):
    """Extrai link real de anúncios e injeta tag de afiliado"""
    try:
        if "click1.mercadolivre" in url and "u=" in url:
            url = urllib.parse.unquote(url.split("u=")[1].split("&")[0])
        url_puro = url.split('#')[0].split('?')[0]
        return f"{url_puro}?matt_tool={MEU_TOOL_ID}&matt_word={MEU_TAG_AFILIADO}"
    except: return url

# --- 5. O MOTOR DE MONITORAMENTO (LOOP) ---

def monitor():
    global stats
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    
    print("🚀 DescontoMEN v32.3 - Scanner de Preços Online!", flush=True)

    while True:
        # Carrega o histórico a cada volta para evitar conflito
        historico = json.load(open(ARQUIVO_HISTORICO, 'r')) if os.path.exists(ARQUIVO_HISTORICO) else {}
        
        stats["status"] = "Varrendo Mercado Livre..."
        stats["ultima_varredura"] = time.strftime('%H:%M:%S')
        print(f"\n⏰ {stats['ultima_varredura']} - Iniciando varredura...", flush=True)
        
        sacola_geral = []
        for termo in TERMOS_BUSCA:
            url_busca = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
            try:
                res = scraper.get(url_busca, timeout=20)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    # Seletores atualizados (Poly-card ou UI-search)
                    cards = soup.select('.poly-card') or soup.select('.ui-search-result__wrapper')
                    
                    print(f"🔎 {termo}: {len(cards)} itens encontrados na página.", flush=True)
                    
                    for card in cards:
                        try:
                            # DEBUG DE PREÇOS (O "Dedo-duro")
                            p_tags = card.select('.andes-money-amount__fraction')
                            
                            # Loga o primeiro item de cada página para vermos a estrutura
                            if card == cards[0]:
                                print(f"   DEBUG [Preços]: Encontrei {len(p_tags)} tags de preço no primeiro card.", flush=True)

                            # Só prossegue se houver pelo menos 2 preços (De: e Por:)
                            if len(p_tags) < 2:
                                continue 

                            p_old = float(p_tags[0].text.replace('.',''))
                            p_new = float(p_tags[1].text.replace('.',''))
                            
                            # Filtro de Avaliação (Baixado para 4.0 para testes)
                            r_tag = card.select_one('.poly-reviews__rating') or card.select_one('.ui-search-reviews__rating-number')
                            rating = float(r_tag.text.replace(',', '.')) if r_tag else 0
                            if rating > 0 and rating < 4.0: continue

                            nome_original = (card.select_one('.poly-component__title') or card.select_one('h2')).text
                            nome_limpo = limpar_titulo(nome_original)
                            
                            # VERIFICAÇÃO DE OFERTA
                            if p_new < p_old:
                                # Regra: Produto novo ou com queda de mais de R$ 1.00
                                if nome_limpo not in historico or p_new < (historico[nome_limpo] - 1):
                                    historico[nome_limpo] = p_new
                                    
                                    link_final = encurtar_link(gerar_link_longo(card.select_one('a')['href']))
                                    foto_hd = melhorar_foto_ml(card.select_one('img').get('data-src') or card.select_one('img').get('src'))
                                    
                                    # Matemática do Sucesso
                                    desconto = int(100 - ((p_new * 100) / p_old))
                                    economia = p_old - p_new
                                    
                                    msg = (f"<b>{obter_chamada(nome_limpo)}</b>\n\n"
                                           f"📦 {nome_limpo}\n\n"
                                           f"❌ <s>De: R$ {p_old:.2f}</s>\n"
                                           f"✅ <b>Por: R$ {p_new:.2f}</b>\n\n"
                                           f"📉 <b>Economia de {desconto}% (R$ {economia:.2f})</b>")
                                    
                                    markup = {"inline_keyboard": [[{"text": "🛒 VER OFERTA NO ML", "url": link_final}]]}
                                    sacola_geral.append({'foto': foto_hd, 'msg': msg, 'markup': markup})
                        except: continue
                else:
                    print(f"⚠️ Erro de Resposta no ML ({termo}): {res.status_code}", flush=True)
            except Exception as e:
                print(f"❌ Falha na conexão com {termo}: {e}", flush=True)
                stats["erros_conexao"] += 1

        # ENVIO DAS OFERTAS ENCONTRADAS
        if sacola_geral:
            print(f"✅ Sucesso! {len(sacola_geral)} ofertas válidas passaram no funil.", flush=True)
            random.shuffle(sacola_geral)
            for item in sacola_geral[:10]: # Posta até 10 ofertas por vez
                requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                             json={"chat_id": CHAT_ID, "photo": item['foto'], "caption": item['msg'], "parse_mode": "HTML", "reply_markup": item['markup']})
                stats["ofertas_enviadas_hoje"] += 1
                time.sleep(15)
        else:
            print("❌ FIM DA VARREDURA: Nenhum item novo com desconto real foi encontrado.", flush=True)

        # Salva o histórico atualizado
        json.dump(historico, open(ARQUIVO_HISTORICO, 'w'), indent=4)
        
        stats["status"] = "Dormindo (Sleep)"
        print("😴 Dormindo por 10 minutos antes da próxima volta...", flush=True)
        time.sleep(600)

if __name__ == "__main__":
    Thread(target=run).start()
    monitor()