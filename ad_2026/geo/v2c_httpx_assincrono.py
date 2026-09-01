import os
import asyncio
import httpx
from dotenv import load_dotenv

# SEGURANÇA: Carrega a chave de API a partir do arquivo externo .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


async def buscar_coordenadas():
    endereco = "Rua Paese, 198, Videira, SC, Brazil"
    BASE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'

    parameters = {
        'address': endereco,
        'key': API_KEY
    }

    try:
        print(f"Buscando endereço (Assíncrono): {endereco}")
        print(f"Enviando requisição HTTP GET para: {BASE_URL}")

        # Uso do cliente assíncrono do httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # A palavra 'await' pausa temporariamente ESTA função liberando o processador para outras tarefas
            response = await client.get(BASE_URL, params=parameters)

            # BOAS PRÁTICAS: Verifica erros de protocolo HTTP
            response.raise_for_status()

        # Converte o corpo da resposta HTTP em um dicionário Python
        answer = response.json()

        print(f"\nStatus retornado no JSON da API: {answer.get('status')}")

        # TRATAMENTO DE REGRAS DE NEGÓCIO DA API
        if answer.get('status') == 'OK' and answer.get('results'):
            primeiro_resultado = answer['results'][0]
            location = primeiro_resultado['geometry']['location']

            print(f"Endereço Formatado Oficial: {primeiro_resultado.get('formatted_address')}")
            print(f"Lat: {location['lat']}, Lng: {location['lng']}")
        elif answer.get('status') == 'REQUEST_DENIED':
            print("\n[Erro de Autenticação] A chave de API é inválida ou o faturamento não está ativo no Google Cloud.")
            print(f"Mensagem do Google: {answer.get('error_message')}")
        else:
            print(f"\n[Erro na Busca] O Google retornou o status: {answer.get('status')}")
            print("Verifique se o endereço está correto.")

    # TRATAMENTO DE EXCEÇÕES DE REDE ESPECÍFICAS DO HTTPX
    except httpx.HTTPStatusError as e:
        print(f"\n[Erro de Protocolo] Resposta de erro do servidor (HTTP {e.response.status_code}): {e}")
    except httpx.RequestError as e:
        print(f"\n[Erro de Conexão] Falha de rede ao se comunicar com o Google: {e}")
    except Exception as e:
        print(f"\n[Erro Inesperado] Ocorreu uma falha interna no script: {e}")


# Ponto de entrada obrigatório para rodar códigos assíncronos em Python
if __name__ == "__main__":
    asyncio.run(buscar_coordenadas())
