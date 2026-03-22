import cloudscraper
from bs4 import BeautifulSoup
import time
import json
import requests
import os
import random

# --- 1. CONFIGURAÇÕES (SUAS CHAVES) ---
TOKEN_TELEGRAM = "8610297805:AAHq2rzzImn9WEfOPdRrz4y_xM83MQ1qx6w"
CHAT_ID = "2050785699"

# SEUS DADOS OFICIAIS DE AFILIADO
MEU_TAG_AFILIADO = "gd20260319125059"
MEU_TOOL_ID = "64029233"

# --- 2. PARÂMETROS DE CURADORIA ---
MIN_AVALIACAO = 4.6
MIN_DESCONTO = 10
MAX_DESCONTO = 65
INTERVALO_ENTRE_POSTS = 15 # Segundos entre cada mensagem enviada
INTERVALO_VARREDURA = 30    # Minutos entre cada busca completa
ARQUIVO_HISTORICO = "historico_precos.json"

TERMOS_BUSCA = [
    "perfume arabe masculino", "perfume nacional masculino", "perfume importado masculino",
    "camiseta masculina premium ribana", "calça jeans masculina streetwear", 
    "relógio masculino luxo", "tênis nike masculino", "camisa social masculina"
]

# --- 3. FUNÇÕES DE SUPORTE ---

def gerar_link_afiliado(url_original):
    try:
        url_limpa = url_original.split('?')[0].split('#')[0]
        return f"{url_limpa}?matt_tool={MEU_TOOL_ID}&matt_word={MEU_TAG_AFILIADO}"
    except:
        return url_original

def categorizar(nome):
    n = nome.lower()
    if any(x in n for x in ['relógio', 'relogio']): return "Acessórios"
    if any(x in n for x in ['tênis', 'tenis']): return "Calçados"
    if any(x in n for x in ['camiseta', 'calça', 'jeans', 'camisa', 'suéter']): return "Vestuário"
    return "Perfumaria"

def obter_chamada(nome, preco_caiu):
    if preco_caiu:
        return "CORRE, MENOR VALOR HISTÓRICO 🔥"
    
    n = nome.lower()
    if "perfume" in n:
        return random.choice(["CHEIRINHO DE MANGA 🔥", "CHEIRINHO DE SUCESSO 🔥", "PRESENÇA MARCANTE 🔥"])
    if "camiseta" in n or "camisa" in n:
        return "A BÁSICA TEM SEU CHARME 🔥"
    if "calça" in n or "jeans" in n:
        return "PRA ANDAR ESTILOSO 🔥"
    
    return "OPORTUNIDADE ÚNICA 🔥"

def enviar_telegram(mensagem, url_foto):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendPhoto"
    payload = {"chat_id": CHAT_ID, "photo": url_foto, "caption": mensagem, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except:
        print("❌ Erro ao enviar para o Telegram.")

# --- 4. MONITOR PRINCIPAL (VERSÃO MIX/SORTIDA) ---

def monitor_principal():
    scraper = cloudscraper.create_scraper()
    
    if os.path.exists(ARQUIVO_HISTORICO):
        with open(ARQUIVO_HISTORICO, 'r', encoding='utf-8') as f:
            historico = json.load(f)
    else:
        historico = {}

    print(f"💰 DescontoMEN Online! Modo 'Mix de Ofertas' Ativado.")

    while True:
        print(f"\n⏰ {time.strftime('%H:%M:%S')} - Iniciando varredura geral...")
        sacola_de_ofertas = [] # Lista para guardar tudo o que for achado nesta volta
        
        for termo in TERMOS_BUSCA:
            url = f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}"
            try:
                res = scraper.get(url)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    cards = soup.select('.poly-card') or soup.select('.ui-search-result__wrapper')
                    
                    for card in cards:
                        try:
                            # Filtro Avaliação
                            rating = card.select_one('.poly-component__review-compacted') or \
                                     card.select_one('.ui-search-reviews__rating-number')
                            nota = float(rating.text.split('(')[0].strip().replace(',', '.')) if rating else 0.0
                            if nota < MIN_AVALIACAO: continue

                            # Filtro Preço e Desconto
                            precos = card.select('.andes-money-amount__fraction')
                            if len(precos) >= 2:
                                p_orig = float(precos[0].text.replace('.', '').replace(',', '.'))
                                p_atual = float(precos[1].text.replace('.', '').replace(',', '.'))
                                desc_perc = 100 - (p_atual * 100 / p_orig)
                                
                                if MIN_DESCONTO <= desc_perc <= MAX_DESCONTO:
                                    titulo = card.select_one('.poly-component__title') or card.select_one('h2')
                                    nome_prod = titulo.text.strip()
                                    
                                    # Verifica se devemos enviar (Novo ou Baixou)
                                    enviar_este = False
                                    aviso_queda = False
                                    
                                    if nome_prod not in historico:
                                        enviar_este = True
                                        historico[nome_prod] = p_atual
                                    elif p_atual < historico[nome_prod]:
                                        enviar_este = True
                                        aviso_queda = True
                                        historico[nome_prod] = p_atual
                                    
                                    if enviar_este:
                                        # Guarda os dados na sacola em vez de enviar agora
                                        link = gerar_link_afiliado(card.select_one('a')['href'])
                                        foto = (card.select_one('img').get('data-src') or card.select_one('img').get('src'))
                                        chamada = obter_chamada(nome_prod, aviso_queda)

                                        sacola_de_ofertas.append({
                                            'msg': (f"{chamada}\n\n"
                                                    f"✅ {nome_prod}\n\n"
                                                    f"De R$ {p_orig:.2f} ❌\n"
                                                    f"Por R$ {p_atual:.2f} ✅\n\n"
                                                    f"🔗 Link: {link}"),
                                            'foto': foto
                                        })
                        except: continue
                time.sleep(1) # Pequena pausa entre termos de busca
            except: continue

        # --- MOMENTO DO SORTEIO/MIX ---
        if sacola_de_ofertas:
            print(f"📦 Encontrei {len(sacola_de_ofertas)} ofertas. Embaralhando e enviando...")
            random.shuffle(sacola_de_ofertas) # A mágica acontece aqui
            
            for item in sacola_de_ofertas:
                enviar_telegram(item['msg'], item['foto'])
                time.sleep(INTERVALO_ENTRE_POSTS) # Pausa para o grupo não "explodir" de mensagens
        else:
            print("🔍 Nenhuma oferta nova que atenda os requisitos nesta rodada.")

        # Salva o histórico atualizado
        with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
            json.dump(historico, f, indent=4, ensure_ascii=False)
            
        print(f"💤 Varredura concluída. Próxima em {INTERVALO_VARREDURA} min.")
        time.sleep(INTERVALO_VARREDURA * 60)

if __name__ == "__main__":
    monitor_principal()