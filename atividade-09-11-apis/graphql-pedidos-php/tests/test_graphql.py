"""Testes HTTP: iniciar um servidor com PEDIDOS_ARQUIVO temporário antes de executar."""

import json
import os
import unittest
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ENDPOINT = os.getenv("GRAPHQL_ENDPOINT", "http://127.0.0.1:8082/graphql")


def enviar(query, variables=None):
    request = Request(ENDPOINT, data=json.dumps({"query": query, "variables": variables or {}}).encode(),
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=10) as response:
        return json.load(response)


class GraphQLTest(unittest.TestCase):
    def test_campos_completos_e_resumidos(self):
        for fields in ("numero cliente status valorTotal", "numero status"):
            data = enviar('query { pedido(numeroPedido: "PED-1001") { ' + fields + ' } }')
            self.assertNotIn("errors", data)
            self.assertEqual(set(data["data"]["pedido"]), set(fields.split()))
            self.assertEqual(data["data"]["pedido"]["numero"], "PED-1001")

    def test_segundo_pedido(self):
        data = enviar('{ pedido(numeroPedido: "PED-1002") { cliente valorTotal } }')
        self.assertEqual(data["data"]["pedido"], {"cliente": "Carlos Lima", "valorTotal": 89.5})

    def test_inexistente_retorna_null(self):
        data = enviar('{ pedido(numeroPedido: "PED-9999") { numero } }')
        self.assertEqual(data, {"data": {"pedido": None}})

    def test_criacao_duplicidade_alteracao_e_persistencia(self):
        numero = "TEST-" + uuid.uuid4().hex
        pedido = {"numero": numero, "cliente": "Teste integração", "status": "Recebido", "valorTotal": 215.75}
        query = 'mutation($p: PedidoInput!) { criarPedido(pedido: $p) { numero cliente status valorTotal } }'
        self.assertEqual(enviar(query, {"p": pedido})["data"]["criarPedido"], pedido)
        self.assertIsNone(enviar(query, {"p": pedido})["data"]["criarPedido"])
        mutation = 'mutation($n: String!) { atualizarStatusPedido(numeroPedido: $n, novoStatus: "Enviado") { status } }'
        self.assertEqual(enviar(mutation, {"n": numero})["data"]["atualizarStatusPedido"], {"status": "Enviado"})
        # Outra requisição precisa recarregar a alteração do arquivo.
        consulta = 'query($n: String!) { pedido(numeroPedido: $n) { status cliente } }'
        self.assertEqual(enviar(consulta, {"n": numero})["data"]["pedido"],
                         {"status": "Enviado", "cliente": "Teste integração"})

    def test_alterar_inexistente(self):
        data = enviar('mutation { atualizarStatusPedido(numeroPedido: "PED-9999", novoStatus: "Enviado") { numero } }')
        self.assertIsNone(data["data"]["atualizarStatusPedido"])

    def test_campo_invalido_e_tipo_incorreto(self):
        for query in ('{ pedido(numeroPedido: "PED-1001") { senha } }',
                      '{ pedido(numeroPedido: 123) { numero } }'):
            data = enviar(query)
            self.assertIn("errors", data)
            self.assertNotIn("data", data)

    def test_json_invalido(self):
        request = Request(ENDPOINT, data=b"{", headers={"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=10)
        with caught.exception as response:
            self.assertEqual(response.code, 400)
            self.assertIn("errors", json.load(response))

    def test_metodo_e_rota(self):
        for url, status in ((ENDPOINT, 405), (ENDPOINT.removesuffix("/graphql") + "/outra-rota", 404)):
            with self.assertRaises(HTTPError) as caught:
                urlopen(url, timeout=10)
            with caught.exception as response:
                self.assertEqual(response.code, status)


if __name__ == "__main__":
    unittest.main()
