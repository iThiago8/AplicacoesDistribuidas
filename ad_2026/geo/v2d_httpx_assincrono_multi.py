import os
import asyncio
import httpx
from dotenv import load_dotenv

# SEGURANÇA: Carrega a chave de API a partir do arquivo externo .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

BASE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'


# Função assíncrona responsável por processar UM único endereço utilizando um cliente compartilhado
async def geocodificar_endereco(client: httpx.AsyncClient, endereco: str):
    parameters = {
        'address': endereco,
        'key': API_KEY
    }

    try:
        # Dispara a requisição de forma assíncrona
        response = await client.get(BASE_URL, params=parameters)
        response.raise_for_status()
        answer = response.json()

        status = answer.get('status')

        if status == 'OK' and answer.get('results'):
            primeiro_resultado = answer['results'][0]
            location = primeiro_resultado['geometry']['location']
            print(f"✅ SUCESSO | {endereco} -> Lat: {location['lat']}, Lng: {location['lng']}")
        elif status == 'REQUEST_DENIED':
            print(f"❌ NEGADO   | {endereco} -> Chave inválida ou faturamento desativado.")
        else:
            print(f"⚠️ FALHA    | {endereco} -> Status da API: {status}")
    except httpx.HTTPStatusError as e:
        print(f"💥 ERRO HTTP| {endereco} -> Código {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"🌐 ERRO REDE| {endereco} -> Falha de conexão: {e}")
    except Exception as e:
        print(f"❗ ERRO INES| {endereco} -> {e}")


# Função principal que gerencia o lote de tarefas
async def main():
    # Lista didática com múltiplos endereços para teste simultâneo
    lista_enderecos = [
        "Rua Paese, 198, Videira, SC, Brazil",
        "Avenida Paulista, 1000, São Paulo, SP, Brazil",
        "Copacabana Palace, Rio de Janeiro, RJ, Brazil",
        "Esplanada dos Ministérios, Brasília, DF, Brazil"
    ]

    print(f"Iniciando a busca simultânea de {len(lista_enderecos)} endereços...\n")

    # Criamos um único cliente assíncrono para ser reaproveitado por todas as requisições (boa prática)
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Cria uma lista de "tarefas" (coroutines) pendentes, uma para cada endereço
        tarefas = [geocodificar_endereco(client, end)
                   for end in lista_enderecos]

        # O asyncio.gather executa todas as tarefas da lista SIMULTANEAMENTE e espera todas terminarem
        await asyncio.gather(*tarefas)

    print("\nTodos os endereços foram processados.")


# Ponto de entrada para iniciar o loop de eventos assíncronos
if __name__ == "__main__":
    asyncio.run(main())
