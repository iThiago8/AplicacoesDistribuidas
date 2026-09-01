import os
import socket
import ssl
import json
from urllib.parse import quote_plus
from dotenv import load_dotenv

# VANTAGEM REUNIDA: Segurança máxima com python-dotenv para proteção da chave
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

HOST = 'maps.googleapis.com'
endereco = "Rua Paese, 198, Videira, SC, Brazil"

request_text = """\
GET /maps/api/geocode/json?address={}&key={} HTTP/1.1\r\n\
Host: {}\r\n\
User-Agent: geo_v5_final_socket\r\n\
Connection: close\r\n\
\r\n
"""

try:
    context = ssl.create_default_context()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_sock = context.wrap_socket(sock, server_hostname=HOST)

    print(f"Conectando a {HOST}...")
    s_sock.connect((HOST, 443))

    request = request_text.format(quote_plus(endereco), API_KEY, HOST)
    s_sock.sendall(request.encode('utf-8'))

    # 2. VANTAGEM DO SEU CÓDIGO: Coleta eficiente acumulando bytes puros na memória
    raw_reply = b''
    while True:
        more = s_sock.recv(4096)
        if not more:
            break
        raw_reply += more

    s_sock.close()

    # Decodifica a resposta completa uma única vez fora do laço
    response_text = raw_reply.decode('utf-8')

    # Separa Cabeçalhos HTTP do Corpo (JSON) através da quebra dupla \r\n\r\n
    parts = response_text.split('\r\n\r\n', 1)

    if len(parts) == 2:
        headers, body = parts

        # 3. VANTAGEM DO SEU CÓDIGO: Validação cirúrgica do status HTTP na primeira linha
        status_line = headers.split('\r\n')[0]
        if '200 OK' not in status_line:
            print(f"Erro HTTP do Servidor: {status_line}")
        else:
            # 4. VANTAGEM DA MINHA VERSÃO: Máquina de estados para limpar Chunks se existirem
            # Verifica se o servidor usou codificação em pedaços analisando os cabeçalhos
            if 'Transfer-Encoding: chunked' in headers:
                print("[Protocolo] Detectado Transfer-Encoding: chunked. Limpando metadados de rede...")
                linhas = body.split('\r\n')
                corpo_limpo = []
                alternar_leitura = True

                for linha in linhas:
                    if not linha:
                        continue
                    if alternar_leitura:
                        if linha.strip() == '0':  # Fim dos chunks
                            break
                        alternar_leitura = False  # Próxima linha contém os dados legítimos
                    else:
                        corpo_limpo.append(linha)
                        alternar_leitura = True

                body_final = "".join(corpo_limpo)
            else:
                # Se não for chunked (caso padrão do Google Maps), usa o corpo limpo direto
                body_final = body

            # Processamento final do JSON limpo
            try:
                data = json.loads(body_final)
                status = data.get('status')

                if status == 'OK':
                    if len(data['results']) > 0:
                        loc = data['results'][0]['geometry']['location']
                        print(f"\nEndereço: {endereco}")
                        print(f"Latitude: {loc['lat']}")
                        print(f"Longitude: {loc['lng']}")
                    else:
                        print("Erro: Nenhum resultado encontrado (lista vazia).")
                else:
                    print(f"Erro da API do Google: {status}")
                    if 'error_message' in data:
                        print(f"Detalhe: {data['error_message']}")
            except json.JSONDecodeError:
                print("Erro Crítico: Não foi possível ler o JSON da resposta.")
                print(f"Corpo bruto que falhou no parsing: {body_final}")
    else:
        print("Erro: Formato de resposta HTTP inválido (Falta de cabeçalhos).")
except ssl.SSLError as e:
    print(f"Erro de criptografia SSL/TLS: {e}")
except socket.error as e:
    print(f"Erro físico de Socket/Conexão de rede: {e}")
except Exception as e:
    print(f"Erro inesperado: {e}")
