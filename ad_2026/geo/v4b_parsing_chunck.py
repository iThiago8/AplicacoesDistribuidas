import os
import socket
import ssl
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

HOST = 'httpbin.org'
PORT = 443

# Este endpoint do httpbin gera uma resposta dividida obrigatoriamente em 3 pedaços (chunks)
request_text = (
    "GET /stream/3 HTTP/1.1\r\n"
    f"Host: {HOST}\r\n"
    "User-Agent: teste_acadêmico_v8\r\n"
    "Connection: close\r\n"  # Pode usar close aqui que ele vai quebrar do mesmo jeito!
    "\r\n"
)

try:
    context = ssl.create_default_context()
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.settimeout(5.0)  # Importante: Como a conexão fica viva, precisamos do timeout para sair do loop

    secure_socket = context.wrap_socket(raw_socket, server_hostname=HOST)
    secure_socket.connect((HOST, PORT))
    secure_socket.sendall(request_text.encode('utf-8'))

    print("=" * 40 + " DADOS BRUTOS (FORCED CHUNK) " + "=" * 40)

    while True:
        try:
            dados_recebidos = secure_socket.recv(4096)
            if not dados_recebidos:
                break

            # Imprime os bytes brutos exatamente como chegam da placa de rede
            print(dados_recebidos.decode('utf-8'), end='')

            # Se encontrar o chunk final (um 0 isolado seguido de quebras de linha), encerra o laço
            if b'\r\n0\r\n\r\n' in dados_recebidos:
                print("\n\n[Socket] Detectado o marcador de fim de chunk (0). Encerrando leitura.")
                break

        except socket.timeout:
            # Como usamos 'keep-alive', o Google não fecha a conexão sozinho imediatamente,
            # o timeout garante que o script não fique travado após receber tudo.
            print("\n\n[Socket] Timeout atingido. Conexão mantida viva pelo servidor.")
            break

    secure_socket.close()
    print("=" * 109)

except Exception as e:
    print(f"\nErro: {e}")
