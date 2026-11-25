package com.exemplo.pedidos.graphql;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

public class ClienteGraphQL {
    private static final Set<String> CAMPOS_PERMITIDOS = Set.of("numero", "cliente", "status", "valorTotal");
    private static final HttpClient CLIENTE_HTTP = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10)).build();

    public static void main(String[] args) throws IOException, InterruptedException {
        String numero = args.length > 0 ? args[0] : "PED-1001";
        for (Consulta consulta : List.of(
                new Consulta("Consulta completa", List.of("numero", "cliente", "status", "valorTotal")),
                new Consulta("Consulta resumida", List.of("numero", "status")))) {
            System.out.println("\n=== " + consulta.descricao() + " ===");
            HttpResponse<String> resposta = consultarPedido(numero, consulta.campos());
            System.out.println("Status HTTP: " + resposta.statusCode());
            System.out.println("Resposta JSON recebida:");
            System.out.println(resposta.body());
            if (resposta.statusCode() / 100 != 2) {
                throw new IOException("Servidor GraphQL retornou HTTP " + resposta.statusCode());
            }
        }
    }

    private static HttpResponse<String> consultarPedido(String numero, List<String> campos)
            throws IOException, InterruptedException {
        var unicos = new LinkedHashSet<>(campos);
        if (unicos.isEmpty() || !CAMPOS_PERMITIDOS.containsAll(unicos)) {
            throw new IllegalArgumentException("Informe campos válidos para a consulta.");
        }
        String consulta = """
                query ConsultarPedido($numeroPedido: String!) {
                    pedido(numeroPedido: $numeroPedido) { %s }
                }
                """.formatted(String.join(" ", unicos));
        String corpo = """
                {"query":"%s","variables":{"numeroPedido":"%s"}}
                """.formatted(escaparJson(consulta), escaparJson(numero));
        String endpoint = System.getenv().getOrDefault("GRAPHQL_ENDPOINT", "http://127.0.0.1:8082/graphql");
        HttpRequest requisicao = HttpRequest.newBuilder(URI.create(endpoint))
                .timeout(Duration.ofSeconds(10))
                .header("Content-Type", "application/json; charset=UTF-8")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(corpo, StandardCharsets.UTF_8)).build();
        return CLIENTE_HTTP.send(requisicao, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
    }

    private static String escaparJson(String texto) {
        StringBuilder resultado = new StringBuilder();
        for (char caractere : texto.toCharArray()) {
            switch (caractere) {
                case '"' -> resultado.append("\\\"");
                case '\\' -> resultado.append("\\\\");
                case '\b' -> resultado.append("\\b");
                case '\f' -> resultado.append("\\f");
                case '\n' -> resultado.append("\\n");
                case '\r' -> resultado.append("\\r");
                case '\t' -> resultado.append("\\t");
                default -> {
                    if (caractere < 0x20) {
                        resultado.append(String.format("\\u%04x", (int) caractere));
                    } else {
                        resultado.append(caractere);
                    }
                }
            }
        }
        return resultado.toString();
    }

    private record Consulta(String descricao, List<String> campos) { }
}
