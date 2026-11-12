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

As etapas SOAP PHP e SOAP Java ainda não foram implementadas.
