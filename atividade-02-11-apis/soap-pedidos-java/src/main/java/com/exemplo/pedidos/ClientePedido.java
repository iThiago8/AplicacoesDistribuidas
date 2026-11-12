package com.exemplo.pedidos;

import jakarta.xml.ws.BindingProvider;
import jakarta.xml.ws.WebServiceException;
import jakarta.xml.ws.soap.SOAPFaultException;
import org.apache.cxf.binding.soap.SoapFault;
import java.net.URL;

public class ClientePedido {
    public static void main(String[] args) {
        URL wsdl = ClientePedido.class.getResource("/wsdl/pedido.wsdl");
        if (wsdl == null) {
            throw new IllegalStateException("Não foi possível encontrar pedido.wsdl");
        }
        String numero = args.length > 0 ? args[0] : "PED-1001";
        String endereco = System.getenv("SOAP_ENDPOINT");
        if (endereco == null || endereco.isBlank()) {
            endereco = "http://127.0.0.1:8002/servidor.php";
        }
        PedidoPortType porta = new PedidoService(wsdl).getPedidoPort();
        ((BindingProvider) porta).getRequestContext()
            .put(BindingProvider.ENDPOINT_ADDRESS_PROPERTY, endereco);

        try {
            Pedido pedido = porta.consultarPedido(numero);
            System.out.println("Número: " + pedido.getNumero());
            System.out.println("Cliente: " + pedido.getCliente());
            System.out.println("Status: " + pedido.getStatus());
            System.out.println("Valor total: R$ " + pedido.getValorTotal().toPlainString());
        } catch (SOAPFaultException erro) {
            System.err.println("Falha SOAP: " + erro.getFault().getFaultString());
            System.err.println("Código SOAP: " + erro.getFault().getFaultCode());
            System.exit(1);
        } catch (SoapFault erro) {
            System.err.println("Falha SOAP: " + erro.getMessage());
            System.err.println("Código SOAP: " + erro.getFaultCode());
            System.exit(1);
        } catch (WebServiceException erro) {
            Throwable causa = erro;
            while (causa.getCause() != null) {
                causa = causa.getCause();
            }
            System.err.println("Falha na chamada SOAP: " + causa.getMessage());
            System.exit(1);
        }
    }
}
