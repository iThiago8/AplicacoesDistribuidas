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

As etapas v5, SOAP PHP e SOAP Java ainda não foram implementadas.
