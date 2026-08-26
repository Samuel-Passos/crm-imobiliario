import time
import requests

API_KEY = "3034371d153a98d79e1546db4146fe4a"
SITE_KEY = "6LdeSBITAAAAAMq-ckp15zFfmVs0ZXMNwnCPxkob"

def solve_recaptcha(url, api_key=API_KEY, site_key=SITE_KEY):
    print("Enviando captcha para 2Captcha...")
    r1 = requests.post("http://2captcha.com/in.php", data={
        "key": api_key,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": url,
        "json": 1
    })
    
    res1 = r1.json()
    if res1.get("status") != 1:
        print(f"Erro ao enviar: {res1}")
        return None
        
    req_id = res1["request"]
    print(f"Captcha enviado. ID: {req_id}. Aguardando solucao...")
    
    # Poll
    for _ in range(30):
        time.sleep(5)
        r2 = requests.get(f"http://2captcha.com/res.php?key={api_key}&action=get&id={req_id}&json=1")
        res2 = r2.json()
        if res2.get("status") == 1:
            print("CAPTCHA RESOLVIDO!")
            return res2["request"]
        elif res2.get("request") != "CAPCHA_NOT_READY":
            print(f"Erro no poll: {res2}")
            return None
            
    print("Timeout esperando 2Captcha.")
    return None
