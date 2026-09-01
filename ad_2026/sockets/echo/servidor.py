import sys
import socket

# Verifica se o IP foi passado como argumento, senão usa localhost por padrão
HOST = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
PORT = 5000

# Cria o socket TCP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Permite reusar a porta imediatamente após fechar o servidor
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Vincula o servidor ao IP local e à porta 5000
server.bind((HOST, PORT))

# Define o limite de conexões em espera
server.listen(1)
print(f"[-] Servidor rodando em {HOST}:{PORT}... Pressione Ctrl+C para interromper.")

try:
    #  Bloqueia a execução até que um cliente se conecte e aceita a conexão do cliente
    conexao, cliente_ip = server.accept()
    print(f"[+] Conectado por: {cliente_ip}")

    # Loop para receber dados do cliente
    while True:
        # Recebe até 1024 bytes
        dados = conexao.recv(1024)
        if not dados:
            # Se o cliente der Ctrl+C no servidor, o socket recebe dados vazios e fecha
            print("[*] Conexão encerrada pelo cliente.")
            break

        # Mostra mensagem original
        print(f"[Recebido do cliente]: {repr(dados)}")

        # Decodifica os bytes da rede para string usando UTF-8
        mensagem_decodificada = dados.decode('utf-8')

        # .strip() remove o '\n' enviado pelo Enter do Netcat e espaços extras
        mensagem_limpa = mensagem_decodificada.strip()

        # Se a mensagem digitada (sem o \n) for 'sair', quebra o loop e fecha o servidor
        if mensagem_limpa.lower() == 'sair':
            print("[*] Comando 'sair' recebido. Finalizando servidor...")
            # Envia um aviso de despedida antes de fechar (opcional)
            conexao.sendall("Conexão encerrada pelo servidor.\n".encode('utf-8'))
            break

        # Converte para maiúsculas
        mensagem_maiuscula = mensagem_limpa.upper()

        print(f"[Mensagem limpa]: {mensagem_limpa} -> [Processada]: {mensagem_maiuscula}")

        # Codifica de volta para bytes em UTF-8 antes de enviar pelo socket
        # Devolve (ecoa) de volta o mesmo texto em maiúsculas (Eco Modificado)
        # Ecoa de volta com uma quebra de linha para o terminal do Netcat ficar organizado
        resposta = mensagem_maiuscula + "\n"
        conexao.sendall(resposta.encode('utf-8'))

    print("[-] Fechando conexão.")
    conexao.close()

# CASO 2: Ctrl+C pressionado no próprio SERVIDOR
except KeyboardInterrupt:
    print("\n[*] Ctrl+C detectado! Desligando o servidor com segurança...")

finally:
    # Garante que o socket principal do servidor seja fechado em qualquer situação
    server.close()
    print("[*] Porta liberada. Finalizado.")