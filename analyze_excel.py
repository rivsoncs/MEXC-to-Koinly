import pandas as pd
import sys

def analyze_excel(file_path):
    try:
        # Lê o arquivo Excel
        df = pd.read_excel(file_path)
        
        # Imprime informações sobre o arquivo
        print("\nColunas encontradas:")
        print(df.columns.tolist())
        
        print("\nPrimeiras 5 linhas:")
        print(df.head())
        
        print("\nTipos de dados das colunas:")
        print(df.dtypes)
        
    except Exception as e:
        print(f"Erro ao analisar o arquivo: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_excel(sys.argv[1])
    else:
        analyze_excel("mexc.xlsx") 