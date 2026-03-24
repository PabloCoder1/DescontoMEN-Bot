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

    print("🚀 DescontoMEN v32.2 - Modo Deep Debug!", flush=True)

    while True:
        stats["status"] = "Varrendo Mercado Livre..."
        print(f"\n⏰ {time.strftime('%H:%M:%S')} - Iniciando varredura...", flush=True)
        
        sacola_geral = []
        for termo in TERMOS_BUSCA:
            url_busca = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
            try:
                res = scraper.get(url_busca, timeout=20)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    # Tentando dois tipos de seletores (o novo e o antigo do ML)
                    cards = soup.select('.poly-card') or soup.select('.ui-search-result__wrapper')
                    
                    print(f"🔎 {termo}: Achei {len(cards)} produtos na página.", flush=True)
                    
                    for card in cards:
                        try:
                            # Captura de Preços
                            p_tags = card.select('.andes-money-amount__fraction')
                            if len(p_tags) < 2: continue # Não tem desconto
                            
                            p_old = float(p_tags[0].text.replace('.',''))
                            p_new = float(p_tags[1].text.replace('.',''))
                            
                            # Filtro de Avaliação (Baixei um pouco para teste: 4.0)
                            r_tag = card.select_one('.poly-reviews__rating') or card.select_one('.ui-search-reviews__rating-number')
                            rating = float(r_tag.text.replace(',', '.')) if r_tag else 0
                            
                            if rating > 0 and rating < 4.0: 
                                continue # Ignora apenas os realmente ruins

                            nome_original = (card.select_one('.poly-component__title') or card.select_one('h2')).text
                            nome_limpo = limpar_titulo(nome_original)
                            
                            # REGRA DE OURO: Preço novo tem que ser menor que o antigo
                            if p_new < p_old:
                                if nome_limpo not in historico or p_new < historico[nome_limpo]:
                                    historico[nome_limpo] = p_new
                                    
                                    link = encurtar_link(gerar_link_longo(card.select_one('a')['href']))
                                    foto = melhorar_foto_ml(card.select_one('img').get('data-src') or card.select_one('img').get('src'))
                                    desconto = int(100 - ((p_new * 100) / p_old))
                                    
                                    msg = (f"<b>{obter_chamada(nome_limpo)}</b>\n\n📦 {nome_limpo}\n\n"
                                           f"❌ <s>De: R$ {p_old:.2f}</s>\n✅ <b>Por: R$ {p_new:.2f}</b>\n\n"
                                           f"📉 <b>Economia de {desconto}%</b>")
                                    
                                    markup = {"inline_keyboard": [[{"text": "🛒 VER OFERTA NO ML", "url": link}]]}
                                    sacola_geral.append({'foto': foto, 'msg': msg, 'markup': markup})
                        except: continue
                else:
                    print(f"⚠️ Bloqueio ou Erro no ML ({termo}): {res.status_code}", flush=True)
            except Exception as e:
                print(f"❌ Erro na conexão: {e}", flush=True)

        if sacola_geral:
            print(f"✅ Sucesso! {len(sacola_geral)} ofertas válidas encontradas.", flush=True)
            random.shuffle(sacola_geral)
            for item in sacola_geral[:8]:
                requests.post(f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto", 
                             json={"chat_id": CHAT_ID, "photo": item['foto'], "caption": item['msg'], "parse_mode": "HTML", "reply_markup": item['markup']})
                stats["ofertas_enviadas_hoje"] += 1
                time.sleep(20)
        else:
            print("❌ Varredura completa, mas nenhuma oferta passou nos filtros.", flush=True)

        print("😴 Dormindo por 10 minutos...", flush=True)
        time.sleep(600)
        
if __name__ == "__main__":
    Thread(target=run).start()
    monitor()
