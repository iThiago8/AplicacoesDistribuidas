import http.client
import json
from urllib.parse import quote_plus

endereco = "Rua Paese, 198, Videira, SC, Brazil"
api_key = 'AIzaSyBsbsxRz3S-0jMX17RB6-CbtjNHgH4qCxk'

# Codifica o endereço para URL (substitui espaços por %20, etc.)
endereco_codificado = quote_plus(endereco)

# Constrói o caminho da requisição SEM o parâmetro 'sensor' (obsoleto)
path = f'/maps/api/geocode/json?address={endereco_codificado}&key={api_key}'

try:
    # Estabelece a conexão segura
    connection = http.client.HTTPSConnection('maps.googleapis.com')

    # Envia a requisição GET
    connection.request('GET', path)

    # Obtém a resposta
    response = connection.getresponse()
    raw_data = response.read().decode('utf-8')

    # Fecha a conexão explicitamente
    connection.close()

    # Verifica se o HTTP foi bem sucedido (código 200)
    if response.status != 200:
        print(f"Erro HTTP: {response.status} {response.reason}")
    else:
        # Parseia o JSON
        data = json.loads(raw_data)
        status = data.get('status')

        if status == 'OK':
            # Verifica se há resultados antes de acessar o índice 0
            if len(data['results']) > 0:
                location = data['results'][0]['geometry']['location']
                print(f"Endereço: {endereco}")
                print(f"Latitude: {location['lat']}")
                print(f"Longitude: {location['lng']}")
            else:
                print("Erro: Nenhum resultado encontrado (lista vazia).")
        else:
            print(f"Erro da API Google: {status}")
            # Exibe mensagem de erro detalhada se a API retornar uma
            if 'error_message' in data:
                print(f"Detalhe: {data['error_message']}")
            else:
                print("Verifique se a Geocoding API está habilitada e a chave está correta.")
except http.client.HTTPException as e:
    print(f"Erro de conexão HTTP: {e}")
except json.JSONDecodeError as e:
    print(f"Erro ao ler a resposta JSON: {e}")
except Exception as e:
    print(f"Erro inesperado: {e}")
