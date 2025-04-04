# MEXC to Koinly Converter

Este script converte arquivos de histórico de transações da exchange MEXC para o formato compatível com o Koinly, facilitando a importação de transações para fins de declaração de impostos.

## Versão Atual
v1.0.0

## Requisitos
- Python 3.6 ou superior
- Bibliotecas Python:
  - pandas
  - openpyxl

## Instalação

1. Clone este repositório:
```bash
git clone https://github.com/seu-usuario/MEXC-to-Koinly.git
cd MEXC-to-Koinly
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Como Usar

1. Exporte seu histórico de transações da MEXC:
   - Acesse sua conta na MEXC
   - Vá para "Histórico de Transações"
   - Selecione o período desejado
   - Exporte como arquivo Excel (.xlsx)

2. Coloque o arquivo exportado na mesma pasta do script

3. Execute o script:
```bash
python mexc_to_koinly.py
```

4. O script irá gerar um arquivo chamado `mexc_koinly.csv` que pode ser importado diretamente no Koinly

## Formatos Suportados

O script suporta dois formatos de exportação da MEXC:
- FORMATO_1: Formato antigo
- FORMATO_2: Formato novo (atual)

O script detecta automaticamente qual formato está sendo usado.

## Tipos de Transações Processadas

- Depósitos
- Airdrops
- Trades (com taxas)
- Taxas de negociação

## Estrutura do Arquivo de Saída

O arquivo CSV gerado contém as seguintes colunas:
- Date: Data e hora da transação (UTC)
- Sent Amount: Quantidade enviada
- Sent Currency: Moeda enviada
- Received Amount: Quantidade recebida
- Received Currency: Moeda recebida
- Fee Amount: Valor da taxa
- Fee Currency: Moeda da taxa
- Net Worth Amount: Valor líquido
- Net Worth Currency: Moeda do valor líquido
- Label: Tipo da transação (Deposit, Airdrop, Trade)
- Description: Descrição detalhada da transação
- TxHash: Hash da transação (quando disponível)

## Solução de Problemas

Se encontrar algum erro, verifique:
1. Se o arquivo de entrada está no formato correto
2. Se todas as dependências estão instaladas
3. Se o arquivo de entrada está na mesma pasta do script

Para mais detalhes, consulte o CHANGELOG.md para ver as últimas atualizações e correções.

## Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue para discutir mudanças ou melhorias antes de submeter um pull request.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.
