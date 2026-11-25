package com.exemplo.pedidos.grpc;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import java.util.concurrent.TimeUnit;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.*;

public class ServicoPedidosTest {
    private Server servidor;
    private ManagedChannel canal;
    private PedidoServiceGrpc.PedidoServiceBlockingStub cliente;

    @Before
    public void iniciar() throws Exception {
        // Porta efêmera para exercitar transporte e serialização sem conflito com o exemplo.
        servidor = ServerBuilder.forPort(0).addService(new ServidorPedido.ServicoPedidos()).build().start();
        canal = ManagedChannelBuilder.forAddress("127.0.0.1", servidor.getPort()).usePlaintext().build();
        cliente = PedidoServiceGrpc.newBlockingStub(canal).withDeadlineAfter(5, TimeUnit.SECONDS);
    }

    @After
    public void encerrar() throws Exception {
        if (canal != null) {
            canal.shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
        }
        if (servidor != null) {
            servidor.shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
        }
    }

    @Test
    public void consultaPrimeiroPedido() {
        Pedido pedido = consultar("PED-1001");
        assertEquals("PED-1001", pedido.getNumero());
        assertEquals("Ana Souza", pedido.getCliente());
        assertEquals("Em separação", pedido.getStatus());
        assertEquals(159.90, pedido.getValorTotal(), 0.001);
    }

    @Test
    public void consultaSegundoPedido() {
        Pedido pedido = consultar("PED-1002");
        assertEquals("Carlos Lima", pedido.getCliente());
        assertEquals("Enviado", pedido.getStatus());
        assertEquals(89.50, pedido.getValorTotal(), 0.001);
    }

    @Test
    public void pedidoInexistenteRetornaNotFound() {
        StatusRuntimeException erro = assertThrows(StatusRuntimeException.class, () -> consultar("PED-9999"));
        assertEquals(Status.Code.NOT_FOUND, erro.getStatus().getCode());
        assertEquals("Pedido PED-9999 não encontrado.", erro.getStatus().getDescription());
    }

    private Pedido consultar(String numero) {
        return cliente.consultarPedido(ConsultarPedidoRequest.newBuilder().setNumeroPedido(numero).build());
    }
}
