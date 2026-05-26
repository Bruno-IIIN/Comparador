import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import base64
from io import BytesIO

def generate_html_dashboard(df1, df2, numeric_cols, diff_df, output_file="dashboard.html"):
    # Gerar gráfico como imagem base64 para embutir no HTML
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(numeric_cols))
    width = 0.35
    sums1 = [df1[col].sum() for col in numeric_cols]
    sums2 = [df2[col].sum() for col in numeric_cols]
    ax.bar([i - width/2 for i in x], sums1, width, label='Semana 1', color='#4CAF50')
    ax.bar([i + width/2 for i in x], sums2, width, label='Semana 2', color='#FF9800')
    ax.set_xticks(x)
    ax.set_xticklabels(numeric_cols, rotation=45, ha='right')
    ax.set_ylabel('Soma')
    ax.set_title('Comparação de Totais por Coluna')
    ax.legend()
    plt.tight_layout()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    
    # Gerar tabela de diferenças em HTML
    diff_html = diff_df.to_html(classes='diff-table', border=0, float_format="%.2f")
    
    # Gerar métricas em HTML
    metrics_html = "<table class='metrics'>"
    for col in numeric_cols:
        total1 = df1[col].sum()
        total2 = df2[col].sum()
        diff_total = total2 - total1
        mean1 = df1[col].mean()
        mean2 = df2[col].mean()
        diff_mean = mean2 - mean1
        metrics_html += f"""
        <tr>
            <td><strong>{col}</strong></td>
            <td>Soma Sem1: {total1:.2f}</td>
            <td>Soma Sem2: {total2:.2f}</td>
            <td style="color:{'red' if diff_total!=0 else 'green'}">Δ = {diff_total:.2f}</td>
            <td>Média: {mean1:.2f} → {mean2:.2f} (Δ {diff_mean:.2f})</td>
        </tr>
        """
    metrics_html += "</table>"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Comparativo Semanas</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; background: #f5f5f5; }}
            h1, h2 {{ color: #333; }}
            .container {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .metrics table {{ width: 100%; border-collapse: collapse; }}
            .metrics td, .metrics th {{ padding: 8px; border-bottom: 1px solid #ddd; text-align: left; }}
            .metrics tr:hover {{ background: #f1f1f1; }}
            .diff-table {{ width: 100%; border-collapse: collapse; }}
            .diff-table th, .diff-table td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            .diff-table th {{ background: #4CAF50; color: white; }}
            .graph {{ text-align: center; margin: 20px 0; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #ccc; }}
            .footer {{ font-size: 0.8em; color: gray; text-align: center; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h1>📊 Comparação Semana 1 vs Semana 2</h1>
        <div class="container">
            <h2>📈 Métricas Resumo</h2>
            {metrics_html}
        </div>
        <div class="container graph">
            <h2>📉 Gráfico Comparativo</h2>
            <img src="data:image/png;base64,{image_base64}" alt="Gráfico de barras">
        </div>
        <div class="container">
            <h2>🔍 Tabela de Diferenças (Linha a Linha)</h2>
            {diff_html}
        </div>
        <div class="footer">
            Gerado automaticamente por GitHub Actions em {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Dashboard salvo em {output_file}")

def main():
    if len(sys.argv) != 3:
        print("Uso: python compare_excel.py <arquivo_semana1> <arquivo_semana2>")
        sys.exit(1)
    
    path1 = sys.argv[1]
    path2 = sys.argv[2]
    
    if not os.path.exists(path1) or not os.path.exists(path2):
        print("Erro: um dos arquivos não existe.")
        sys.exit(1)
    
    print(f"Lendo {path1}...")
    df1 = pd.read_excel(path1)
    print(f"Lendo {path2}...")
    df2 = pd.read_excel(path2)
    
    # Alinhar colunas e linhas
    common_cols = list(set(df1.columns) & set(df2.columns))
    if not common_cols:
        print("Nenhuma coluna em comum. Abortando.")
        sys.exit(1)
    
    df1 = df1[common_cols]
    df2 = df2[common_cols]
    min_rows = min(len(df1), len(df2))
    df1_aligned = df1.iloc[:min_rows].reset_index(drop=True)
    df2_aligned = df2.iloc[:min_rows].reset_index(drop=True)
    
    # Identificar colunas numéricas
    numeric_cols = []
    for col in common_cols:
        if pd.api.types.is_numeric_dtype(df1_aligned[col]) and pd.api.types.is_numeric_dtype(df2_aligned[col]):
            numeric_cols.append(col)
    
    if not numeric_cols:
        print("Nenhuma coluna numérica para comparar.")
        sys.exit(1)
    
    # Construir dataframe de diferenças
    diff_data = {}
    for col in numeric_cols:
        diff_data[f'{col} (Sem1)'] = df1_aligned[col]
        diff_data[f'{col} (Sem2)'] = df2_aligned[col]
        diff_data[f'{col} Δ'] = df2_aligned[col] - df1_aligned[col]
    diff_df = pd.DataFrame(diff_data)
    
    generate_html_dashboard(df1_aligned, df2_aligned, numeric_cols, diff_df)
    print("Processo concluído com sucesso!")

if __name__ == "__main__":
    main()
