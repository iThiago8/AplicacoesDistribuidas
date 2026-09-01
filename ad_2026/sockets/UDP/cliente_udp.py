import socket
import sys
HOST = '127.0.0.1'
PORT = 6000

if len(sys.argv) > 1:
    HOST = sys.argv[1]

if len(sys.argv) > 2:
    try:
        PORT = int(sys.argv[2])
    except ValueError:
        print("Erro: A porta deve ser um número inteiro.")
        sys.exit(1)

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
destino = (HOST, PORT)

mensagem = "Testando conexao UDP"
# No UDP, enviamos direto para o destino sem precisar de connect()
client.sendto(mensagem.encode('utf-8'), destino)

# Recebe a resposta e o endereço do servidor
dados, servidor = client.recvfrom(1024)
print(f"[Servidor]: {dados.decode('utf-8')}")

client.close()
