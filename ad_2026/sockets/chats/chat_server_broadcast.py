import socket
import sys
import threading

HOST = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

# Lista global para rastrear todos os clientes conectados
clientes = []


def gerenciar_cliente(client_socket, client_address):
    print(f"[+] {client_address} entrou no chat.")
    # Adiciona o novo cliente à lista
    clientes.append(client_socket)

    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            mensagem = data.decode('utf-8').strip()
            if mensagem.lower() == 'sair':
                break

            formato_msg = f"\n[{client_address}]: {mensagem}\n[Você]: "
            print(f"Transmitindo de {client_address}: {mensagem}")

            # BROADCAST: Envia para todos os OUTROS clientes conectados
            for c in clientes:
                if c != client_socket:
                    try:
                        c.sendall(formato_msg.encode('utf-8'))
                    except:
                        # Remove clientes que caíram ou desconectaram abruptamente
                        if c in clientes:
                            clientes.remove(c)

    except Exception as e:
        print(f"[-] Erro com {client_address}: {e}")
    finally:
        if client_socket in clientes:
            clientes.remove(client_socket)
        client_socket.close()
        print(f"[-] {client_address} saiu do chat.")


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(10)  # Suporta até 10 conexões na fila
print(f"[*] Servidor de Broadcast Centralizado rodando em {HOST}:{PORT}")

try:
    while True:
        client_socket, client_address = server.accept()
        t = threading.Thread(target=gerenciar_cliente, args=(client_socket, client_address), daemon=True)
        t.start()
except KeyboardInterrupt:
    print("\n[*] Fechando servidor central...")
finally:
    server.close()
