from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import httpx
import random
import string

app = FastAPI()
templates = Jinja2Templates(directory="templates")

MAIL_TM_API = "https://api.mail.tm"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/api/create-account")
async def create_account():
    async with httpx.AsyncClient() as client:
        try:
            # 1. Önce kullanılabilir bir domain al
            domain_res = await client.get(f"{MAIL_TM_API}/domains")
            if domain_res.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Domain alınamadı: {domain_res.text}")
            
            domains_list = domain_res.json().get("hydra:member", [])
            if not domains_list:
                raise HTTPException(status_code=500, detail="Kullanılabilir domain bulunamadı.")
            domain = domains_list[0]["domain"]
            
            # Rastgele kullanıcı adı ve şifre üret
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            address = f"{username}@{domain}"
            password = "Password123!"
            
            # 2. Hesap oluştur
            acc_res = await client.post(f"{MAIL_TM_API}/accounts", json={
                "address": address,
                "password": password
            })
            if acc_res.status_code != 201:
                raise HTTPException(status_code=500, detail=f"Hesap oluşturulamadı: {acc_res.text}")
                
            # 3. Token al
            token_res = await client.post(f"{MAIL_TM_API}/token", json={
                "address": address,
                "password": password
            })
            if token_res.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Token alınamadı: {token_res.text}")
                
            token = token_res.json().get("token")
            return {"email": address, "token": token}
            
        except Exception as e:
            print("HATA OLUŞTU:", str(e))
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/messages")
async def get_messages(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{MAIL_TM_API}/messages", headers=headers)
        if res.status_code != 200:
            return []
        return res.json().get("hydra:member", [])

@app.get("/api/message/{message_id}")
async def get_message_detail(message_id: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{MAIL_TM_API}/messages/{message_id}", headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=404, detail="Mesaj bulunamadı.")
        return res.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
