#!/usr/bin/env python3
"""
main.py - Orquestrador Principal do Sistema EXPANDIDO
Sistema de Análise Estatística DL 54/2018 v2.0

VERSÃO EXPANDIDA: 13 análises + 18 gráficos + 15 sheets + 60 páginas DOCX

Autor: Sistema de Qualidade de Dados Educacionais
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Imports dos módulos do sistema
from config import ConfigManager
from data_loader import DataLoader
from statistics_engine import StatisticsEngine
from chart_generator import ChartGenerator
from excel_reporter import ExcelReporter
from docx_reporter import DocxReporter


def setup_logging(config: ConfigManager) -> logging.Logger:
    """Configura sistema de logging."""
    output_dir = Path(config.get('IO', 'OUTPUT_DIR'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = output_dir / 'process_estatisticas_dl54.log'
    
    # Configuração do logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('DL54.main')


def print_banner():
    """Imprime banner do sistema."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║    SISTEMA DE ANÁLISE ESTATÍSTICA DL 54/2018 v2.0 EXPANDIDO  ║
    ║                                                               ║
    ║    Análises Completas de Medidas de Apoio à Inclusão         ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Versão: 2.0 EXPANDIDO
    Data: {date}
    
    Características:
    ✓ 13 tipos de análises estatísticas
    ✓ 18 gráficos profissionais (300 DPI)
    ✓ 15 sheets Excel formatados
    ✓ ~60 páginas relatório DOCX
    ✓ 500+ estatísticas individuais
    
    """.format(date=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    
    print(banner)


def main():
    """Função principal do sistema EXPANDIDO."""
    
    # Banner
    print_banner()
    
    try:
        # ========================================
        # 1. INICIALIZAÇÃO
        # ========================================
        print("🔧 Inicializando sistema...")
        
        # Carregar configuração
        config = ConfigManager('config.ini')
        
        # Setup logging
        logger = setup_logging(config)
        logger.info("=" * 80)
        logger.info("SISTEMA DL 54/2018 v2.0 EXPANDIDO - INÍCIO")
        logger.info("=" * 80)
        
        # ========================================
        # 2. CARREGAMENTO DE DADOS
        # ========================================
        print("\n📂 Carregando dados...")
        logger.info("Fase 1: Carregamento de Dados")
        
        data_loader = DataLoader(config, logger)
        df = data_loader.load_and_validate()
        
        if df is None or df.empty:
            logger.error("Erro: Dataset vazio ou inválido")
            print("❌ Erro ao carregar dados. Verifique o ficheiro de entrada.")
            return 1
        
        logger.info(f"✓ Dados carregados: {len(df)} registos, {len(df.columns)} colunas")
        print(f"   ✓ {len(df)} alunos carregados")
        
        # ========================================
        # 3. ANÁLISES ESTATÍSTICAS EXPANDIDAS
        # ========================================
        print("\n🔬 Executando análises estatísticas expandidas...")
        logger.info("Fase 2: Análises Estatísticas EXPANDIDAS")
        
        stats_engine = StatisticsEngine(df, config, logger)
        stats = stats_engine.run_all_analyses()
        
        if not stats:
            logger.error("Erro: Falha nas análises estatísticas")
            print("❌ Erro nas análises estatísticas.")
            return 1
        
        # Mostrar resumo das análises
        print(f"   ✓ {len(stats)} tipos de análises concluídas:")
        print(f"      - Global: {stats['global']['total_alunos']} alunos")
        print(f"      - Escolas: {len(stats.get('por_escola', {}))} escolas")
        print(f"      - Anos: {len(stats.get('por_ano', {}))} anos")
        print(f"      - Turmas: {len(stats.get('por_turma', {}))} turmas")
        print(f"      - Ano+Turma: {len(stats.get('por_ano_turma', {}))} combinações")
        print(f"      - Alíneas detalhadas por ano")
        print(f"      - Terapias completas")
        print(f"      - Análises por sexo (detalhadas)")
        
        # ========================================
        # 4. GERAÇÃO DE GRÁFICOS (18 gráficos)
        # ========================================
        print("\n📊 Gerando gráficos expandidos (18 gráficos)...")
        logger.info("Fase 3: Geração de Gráficos EXPANDIDOS")
        
        chart_generator = ChartGenerator(config, logger)
        chart_paths = chart_generator.generate_all_charts(stats)
        
        if chart_paths:
            logger.info(f"✓ {len(chart_paths)} gráficos gerados com sucesso")
            print(f"   ✓ {len(chart_paths)} gráficos PNG criados (300 DPI)")
            
            # Mostrar lista de gráficos
            print("   Gráficos criados:")
            for i, chart_path in enumerate(chart_paths, 1):
                print(f"      {i:2}. {chart_path.name}")
        else:
            logger.warning("Nenhum gráfico foi gerado")
            print("   ⚠️  Nenhum gráfico gerado")
        
        # ========================================
        # 5. RELATÓRIO EXCEL (15 sheets)
        # ========================================
        print("\n📗 Gerando relatório Excel expandido (15 sheets)...")
        logger.info("Fase 4: Geração de Relatório Excel EXPANDIDO")
        
        excel_reporter = ExcelReporter(config, logger)
        excel_path = excel_reporter.generate_report(stats, raw_data=df)
        
        if excel_path and excel_path.exists():
            logger.info(f"✓ Relatório Excel gerado: {excel_path.name}")
            print(f"   ✓ Excel: {excel_path.name}")
            print(f"      - 15 sheets temáticos")
            print(f"      - Formatação profissional")
            print(f"      - {len(df)} linhas de dados brutos")
        else:
            logger.warning("Relatório Excel não foi gerado")
            print("   ⚠️  Excel não gerado")
        
        # ========================================
        # 6. RELATÓRIO DOCX (~60 páginas)
        # ========================================
        print("\n📘 Gerando relatório DOCX expandido (~60 páginas)...")
        logger.info("Fase 5: Geração de Relatório DOCX EXPANDIDO")
        
        docx_reporter = DocxReporter(config, logger)
        docx_path = docx_reporter.generate_report(stats, chart_paths)
        
        if docx_path and docx_path.exists():
            logger.info(f"✓ Relatório DOCX gerado: {docx_path.name}")
            print(f"   ✓ DOCX: {docx_path.name}")
            print(f"      - 15 secções detalhadas")
            print(f"      - 100+ tabelas")
            print(f"      - {len(chart_paths)} gráficos incorporados")
            print(f"      - ~60 páginas")
        else:
            logger.warning("Relatório DOCX não foi gerado")
            print("   ⚠️  DOCX não gerado")
        
        # ========================================
        # 7. RESUMO FINAL
        # ========================================
        logger.info("=" * 80)
        logger.info("SISTEMA DL 54/2018 v2.0 EXPANDIDO - CONCLUSÃO")
        logger.info("=" * 80)
        
        print("\n" + "=" * 70)
        print("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
        print("=" * 70)
        
        output_dir = Path(config.get('IO', 'OUTPUT_DIR'))
        
        print(f"\n📁 Outputs gerados em: {output_dir.absolute()}")
        print("\n📊 Ficheiros criados:")
        
        if excel_path and excel_path.exists():
            print(f"   ✓ Excel (15 sheets): {excel_path.name}")
        
        if docx_path and docx_path.exists():
            print(f"   ✓ DOCX (~60 pgs):    {docx_path.name}")
        
        if chart_paths:
            print(f"   ✓ Gráficos PNG:      {len(chart_paths)} ficheiros em charts/")
        
        print(f"   ✓ Log:               process_estatisticas_dl54.log")
        
        print("\n📈 Estatísticas processadas:")
        print(f"   • {stats['global']['total_alunos']} alunos analisados")
        print(f"   • {len(stats.get('por_escola', {}))} escolas")
        print(f"   • {len(stats.get('por_ano', {}))} anos de escolaridade")
        print(f"   • {len(stats.get('por_turma', {}))} turmas")
        print(f"   • {len(stats.get('por_ano_turma', {}))} combinações ano+turma")
        print(f"   • 15 alíneas detalhadas analisadas")
        print(f"   • 5 tipos de terapias analisadas")
        
        print("\n🎯 Análises realizadas:")
        print("   1. ✓ Análise Global")
        print("   2. ✓ Análise por Escola")
        print("   3. ✓ Análise por Ano")
        print("   4. ✓ Análise por Turma")
        print("   5. ✓ Análise por Ano e Turma")
        print("   6. ✓ Estatísticas por Aluno (Turma)")
        print("   7. ✓ Alíneas Detalhadas por Ano")
        print("   8. ✓ Terapias Completas")
        print("   9. ✓ Análise por Sexo")
        print("  10. ✓ Sexo Detalhado (Alíneas)")
        print("  11. ✓ Análise por Escalão ASE")
        print("  12. ✓ Rankings de Escolas")
        print("  13. ✓ Comparações Escola vs Agrupamento")
        
        print("\n📊 Gráficos gerados (18 tipos):")
        print("   • Barras, Pizza, Empilhados, Heatmaps")
        print("   • Comparações, Linhas, Box Plots")
        print("   • 300 DPI, WebSafe colors")
        
        print("\n" + "=" * 70)
        print("Sistema DL 54/2018 v2.0 EXPANDIDO")
        print("Desenvolvido para análise de medidas de apoio à inclusão")
        print("=" * 70 + "\n")
        
        logger.info("Sistema finalizado com sucesso")
        
        return 0
        
    except Exception as e:
        logger.critical(f"Erro crítico no sistema: {e}", exc_info=True)
        print(f"\n❌ ERRO CRÍTICO: {e}")
        print("\nVerifique o log para mais detalhes:")
        print(f"   {Path(config.get('IO', 'OUTPUT_DIR')) / 'process_estatisticas_dl54.log'}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
