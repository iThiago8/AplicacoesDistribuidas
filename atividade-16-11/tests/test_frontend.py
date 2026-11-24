import json
import time
from pathlib import Path

import jwt
import pytest
import requests
from streamlit.testing.v1 import AppTest

from api_client import APIClient, APIError, APIUnavailable, SessionExpired
from backend_fastapi import SECRET_KEY


@pytest.fixture
def bridge(client, monkeypatch):
    """Transporta chamadas reais do frontend à API isolada sem abrir portas."""
    calls = []

    def send(self, method, path, **kwargs):
        calls.append((method, path))
        result = client.request(method, path, **kwargs)
        response = requests.Response()
        response.status_code = result.status_code
        response._content = result.content
        return response

    monkeypatch.setattr(APIClient, "_send", send)
    return calls


def button(at, label):
    return next(btn for btn in at.button if btn.label == label)


def test_cliente_renova_uma_vez_e_repete_chamada(bridge):
    api = APIClient("http://teste")
    api.login("admin", "admin123")
    payload = jwt.decode(api.tokens["access_token"], SECRET_KEY, algorithms=["HS256"])
    payload["exp"] = int(time.time()) - 1
    api.tokens["access_token"] = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    anterior = api.tokens["refresh_token"]
    assert api.request("GET", "/me")["username"] == "admin"
    assert api.tokens["refresh_token"] != anterior
    assert bridge == [("POST", "/token"), ("GET", "/me"), ("POST", "/refresh"), ("GET", "/me")]


def test_cliente_falha_login_nao_renova(bridge):
    api = APIClient("http://teste")
    with pytest.raises(APIError, match="401"):
        api.login("admin", "senha_errada")
    assert not api.logged_in
    assert bridge == [("POST", "/token")]


def test_cliente_logout_expiracao_e_403(bridge):
    api = APIClient("http://teste")
    api.request("POST", "/usuarios", authenticated=False, json={"username": "leitor", "senha": "teste123"})
    api.login("leitor", "teste123")
    with pytest.raises(APIError, match="403"):
        api.request("GET", "/auditoria")
    assert api.logged_in
    assert ("POST", "/refresh") not in bridge
    api.request("POST", "/logout", authenticated=False, json={"refresh_token": api.tokens["refresh_token"]})
    with pytest.raises(SessionExpired):
        api.request("GET", "/me")
    assert not api.logged_in
    assert bridge.count(("POST", "/refresh")) == 1


def test_cliente_erro_rede_preserva_sessao_e_logout_nao_confirmado(monkeypatch, admin):
    api = APIClient("http://teste")
    api._store_tokens(admin)

    def falhar(*args, **kwargs):
        raise requests.ConnectionError("Servidor indisponível")

    monkeypatch.setattr(api.http, "request", falhar)
    with pytest.raises(APIUnavailable):
        api.request("GET", "/me")
    assert api.logged_in
    with pytest.raises(APIUnavailable):
        api.logout()
    assert api.logged_in


@pytest.mark.parametrize("body", ["não é JSON", json.dumps({"access_token": "incompleto"})])
def test_cliente_rejeita_respostas_login_invalidas(monkeypatch, body):
    api = APIClient("http://teste")
    response = requests.Response()
    response.status_code = 200
    response._content = body.encode()
    monkeypatch.setattr(api, "_send", lambda *args, **kwargs: response)
    with pytest.raises(APIError):
        api.login("admin", "admin123")
    assert not api.logged_in


def test_interface_admin_login_crud_e_logout(bridge, client, headers):
    arquivo = Path(__file__).resolve().parents[1] / "frontend_streamlit.py"
    at = AppTest.from_file(str(arquivo), default_timeout=15).run()
    assert not at.exception
    at.text_input(key="login_usuario").set_value("admin")
    at.text_input(key="login_senha").set_value("admin123")
    button(at, "Entrar").click().run()
    assert not at.exception
    assert [tab.label for tab in at.tabs] == ["Acervo", "Cadastrar livro", "Gerenciar livros", "Auditoria"]
    assert [metric.value for metric in at.metric] == ["3", "9", "2"]
    at.text_input(key="novo_titulo").set_value("Livro pela interface")
    at.text_input(key="novo_autor").set_value("Autora UI")
    at.number_input(key="novo_ano").set_value(2024)
    at.number_input(key="novo_exemplares").set_value(7)
    button(at, "Cadastrar livro").click().run()
    assert not at.exception
    livro = client.get("/livros", params={"titulo": "Livro pela interface"}, headers=headers).json()[0]
    id_ = livro["id"]
    at.selectbox[0].set_value(id_).run()
    at.number_input(key=f"editar_{id_}_exemplares").set_value(10)
    button(at, "Salvar alterações").click().run()
    assert not at.exception
    assert client.get(f"/livros/{id_}", headers=headers).json()["exemplares"] == 10
    # Exclusão exige confirmação explícita na interface.
    button(at, "Excluir livro").click().run()
    assert client.get(f"/livros/{id_}", headers=headers).status_code == 200
    at.checkbox[0].check()
    button(at, "Excluir livro").click().run()
    assert not at.exception
    assert client.get(f"/livros/{id_}", headers=headers).status_code == 404
    button(at, "Sair").click().run()
    assert not at.exception
    assert not at.tabs
    assert not at.session_state["api"].logged_in


def test_interface_cadastro_e_permissoes_comuns(bridge):
    arquivo = Path(__file__).resolve().parents[1] / "frontend_streamlit.py"
    at = AppTest.from_file(str(arquivo), default_timeout=15).run()
    # Os três inputs sem chave explícita são os campos do cadastro.
    campos = {campo.label: campo for campo in at.text_input}
    campos["Novo usuário"].set_value("novo_leitor")
    campos["Nova senha"].set_value("teste123")
    campos["Confirmar senha"].set_value("teste123")
    button(at, "Criar conta").click().run()
    assert not at.exception
    assert any("Conta criada" in msg.value for msg in at.success)
    at.text_input(key="login_usuario").set_value("novo_leitor")
    at.text_input(key="login_senha").set_value("teste123")
    button(at, "Entrar").click().run()
    assert not at.exception
    assert "Auditoria" not in [tab.label for tab in at.tabs]
    assert "Excluir livro" not in [btn.label for btn in at.button]
