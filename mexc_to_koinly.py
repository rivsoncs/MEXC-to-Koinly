import sys
import subprocess
import pandas as pd
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import traceback

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

##############################################################################
# 1) Funções para checar e instalar dependências
##############################################################################
def check_and_install(package_name):
    try:
        __import__(package_name)
    except ImportError:
        logger.info(f"Pacote '{package_name}' não encontrado. Instalando agora...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"Pacote '{package_name}' instalado com sucesso!")

check_and_install("pandas")
check_and_install("openpyxl")

##############################################################################
# 2) Definição dos formatos suportados e mapeamento de colunas
##############################################################################

# Formatos conhecidos de extratos MEXC
FORMATOS = {
    "FORMATO_1": {
        "COL_PARES": "Pares",
        "COL_HORA": "Hora",
        "COL_TIPO": "Tipo",
        "COL_DIRECAO": "Direção",
        "COL_PRECO_MEDIO": "Preço Médio Preenchido",
        "COL_PRECO_ORDEM": "Preço da Ordem",
        "COL_QTD_PREENCHIDA": "Quantidade Preenchida",
        "COL_QTD_ORDEM": "Quantidade da Ordem",
        "COL_MONTANTE_ORDEM": "Montante da Ordem",
        "COL_STATUS": "Status"
    },
    "FORMATO_2": {
        "COL_DATA": "Data de criação(UTC+-3)",
        "COL_CRIPTO": "Cripto",
        "COL_TIPO": "Tipo de transação",
        "COL_DIRECAO": "Direção",
        "COL_QUANTIDADE": "Quantidade"
    }
}

COLUNAS_KOINLY = [
    'Date',
    'Sent Amount',
    'Sent Currency',
    'Received Amount',
    'Received Currency',
    'Fee Amount',
    'Fee Currency',
    'Net Worth Amount',
    'Net Worth Currency',
    'Label',
    'Description',
    'TxHash'
]

def detectar_formato(df: pd.DataFrame) -> Optional[str]:
    """
    Detecta qual formato de extrato está sendo usado baseado nas colunas presentes.
    Retorna o nome do formato ou None se não reconhecer.
    """
    for formato, mapeamento in FORMATOS.items():
        colunas_necessarias = set(mapeamento.values())
        colunas_presentes = set(df.columns)
        if colunas_necessarias.issubset(colunas_presentes):
            return formato
    return None

def parse_datetime_to_koinly(date_str: str) -> str:
    """
    Converte 'YYYY-MM-DD HH:MM:SS' -> 'YYYY-MM-DD HH:MM:SS UTC'.
    Se falhar, retorna 'Invalid Date'.
    """
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        logger.warning(f"Falha ao converter data: {date_str}")
        return "Invalid Date"

def parse_float(value) -> float:
    """
    Converte valor numérico em float, tratando vírgulas decimais.
    Retorna 0.0 se não for possível.
    """
    if pd.isnull(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).replace(',', '.').strip()
    try:
        return float(s)
    except ValueError:
        logger.warning(f"Falha ao converter valor numérico: {value}")
        return 0.0

def read_mexc_file(input_file: str) -> pd.DataFrame:
    """
    Detecta extensão do arquivo e lê o conteúdo.
    Suporta .xlsx, .xls e .csv.
    """
    ext = os.path.splitext(input_file)[1].lower()
    try:
        if ext in [".xlsx", ".xls"]:
            df = pd.read_excel(input_file)
        elif ext == ".csv":
            df = pd.read_csv(input_file, delimiter=';')
        else:
            raise ValueError(f"Formato de arquivo não suportado: {ext}")
        return df
    except Exception as e:
        logger.error(f"Erro ao ler arquivo {input_file}: {str(e)}")
        raise

def processar_linha(row: pd.Series, mapeamento: Dict[str, str]) -> List[str]:
    """
    Processa uma linha do DataFrame de acordo com o mapeamento de colunas.
    Retorna uma linha no formato Koinly.
    """
    # Inicializa todas as variáveis necessárias
    sent_amount = ""
    sent_currency = ""
    received_amount = ""
    received_currency = ""
    fee_amount = ""
    fee_currency = ""
    net_worth_amount = ""
    net_worth_currency = ""
    label = ""
    description = ""

    # Verifica qual formato está sendo usado
    if "COL_PARES" in mapeamento:
        # Formato 1 (antigo)
        pares = str(row[mapeamento["COL_PARES"]]).strip()
        hora = str(row[mapeamento["COL_HORA"]]).strip()
        tipo = str(row[mapeamento["COL_TIPO"]]).strip()
        direcao = str(row[mapeamento["COL_DIRECAO"]]).strip()
        status = str(row[mapeamento["COL_STATUS"]]).strip()

        preco_medio = parse_float(row[mapeamento["COL_PRECO_MEDIO"]])
        preco_ordem = parse_float(row[mapeamento["COL_PRECO_ORDEM"]])
        qtd_preench = parse_float(row[mapeamento["COL_QTD_PREENCHIDA"]])
        qtd_ordem = parse_float(row[mapeamento["COL_QTD_ORDEM"]])
        montante_ord = parse_float(row[mapeamento["COL_MONTANTE_ORDEM"]])

        date_koinly = parse_datetime_to_koinly(hora)

        if "_" in pares:
            base_asset, quote_asset = pares.split("_", 1)
        else:
            base_asset = pares
            quote_asset = ""

        label = "Trade"
        description = f"{direcao} ({tipo}) de {pares} - Status: {status}"

        if direcao.lower() == "comprar":
            sent_amount = montante_ord
            sent_currency = quote_asset
            received_amount = qtd_preench
            received_currency = base_asset
        elif direcao.lower() == "vender":
            sent_amount = qtd_preench
            sent_currency = base_asset
            received_amount = montante_ord
            received_currency = quote_asset

    else:
        # Formato 2 (novo)
        data = str(row[mapeamento["COL_DATA"]]).strip()
        cripto = str(row[mapeamento["COL_CRIPTO"]]).strip()
        tipo = str(row[mapeamento["COL_TIPO"]]).strip()
        direcao = str(row[mapeamento["COL_DIRECAO"]]).strip()
        quantidade = parse_float(row[mapeamento["COL_QUANTIDADE"]])

        # Converte a data para o formato Koinly
        date_koinly = parse_datetime_to_koinly(data)

        # Determina se é entrada ou saída
        is_entrada = "entrada" in direcao.lower()

        # Configura os valores baseado no tipo de transação
        if tipo == "Depositar":
            label = "Deposit"
            description = f"Depósito de {cripto}"
            if is_entrada:
                received_amount = abs(quantidade)
                received_currency = cripto
            else:
                sent_amount = abs(quantidade)
                sent_currency = cripto

        elif tipo == "Airdrop":
            label = "Airdrop"
            description = f"Airdrop de {cripto}"
            received_amount = abs(quantidade)
            received_currency = cripto

        elif "Negociação Spot" in tipo:
            label = "Trade"
            description = f"Negociação Spot de {cripto}"
            if is_entrada:
                received_amount = abs(quantidade)
                received_currency = cripto
            else:
                sent_amount = abs(quantidade)
                sent_currency = cripto

        elif "Taxas" in tipo:
            label = "Fee"
            description = f"Taxa de {tipo}"
            sent_amount = abs(quantidade)
            sent_currency = cripto

        else:
            label = "Other"
            description = f"{tipo} de {cripto}"
            if is_entrada:
                received_amount = abs(quantidade)
                received_currency = cripto
            else:
                sent_amount = abs(quantidade)
                sent_currency = cripto

    # Garante que os valores numéricos sejam strings vazias se não definidos
    sent_amount = str(sent_amount) if sent_amount else ""
    received_amount = str(received_amount) if received_amount else ""

    return [
        date_koinly,
        sent_amount,
        sent_currency,
        received_amount,
        received_currency,
        fee_amount,
        fee_currency,
        net_worth_amount,
        net_worth_currency,
        label,
        description,
        ""
    ]

def parse_float_value(value):
    """
    Converte um valor para float, seja ele string ou float.
    """
    if isinstance(value, float):
        return value
    elif isinstance(value, str):
        return float(value.replace(',', '.'))
    return 0.0

def processar_trades_relacionados(df, timestamp):
    """
    Processa trades relacionados em um determinado timestamp.
    
    Args:
        df (pd.DataFrame): DataFrame com as transações
        timestamp (str): Timestamp a ser processado
        
    Returns:
        list: Lista de dicionários no formato Koinly
    """
    # Initialize list to store Koinly entries
    linhas_koinly = []

    # Process deposits
    depositos = df[
        (df['Data de criação(UTC+-3)'] == timestamp) & 
        (df['Tipo de transação'] == 'Depositar')
    ]
    for _, deposito in depositos.iterrows():
        linha_koinly = {
            'Date': f"{timestamp} UTC",
            'Sent Amount': '',
            'Sent Currency': '',
            'Received Amount': str(abs(parse_float_value(deposito['Quantidade']))),
            'Received Currency': deposito['Cripto'],
            'Fee Amount': '',
            'Fee Currency': '',
            'Net Worth Amount': '',
            'Net Worth Currency': '',
            'Label': 'Deposit',
            'Description': f"Depósito de {deposito['Cripto']}",
            'TxHash': ''
        }
        linhas_koinly.append(linha_koinly)

    # Process airdrops
    airdrops = df[
        (df['Data de criação(UTC+-3)'] == timestamp) & 
        (df['Tipo de transação'] == 'Airdrop')
    ]
    for _, airdrop in airdrops.iterrows():
        linha_koinly = {
            'Date': f"{timestamp} UTC",
            'Sent Amount': '',
            'Sent Currency': '',
            'Received Amount': str(abs(parse_float_value(airdrop['Quantidade']))),
            'Received Currency': airdrop['Cripto'],
            'Fee Amount': '',
            'Fee Currency': '',
            'Net Worth Amount': '',
            'Net Worth Currency': '',
            'Label': 'Airdrop',
            'Description': f"Airdrop de {airdrop['Cripto']}",
            'TxHash': ''
        }
        linhas_koinly.append(linha_koinly)

    # Process trades
    trades = df[
        (df['Data de criação(UTC+-3)'] == timestamp) & 
        (df['Tipo de transação'].isin(['Negociação Spot', 'Taxas de Negociação Spot']))
    ]

    if len(trades) > 0:
        # Get spot trades (excluding fees)
        spot_trades = trades[trades['Tipo de transação'] == 'Negociação Spot']
        print(f"  Número de spot trades: {len(spot_trades)}")
        
        # Group trades by crypto
        trades_por_cripto = {}
        for _, trade in spot_trades.iterrows():
            cripto = trade['Cripto']
            if cripto not in trades_por_cripto:
                trades_por_cripto[cripto] = {'entrada': [], 'saida': []}
            
            if trade['Direção'] == 'Fluxo de entrada':
                trades_por_cripto[cripto]['entrada'].append(trade)
            else:
                trades_por_cripto[cripto]['saida'].append(trade)
        
        print(f"  Moedas encontradas: {list(trades_por_cripto.keys())}")
        
        # Find pairs of trades (one entrada and one saída)
        moedas = list(trades_por_cripto.keys())
        for i in range(0, len(moedas), 2):
            moeda1 = moedas[i]
            moeda2 = moedas[i + 1] if i + 1 < len(moedas) else None
            
            if moeda2 is None:
                continue
                
            print(f"  Processando par {moeda1}/{moeda2}:")
            
            # Get the entrada and saída trades
            trades1 = trades_por_cripto[moeda1]
            trades2 = trades_por_cripto[moeda2]
            
            # Calculate total amounts for each currency
            total1_entrada = sum(abs(parse_float_value(t['Quantidade'])) for t in trades1['entrada'])
            total1_saida = sum(abs(parse_float_value(t['Quantidade'])) for t in trades1['saida'])
            total2_entrada = sum(abs(parse_float_value(t['Quantidade'])) for t in trades2['entrada'])
            total2_saida = sum(abs(parse_float_value(t['Quantidade'])) for t in trades2['saida'])
            
            print(f"    {moeda1} - Entrada: {total1_entrada}, Saída: {total1_saida}")
            print(f"    {moeda2} - Entrada: {total2_entrada}, Saída: {total2_saida}")
            
            # Find associated fee
            fee = trades[
                (trades['Tipo de transação'] == 'Taxas de Negociação Spot') & 
                (trades['Cripto'] == 'USDT')
            ]
            fee_amount = str(abs(parse_float_value(fee['Quantidade'].sum()))) if not fee.empty else ''
            print(f"    Taxa: {fee_amount}")
            
            # Create the trade entry
            if total1_entrada > 0 and total2_saida > 0:
                # moeda1 was received, moeda2 was sent
                linha_koinly = {
                    'Date': f"{timestamp} UTC",
                    'Sent Amount': str(total2_saida),
                    'Sent Currency': moeda2,
                    'Received Amount': str(total1_entrada),
                    'Received Currency': moeda1,
                    'Fee Amount': fee_amount,
                    'Fee Currency': 'USDT' if fee_amount else '',
                    'Net Worth Amount': '',
                    'Net Worth Currency': '',
                    'Label': 'Trade',
                    'Description': f"Trade: {moeda2} -> {moeda1}",
                    'TxHash': ''
                }
                linhas_koinly.append(linha_koinly)
                print(f"    Linha gerada: {linha_koinly}")
            elif total1_saida > 0 and total2_entrada > 0:
                # moeda1 was sent, moeda2 was received
                linha_koinly = {
                    'Date': f"{timestamp} UTC",
                    'Sent Amount': str(total1_saida),
                    'Sent Currency': moeda1,
                    'Received Amount': str(total2_entrada),
                    'Received Currency': moeda2,
                    'Fee Amount': fee_amount,
                    'Fee Currency': 'USDT' if fee_amount else '',
                    'Net Worth Amount': '',
                    'Net Worth Currency': '',
                    'Label': 'Trade',
                    'Description': f"Trade: {moeda1} -> {moeda2}",
                    'TxHash': ''
                }
                linhas_koinly.append(linha_koinly)
                print(f"    Linha gerada: {linha_koinly}")

    return linhas_koinly

def converter_mexc_para_koinly(input_file: str, output_file: str = "mexc_koinly.csv"):
    """
    Converte um arquivo Excel do MEXC para o formato CSV do Koinly.
    
    Args:
        input_file (str): Caminho do arquivo Excel de entrada
        output_file (str): Caminho do arquivo CSV de saída
    """
    try:
        # Ler o arquivo Excel
        df = pd.read_excel(input_file)
        
        # Verificar o formato e obter o mapeamento
        formato = detectar_formato(df)
        if formato not in FORMATOS:
            raise ValueError(f"Formato não suportado: {formato}")
            
        logging.info(f"Formato detectado: {formato}")
        
        # Print available columns and unique transaction types
        print("\nColunas disponíveis:")
        print(df.columns.tolist())
        print("\nTipos de transações únicos:")
        print(df['Tipo de transação'].unique())
        print("\nDireções únicas:")
        print(df['Direção'].unique())
        
        # Aplicar o mapeamento de colunas
        mapeamento = FORMATOS[formato]
        
        # Inicializar lista para armazenar as linhas do Koinly
        linhas_koinly = []
        
        # Processar depósitos
        depositos = df[df['Tipo de transação'] == 'Depositar']
        print(f"\nNúmero de depósitos: {len(depositos)}")
        for _, deposito in depositos.iterrows():
            linha_koinly = {
                'Date': f"{deposito['Data de criação(UTC+-3)']} UTC",
                'Sent Amount': '',
                'Sent Currency': '',
                'Received Amount': str(abs(parse_float_value(deposito['Quantidade']))),
                'Received Currency': deposito['Cripto'],
                'Fee Amount': '',
                'Fee Currency': '',
                'Net Worth Amount': '',
                'Net Worth Currency': '',
                'Label': 'Deposit',
                'Description': f"Depósito de {deposito['Cripto']}",
                'TxHash': ''
            }
            linhas_koinly.append(linha_koinly)
            
        # Processar airdrops
        airdrops = df[df['Tipo de transação'] == 'Airdrop']
        print(f"\nNúmero de airdrops: {len(airdrops)}")
        for _, airdrop in airdrops.iterrows():
            linha_koinly = {
                'Date': f"{airdrop['Data de criação(UTC+-3)']} UTC",
                'Sent Amount': '',
                'Sent Currency': '',
                'Received Amount': str(abs(parse_float_value(airdrop['Quantidade']))),
                'Received Currency': airdrop['Cripto'],
                'Fee Amount': '',
                'Fee Currency': '',
                'Net Worth Amount': '',
                'Net Worth Currency': '',
                'Label': 'Airdrop',
                'Description': f"Airdrop de {airdrop['Cripto']}",
                'TxHash': ''
            }
            linhas_koinly.append(linha_koinly)
            
        # Processar trades
        trades_df = df[df['Tipo de transação'].isin(['Negociação Spot', 'Taxas de Negociação Spot'])]
        print(f"\nNúmero total de trades e taxas: {len(trades_df)}")
        
        timestamps = trades_df['Data de criação(UTC+-3)'].unique()
        print(f"\nNúmero de timestamps únicos: {len(timestamps)}")
        
        for timestamp in timestamps:
            trades = df[
                (df['Data de criação(UTC+-3)'] == timestamp) & 
                (df['Tipo de transação'].isin(['Negociação Spot', 'Taxas de Negociação Spot']))
            ]
            print(f"\nProcessando timestamp {timestamp}:")
            print(f"Número de trades neste timestamp: {len(trades)}")
            
            if len(trades) > 0:
                novas_linhas = processar_trades_relacionados(trades, timestamp)
                print(f"Número de linhas geradas: {len(novas_linhas)}")
                linhas_koinly.extend(novas_linhas)
        
        print(f"\nNúmero total de linhas a serem escritas: {len(linhas_koinly)}")
        
        # Convert to DataFrame for better handling
        df_koinly = pd.DataFrame(linhas_koinly)
        
        # Ensure all columns are present
        for col in COLUNAS_KOINLY:
            if col not in df_koinly.columns:
                df_koinly[col] = ''
                
        # Reorder columns
        df_koinly = df_koinly[COLUNAS_KOINLY]
        
        # Write to CSV
        df_koinly.to_csv(output_file, index=False, encoding='utf-8-sig')
            
        logging.info(f"Conversão finalizada: {output_file} (linhas: {len(linhas_koinly)})")
        print("Processo concluído!")
        
    except Exception as e:
        logging.error(f"Erro durante a conversão: {str(e)}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    input_file = "mexc.xlsx"
    output_file = "mexc_koinly.csv"
    converter_mexc_para_koinly(input_file, output_file)
