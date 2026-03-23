import requests

def encurtar_link(link_longo):
    try:
        url_api = f"http://tinyurl.com/api-create.php?url={link_longo}"
        res = requests.get(url_api, timeout=10)
        return res.text if res.status_code == 200 else link_longo
    except:
        return link_longo