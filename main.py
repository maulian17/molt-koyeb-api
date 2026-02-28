import time
import requests
from fastapi import FastAPI, Request, HTTPException
from functools import lru_cache

app = FastAPI(title="Molty Royale Proxy Stabilizer")

TARGET_BASE_URL = "https://cdn.moltyroyale.com"

# Cache untuk data statis/jarang berubah (misal: info region) selama 30 detik
@lru_cache(maxsize=100)
def get_cached_data(url, headers_str):
    # Logika cache internal untuk mengurangi hit ke server pusat
    pass

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_engine(path: str, request: Request):
    url = f"{TARGET_BASE_URL}/{path}"
    method = request.method
    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}
    body = await request.body()

    # KONFIGURASI STABILIZER
    max_retries = 5
    retry_delay = 1.5 # detik

    for attempt in range(max_retries):
        try:
            # Menggunakan session untuk koneksi yang lebih cepat (Keep-Alive)
            with requests.Session() as session:
                response = session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=body,
                    timeout=12 # Timeout agresif agar tidak nunggu lama saat server lag
                )

            # Jika server game sukses (200) atau error user (400), langsung kembalikan
            if response.status_code < 500:
                return response.json()
            
            # Jika error server (502, 503, 504), lakukan retry otomatis
            print(f"Server Busy ({response.status_code}). Attempt {attempt+1}/{max_retries}...")
            time.sleep(retry_delay)
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            print(f"Connection/Timeout Error. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)

    raise HTTPException(status_code=504, detail="Molty Server is completely unresponsive after retries.")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)