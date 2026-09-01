import socket
import sys
import threading

# 1. Configuração dos valores padrões (Localhost na porta 5000)
HOST = '127.0.0.1'
PORT = 5000

# 2. Tratamento dos argumentos da linha de comando
if len(sys.argv) > 1:
    HOST = sys.argv[1]

if len(sys.argv) > 2:
    try:
        PORT = int(sys.argv[2])
    except ValueError:
        print("Erro: A porta deve ser um número inteiro.")
        sys.exit(1)

# Função executada em background APENAS para escutar o servidor
def receber_mensagens(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                print("\n[*] O servidor encerrou o chat.")
                break

            print(f"\n[Servidor]: {data.decode('utf-8').strip()}")
            print("[Você]: ", end="", flush=True)
        except (OSError, socket.error):
            # Captura silenciosamente o Bad file descriptor (Errno 9) ou Connection reset
            # quando o cliente ou o servidor fecham o socket abruptamente
            break
        except:
            break

    # Removemos o print daqui para evitar mensagens duplicadas ou fora de hora
    try:
        client_socket.close()
    except:
        pass

# 3. Inicialização do Socket TCP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    print(f"[*] Conectando ao chat em {HOST}:{PORT}...")
    client.connect((HOST, PORT))
    print("[+] Conectado à sala de chat!")
    print("Digite suas mensagens livremente. Digite 'sair' para encerrar.")
    print("-" * 50)

    # 4. Dispara a Thread em background para RECEBER dados do servidor
    t = threading.Thread(target=receber_mensagens, args=(client,), daemon=True)
    t.start()

    # 5. O loop principal do script fica livre apenas para ENVIAR dados
    while True:
        mensagem = input("[Você]: ")
        mensagem_limpa = message_clean = mensagem.strip()

        if not mensagem_limpa:
            continue

        if mensagem_limpa.lower() == 'sair':
            try:
                client.sendall("sair\n".encode('utf-8'))
            except:
                pass
            break

        try:
            client.sendall((mensagem_limpa + "\n").encode('utf-8'))
        except (OSError, socket.error):
            print("\n[-] Erro: Não foi possível enviar a mensagem. O servidor caiu.")
            break
except KeyboardInterrupt:
    print("\n[*] Você saiu do chat (Ctrl+C).")
except ConnectionRefusedError:
    print(f"[-] Erro: Não foi possível conectar ao chat em {HOST}:{PORT}.")
except Exception as e:
    # Este bloco agora só pegará erros REAIS de inicialização, não de encerramento
    print(f"[-] Erro inesperado na conexão: {e}")
finally:
    # Fecha o socket de forma segura no final do script
    try:
        client.close()
    except:
        pass
    print("[*] Programa finalizado.")
