# Atividade 02/11 — APIs

Implementações da atividade descrita no documento APIs.docx.

## V4 — YouTube com HTML, CSS e JavaScript

A pasta `v4` contém a versão sem bibliotecas externas e sem backend.

Recursos: seleção de Unoesc, Google for Developers e NASA; consulta por Fetch
com async/await; pesquisa local por título ou descrição; paginação com
`nextPageToken`; cards responsivos; carregamento e mensagens de erro; player
em `<dialog>` e interrupção da reprodução ao fechar (botão ou Escape).

### Executar

Abra `v4/index.html` com **Open with Live Server** no VS Code.
Como alternativa, na raiz do repositório:

```bash
python3 -m http.server 5500 --directory atividade-02-11-apis/v4
```

Acesse http://localhost:5500.

### Configurar a chave depois

1. Crie uma chave no Google Cloud e habilite a **YouTube Data API v3**.
2. Em `v4/assets/js/script.js`, preencha `const CHAVE_API = ""`.
3. Salve e recarregue a página.

Sem chave, a página exibe um aviso e não faz requisições ao YouTube.
Na v4, a chave fica visível no navegador: restrinja-a à YouTube Data API v3
e aos endereços HTTP usados no desenvolvimento. Não publique a chave no Git.
A v5 do roteiro moverá essa configuração para o backend.

### Conferir a atividade

Com a chave configurada, selecione um canal, filtre os vídeos, carregue outra
página e confira o player e seu fechamento. Troque de canal para conferir a
limpeza dos resultados. Faça uma pesquisa e capture a tela do navegador para
inserir no documento, conforme solicitado no enunciado.

## V5 — Frontend + FastAPI

O navegador consulta `GET /api/canal` e `GET /api/videos` no backend.
O FastAPI acessa o YouTube e retorna os dados dos vídeos e o token de
paginação. A pesquisa continua local, sem consumir novas consultas.

### Executar no Linux

Em um terminal, a partir da raiz do repositório:

```bash
cd atividade-02-11-apis/v5/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edite o `.env`, preenchendo `YOUTUBE_API_KEY` com sua chave. A chave fica
somente nesse arquivo, ignorado pelo Git. O `.env.example` pode ser publicado.
Se a chave usada na v4 tiver restrição de referenciador HTTP, configure uma
chave para uso no servidor: restrinja à YouTube Data API v3; a restrição por
referenciador de navegador não serve para as chamadas do FastAPI.

Inicie o backend no mesmo terminal:

```bash
uvicorn app:app --reload
```

Documentação interativa: http://localhost:8000/docs. Sem chave, o servidor
inicia, mas os endpoints de consulta retornam uma mensagem de configuração.
Reinicie o servidor após alterar o `.env`.

Em outro terminal, na raiz do repositório:

```bash
python3 -m http.server 5500 --directory atividade-02-11-apis/v5/frontend
```

Abra http://localhost:5500. Também é possível usar o Live Server na porta
5500. O CORS permite `localhost:5500` e `127.0.0.1:5500`.
Se a v4 ainda estiver servindo nessa porta, encerre seu servidor primeiro.

### Validar e entregar

Confira seleção de canal, pesquisa, carregamento de mais vídeos e modal.
Na aba Network do navegador, as consultas de dados devem ir para
`localhost:8000/api/...`, sem chave nos parâmetros ou respostas. As imagens
e o player continuam sendo carregados dos serviços do YouTube.
Faça uma pesquisa e insira o print no documento da atividade.

Testes do backend, a partir de `v5/backend`, com o ambiente virtual ativo:

```bash
python -m unittest discover -s tests -v
```

Os testes usam respostas simuladas para verificar contrato, paginação,
falhas, validação e ausência da chave nas respostas. Antes de um commit,
confira `git status --short` e `git diff --cached`: `.env` não deve aparecer,
e a chave não deve estar em nenhum arquivo preparado para publicação.

## SOAP — PHP e Java

`soap-pedidos-php` contém o contrato `pedido.wsdl`, o servidor, o cliente PHP
e o inicializador para Linux. `soap-pedidos-java` contém o cliente Maven/CXF
e uma cópia idêntica do contrato. O contrato usa SOAP 1.1, estilo RPC/literal.
Os pedidos ficam em memória; não é necessário banco de dados ou chave de API.

A porta padrão é **8002**, para evitar conflitos com as aplicações anteriores.

### Executar PHP no Linux

Requer PHP com as extensões `soap` e `dom`. Confira com `php -m`.
Para localizar a configuração do PHP, execute `php --ini`. Em instalações
que disponibilizam SOAP como extensão compartilhada, habilite `extension=soap`
no `php.ini` indicado. O inicializador informa se SOAP não estiver habilitado.

Terminal 1, na raiz do repositório:

```bash
cd atividade-02-11-apis/soap-pedidos-php
php iniciar-servidor.php
```

Terminal 2, na mesma pasta:

```bash
php cliente.php
php cliente.php PED-1002
php cliente.php PED-9999
```

O primeiro retorna Ana Souza, Em separação, R$ 159.90. O segundo retorna
Carlos Lima, Enviado, R$ 89.50. O terceiro exibe um `SoapFault` de pedido
inexistente e termina com código 1. O cliente imprime os envelopes XML de
requisição e resposta, inclusive nas falhas. Encerre o servidor com Ctrl+C.

Para outra porta, use `php iniciar-servidor.php 8003` e execute os clientes
com `SOAP_ENDPOINT=http://127.0.0.1:8003/servidor.php` antes do comando.
A opção de endereço do cliente substitui o endereço padrão do WSDL.

### Executar o cliente Java

Requer JDK 17 ou superior e Maven. Mantenha o servidor PHP aberto e, em outro
terminal, a partir da raiz do repositório:

```bash
cd atividade-02-11-apis/soap-pedidos-java
mvn compile exec:java
mvn compile exec:java -Dexec.args=PED-1002
mvn compile exec:java -Dexec.args=PED-9999
```

O Maven gera `Pedido`, `PedidoService`, `PedidoPortType` e auxiliares a partir
do WSDL em `target/generated-sources/cxf`. As classes geradas não precisam
ser escritas manualmente ou versionadas. O cliente consulta o mesmo servidor
PHP e trata falhas SOAP para o pedido inexistente (código de saída 1).
Também é possível importar o `pom.xml` no IntelliJ, executar `compile` no Maven
e iniciar `ClientePedido.main()` pela IDE.

Se alterar o contrato PHP, atualize também a cópia em
`soap-pedidos-java/src/main/resources/wsdl/pedido.wsdl` e rode `mvn clean compile`.

### Alternativa com Docker (sem PHP/JDK/Maven no sistema)

Na raiz do repositório, construa a imagem e mantenha o servidor aberto:

```bash
docker build -t atividade-apis-soap-php atividade-02-11-apis/soap-pedidos-php
docker run --rm --name atividade-apis-soap -p 127.0.0.1:8002:8002 atividade-apis-soap-php
```

Em outro terminal, execute o cliente PHP no mesmo contêiner:

```bash
docker exec atividade-apis-soap php cliente.php
docker exec atividade-apis-soap php cliente.php PED-9999
```

Para o cliente Java no Linux, na raiz do repositório:

```bash
docker run --rm --network host --user "$(id -u):$(id -g)" \
  -e MAVEN_CONFIG=/tmp/.m2 \
  -e MAVEN_OPTS=-Duser.home=/tmp \
  -v "$PWD/atividade-02-11-apis/soap-pedidos-java:/projeto" -w /projeto \
  maven:3.9-eclipse-temurin-17 \
  mvn -Dmaven.repo.local=/projeto/.m2 compile exec:java
```

Adicione `-Dexec.args=PED-9999` ao comando Maven para conferir o Fault no Java.
Os downloads iniciais precisam de internet. O cache `.m2` e `target` são
ignorados pelo Git. As duas linguagens devem retornar os mesmos dados para
o mesmo pedido, demonstrando a interoperabilidade por WSDL e XML/HTTP.
