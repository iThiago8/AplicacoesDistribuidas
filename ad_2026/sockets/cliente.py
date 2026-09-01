import socket
import sys

# 1. Configuração dos valores padrões
HOST = '127.0.0.1'
PORT = 5001

# 2. Tratamento dos argumentos da linha de comando
if len(sys.argv) > 1:
    HOST = sys.argv[1]  # Se fornecido, substitui o IP padrão

if len(sys.argv) > 2:
    try:
        PORT = int(sys.argv[2])  # Se fornecido, substitui a porta padrão
    except ValueError:
        print("Erro: A porta deve ser um número inteiro.")
        print("Uso correto: python3 cliente.py <IP_DO_SERVIDOR> <PORTA>")
        print("Exemplo:     python3 cliente.py 192.168.1.50 10000")
        sys.exit(1)

# 3. Criação do socket TCP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    print(f"[*] Tentando conectar a {HOST}:{PORT}...")
    client.connect((HOST, PORT))
    print(f"[+] Conectado com sucesso!\n")
    print("Digite suas mensagens, contas ou 'sair' para encerrar.")
    print("-" * 50)

    # 4. Loop de envio e recepção
    while True:
        texto = input("Envio > ")

        # Remove espaços desnecessários antes de checar e enviar
        texto_limpo = texto.strip()

        if not texto_limpo:
            continue

        if texto_limpo.lower() == 'sair':
            # Envia o comando de saída para o servidor também saber que terminou
            client.sendall(texto_limpo.encode('utf-8'))
            break

        # Envia a string codificada em bytes para o socket
        client.sendall(texto_limpo.encode('utf-8'))

        # Aguarda a resposta do servidor (seja o Eco ou o resultado do cálculo)
        resposta_bytes = client.recv(1024)
        if not resposta_bytes:
            print("[*] O servidor encerrou a conexão.")
            break

        resposta_texto = resposta_bytes.decode('utf-8').strip()
        print(f"Retorno < {resposta_texto}\n")
except KeyboardInterrupt:
    print("\n[*] Conexão interrompida pelo usuário (Ctrl+C).")
except ConnectionRefusedError:
    print(f"[-] Erro: Conexão recusada em {HOST}:{PORT}.")
    print("Certifique-se de que o servidor correspondente está rodando nesta porta.")
except Exception as e:
    print(f"[-] Ocorreu um erro inesperado: {e}")
finally:
    client.close()
    print("[*] Socket fechado. Programa finalizado.")