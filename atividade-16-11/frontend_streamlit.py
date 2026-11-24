"""Interface da biblioteca. Toda operação de dados passa pela API REST."""

import os
import time
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from api_client import APIClient, APIError, SessionExpired

load_dotenv(Path(__file__).resolve().parent / ".env")
st.set_page_config(page_title="Biblioteca | Acervo", page_icon="📚", layout="wide")

if "api" not in st.session_state:
    st.session_state.api = APIClient(os.getenv("API_URL", "http://127.0.0.1:8000"))
api = st.session_state.api


def chamar(method, path, **kwargs):
    try:
        return api.request(method, path, **kwargs)
    except SessionExpired as exc:
        st.session_state.aviso = str(exc)
        st.rerun()
    except APIError as exc:
        st.error(str(exc))
        return None


def sucesso(texto):
    st.session_state.sucesso = texto
    st.rerun()


def campos_livro(prefixo, livro=None):
    livro = livro or {"titulo": "", "autor": "", "ano_publicacao": datetime.now().year, "exemplares": 1}
    titulo = st.text_input("Título", value=livro["titulo"], max_chars=200, key=f"{prefixo}_titulo")
    autor = st.text_input("Autor", value=livro["autor"], max_chars=150, key=f"{prefixo}_autor")
    col1, col2 = st.columns(2)
    ano = col1.number_input("Ano de publicação", min_value=1, max_value=datetime.now().year + 1,
                            value=livro["ano_publicacao"], step=1, key=f"{prefixo}_ano")
    exemplares = col2.number_input("Exemplares no acervo", min_value=0, max_value=100000,
                                   value=livro["exemplares"], step=1, key=f"{prefixo}_exemplares")
    return {"titulo": titulo, "autor": autor, "ano_publicacao": ano, "exemplares": exemplares}


st.title("📚 Biblioteca")
st.caption("Catálogo do acervo · Aplicações Distribuídas · Versão 9")
if aviso := st.session_state.pop("aviso", None):
    st.warning(aviso)
if mensagem := st.session_state.pop("sucesso", None):
    st.success(mensagem)

if not api.logged_in:
    st.write("Entre para consultar e organizar os livros da biblioteca.")
    entrar, cadastrar = st.columns(2)
    with entrar:
        st.subheader("Entrar")
        with st.form("login"):
            username = st.text_input("Usuário", key="login_usuario")
            senha = st.text_input("Senha", type="password", key="login_senha")
            if st.form_submit_button("Entrar", type="primary"):
                try:
                    api.login(username, senha)
                    st.rerun()
                except APIError as exc:
                    st.error(str(exc))
        st.caption("Demonstração local: admin / admin123")
    with cadastrar:
        st.subheader("Criar conta")
        with st.form("cadastro_usuario", clear_on_submit=True):
            username = st.text_input("Novo usuário", max_chars=50)
            senha = st.text_input("Nova senha", type="password", max_chars=128)
            confirmar = st.text_input("Confirmar senha", type="password", max_chars=128)
            st.caption("Usuário: 3–50 letras minúsculas, números, ponto, hífen ou sublinhado. Senha: 6–128 caracteres.")
            if st.form_submit_button("Criar conta"):
                if senha != confirmar:
                    st.error("As senhas precisam ser iguais.")
                elif chamar("POST", "/usuarios", authenticated=False, json={"username": username, "senha": senha}) is not None:
                    st.success("Conta criada. Entre com seu usuário e senha.")
    st.stop()

# Apenas interações que reexecutam o painel consultam /me. O relógio abaixo
# é um fragmento independente e não mantém a sessão viva com polling.
perfil = chamar("GET", "/me")
if perfil is None:
    st.stop()
api.usuario = perfil
scopes = set(perfil["scopes"])


@st.fragment(run_every="1s")
def contador_sessao():
    restante = api.idle_remaining
    if restante <= 0:
        try:
            api.logout()
        except APIError:
            api.clear()
        st.session_state.aviso = "Limite local de inatividade atingido. Entre novamente; a API também verifica a inatividade."
        st.rerun()
    st.caption(f"Inatividade: {restante // 60:02d}:{restante % 60:02d}")
    access = max(0, int(api.access_expires_at - time.time()))
    refresh = max(0, int(api.refresh_expires_at - time.time()))
    st.caption(f"Access token: {access // 60:02d}:{access % 60:02d} · Refresh: {refresh // 3600}h {(refresh % 3600) // 60}min")
    st.caption("Contadores estimados. A API valida os prazos e renova o acesso quando necessário.")


with st.sidebar:
    st.subheader(perfil["username"])
    st.write("Administrador" if perfil["role"] == "admin" else "Usuário")
    contador_sessao()
    with st.expander("Permissões"):
        for scope in sorted(scopes):
            st.text(scope)
    if st.button("Sair", use_container_width=True):
        try:
            api.logout()
            sucesso("Sessão encerrada.")
        except APIError as exc:
            st.error(str(exc))

abas = ["Acervo"]
if "livros:create" in scopes:
    abas.append("Cadastrar livro")
if {"livros:update", "livros:delete"} & scopes:
    abas.append("Gerenciar livros")
if "auditoria:read" in scopes:
    abas.append("Auditoria")
paineis = dict(zip(abas, st.tabs(abas)))

with paineis["Acervo"]:
    resumo = chamar("GET", "/livros/resumo")
    if resumo:
        cols = st.columns(3)
        for col, (rotulo, chave) in zip(cols, [("Títulos", "titulos"), ("Exemplares", "exemplares"), ("Autores", "autores")]):
            col.metric(rotulo, resumo[chave])
    st.subheader("Consultar acervo")
    with st.form("busca"):
        cols = st.columns(3)
        titulo = cols[0].text_input("Parte do título")
        autor = cols[1].text_input("Parte do autor")
        minimo = cols[2].number_input("Mínimo de exemplares", min_value=0, step=1)
        st.form_submit_button("Buscar / atualizar")
    livros = chamar("GET", "/livros", params={"titulo": titulo, "autor": autor, "min_exemplares": minimo})
    if livros:
        st.dataframe(livros, hide_index=True, use_container_width=True,
                     column_config={"id": "ID", "titulo": "Título", "autor": "Autor",
                                    "ano_publicacao": st.column_config.NumberColumn("Publicação", format="%d"),
                                    "exemplares": "Exemplares"})
        st.caption(f"{len(livros)} título(s) encontrado(s). Os indicadores representam todo o acervo.")
    elif livros is not None:
        st.info("Nenhum livro encontrado.")

if "Cadastrar livro" in paineis:
    with paineis["Cadastrar livro"]:
        st.subheader("Novo livro")
        with st.form("novo_livro", clear_on_submit=True):
            dados = campos_livro("novo")
            if (st.form_submit_button("Cadastrar livro", type="primary")
                    and chamar("POST", "/livros", json=dados) is not None):
                sucesso("Livro cadastrado.")

if "Gerenciar livros" in paineis:
    with paineis["Gerenciar livros"]:
        st.subheader("Editar ou excluir")
        acervo = chamar("GET", "/livros")
        if acervo:
            por_id = {livro["id"]: livro for livro in acervo}
            selecionado = st.selectbox("Selecione o livro", list(por_id),
                                       format_func=lambda id_: f"{id_} · {por_id[id_]['titulo']} — {por_id[id_]['autor']}")
            livro = por_id[selecionado]
            if "livros:update" in scopes:
                with st.form(f"editar_{selecionado}"):
                    dados = campos_livro(f"editar_{selecionado}", livro)
                    if (st.form_submit_button("Salvar alterações", type="primary")
                            and chamar("PUT", f"/livros/{selecionado}", json=dados) is not None):
                        sucesso("Livro atualizado.")
            if "livros:delete" in scopes:
                with st.form(f"excluir_{selecionado}"):
                    confirmar_exclusao = st.checkbox(f"Confirmo a exclusão de “{livro['titulo']}”.")
                    if st.form_submit_button("Excluir livro"):
                        if not confirmar_exclusao:
                            st.warning("Marque a confirmação para excluir o livro selecionado.")
                        elif chamar("DELETE", f"/livros/{selecionado}") is not None:
                            sucesso("Livro excluído.")
        elif acervo is not None:
            st.info("Cadastre um livro para gerenciar o acervo.")

if "Auditoria" in paineis:
    with paineis["Auditoria"]:
        st.subheader("Histórico de operações")
        with st.form("filtro_auditoria"):
            limite = st.number_input("Quantidade de registros recentes", min_value=1, max_value=500, value=100)
            st.form_submit_button("Atualizar auditoria")
        logs = chamar("GET", "/auditoria", params={"limite": limite})
        if logs:
            for log in logs:
                data = datetime.fromisoformat(log["data_hora"])
                log["data_hora"] = data.replace(tzinfo=UTC).strftime("%d/%m/%Y %H:%M:%S UTC")
            st.dataframe(logs, hide_index=True, use_container_width=True,
                         column_config={"id": "ID", "usuario": "Usuário", "operacao": "Operação",
                                        "recurso": "Recurso", "recurso_id": "ID do recurso", "data_hora": "Data e hora",
                                        "resultado": "Resultado", "detalhes": "Detalhes"})
        elif logs is not None:
            st.info("Nenhum evento registrado.")
