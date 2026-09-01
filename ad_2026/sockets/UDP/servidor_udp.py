import socket
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 6000

# SOCK_DGRAM define que o protocolo é UDP
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

print("[-] Servidor UDP pronto na porta 6000...")

while True:
    # recvfrom retorna os dados e o endereço (IP, Porta) de quem enviou
    dados, endereço_cliente = server.recvfrom(1024)
    mensagem = dados.decode('utf-8')
    print(f"[{endereço_cliente}]: {mensagem}")

    # Resposta direta para o endereço que acabou de enviar
    resposta = f"UDP Echo: {mensagem.upper()}"
    server.sendto(resposta.encode('utf-8'), endereço_cliente)
