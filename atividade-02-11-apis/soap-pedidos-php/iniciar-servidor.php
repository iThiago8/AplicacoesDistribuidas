<?php
// stream_socket_server funciona no Linux sem SO_EXCLUSIVEADDRUSE (Windows).
if (!extension_loaded('soap')) {
    fwrite(STDERR, "Habilite a extensão soap no PHP.\n");
    exit(1);
}
$porta = filter_var($argv[1] ?? '8002', FILTER_VALIDATE_INT,
    ['options' => ['min_range' => 1, 'max_range' => 65535]]);
if ($porta === false) {
    fwrite(STDERR, "Informe uma porta válida entre 1 e 65535.\n");
    exit(1);
}
$endereco = "127.0.0.1:{$porta}";
$socket = @stream_socket_server("tcp://{$endereco}", $codigo, $erro);
if ($socket === false) {
    fwrite(STDERR, "Porta {$porta} ocupada ou indisponível: {$erro}\n");
    exit(1);
}
fclose($socket);
echo "Iniciando SOAP em http://{$endereco}/servidor.php\n";
passthru(escapeshellarg(PHP_BINARY) . ' -S ' . escapeshellarg($endereco)
    . ' -t ' . escapeshellarg(__DIR__), $codigoSaida);
exit($codigoSaida);
