"""Cliente HTTP do frontend; não acessa o banco nem interpreta senhas/tokens."""

import time

import requests


class APIError(Exception):
    pass


class APIUnavailable(APIError):
    pass


class SessionExpired(APIError):
    pass


class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.http = requests.Session()
        self.clear()

    def clear(self):
        self.tokens = None
        self.usuario = None
        self.last_activity = 0
        self.access_expires_at = 0
        self.refresh_expires_at = 0

    @property
    def logged_in(self):
        return self.tokens is not None

    @property
    def idle_remaining(self):
        if not self.tokens:
            return 0
        return max(0, int(self.last_activity + self.tokens["session_idle_seconds"] - time.time()))

    def _send(self, method, path, **kwargs):
        try:
            return self.http.request(method, f"{self.base_url}{path}", timeout=(3, 10), **kwargs)
        except requests.RequestException as exc:
            raise APIUnavailable("Não foi possível comunicar com a API. Confira se o backend está em execução.") from exc

    @staticmethod
    def _decode(response):
        try:
            data = response.json()
        except ValueError as exc:
            raise APIError("A API retornou uma resposta inválida.") from exc
        if not response.ok:
            detail = data.get("detail", "Falha na requisição") if isinstance(data, dict) else str(data)
            if isinstance(detail, list):
                detail = "; ".join(f"{'.'.join(map(str, item.get('loc', [])[1:]))}: {item.get('msg', '')}" for item in detail)
            raise APIError(f"HTTP {response.status_code}: {detail}")
        return data

    def _store_tokens(self, data):
        strings = ("access_token", "refresh_token")
        durations = ("expires_in", "refresh_expires_in", "session_idle_seconds")
        if (not isinstance(data, dict)
                or not all(isinstance(data.get(k), str) and data[k] for k in strings)
                or not all(type(data.get(k)) is int and data[k] > 0 for k in durations)
                or not isinstance(data.get("usuario"), dict)
                or not isinstance(data["usuario"].get("scopes"), list)):
            raise APIError("A API retornou dados de login incompletos.")
        self.tokens = data
        self.usuario = data["usuario"]
        self.last_activity = time.time()
        self.access_expires_at = self.last_activity + data["expires_in"]
        self.refresh_expires_at = self.last_activity + data["refresh_expires_in"]

    def login(self, username, password):
        response = self._send("POST", "/token", data={"username": username, "password": password})
        self._store_tokens(self._decode(response))

    def request(self, method, path, authenticated=True, **kwargs):
        headers = dict(kwargs.pop("headers", {}))
        if authenticated:
            if not self.logged_in:
                raise SessionExpired("Entre na sua conta para continuar.")
            headers["Authorization"] = f"Bearer {self.tokens['access_token']}"
        response = self._send(method, path, headers=headers, **kwargs)
        if authenticated and response.status_code == 401:
            # Apenas uma renovação e uma repetição; erros de rede preservam a sessão.
            refresh = self._send("POST", "/refresh", json={"refresh_token": self.tokens["refresh_token"]})
            if refresh.status_code == 401:
                self.clear()
                raise SessionExpired("A sessão foi encerrada ou expirou. Entre novamente.")
            self._store_tokens(self._decode(refresh))
            headers["Authorization"] = f"Bearer {self.tokens['access_token']}"
            response = self._send(method, path, headers=headers, **kwargs)
            if response.status_code == 401:
                self.clear()
                raise SessionExpired("A sessão foi recusada. Entre novamente.")
        data = self._decode(response)
        if authenticated:
            self.last_activity = time.time()
        return data

    def logout(self):
        if self.tokens:
            self.request("POST", "/logout", authenticated=False,
                         json={"refresh_token": self.tokens["refresh_token"]})
        self.clear()
