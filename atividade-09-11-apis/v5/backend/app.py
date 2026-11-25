import os
from pathlib import Path
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

CHAVE_API = os.getenv("YOUTUBE_API_KEY")

URL_CANAIS = "https://www.googleapis.com/youtube/v3/channels"
URL_VIDEOS = "https://www.googleapis.com/youtube/v3/playlistItems"

app = FastAPI(
    title="API YouTube - Versão 5",
    description="Backend intermediário para acesso seguro à YouTube Data API",
    version="5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
def inicio():
    return {"mensagem": "API está no ar!"}

@app.get("/api/canal")
async def buscar_canal(handle: str = Query(..., min_length=1, max_length=100)):
    if not CHAVE_API or CHAVE_API == "SUA_CHAVE_AQUI":
        raise HTTPException(503, "Configure YOUTUBE_API_KEY no arquivo backend/.env e reinicie o servidor.")

    parametros = {
        "part": "snippet,contentDetails",
        "forHandle": handle,
        "key": CHAVE_API
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as cliente:
            resposta = await cliente.get(URL_CANAIS, params=parametros)

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível acessar a API do YouTube."
        )

    if resposta.status_code != 200:
        raise HTTPException(
            status_code=resposta.status_code,
            detail="Erro ao consultar o canal no YouTube."
        )

    dados = resposta.json()

    if not dados.get("items"):
        raise HTTPException(
            status_code=404,
            detail="Canal não encontrado."
        )

    canal = dados["items"][0]

    return {
        "titulo": canal["snippet"]["title"],
        "playlist": canal["contentDetails"]["relatedPlaylists"]["uploads"]
    }

@app.get("/api/videos")
async def buscar_videos(
    playlist: str = Query(..., min_length=1, max_length=200),
    page_token: str | None = Query(None),
    max_results: int = Query(12, ge=1, le=50)
):
    if not CHAVE_API or CHAVE_API == "SUA_CHAVE_AQUI":
        raise HTTPException(503, "Configure YOUTUBE_API_KEY no arquivo backend/.env e reinicie o servidor.")

    parametros = {
        "part": "snippet",
        "playlistId": playlist,
        "maxResults": max_results,
        "key": CHAVE_API
    }

    if page_token:
        parametros["pageToken"] = page_token

    try:
        async with httpx.AsyncClient(timeout=10.0) as cliente:
            resposta = await cliente.get(URL_VIDEOS, params=parametros)

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível acessar a API do YouTube."
        )

    if resposta.status_code != 200:
        raise HTTPException(
            status_code=resposta.status_code,
            detail="Erro ao consultar os vídeos no YouTube."
        )

    dados = resposta.json()
    videos = []

    for item in dados.get("items", []):
        snippet = item.get("snippet", {})
        video_id = snippet.get("resourceId", {}).get("videoId")

        if not video_id:
            continue

        videos.append({
            "videoId": video_id,
            "titulo": snippet.get("title", ""),
            "descricao": snippet.get("description", ""),
            "publicadoEm": snippet.get("publishedAt"),
            "thumbnail": obter_thumbnail(
                snippet.get("thumbnails", {})
            )
        })

    return {
        "videos": videos,
        "nextPageToken": dados.get("nextPageToken")
    }

def obter_thumbnail(thumbnails):
    for tamanho in ["maxres", "standard", "high", "medium", "default"]:
        if tamanho in thumbnails:
            return thumbnails[tamanho]["url"]

    return ""
