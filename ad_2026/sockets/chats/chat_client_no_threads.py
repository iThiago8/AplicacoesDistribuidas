import socket
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
print("[+] Conectado ao servidor síncrono!")

try:
    while True:
        # O cliente é forçado a seguir um protocolo rígido de "Ping-Pong" (Turnos)
        mensagem = input("[Você]: ")
        client.sendall((mensagem + "\n").encode('utf-8'))

        if mensagem.lower() == 'sair':
            break

        print("[*] Aguardando resposta do servidor...")
        # O cliente trava aqui e não consegue digitar nada até o servidor responder
        data = client.recv(1024)
        if not data:
            break
        print(f"[Servidor]: {data.decode('utf-8').strip()}")
finally:
    client.close()
