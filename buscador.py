import os, cloudscraper, time, json, requests, random, re, urllib.parse
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from threading import Thread

# Tentativa de importação de credenciais
try:
    from config import TOKEN_TELEGRAM, CHAT_ID, MEU_TAG_AFILIADO, MEU_TOOL_ID
except ImportError:
    TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
    CHAT_ID = os.getenv("CHAT_ID")
    MEU_TAG_AFILIADO = os.getenv("MEU_TAG_AFILIADO")
    MEU_TOOL_ID = os.getenv("MEU_TOOL_ID")

from encurtador import encurtar_link

# VARIÁVEIS DE CONTROLE PARA O PABLO (QA)
stats = {
    "status": "Iniciando...",
    "ofertas_enviadas_hoje": 0,
    "ultima_varredura": "Nunca",
    "erros_encontrados": 0
}

app = Flask('')

@app.route('/')
def home(): 
    return f"<h1>DescontoMEN v32.1</h1><p>Status: {stats['status']}</p><p>Ofertas hoje: {stats['ofertas_enviadas_hoje']}</p>"

@app.route('/status')
def get_status():
    return jsonify(stats)

def run(): app.run(host='0.0.0.0', port=8080)

ARQUIVO_HISTORICO = "historico_precos.json"
TERMOS_BUSCA = ["perfume masculino", "camiseta masculina", "tenis masculino", "relogio masculino"]

# ... (Funções limpar_titulo, melhorar_foto_ml, obter_chamada, gerar_link_longo iguais)
# [MANTENHA AS FUNÇÕES QUE JÁ TEMOS]

def monitor():
    global stats
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows'})
    historico = json.load(open(ARQUIVO_HISTORICO, 'r')) if os.path.exists(ARQUIVO_HISTORICO) else {}

    print("🚀 DescontoMEN v32.1 - Diagnóstico Ativado!", flush=True)

    while True:
        stats["status"] = "Varrendo Mercado Livre..."
        stats["ultima_varredura"] = time.strftime('%H:%M:%S')
        print(f"⏰ {stats['ultima_varredura']} - Iniciando nova varredura...", flush=True)
        
        sacola_geral = []
        for termo in TERMOS_BUSCA:
            url_busca = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
            try:
                res = scraper.get(url_busca, timeout=20)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    cards = soup.select('.poly-card') or soup.select('.ui-search-result__wrapper')
                    
                    for card in cards:
                        try:
                            # Filtro de Avaliação
                            r_tag = card.select_one('.poly-reviews__rating') or card.select_one('.ui-search-reviews__rating-number')
                            rating = float(r_tag.text.replace(',', '.')) if r_tag else 0
                            if rating > 0 and rating < (4.7 if "perfume" in termo.lower() else 4.6): continue

                            p_tags = card.select('.andes-money-amount__fraction')
                            if len(p_tags) >= 2:
                                p_old = float(p_tags[0].text.replace('.',''))
                                p_new = float(p_tags[1].text.replace('.',''))
                                nome_original = (card.select_one('.poly-component__title') or card.select_one('h2')).text
                                nome_limpo = limpar_titulo(nome_original)
                                
                                if nome_limpo not in historico or p_new < historico[nome_limpo]:
                                    historico[nome_limpo] = p_new
                                    if p_new < p_old:
                                        link = encurtar_link(gerar_link_longo(card.select_one('a')['href']))
                                        foto = melhorar_foto_ml(card.select_one('img').get('data-src') or card.select_one('img').get('src'))
                                        
                                        desconto = int(100 - ((p_new * 100) / p_old))
                                        msg = (f"<b>{obter_chamada(nome_limpo)}</b>\n\n📦 {nome_limpo}\n\n"
                                               f"❌ <s>De: R$ {p_old:.2f}</s>\n✅ <b>Por: R$ {p_new:.2f}</b>\n\n"
                                               f"📉 <b>Economia de {desconto}%</b>")
                                        
                                        markup = {"inline_keyboard": [[{"text": "🛒 VER OFERTA NO ML", "url": link}]]}
                                        sacola_geral.append({'foto': foto, 'msg': msg, 'markup': markup})
                        except Exception as e:
                            continue
                else:
                    print(f"⚠️ Erro ao acessar ML ({termo}): {res.status_code}", flush=True)
                    stats["erros_encontrados"] += 1
            except Exception as e:
                print(f"❌ Falha fatal na busca: {e}", flush=True)
                stats["erros_encontrados"] += 1

        if sacola_geral:
            random.shuffle(sacola_geral)
            print(f"📦 Enviando {len(sacola_geral[:12])} ofertas selecionadas...", flush=True)
            for item in sacola_geral[:12]:
                res_tg = requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                             json={"chat_id": CHAT_ID, "photo": item['foto'], "caption": item['msg'], "parse_mode": "HTML", "reply_markup": item['markup']})
                if res_tg.status_code == 200:
                    stats["ofertas_enviadas_hoje"] += 1
                time.sleep(20)

        stats["status"] = "Aguardando próxima varredura (Sleep)"
        print("😴 Varredura finalizada. Dormindo por 15 minutos...", flush=True)
        time.sleep(900) # Diminuí para 15 minutos para ser mais rápido

if __name__ == "__main__":
    Thread(target=run).start()
    monitor()
