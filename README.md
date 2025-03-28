# MEXC to Koinly Converter

Este repositório contém um script em Python que converte o extrato da Exchange MEXC (no formato XLSX ou CSV) para o formato CSV aceito pela plataforma [Koinly](https://koinly.io/). O script automatiza a leitura dos dados (compra, venda, quantidade, montante, etc.) e produz um arquivo de saída pronto para importação no Koinly.

## Estrutura

```
.
├── mexc.xlsx           # Exemplo de extrato da MEXC em formato Excel
├── mexc_to_koinly.py   # Script Python para converter o extrato
└── mexc_koinly.csv     # Exemplo de arquivo convertido (saída Koinly)
```

## Como funciona

1. O script **mexc_to_koinly.py** verifica se as bibliotecas necessárias (`pandas` e `openpyxl`) estão instaladas:
   - Se não estiverem, o script tentará instalá-las automaticamente via `pip`.
2. Em seguida, o script lê o arquivo **mexc.xlsx** (ou `mexc.csv`, caso você ajuste o nome do arquivo) e realiza o parsing das colunas de data, pares de cripto, quantidade e valores.
3. Cria um arquivo **mexc_koinly.csv** no layout aceito pela Koinly, que inclui colunas como `Date`, `Sent Amount`, `Received Amount`, entre outras.

## Pré-requisitos

- **Python 3.7 ou superior** (pode funcionar em versões anteriores, mas não foi testado).
- Acesso à internet (se o script precisar instalar as bibliotecas automaticamente).
- Se preferir, você pode instalar manualmente as dependências antes de rodar:
  ```bash
  pip install pandas openpyxl
  ```

## Passo a passo para usar

1. **Clone** ou **baixe** este repositório.
2. **Abra** o terminal (Prompt de Comando, PowerShell ou outra shell) na pasta do projeto.
3. **(Opcional)** Caso deseje alterar o nome do arquivo de entrada ou saída, edite as variáveis `input_file` e `output_file` no final do script `mexc_to_koinly.py`.
4. Execute o script:
   ```bash
   python mexc_to_koinly.py
   ```
5. Ao término, um arquivo **mexc_koinly.csv** será gerado na pasta do projeto (ou outro nome definido no script).

## Observações

- O arquivo de extrato original da MEXC costuma vir em XLSX, mas também pode estar em CSV com `;` como separador. O script detecta automaticamente o formato.
- O script não trata taxas (`Fee`), pois o extrato de exemplo não fornecia essa coluna. Caso a MEXC passe a fornecer taxas em colunas separadas, será necessário ajustar o código para preenchê-las no CSV da Koinly.

## Contribuições

Sinta-se à vontade para abrir **Issues** ou enviar **Pull Requests** se encontrar algum problema ou quiser adicionar funcionalidades.

1. **Bifurque (fork) este repositório**.
2. **Crie um branch** para sua contribuição: `git checkout -b feature/sua-feature`.
3. **Envie um Pull Request** descrevendo as alterações.

## Licença

Este projeto está sob a [MIT License](https://opensource.org/licenses/MIT). Consulte o arquivo LICENSE (se houver) para mais detalhes.
