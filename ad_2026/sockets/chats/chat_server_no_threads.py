import socket
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)

print(f"[*] Servidor SÍNCRONO aguardando conexão em {HOST}:{PORT}...")
client_socket, client_address = server.accept()
print(f"[+] Cliente conectado: {client_address}")

try:
    while True:
        # PROBLEMA 1: O servidor trava aqui e fica esperando o cliente falar algo.
        # Ele é incapaz de enviar uma mensagem por conta própria antes de receber dados.
        data = client_socket.recv(1024)
        if not data:
            break
        print(f"\n[Cliente diz]: {data.decode('utf-8').strip()}")

        # PROBLEMA 2: Após receber, o servidor trava no input do teclado.
        # Se o cliente enviar outra mensagem enquanto o servidor digita, ela ficará presa no buffer.
        mensagem = input("[Sua resposta]: ")
        client_socket.sendall((mensagem + "\n").encode('utf-8'))

        if mensagem.lower() == 'sair':
            break
finally:
    client_socket.close()
    server.close()
