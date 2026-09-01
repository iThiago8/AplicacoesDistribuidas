import os
import socket
import ssl
from urllib.parse import quote_plus
from dotenv import load_dotenv

# SEGURANÇA MÁXIMA: Mantendo a chave protegida no arquivo .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

HOST = 'maps.googleapis.com'
PORT = 443
endereco = "Rua Paese, 198, Videira, SC, Brazil"

# Montagem textual da requisição HTTP/1.1 estrita (Sem o parâmetro obsoleto 'sensor')
request_text = (
    f"GET /maps/api/geocode/json?address={quote_plus(endereco)}&key={API_KEY} HTTP/1.1\r\n"
    f"Host: {HOST}\r\n"
    f"User-Agent: geo_raw_socket_v6\r\n"
    f"Connection: close\r\n"  # Força o Google a fechar o socket após o fim do envio
    f"\r\n"
)

try:
    print(f"Iniciando conexão segura via Socket com {HOST}...")

    # Configuração manual da camada de Transporte e Criptografia
    context = ssl.create_default_context()
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.settimeout(10.0)  # Evita travamento infinito do script

    secure_socket = context.wrap_socket(raw_socket, server_hostname=HOST)
    secure_socket.connect((HOST, PORT))

    print("Enviando requisição HTTP...")
    secure_socket.sendall(request_text.encode('utf-8'))

    print("Recebendo bytes do servidor e exibindo em tempo real:\n")
    print("=" * 50 + " INÍCIO DOS DADOS BRUTOS " + "=" * 50)

    # Laço de repetição que lê os pacotes da rede à medida que eles chegam
    while True:
        # Lê blocos de até 4096 bytes por vez
        dados_recebidos = secure_socket.recv(4096)

        # Se o servidor fechar a conexão (fim dos dados), o retorno será vazio
        if not dados_recebidos:
            break

        # Decodifica e imprime o pedaço do fluxo de rede imediatamente na tela
        print(dados_recebidos.decode('utf-8'), end='')

    print("\n" + "=" * 51 + " FIM DOS DADOS BRUTOS " + "=" * 51)

    # Fecha o canal de comunicação local de forma limpa
    secure_socket.close()
except socket.timeout:
    print("\n[Erro de Rede] Tempo limite esgotado (Timeout) ao aguardar resposta do servidor.")
except Exception as e:
    print(f"\n[Erro Inesperado] Falha na comunicação via Socket: {e}")
