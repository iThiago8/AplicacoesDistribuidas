<?php
declare(strict_types=1);
require __DIR__ . '/cliente-http.php';

$consulta = <<<'GRAPHQL'
mutation CriarPedido($pedido: PedidoInput!) {
    criarPedido(pedido: $pedido) { numero cliente status valorTotal }
}
GRAPHQL;
try {
    $dados = executarGraphQL($consulta, ['pedido' => [
        'numero' => $argv[1] ?? 'PED-1003',
        'cliente' => $argv[2] ?? 'Marina Alves',
        'status' => $argv[3] ?? 'Recebido',
        'valorTotal' => isset($argv[4]) ? filter_var($argv[4], FILTER_VALIDATE_FLOAT, FILTER_NULL_ON_FAILURE) : 215.75,
    ]]);
    if ($dados['criarPedido'] === null) {
        echo 'Pedido não criado. Verifique se esse número já está cadastrado.' . PHP_EOL;
    } else {
        echo 'Pedido criado:' . PHP_EOL;
        imprimirPedido($dados['criarPedido']);
    }
} catch (Throwable $erro) {
    fwrite(STDERR, 'Erro: ' . $erro->getMessage() . PHP_EOL);
    exit(1);
}
