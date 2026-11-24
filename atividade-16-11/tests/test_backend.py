import time
from concurrent.futures import ThreadPoolExecutor

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend_fastapi import IDLE_SECONDS, SECRET_KEY, create_app, hash_token
from models import Livro, LogAuditoria, RefreshToken, Sessao, Usuario

LIVRO = {"titulo": "Livro de teste", "autor": "Autora de teste", "ano_publicacao": 2020, "exemplares": 5}


def test_crud_filtros_resumo_e_auditoria(client, headers):
    assert client.get("/livros/resumo", headers=headers).json() == {"titulos": 3, "exemplares": 9, "autores": 2}
    response = client.post("/livros", headers=headers, json=LIVRO)
    assert response.status_code == 201
    livro = response.json()
    id_ = livro["id"]
    assert client.get(f"/livros/{id_}", headers=headers).json() == livro
    assert client.get("/livros", params={"titulo": "TESTE", "autor": "autora", "min_exemplares": 5}, headers=headers).json() == [livro]
    assert client.get("/livros", params={"titulo": "%"}, headers=headers).json() == []
    assert client.get("/livros", params={"min_exemplares": 100}, headers=headers).json() == []
    assert client.get("/livros/resumo", headers=headers).json() == {"titulos": 4, "exemplares": 14, "autores": 3}
    response = client.put(f"/livros/{id_}", headers=headers, json={**LIVRO, "titulo": "Atualizado", "exemplares": 0})
    assert response.status_code == 200
    assert response.json()["exemplares"] == 0
    assert client.delete(f"/livros/{id_}", headers=headers).status_code == 200
    assert client.get(f"/livros/{id_}", headers=headers).status_code == 404
    logs = client.get("/auditoria", headers=headers).json()
    eventos = {(log["operacao"], log["resultado"]) for log in logs if log["recurso_id"] == id_ and log["recurso"] == "livro"}
    assert {("CREATE", "sucesso"), ("UPDATE", "sucesso"), ("DELETE", "sucesso"), ("READ", "falha")} <= eventos
    assert [log["id"] for log in logs] == sorted([log["id"] for log in logs], reverse=True)


@pytest.mark.parametrize("campo,valor", [("titulo", "  "), ("autor", ""), ("titulo", "x" * 201),
                                        ("ano_publicacao", 0), ("ano_publicacao", 9999),
                                        ("exemplares", -1), ("exemplares", 1.5)])
def test_validacao_livros(client, headers, campo, valor):
    assert client.post("/livros", headers=headers, json={**LIVRO, campo: valor}).status_code == 422


def test_normalizacao_e_hash_usuario(client, app):
    dados = {"username": "  Leitor.TESTE  ", "senha": "segredo123"}
    response = client.post("/usuarios", json=dados)
    assert response.status_code == 201
    assert response.json()["username"] == "leitor.teste"
    assert "senha_hash" not in response.text
    assert "senha" not in response.json()
    assert client.post("/usuarios", json=dados).status_code == 409
    assert client.post("/usuarios", json={**dados, "role": "admin"}).status_code == 422
    assert client.post("/usuarios", json={"username": "  ", "senha": "123"}).status_code == 422
    with Session(app.state.engine) as db:
        usuario = db.exec(select(Usuario).where(Usuario.username == "leitor.teste")).one()
        assert usuario.role == "usuario"
        assert usuario.senha_hash.startswith("$argon2")
        assert usuario.senha_hash != dados["senha"]


def test_perfil_comum_pode_editar_mas_nao_excluir_ou_auditar(client, headers):
    client.post("/usuarios", json={"username": "leitor", "senha": "teste123"})
    token = client.post("/token", data={"username": "LEITOR", "password": "teste123"}).json()
    comum = {"Authorization": f"Bearer {token['access_token']}"}
    livro = client.post("/livros", headers=comum, json=LIVRO).json()
    assert client.get("/livros", headers=comum).status_code == 200
    assert client.put(f"/livros/{livro['id']}", headers=comum, json=LIVRO).status_code == 200
    assert client.delete(f"/livros/{livro['id']}", headers=comum).status_code == 403
    assert client.get("/auditoria", headers=comum).status_code == 403
    assert any(log["usuario"] == "leitor" and log["resultado"] == "negado" for log in client.get("/auditoria", headers=headers).json())


def test_scopes_limitados_preservados_apos_refresh(client):
    response = client.post("/token", data={"username": "admin", "password": "admin123", "scope": "livros:read"})
    token = response.json()
    renovado = client.post("/refresh", json={"refresh_token": token["refresh_token"]}).json()
    assert renovado["usuario"]["scopes"] == ["livros:read"]
    headers = {"Authorization": f"Bearer {renovado['access_token']}"}
    assert client.get("/livros", headers=headers).status_code == 200
    assert client.post("/livros", headers=headers, json=LIVRO).status_code == 403
    assert client.post("/token", data={"username": "admin", "password": "admin123", "scope": "inexistente"}).status_code == 400


def test_reducao_de_role_aplica_imediatamente(client, app, admin, headers):
    with Session(app.state.engine) as db:
        usuario = db.get(Usuario, admin["usuario"]["id"])
        usuario.role = "usuario"
        db.add(usuario)
        db.commit()
    assert client.get("/auditoria", headers=headers).status_code == 403
    renovado = client.post("/refresh", json={"refresh_token": admin["refresh_token"]}).json()
    assert "livros:delete" not in renovado["usuario"]["scopes"]


def test_rotacao_logout_revoga_access_e_preserva_outra_sessao(client, app, admin, headers):
    outra = client.post("/token", data={"username": "admin", "password": "admin123"}).json()
    response = client.post("/refresh", json={"refresh_token": admin["refresh_token"]})
    assert response.status_code == 200
    novo = response.json()
    assert novo["refresh_token"] != admin["refresh_token"]
    assert novo["usuario"]["sessao_id"] == admin["usuario"]["sessao_id"]
    assert client.post("/refresh", json={"refresh_token": admin["refresh_token"]}).status_code == 401
    with Session(app.state.engine) as db:
        hashes = [r.token_hash for r in db.exec(select(RefreshToken)).all()]
        assert hash_token(novo["refresh_token"]) in hashes
        assert novo["refresh_token"] not in hashes
    # O roteiro permite logout por um refresh antigo da mesma sessão.
    assert client.post("/logout", json={"refresh_token": admin["refresh_token"]}).status_code == 200
    assert client.get("/me", headers=headers).status_code == 401
    assert client.get("/me", headers={"Authorization": f"Bearer {novo['access_token']}"}).status_code == 401
    assert client.post("/refresh", json={"refresh_token": novo["refresh_token"]}).status_code == 401
    assert client.get("/me", headers={"Authorization": f"Bearer {outra['access_token']}"}).status_code == 200


@pytest.mark.parametrize("rota", ["/me", "/refresh"])
def test_inatividade_no_servidor(client, app, admin, headers, rota):
    with Session(app.state.engine) as db:
        sessao = db.get(Sessao, admin["usuario"]["sessao_id"])
        sessao.ultima_atividade = int(time.time()) - IDLE_SECONDS
        db.add(sessao)
        db.commit()
    response = client.post(rota, json={"refresh_token": admin["refresh_token"]}) if rota == "/refresh" else client.get(rota, headers=headers)
    assert response.status_code == 401
    assert "inatividade" in response.json()["detail"]
    with Session(app.state.engine) as db:
        assert db.get(Sessao, admin["usuario"]["sessao_id"]).encerrada
        assert db.exec(select(LogAuditoria).where(LogAuditoria.operacao == "SESSION_TIMEOUT")).first()


def test_refresh_expirado(client, app, admin, headers):
    with Session(app.state.engine) as db:
        registro = db.exec(select(RefreshToken)).one()
        registro.expira_em = int(time.time()) - 1
        db.add(registro)
        db.commit()
    assert client.post("/refresh", json={"refresh_token": admin["refresh_token"]}).status_code == 401
    assert client.get("/me", headers=headers).status_code == 401


def test_access_expirado_permite_renovar_sem_auditar_negacao(client, app, admin):
    payload = jwt.decode(admin["access_token"], SECRET_KEY, algorithms=["HS256"])
    payload["exp"] = int(time.time()) - 1
    expirado = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    response = client.get("/me", headers={"Authorization": f"Bearer {expirado}"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    with Session(app.state.engine) as db:
        assert not db.exec(select(LogAuditoria).where(LogAuditoria.resultado == "negado")).all()
    assert client.post("/refresh", json={"refresh_token": admin["refresh_token"]}).status_code == 200


def test_falhas_auditadas_e_limites(client, headers):
    assert client.get("/livros").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer adulterado"}).status_code == 401
    assert client.post("/token", data={"username": "admin", "password": "errada"}).status_code == 401
    assert client.post("/refresh", json={"refresh_token": "desconhecido"}).status_code == 401
    assert client.put("/livros/99999", headers=headers, json=LIVRO).status_code == 404
    assert client.delete("/livros/99999", headers=headers).status_code == 404
    for limite in (0, 501):
        assert client.get("/auditoria", params={"limite": limite}, headers=headers).status_code == 422
    assert len(client.get("/auditoria", params={"limite": 2}, headers=headers).json()) == 2


def test_rotacao_concorrente_consumida_uma_unica_vez(client, admin):
    def renovar(_):
        return client.post("/refresh", json={"refresh_token": admin["refresh_token"]}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(renovar, range(2))) == [200, 401]


def test_persistencia_e_seed_sem_recriar_livros(client, app, headers, tmp_path):
    for livro in client.get("/livros", headers=headers).json():
        client.delete(f"/livros/{livro['id']}", headers=headers)
    with TestClient(create_app(f"sqlite:///{tmp_path / 'teste.db'}")) as reiniciado:
        assert reiniciado.get("/livros", headers=headers).json() == []
        assert reiniciado.get("/livros/resumo", headers=headers).json() == {"titulos": 0, "exemplares": 0, "autores": 0}
        assert len(reiniciado.get("/auditoria", headers=headers).json()) >= 4


def test_operacao_e_log_revertidos_juntos(client, app, headers, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    original_commit = Session.commit

    def falhar_ao_gravar_livro(db):
        if any(isinstance(obj, LogAuditoria) and obj.recurso == "livro" for obj in db.new):
            raise SQLAlchemyError("Falha de persistência simulada")
        original_commit(db)

    monkeypatch.setattr(Session, "commit", falhar_ao_gravar_livro)
    with pytest.raises(SQLAlchemyError):
        client.post("/livros", headers=headers, json=LIVRO)
    with Session(app.state.engine) as db:
        assert not db.exec(select(Livro).where(Livro.titulo == LIVRO["titulo"])).all()
        assert not db.exec(select(LogAuditoria).where(LogAuditoria.recurso == "livro")).all()
