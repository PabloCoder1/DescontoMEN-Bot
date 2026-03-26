import os, time, json, requests, random, re, urllib.parse, urllib3, platform
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# --- 0. SEGURANÇA ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. CONFIGURAÇÕES COM FALLBACK ---
try:
    import config
    TERMOS_PESQUISA = config.TERMOS_PESQUISA
    MIN_DESCONTO = config.MIN_DESCONTO 
    MIN_RATING = config.MIN_RATING     
    EVOLUTION_API_URL = config.EVOLUTION_API_URL
    EVOLUTION_API_KEY = config.EVOLUTION_API_KEY 
    EVOLUTION_INSTANCE = config.EVOLUTION_INSTANCE
    WA_GROUP_ID = config.WA_GROUP_ID
    CHAMADAS = config.CHAMADAS
    GATILHOS_DE_CORTE = config.GATILHOS_DE_CORTE
    URL_GERADOR_ML = config.URL_GERADOR_ML
    TAG_AFILIADO = config.MEU_TAG_AFILIADO
    TOOL_ID = config.MEU_TOOL_ID
    print(f"✅ [SISTEMA] v38.8 - Limpeza de Link Click1 Reforçada!")
except Exception as e:
    print(f"⚠️ [ERRO] Falha no config.py: {e}")
    URL_GERADOR_ML = "https://www.mercadolivre.com.br/afiliados/linkbuilder#hub"

# --- 2. MOTOR DE REFINAMENTO ---

def limpar_titulo_ninja(titulo_bruto):
    titulo = titulo_bruto.upper()
    for gatilho in GATILHOS_DE_CORTE:
        titulo = titulo.replace(gatilho.upper(), "")
    titulo = re.sub(r'\s+', ' ', titulo).strip()
    palavras = titulo.split()
    return " ".join(palavras[:6]).title()

def obter_chamada_inteligente(nome_produto):
    n = nome_produto.lower()
    if any(x in n for x in ["perfum", "colonia", "eau", "toilette"]): cat = "perfume"
    elif any(x in n for x in ["tenis", "sapato", "bota", "chinelo"]): cat = "tenis"
    elif any(x in n for x in ["camiseta", "polo", "calça", "jeans"]): cat = "roupa"
    else: cat = "geral"
    return random.choice(CHAMADAS.get(cat, CHAMADAS["geral"]))

# --- 3. MOTOR DE URL (CORREÇÃO CRÍTICA DO CLICK1) ---

def limpar_url_pure(url_original):
    """Garante que apenas links REAIS de produtos cheguem ao gerador."""
    if "click1.mercadolivre" in url_original:
        # Busca o ID MLB em qualquer parte da URL (no parâmetro wid ou na própria rota)
        match = re.search(r'(MLB-?\d+)', url_original)
        if match:
            # Extrai apenas os números (ex: MLB-12345 -> 12345)
            id_limpo = re.sub(r'\D', '', match.group(1))
            print(f"   🎯 [URL] Convertendo Click1 para: MLB-{id_limpo}")
            return f"https://produto.mercadolivre.com.br/MLB-{id_limpo}"
        else:
            # Se for anúncio e não achamos o ID, retornamos None para o bot ignorar
            return None
    
    # Se for link normal, removemos o rastreio (tudo após o ?)
    return url_original.split('?')[0].split('#')[0]

def gerar_link_meli_rpa(driver, url_limpa):
    wait = WebDriverWait(driver, 15)
    try:
        driver.get(URL_GERADOR_ML)
        time.sleep(4) 
        textarea = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "textarea")))
        textarea.click()
        textarea.clear()
        textarea.send_keys(url_limpa)
        time.sleep(1)
        textarea.send_keys(Keys.TAB)
        time.sleep(1)

        btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Gerar')]")))
        driver.execute_script("arguments[0].click();", btn)
        
        # Captura com Regex (Anti-lixo na mensagem)
        for tentativa in range(12):
            try:
                elementos = driver.find_elements(By.XPATH, "//input[contains(@value, 'meli.la')] | //*[contains(text(), 'meli.la')]")
                for el in elementos:
                    texto = el.get_attribute("value") or el.text
                    match = re.search(r'(https://meli\.la/\S+)', texto)
                    if match: return match.group(1)
            except: pass
            time.sleep(1.5)
        raise Exception("Timeout meli.la")
    except Exception as e:
        print(f" ⚠️ [RPA] Falha: {e}. Usando Fallback.")
        url_enc = urllib.parse.quote(url_limpa)
        return f"https://www.mercadolivre.com.br/social/{TAG_AFILIADO}?matt_word={TAG_AFILIADO}&matt_tool={TOOL_ID}&forceInApp=true&ref={url_enc}"

# --- FUNÇÃO DE PREÇO (CENTENA VS MILHAR) ---
def extrair_preco(tag):
    inteiro_tag = tag.select_one('.andes-money-amount__fraction')
    centavos_tag = tag.select_one('.andes-money-amount__cents')
    if not inteiro_tag: return 0.0
    
    # Remove o ponto de milhar para não virar dezenas de milhares
    inteiro_texto = inteiro_tag.text.replace('.', '')
    valor_final = f"{inteiro_texto}.{centavos_tag.text}" if centavos_tag else inteiro_texto
    try: return float(valor_final)
    except: return 0.0

# --- 4. MONITORAMENTO ---

def monitor():
    sistema = platform.system()
    print(f"🚀 v38.8 MASTERMIND | Sistema: {sistema}")
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={os.path.join(os.getcwd(), 'chrome_profile')}")
    driver = uc.Chrome(options=options, version_main=146) if sistema == "Windows" else uc.Chrome(options=options)

    if sistema == "Windows":
        driver.get(URL_GERADOR_ML)
        print("\n" + "="*50 + "\nLOGUE NA CENTRAL E APERTE ENTER NO TERMINAL\n" + "="*50)
        input("👉 Vamos gerar esses links?")

    while True:
        try:
            if os.path.exists("historico_precos.json"):
                with open("historico_precos.json", 'r') as f: historico = json.load(f)
            else: historico = {}

            random.shuffle(TERMOS_PESQUISA)
            for termo in TERMOS_PESQUISA:
                print(f"🔎 Analisando: {termo.upper()}")
                driver.get(f"https://lista.mercadolivre.com.br/{termo.replace(' ', '-')}_NoIndex_True")
                
                driver.execute_script("window.scrollBy(0, 450);")
                time.sleep(2)
                driver.execute_script("document.querySelectorAll('.poly-card, .ui-search-result__wrapper').forEach(c => c.dispatchEvent(new MouseEvent('mouseover', {bubbles: true})));")
                time.sleep(3)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                cards = soup.select('.poly-card') or soup.select('.ui-search-result__wrapper')

                candidatos = []
                for card in cards[:8]:
                    try:
                        txt = f"{card.get_text(separator=' ')} {card.get('aria-label', '')}".lower()
                        rating = 0
                        m_r = re.search(r'(\d[.,]\d)\s*(?=estrelas|de 5|avalia|nota|\()', txt)
                        if m_r: rating = float(m_r.group(1).replace(',', '.'))

                        precos_tags = card.select('.andes-money-amount')
                        if len(precos_tags) >= 2:
                            p_old = extrair_preco(precos_tags[0])
                            p_new = extrair_preco(precos_tags[1])
                            
                            if p_old > 0 and p_new > 0:
                                desc = int(100 - ((p_new * 100) / p_old))
                                if desc > 90: continue 

                                if rating >= MIN_RATING and desc >= MIN_DESCONTO:
                                    raw_title = (card.select_one('.poly-component__title') or card.select_one('h2')).text
                                    nome_ninja = limpar_titulo_ninja(raw_title)

                                    if nome_ninja not in historico or p_new < (historico[nome_ninja] - 1):
                                        # LIMPEZA CRÍTICA AQUI
                                        link_puro = limpar_url_pure(card.select_one('a')['href'])
                                        if not link_puro: continue # Ignora se for click1 sem ID
                                        
                                        img = card.select_one('img')
                                        foto = (img.get('data-src') or img.get('src')).replace("-I.jpg", "-O.jpg")
                                        
                                        candidatos.append({
                                            'nome': nome_ninja, 'p_old': p_old, 'p_new': p_new, 
                                            'foto': foto, 'link_limpo': link_puro
                                        })
                                        historico[nome_ninja] = p_new
                    except: continue

                if candidatos:
                    for item in candidatos:
                        link_meli = gerar_link_meli_rpa(driver, item['link_limpo'])
                        frase = obter_chamada_inteligente(item['nome'])
                        
                        msg = (f"🔥 *{item['nome'].upper()}* 🔥\n\n"
                               f"❌ De ~R$ {item['p_old']:.2f}~\n"
                               f"✅ *Por R$ {item['p_new']:.2f}* 💰\n\n"
                               f"> {frase} 🚀\n\n"
                               f"🛒 *LINK:* {link_meli}")

                        requests.post(f"{EVOLUTION_API_URL}/message/sendMedia/{EVOLUTION_INSTANCE}", 
                                      json={"number": WA_GROUP_ID, "mediatype": "image", "media": item['foto'], "caption": msg},
                                      headers={"Content-Type": "application/json", "apikey": EVOLUTION_API_KEY}, verify=False)
                        print(f" 📲 Enviado: {item['nome']}")
                        time.sleep(random.randint(45, 65))

            with open("historico_precos.json", 'w') as f: json.dump(historico, f, indent=4)
            print("\n😴 Ciclo OK. Dormindo 15 min...")
            time.sleep(900)
        except Exception as e:
            print(f"💥 Erro: {e}")
            time.sleep(60)

if __name__ == "__main__":
    Thread(target=lambda: Flask('').run(host='0.0.0.0', port=10000)).start()
    monitor()