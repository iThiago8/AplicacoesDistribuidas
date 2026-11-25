<?php
if (!extension_loaded('soap') || !extension_loaded('dom')) {
    fwrite(STDERR, "Habilite as extensões soap e dom no PHP.\n");
    exit(1);
}

function formatarXml(?string $xml): string
{
    if (!$xml) {
        return '(XML não disponível)' . PHP_EOL;
    }
    $documento = new DOMDocument('1.0', 'UTF-8');
    $documento->preserveWhiteSpace = false;
    $documento->formatOutput = true;
    if (!$documento->loadXML($xml, LIBXML_NONET)) {
        return $xml;
    }
    return $documento->saveXML();
}

$numero = $argv[1] ?? 'PED-1001';
$endereco = getenv('SOAP_ENDPOINT') ?: 'http://127.0.0.1:8002/servidor.php';
$cliente = new SoapClient(__DIR__ . '/pedido.wsdl', [
    'location' => $endereco,
    'trace' => true,
    'exceptions' => true,
    'connection_timeout' => 10,
    'cache_wsdl' => WSDL_CACHE_NONE,
]);
$codigoSaida = 0;
try {
    $pedido = $cliente->__soapCall('consultarPedido', [$numero]);
    echo "Número: {$pedido->numero}" . PHP_EOL;
    echo "Cliente: {$pedido->cliente}" . PHP_EOL;
    echo "Status: {$pedido->status}" . PHP_EOL;
    echo "Valor total: R$ {$pedido->valorTotal}" . PHP_EOL;
} catch (SoapFault $erro) {
    echo "Falha SOAP: {$erro->faultstring}" . PHP_EOL;
    echo "Código SOAP: {$erro->faultcode}" . PHP_EOL;
    $codigoSaida = 1;
} finally {
    echo PHP_EOL . "--- Requisição SOAP enviada ---" . PHP_EOL;
    echo formatarXml($cliente->__getLastRequest());
    echo PHP_EOL . "--- Resposta SOAP recebida ---" . PHP_EOL;
    echo formatarXml($cliente->__getLastResponse());
}
exit($codigoSaida);
