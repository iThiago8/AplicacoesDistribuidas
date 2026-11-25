<?php
declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use GraphQL\GraphQL;
use GraphQL\Type\Definition\InputObjectType;
use GraphQL\Type\Definition\ObjectType;
use GraphQL\Type\Definition\Type;
use GraphQL\Type\Schema;

if (parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) !== '/graphql') {
    http_response_code(404);
    exit('Endpoint GraphQL não encontrado.');
}
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    header('Allow: POST');
    exit('Use POST para enviar uma operação GraphQL.');
}

header('Content-Type: application/json; charset=utf-8');
$arquivo = null;
try {
    $entrada = json_decode(file_get_contents('php://input'), true, 512, JSON_THROW_ON_ERROR);
    if (!is_array($entrada) || !is_string($entrada['query'] ?? null)
        || (isset($entrada['variables']) && !is_array($entrada['variables']))
        || (isset($entrada['operationName']) && !is_string($entrada['operationName']))) {
        http_response_code(400);
        $saida = ['errors' => [['message' => 'Envie query como texto e variables como objeto JSON.']]];
    } else {
        // Bloqueia leitura e escrita juntas para evitar perder uma alteração concorrente.
        $caminho = getenv('PEDIDOS_ARQUIVO') ?: __DIR__ . '/pedidos.json';
        $arquivo = fopen($caminho, 'c+');
        if ($arquivo === false || !flock($arquivo, LOCK_EX)) {
            throw new RuntimeException('Não foi possível abrir o arquivo de pedidos.');
        }
        $conteudo = stream_get_contents($arquivo);
        if ($conteudo === false) {
            throw new RuntimeException('Não foi possível ler os pedidos.');
        }
        $pedidos = $conteudo === '' ? [
            'PED-1001' => ['numero' => 'PED-1001', 'cliente' => 'Ana Souza',
                'status' => 'Em separação', 'valorTotal' => 159.90],
            'PED-1002' => ['numero' => 'PED-1002', 'cliente' => 'Carlos Lima',
                'status' => 'Enviado', 'valorTotal' => 89.50],
        ] : json_decode($conteudo, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($pedidos)) {
            throw new RuntimeException('O arquivo de pedidos possui formato inválido.');
        }

        $salvar = static function () use ($arquivo, &$pedidos): void {
            $json = json_encode($pedidos, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR) . PHP_EOL;
            rewind($arquivo);
            if (!ftruncate($arquivo, 0) || fwrite($arquivo, $json) !== strlen($json) || !fflush($arquivo)) {
                throw new RuntimeException('Não foi possível salvar os pedidos.');
            }
        };
        if ($conteudo === '') {
            $salvar();
        }

        $campos = static fn(): array => [
            'numero' => Type::nonNull(Type::string()),
            'cliente' => Type::nonNull(Type::string()),
            'status' => Type::nonNull(Type::string()),
            'valorTotal' => Type::nonNull(Type::float()),
        ];
        $pedidoType = new ObjectType(['name' => 'Pedido', 'fields' => $campos()]);
        $pedidoInputType = new InputObjectType(['name' => 'PedidoInput', 'fields' => $campos()]);
        $queryType = new ObjectType([
            'name' => 'Query',
            'fields' => [
                'pedido' => [
                    'type' => $pedidoType,
                    'args' => ['numeroPedido' => Type::nonNull(Type::string())],
                    'resolve' => static function ($raiz, array $args) use (&$pedidos) {
                        return $pedidos[$args['numeroPedido']] ?? null;
                    },
                ],
            ],
        ]);
        $mutationType = new ObjectType([
            'name' => 'Mutation',
            'fields' => [
                'atualizarStatusPedido' => [
                    'type' => $pedidoType,
                    'args' => [
                        'numeroPedido' => Type::nonNull(Type::string()),
                        'novoStatus' => Type::nonNull(Type::string()),
                    ],
                    'resolve' => static function ($raiz, array $args) use (&$pedidos, $salvar) {
                        $numero = $args['numeroPedido'];
                        if (!isset($pedidos[$numero])) {
                            return null;
                        }
                        $pedidos[$numero]['status'] = $args['novoStatus'];
                        $salvar();
                        return $pedidos[$numero];
                    },
                ],
                'criarPedido' => [
                    'type' => $pedidoType,
                    'args' => ['pedido' => Type::nonNull($pedidoInputType)],
                    'resolve' => static function ($raiz, array $args) use (&$pedidos, $salvar) {
                        $novo = $args['pedido'];
                        if (isset($pedidos[$novo['numero']])) {
                            return null;
                        }
                        $pedidos[$novo['numero']] = $novo;
                        $salvar();
                        return $novo;
                    },
                ],
            ],
        ]);
        $schema = new Schema(['query' => $queryType, 'mutation' => $mutationType]);
        $saida = GraphQL::executeQuery(
            $schema, $entrada['query'], null, null,
            $entrada['variables'] ?? null, $entrada['operationName'] ?? null
        )->toArray();
    }
} catch (JsonException $erro) {
    http_response_code(400);
    $saida = ['errors' => [['message' => 'JSON inválido no corpo ou no arquivo de pedidos.']]];
} catch (Throwable $erro) {
    http_response_code(500);
    error_log($erro->getMessage());
    $saida = ['errors' => [['message' => 'Não foi possível processar a operação GraphQL.']]];
} finally {
    if (is_resource($arquivo)) {
        flock($arquivo, LOCK_UN);
        fclose($arquivo);
    }
}
echo json_encode($saida, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
