package calculadora.cliente;

import calculadora.comum.Calculadora; // <- Importa a interface
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

public class Cliente {
    public static void main(String[] args) {
        try {
            String ipServidor = (args.length > 0) ? args[0] : "localhost";
            System.out.println("Conectando ao calculadora.servidor em: " + ipServidor);

            Registry registry = LocateRegistry.getRegistry(ipServidor, 1099);
            Calculadora calc = (Calculadora) registry.lookup("ServicoCalculadora");

            System.out.println("15 + 25 = " + calc.somar(15, 25));
            System.out.println("15 - 25 = " + calc.subtrair(15, 25));
            System.out.println("15 * 25 = " + calc.multiplicar(15, 25));
            System.out.println("15 / 25 = " + calc.dividir(15, 25));

            try {
                System.out.println("15 / 0 = " + calc.dividir(15, 0));
            } catch (ArithmeticException e) {
                System.out.println("15 / 0 -> Erro retornado pelo calculadora.servidor: " + e.getMessage());
            }
        } catch (Exception e) {
            System.err.println("Erro no calculadora.cliente: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
