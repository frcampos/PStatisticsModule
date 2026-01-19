#!/usr/bin/env python3
"""
statistics_engine.py - Motor de Análises Estatísticas EXPANDIDO
Sistema de Análise Estatística DL 54/2018 v2.0

VERSÃO EXPANDIDA com 11+ tipos de análises detalhadas

Autor: Sistema de Qualidade de Dados Educacionais
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import OrderedDict

from config import ConfigManager
from utils import (
    calculate_percentage, safe_divide, get_value_counts_dict,
    calculate_quartiles, rank_values, create_crosstab_percentage
)


logger = logging.getLogger('DL54.statistics')


class StatisticsEngine:
    """
    Motor de análises estatísticas EXPANDIDO para dados DL 54/2018.
    
    Implementa 11+ níveis de análise:
    1. Global
    2. Por escola
    3. Por ano
    4. Por turma
    5. Por ano + turma (combinado)
    6. Por sexo (detalhado)
    7. Por escalão ASE
    8. Estatísticas por aluno (dentro de turma)
    9. Alíneas detalhadas
    10. Terapias completas
    11. Rankings
    + Análises cruzadas
    """
    
    def __init__(self, df: pd.DataFrame, config: ConfigManager, 
                 logger_instance: logging.Logger):
        """Inicializa motor estatístico expandido."""
        self.df = df
        self.config = config
        self.logger = logger_instance
        
        self.escola_mapping = config.get_escola_mapping()
        self.column_mappings = config.get_column_mappings()
        self.analysis_config = config.get_analysis_config()
        self.grouping_cols = config.get_grouping_columns()
        
        self._cache: Dict[str, Any] = {}
    
    def run_all_analyses(self) -> Dict[str, Any]:
        """Executa TODAS as análises expandidas."""
        self.logger.info("=" * 80)
        self.logger.info("EXECUTANDO ANÁLISES ESTATÍSTICAS EXPANDIDAS")
        self.logger.info("=" * 80)
        
        results = {
            'metadata': {
                'total_alunos': len(self.df),
                'colunas': len(self.df.columns),
                'versao': 'EXPANDIDA v2.0'
            }
        }
        
        # Análises base
        results['global'] = self.analise_global()
        results['por_escola'] = self.analise_por_escola()
        results['por_ano'] = self.analise_por_ano()
        results['por_sexo'] = self.analise_por_sexo()
        results['por_escalao_ase'] = self.analise_por_escalao_ase()
        
        # NOVAS: Análises expandidas
        results['por_turma'] = self.analise_por_turma()
        results['por_ano_turma'] = self.analise_ano_turma()
        results['estatisticas_aluno_turma'] = self.estatisticas_aluno_por_turma()
        results['alineas_detalhadas'] = self.analise_alineas_detalhada()
        results['terapias_completas'] = self.analise_terapias_completa()
        results['sexo_detalhado'] = self.analise_sexo_detalhado()
        
        # Rankings e comparações
        results['rankings'] = self.generate_rankings()
        results['comparacoes'] = self.generate_comparisons()
        
        self.logger.info("=" * 80)
        self.logger.info("✓ ANÁLISES EXPANDIDAS CONCLUÍDAS")
        self.logger.info(f"  Total de tipos de análise: {len(results)}")
        self.logger.info("=" * 80)
        
        return results
    
    def analise_global(self) -> Dict[str, Any]:
        """Análise estatística global."""
        self.logger.info("Executando análise global...")
        
        total_alunos = len(self.df)
        
        stats = {
            'total_alunos': total_alunos,
            'medidas_principais': {},
            'medidas_detalhadas': {
                'universais': {},
                'seletivas': {},
                'adicionais': {},
                'adaptacoes_art28': {}
            }
        }
        
        # Medidas principais
        for nome, coluna in self.column_mappings['principais'].items():
            if coluna in self.df.columns:
                n = int(self.df[coluna].sum())
                pct = calculate_percentage(n, total_alunos)
                stats['medidas_principais'][nome] = {
                    'n': n,
                    'percentagem': pct,
                    'sem_medida': total_alunos - n,
                    'sem_medida_pct': calculate_percentage(total_alunos - n, total_alunos)
                }
        
        # Medidas detalhadas por tipo
        for tipo in ['universais', 'seletivas', 'adicionais', 'art28']:
            for nome, coluna in self.column_mappings[tipo].items():
                if coluna in self.df.columns:
                    n = int(self.df[coluna].sum())
                    pct = calculate_percentage(n, total_alunos)
                    
                    key = 'adaptacoes_art28' if tipo == 'art28' else tipo
                    stats['medidas_detalhadas'][key][nome] = {
                        'n': n,
                        'percentagem': pct
                    }
        
        return stats
    
    def analise_por_escola(self) -> Dict[int, Dict]:
        """Análise por escola."""
        self.logger.info("Executando análise por escola...")
        
        escola_col = self.grouping_cols['escola']
        if escola_col not in self.df.columns:
            return {}
        
        stats_por_escola = {}
        
        for codigo in sorted(self.df[escola_col].unique()):
            df_escola = self.df[self.df[escola_col] == codigo]
            total = len(df_escola)
            
            stats = {
                'codigo': int(codigo),
                'nome': self.escola_mapping.get(int(codigo), f"Escola {codigo}"),
                'total_alunos': total,
                'peso_no_agrupamento': calculate_percentage(total, len(self.df)),
                'medidas_principais': {}
            }
            
            for nome, coluna in self.column_mappings['principais'].items():
                if coluna in df_escola.columns:
                    n = int(df_escola[coluna].sum())
                    stats['medidas_principais'][nome] = {
                        'n': n,
                        'percentagem': calculate_percentage(n, total)
                    }
            
            stats_por_escola[int(codigo)] = stats
        
        return stats_por_escola
    
    def analise_por_ano(self) -> Dict[int, Dict]:
        """Análise por ano de escolaridade."""
        self.logger.info("Executando análise por ano...")
        
        ano_col = self.grouping_cols['ano']
        if ano_col not in self.df.columns:
            return {}
        
        stats_por_ano = {}
        
        for ano in sorted(self.df[ano_col].dropna().unique()):
            df_ano = self.df[self.df[ano_col] == ano]
            total = len(df_ano)
            
            # Nome do ano
            ano_nome = "Pré-Escolar" if ano == 0 else f"{int(ano)}º Ano"
            
            stats = {
                'ano': int(ano),
                'ano_nome': ano_nome,
                'total_alunos': total,
                'peso_no_total': calculate_percentage(total, len(self.df)),
                'medidas_principais': {}
            }
            
            for nome, coluna in self.column_mappings['principais'].items():
                if coluna in df_ano.columns:
                    n = int(df_ano[coluna].sum())
                    stats['medidas_principais'][nome] = {
                        'n': n,
                        'percentagem': calculate_percentage(n, total)
                    }
            
            stats_por_ano[int(ano)] = stats
        
        return stats_por_ano
    
    def analise_por_sexo(self) -> Dict[str, Dict]:
        """Análise por sexo (base)."""
        self.logger.info("Executando análise por sexo...")
        
        sexo_col = self.grouping_cols['sexo']
        if sexo_col not in self.df.columns:
            return {}
        
        stats_por_sexo = {}
        total_geral = len(self.df)
        
        for sexo in sorted(self.df[sexo_col].dropna().unique()):
            df_sexo = self.df[self.df[sexo_col] == sexo]
            total = len(df_sexo)
            
            stats = {
                'sexo': str(sexo),
                'total_alunos': total,
                'percentagem_do_total': calculate_percentage(total, total_geral),
                'medidas_principais': {}
            }
            
            for nome, coluna in self.column_mappings['principais'].items():
                if coluna in df_sexo.columns:
                    n = int(df_sexo[coluna].sum())
                    stats['medidas_principais'][nome] = {
                        'n': n,
                        'percentagem_no_grupo': calculate_percentage(n, total),
                        'percentagem_do_total': calculate_percentage(n, total_geral)
                    }
            
            stats_por_sexo[str(sexo)] = stats
        
        # Razão M/F
        if 'M' in stats_por_sexo and 'F' in stats_por_sexo:
            stats_por_sexo['_razao_M_F'] = round(
                safe_divide(stats_por_sexo['M']['total_alunos'],
                           stats_por_sexo['F']['total_alunos'], 1.0), 2
            )
        
        return stats_por_sexo
    
    def analise_por_escalao_ase(self) -> Dict[str, Dict]:
        """Análise por escalão ASE."""
        self.logger.info("Executando análise por escalão ASE...")
        
        ase_col = self.grouping_cols['escalao_ase']
        if ase_col not in self.df.columns:
            return {}
        
        stats_por_ase = {}
        total_geral = len(self.df)
        
        for escalao in sorted(self.df[ase_col].dropna().unique()):
            df_ase = self.df[self.df[ase_col] == escalao]
            total = len(df_ase)
            
            stats = {
                'escalao': str(escalao),
                'total_alunos': total,
                'percentagem_do_total': calculate_percentage(total, total_geral),
                'medidas_principais': {}
            }
            
            for nome, coluna in self.column_mappings['principais'].items():
                if coluna in df_ase.columns:
                    n = int(df_ase[coluna].sum())
                    stats['medidas_principais'][nome] = {
                        'n': n,
                        'percentagem': calculate_percentage(n, total)
                    }
            
            stats_por_ase[str(escalao)] = stats
        
        return stats_por_ase
    
    # ========================================
    # NOVAS ANÁLISES EXPANDIDAS
    # ========================================
    
    def analise_por_turma(self) -> Dict[str, Dict]:
        """NOVA: Análise detalhada por turma."""
        self.logger.info("Executando análise por turma...")
        
        turma_col = self.grouping_cols['turma']
        if turma_col not in self.df.columns:
            return {}
        
        stats_por_turma = {}
        
        for turma in sorted(self.df[turma_col].dropna().unique()):
            df_turma = self.df[self.df[turma_col] == turma]
            total = len(df_turma)
            
            stats = {
                'turma': str(turma),
                'total_alunos': total,
                'medidas_principais': {},
                'medidas_detalhadas': {
                    'universais': {},
                    'seletivas': {},
                    'adicionais': {}
                }
            }
            
            # Medidas principais
            for nome, coluna in self.column_mappings['principais'].items():
                if coluna in df_turma.columns:
                    n = int(df_turma[coluna].sum())
                    stats['medidas_principais'][nome] = {
                        'n': n,
                        'percentagem': calculate_percentage(n, total)
                    }
            
            # Medidas detalhadas
            for tipo in ['universais', 'seletivas', 'adicionais']:
                for nome, coluna in self.column_mappings[tipo].items():
                    if coluna in df_turma.columns:
                        n = int(df_turma[coluna].sum())
                        stats['medidas_detalhadas'][tipo][nome] = {
                            'n': n,
                            'percentagem': calculate_percentage(n, total)
                        }
            
            stats_por_turma[str(turma)] = stats
        
        self.logger.info(f"✓ Análise por turma: {len(stats_por_turma)} turmas")
        return stats_por_turma
    
    def analise_ano_turma(self) -> Dict[str, Dict]:
        """NOVA: Análise combinada ano + turma (ex: 4ºA, 4ºB, Pré-Azul)."""
        self.logger.info("Executando análise ano + turma...")
        
        ano_col = self.grouping_cols['ano']
        turma_col = self.grouping_cols['turma']
        
        if ano_col not in self.df.columns or turma_col not in self.df.columns:
            return {}
        
        stats_ano_turma = {}
        
        # Agrupar por ano e turma
        for (ano, turma), df_grupo in self.df.groupby([ano_col, turma_col]):
            total = len(df_grupo)
            
            # Nome da combinação
            ano_nome = "Pré" if ano == 0 else f"{int(ano)}º"
            chave = f"{ano_nome}_{turma}"
            
            stats = {
                'ano': int(ano),
                'turma': str(turma),
                'nome': f"{ano_nome} - Turma {turma}",
                'total_alunos': total,
                'medidas_principais': {}
            }
            
            for nome, coluna in self.column_mappings['principais'].items():
                if coluna in df_grupo.columns:
                    n = int(df_grupo[coluna].sum())
                    stats['medidas_principais'][nome] = {
                        'n': n,
                        'percentagem': calculate_percentage(n, total)
                    }
            
            stats_ano_turma[chave] = stats
        
        self.logger.info(f"✓ Análise ano+turma: {len(stats_ano_turma)} combinações")
        return stats_ano_turma
    
    def estatisticas_aluno_por_turma(self) -> Dict[str, Dict]:
        """NOVA: Estatísticas POR ALUNO dentro de cada turma (max, min, média, etc.)."""
        self.logger.info("Calculando estatísticas por aluno em cada turma...")
        
        ano_col = self.grouping_cols['ano']
        turma_col = self.grouping_cols['turma']
        
        if ano_col not in self.df.columns or turma_col not in self.df.columns:
            return {}
        
        # Calcular total de medidas por aluno
        medidas_cols = [
            self.column_mappings['principais']['Medidas Universais'],
            self.column_mappings['principais']['Medidas Seletivas'],
            self.column_mappings['principais']['Medidas Adicionais']
        ]
        
        self.df['_total_medidas'] = sum([self.df[col] for col in medidas_cols if col in self.df.columns])
        
        stats_por_turma = {}
        
        for (ano, turma), df_grupo in self.df.groupby([ano_col, turma_col]):
            ano_nome = "Pré" if ano == 0 else f"{int(ano)}º"
            chave = f"{ano_nome}_{turma}"
            
            medidas_alunos = df_grupo['_total_medidas']
            
            stats = {
                'ano': int(ano),
                'turma': str(turma),
                'nome': f"{ano_nome} - Turma {turma}",
                'total_alunos': len(df_grupo),
                'estatisticas_medidas_por_aluno': {
                    'maximo': int(medidas_alunos.max()),
                    'minimo': int(medidas_alunos.min()),
                    'media': round(float(medidas_alunos.mean()), 2),
                    'mediana': float(medidas_alunos.median()),
                    'desvio_padrao': round(float(medidas_alunos.std()), 2),
                    'p25': float(medidas_alunos.quantile(0.25)),
                    'p75': float(medidas_alunos.quantile(0.75))
                }
            }
            
            stats_por_turma[chave] = stats
        
        # Limpar coluna temporária
        self.df.drop(columns=['_total_medidas'], inplace=True)
        
        self.logger.info(f"✓ Estatísticas por aluno: {len(stats_por_turma)} turmas")
        return stats_por_turma
    
    def analise_alineas_detalhada(self) -> Dict[str, Dict]:
        """NOVA: Análise detalhada de TODAS as alíneas por ano."""
        self.logger.info("Executando análise detalhada de alíneas...")
        
        ano_col = self.grouping_cols['ano']
        if ano_col not in self.df.columns:
            return {}
        
        stats_alineas = {}
        
        # Por cada ano
        for ano in sorted(self.df[ano_col].dropna().unique()):
            df_ano = self.df[self.df[ano_col] == ano]
            total = len(df_ano)
            
            ano_nome = "Pré-Escolar" if ano == 0 else f"{int(ano)}º Ano"
            
            stats_alineas[ano_nome] = {
                'total_alunos': total,
                'universais': {},
                'seletivas': {},
                'adicionais': {}
            }
            
            # Todas as alíneas
            for tipo in ['universais', 'seletivas', 'adicionais']:
                for nome, coluna in self.column_mappings[tipo].items():
                    if coluna in df_ano.columns:
                        n = int(df_ano[coluna].sum())
                        stats_alineas[ano_nome][tipo][nome] = {
                            'n': n,
                            'percentagem': calculate_percentage(n, total)
                        }
        
        self.logger.info(f"✓ Análise de alíneas: {len(stats_alineas)} anos")
        return stats_alineas
    
    def analise_terapias_completa(self) -> Dict[str, Any]:
        """NOVA: Análise completa de terapias (por ano, turma, sexo)."""
        self.logger.info("Executando análise completa de terapias...")
        
        terapias_cols = {
            'Terapia da Fala': 'terapia_da_fala',
            'Terapia Ocupacional': 'terapia_ocupacional',
            'Psicomotricidade': 'psicomotricidade',
            'Fisioterapia': 'fisioterapia',
            'Psicologia': 'psicologia'
        }
        
        ano_col = self.grouping_cols['ano']
        turma_col = self.grouping_cols['turma']
        sexo_col = self.grouping_cols['sexo']
        
        stats_terapias = {
            'global': {},
            'por_ano': {},
            'por_sexo': {},
            'por_ano_turma': {}
        }
        
        # Global
        total_alunos = len(self.df)
        for nome, coluna in terapias_cols.items():
            if coluna in self.df.columns:
                n = int(self.df[coluna].sum())
                stats_terapias['global'][nome] = {
                    'n': n,
                    'percentagem': calculate_percentage(n, total_alunos)
                }
        
        # Por ano
        if ano_col in self.df.columns:
            for ano in sorted(self.df[ano_col].dropna().unique()):
                df_ano = self.df[self.df[ano_col] == ano]
                total = len(df_ano)
                ano_nome = "Pré-Escolar" if ano == 0 else f"{int(ano)}º Ano"
                
                stats_terapias['por_ano'][ano_nome] = {}
                for nome, coluna in terapias_cols.items():
                    if coluna in df_ano.columns:
                        n = int(df_ano[coluna].sum())
                        stats_terapias['por_ano'][ano_nome][nome] = {
                            'n': n,
                            'percentagem': calculate_percentage(n, total)
                        }
        
        # Por sexo
        if sexo_col in self.df.columns:
            for sexo in sorted(self.df[sexo_col].dropna().unique()):
                df_sexo = self.df[self.df[sexo_col] == sexo]
                total = len(df_sexo)
                
                stats_terapias['por_sexo'][str(sexo)] = {}
                for nome, coluna in terapias_cols.items():
                    if coluna in df_sexo.columns:
                        n = int(df_sexo[coluna].sum())
                        stats_terapias['por_sexo'][str(sexo)][nome] = {
                            'n': n,
                            'percentagem': calculate_percentage(n, total)
                        }
        
        self.logger.info("✓ Análise de terapias completa")
        return stats_terapias
    
    def analise_sexo_detalhado(self) -> Dict[str, Any]:
        """NOVA: Análise DETALHADA por sexo (incluindo alíneas)."""
        self.logger.info("Executando análise detalhada por sexo...")
        
        sexo_col = self.grouping_cols['sexo']
        if sexo_col not in self.df.columns:
            return {}
        
        stats_sexo = {}
        
        for sexo in sorted(self.df[sexo_col].dropna().unique()):
            df_sexo = self.df[self.df[sexo_col] == sexo]
            total = len(df_sexo)
            
            stats_sexo[str(sexo)] = {
                'total_alunos': total,
                'medidas_detalhadas': {
                    'universais': {},
                    'seletivas': {},
                    'adicionais': {}
                }
            }
            
            # Todas as alíneas por sexo
            for tipo in ['universais', 'seletivas', 'adicionais']:
                for nome, coluna in self.column_mappings[tipo].items():
                    if coluna in df_sexo.columns:
                        n = int(df_sexo[coluna].sum())
                        stats_sexo[str(sexo)]['medidas_detalhadas'][tipo][nome] = {
                            'n': n,
                            'percentagem': calculate_percentage(n, total)
                        }
        
        self.logger.info("✓ Análise detalhada por sexo")
        return stats_sexo
    
    def generate_rankings(self) -> Dict[str, List[Dict]]:
        """Gera rankings de escolas."""
        self.logger.info("Gerando rankings...")
        
        escola_col = self.grouping_cols['escola']
        if escola_col not in self.df.columns:
            return {}
        
        rankings = {}
        
        for nome_medida, coluna in self.column_mappings['principais'].items():
            if coluna in self.df.columns:
                ranking_data = []
                
                for codigo in sorted(self.df[escola_col].unique()):
                    df_escola = self.df[self.df[escola_col] == codigo]
                    n = int(df_escola[coluna].sum())
                    total = len(df_escola)
                    pct = calculate_percentage(n, total)
                    
                    ranking_data.append({
                        'codigo': int(codigo),
                        'nome': self.escola_mapping.get(int(codigo), f"Escola {codigo}"),
                        'total_alunos': total,
                        'alunos_com_medida': n,
                        'percentagem': pct
                    })
                
                ranking_data.sort(key=lambda x: x['percentagem'], reverse=True)
                
                for i, item in enumerate(ranking_data, 1):
                    item['rank'] = i
                
                rankings[nome_medida] = ranking_data
        
        return rankings
    
    def generate_comparisons(self) -> Dict[str, Any]:
        """Gera comparações entre escolas e agrupamento."""
        self.logger.info("Gerando comparações...")
        
        comparisons = {}
        stats_agrupamento = self.analise_global()
        stats_escolas = self.analise_por_escola()
        
        for codigo, stats_escola in stats_escolas.items():
            escola_comparisons = {}
            
            for nome_medida in stats_agrupamento['medidas_principais'].keys():
                pct_escola = stats_escola['medidas_principais'].get(nome_medida, {}).get('percentagem', 0)
                pct_agrupamento = stats_agrupamento['medidas_principais'][nome_medida]['percentagem']
                
                diferenca = pct_escola - pct_agrupamento
                
                escola_comparisons[nome_medida] = {
                    'escola': pct_escola,
                    'agrupamento': pct_agrupamento,
                    'diferenca': round(diferenca, 2),
                    'superior': pct_escola > pct_agrupamento
                }
            
            comparisons[stats_escola['nome']] = escola_comparisons
        
        return comparisons
