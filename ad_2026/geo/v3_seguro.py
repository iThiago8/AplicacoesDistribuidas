import os
import http.client
import json
from urllib.parse import quote_plus
from dotenv import load_dotenv

# SEGURANÇA MÁXIMA: Carrega a chave do arquivo .env (técnica atual para PyCharm)
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

endereco = "Rua Paese, 198, Videira, SC, Brazil"

# Codifica o endereço para o formato aceito em URLs (ex: espaços viram '+')
endereco_codificado = quote_plus(endereco)

# Constrói o caminho completo do recurso (Path) injetando a chave protegida
path = f'/maps/api/geocode/json?address={endereco_codificado}&key={API_KEY}'

try:
    print(f"Iniciando conexão HTTPS de baixo nível com o Google...")
    # ROBUSTEZ: Adicionado 'timeout=10' para o script não travar se a rede falhar
    connection = http.client.HTTPSConnection('maps.googleapis.com', timeout=10)

    # Envia o cabeçalho do protocolo GET
    connection.request('GET', path)

    # Captura o fluxo de dados retornado
    response = connection.getresponse()
    raw_data = response.read().decode('utf-8')

    # Fecha a conexão explicitamente após ler os dados recebidos
    connection.close()

    # TRATAMENTO DO PROTOCOLO HTTP: Verifica se o servidor respondeu com sucesso (200 OK)
    if response.status != 200:
        print(f"Erro no protocolo HTTP: {response.status} {response.reason}")
    else:
        # Transforma o texto bruto de bytes em um dicionário Python
        data = json.loads(raw_data)
        status = data.get('status')

        print(f"\nEndereço pesquisado: {endereco}")
        print(f"Status da API do Google: {status}")

        # 4. TRATAMENTO DA REGRA DE NEGÓCIO DO GOOGLE
        if status == 'OK':
            if len(data.get('results', [])) > 0:
                location = data['results'][0]['geometry']['location']
                print(f"Endereço Oficial Google: {data['results'][0].get('formatted_address')}")
                print(f"Latitude: {location['lat']}")
                print(f"Longitude: {location['lng']}")
            else:
                print("Erro: Nenhum resultado geográfico retornado (lista vazia).")
        elif status == 'REQUEST_DENIED':
            print("\n[Acesso Negado] Verifique sua chave no arquivo .env ou as restrições de IP no painel do Google.")
            print(f"Detalhe do erro: {data.get('error_message', 'Sem mensagem detalhada.')}")
        else:
            print(f"Falha na busca do Google: {status}")
# TRATAMENTO DE EXCEÇÕES DA BIBLIOTECA PADRÃO
except http.client.HTTPException as e:
    print(f"Erro de comunicação na camada HTTP: {e}")
except json.JSONDecodeError as e:
    print(f"Erro crítico: O servidor não retornou um formato JSON válido: {e}")
except Exception as e:
    print(f"Erro inesperado no script: {e}")
