<?php
declare(strict_types=1);

function executarGraphQL(string $consulta, array $variaveis): array
{
    $endpoint = getenv('GRAPHQL_ENDPOINT') ?: 'http://127.0.0.1:8082/graphql';
    $contexto = stream_context_create(['http' => [
        'method' => 'POST',
        'header' => "Content-Type: application/json\r\nAccept: application/json\r\n",
        'content' => json_encode(['query' => $consulta, 'variables' => $variaveis], JSON_THROW_ON_ERROR),
        'timeout' => 10,
        'ignore_errors' => true,
    ]]);
    $json = @file_get_contents($endpoint, false, $contexto);
    if ($json === false) {
        throw new RuntimeException('Não foi possível acessar o servidor GraphQL.');
    }
    $resposta = json_decode($json, true, 512, JSON_THROW_ON_ERROR);
    if (!is_array($resposta)) {
        throw new RuntimeException('O servidor retornou uma resposta inesperada.');
    }
    if (isset($resposta['errors'])) {
        throw new RuntimeException(implode(PHP_EOL, array_map(
            static fn(array $erro): string => $erro['message'] ?? 'Erro GraphQL.',
            $resposta['errors']
        )));
    }
    if (!preg_match('/^HTTP\/\S+ 2\d\d\b/', $http_response_header[0] ?? '')
        || !isset($resposta['data']) || !is_array($resposta['data'])) {
        throw new RuntimeException('Resposta HTTP ou dados GraphQL inválidos.');
    }
    return $resposta['data'];
}

function imprimirPedido(?array $pedido): void
{
    echo json_encode($pedido, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR) . PHP_EOL;
}
