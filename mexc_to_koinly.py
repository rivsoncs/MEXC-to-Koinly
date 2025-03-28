import sys
import subprocess

##############################################################################
# 1) Funções para checar e instalar dependências (pandas, openpyxl)
##############################################################################
def check_and_install(package_name):
    """
    Verifica se 'package_name' está instalado.
    Se não, instala via pip e exibe mensagens de status.
    """
    try:
        __import__(package_name)
    except ImportError:
        print(f"[INFO] Pacote '{package_name}' não encontrado. Instalando agora...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"[INFO] Pacote '{package_name}' instalado com sucesso!")

# Checa e instala as dependências necessárias
check_and_install("pandas")
check_and_install("openpyxl")

##############################################################################
# 2) Agora podemos importar pandas (e afins) sem erro
##############################################################################
import pandas as pd
import csv
import os
from datetime import datetime

##############################################################################
# 3) Definição do script principal de conversão
##############################################################################

# Colunas esperadas no extrato da MEXC
COL_PARES                   = "Pares"
COL_HORA                    = "Hora"
COL_TIPO                    = "Tipo"         # ex.: "Limite", "Mercado"
COL_DIRECAO                 = "Direção"      # ex.: "Comprar", "Vender"
COL_PRECO_MEDIO             = "Preço Médio Preenchido"
COL_PRECO_ORDEM             = "Preço da Ordem"
COL_QTD_PREENCHIDA          = "Quantidade Preenchida"
COL_QTD_ORDEM               = "Quantidade da Ordem"
COL_MONTANTE_ORDEM          = "Montante da Ordem"
COL_STATUS                  = "Status"

def parse_datetime_to_koinly(date_str: str) -> str:
    """
    Converte 'YYYY-MM-DD HH:MM:SS' -> 'YYYY-MM-DD HH:MM:SS UTC'.
    Se falhar, retorna 'Invalid Date'.
    """
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
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
        return 0.0

def read_mexc_file(input_file: str) -> pd.DataFrame:
    """
    Detecta extensão do arquivo:
      - .xlsx / .xls => lê via pandas.read_excel
      - .csv => lê via pandas.read_csv (delimiter=';').
    Retorna DataFrame.
    """
    ext = os.path.splitext(input_file)[1].lower()
    if ext in [".xlsx", ".xls"]:
        df = pd.read_excel(input_file)
    elif ext == ".csv":
        df = pd.read_csv(input_file, delimiter=';')
    else:
        raise ValueError(f"Formato de arquivo não suportado: {ext}")
    return df

def converter_mexc_para_koinly(input_file: str, output_csv: str):
    """
    1) Lê 'input_file' (XLSX ou CSV).
    2) Converte cada linha para CSV Koinly com colunas:
       [Date,Sent Amount,Sent Currency,Received Amount,Received Currency,
        Fee Amount,Fee Currency,Net Worth Amount,Net Worth Currency,
        Label,Description,TxHash].
    3) Salva em 'output_csv'.
    """
    df = read_mexc_file(input_file)

    # Checar se as colunas esperadas existem
    expected_cols = [
        COL_PARES, COL_HORA, COL_TIPO, COL_DIRECAO, COL_PRECO_MEDIO,
        COL_PRECO_ORDEM, COL_QTD_PREENCHIDA, COL_QTD_ORDEM, COL_MONTANTE_ORDEM, COL_STATUS
    ]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"As colunas {missing} não foram encontradas no arquivo.")

    rows_koinly = []

    for _, row in df.iterrows():
        pares = str(row[COL_PARES]).strip()
        hora = str(row[COL_HORA]).strip()
        tipo = str(row[COL_TIPO]).strip()
        direcao = str(row[COL_DIRECAO]).strip()
        status = str(row[COL_STATUS]).strip()

        preco_medio   = parse_float(row[COL_PRECO_MEDIO])
        preco_ordem   = parse_float(row[COL_PRECO_ORDEM])
        qtd_preench   = parse_float(row[COL_QTD_PREENCHIDA])
        qtd_ordem     = parse_float(row[COL_QTD_ORDEM])
        montante_ord  = parse_float(row[COL_MONTANTE_ORDEM])

        # Converte data
        date_koinly = parse_datetime_to_koinly(hora)

        # Extrair base e quote de "FLUID_USDT" => base_asset="FLUID", quote_asset="USDT"
        if "_" in pares:
            base_asset, quote_asset = pares.split("_", 1)
        else:
            base_asset = pares
            quote_asset = ""

        # Campos do Koinly
        sent_amount = ""
        sent_currency = ""
        received_amount = ""
        received_currency = ""
        fee_amount = ""
        fee_currency = ""
        net_worth_amount = ""
        net_worth_currency = ""
        label = "Trade"
        description = f"{direcao} ({tipo}) de {pares} - Status: {status}"

        # Se "Comprar":
        if direcao.lower() == "comprar":
            # Manda a quote (montante_ord), recebe base (qtd_preench)
            sent_amount = montante_ord
            sent_currency = quote_asset
            received_amount = qtd_preench
            received_currency = base_asset

        # Se "Vender":
        elif direcao.lower() == "vender":
            # Manda a base (qtd_preench), recebe quote (montante_ord)
            sent_amount = qtd_preench
            sent_currency = base_asset
            received_amount = montante_ord
            received_currency = quote_asset

        row_koinly = [
            date_koinly,
            sent_amount if sent_amount else "",
            sent_currency if sent_amount else "",
            received_amount if received_amount else "",
            received_currency if received_amount else "",
            fee_amount,       # não há coluna de taxa
            fee_currency,
            net_worth_amount,
            net_worth_currency,
            label,
            description,
            ""
        ]
        rows_koinly.append(row_koinly)

    # Gravar CSV final
    with open(output_csv, 'w', encoding='utf-8', newline='') as f_out:
        writer = csv.writer(f_out, quoting=csv.QUOTE_ALL)
        writer.writerow([
            "Date", "Sent Amount", "Sent Currency",
            "Received Amount", "Received Currency",
            "Fee Amount", "Fee Currency",
            "Net Worth Amount", "Net Worth Currency",
            "Label", "Description", "TxHash"
        ])
        writer.writerows(rows_koinly)

    print(f"[OK] Conversão finalizada: {output_csv} (linhas: {len(rows_koinly)})")

##############################################################################
# Execução principal, se rodar este arquivo diretamente
##############################################################################
if __name__ == "__main__":
    # Ajuste aqui o arquivo de entrada e de saída conforme necessário
    input_file = "mexc.xlsx"
    output_file = "mexc_koinly.csv"
    converter_mexc_para_koinly(input_file, output_file)
    print("Processo concluído!")
