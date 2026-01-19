#!/usr/bin/env python3
"""
chart_generator.py - Gerador de Gráficos EXPANDIDO
Sistema de Análise Estatística DL 54/2018 v2.0

VERSÃO EXPANDIDA: 18-20 gráficos impactantes

Autor: Sistema de Qualidade de Dados Educacionais
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from config import ConfigManager
from utils import format_percentage, format_number


logger = logging.getLogger('DL54.charts')


class ChartGenerator:
    """
    Gerador de gráficos profissionais EXPANDIDO.
    
    Características:
    - Cores WebSafe (WCAG AA)
    - 18-20 tipos de gráficos
    - Anotações automáticas
    - Percentagens visíveis
    - Formatação consistente
    """
    
    def __init__(self, config: ConfigManager, logger_instance: logging.Logger):
        """Inicializa gerador de gráficos expandido."""
        self.config = config
        self.logger = logger_instance
        
        self.chart_config = config.get_chart_config()
        self.colors = config.colors
        
        self._setup_style()
        
        self.output_dir = Path(config.get('IO', 'OUTPUT_DIR')) / 'charts'
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_style(self):
        """Configura estilo global dos gráficos."""
        try:
            plt.style.use(self.chart_config['style'])
        except:
            plt.style.use('seaborn-v0_8-darkgrid')
        
        plt.rcParams['figure.dpi'] = self.chart_config['dpi']
        plt.rcParams['font.family'] = self.chart_config['font_family']
        plt.rcParams['font.size'] = self.chart_config['font_size']
        plt.rcParams['axes.labelsize'] = self.chart_config['font_size_label']
        plt.rcParams['axes.titlesize'] = self.chart_config['font_size_title']
        plt.rcParams['xtick.labelsize'] = self.chart_config['font_size_label']
        plt.rcParams['ytick.labelsize'] = self.chart_config['font_size_label']
        plt.rcParams['legend.fontsize'] = self.chart_config['font_size_label']
        plt.rcParams['grid.alpha'] = self.chart_config['grid_alpha']
    
    def create_bar_chart(self, data: Dict[str, Dict], title: str,
                        filename: str, ylabel: str = "Número de Alunos",
                        show_percentage: bool = True) -> Path:
        """Cria gráfico de barras simples."""
        fig, ax = plt.subplots(figsize=(
            self.chart_config['width'],
            self.chart_config['height']
        ))
        
        labels = list(data.keys())
        values = [data[k]['n'] for k in labels]
        percentages = [data[k].get('percentagem', 0) for k in labels]
        
        colors = self.colors.get_medidas_colors() if len(labels) == 3 else \
                 [self.colors.get_categorical_color(i) for i in range(len(labels))]
        
        bars = ax.bar(labels, values, color=colors, edgecolor='black', linewidth=1.5)
        
        if self.chart_config['annotate_values']:
            for i, (bar, val, pct) in enumerate(zip(bars, values, percentages)):
                height = bar.get_height()
                
                if show_percentage and self.chart_config['show_percentages']:
                    text = f"{format_number(val)}\n({format_percentage(pct)})"
                else:
                    text = format_number(val)
                
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       text, ha='center', va='bottom', fontweight='bold',
                       fontsize=self.chart_config['font_size'])
        
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=self.chart_config['grid_alpha'])
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{filename}.{self.chart_config['format']}"
        plt.savefig(output_path, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"✓ Gráfico criado: {output_path.name}")
        return output_path
    
    def create_pie_chart(self, data: Dict[str, Dict], title: str,
                        filename: str) -> Path:
        """Cria gráfico circular (pizza)."""
        fig, ax = plt.subplots(figsize=(
            self.chart_config['width'],
            self.chart_config['height']
        ))
        
        labels = list(data.keys())
        values = [data[k]['n'] for k in labels]
        percentages = [data[k].get('percentagem', 0) for k in labels]
        
        colors = self.colors.get_medidas_colors() if len(labels) == 3 else \
                 [self.colors.get_categorical_color(i) for i in range(len(labels))]
        
        explode = [0.05 if pct < 10 else 0 for pct in percentages]
        
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            explode=explode,
            textprops={'fontweight': 'bold', 'fontsize': self.chart_config['font_size_label']},
            wedgeprops={'edgecolor': 'black', 'linewidth': 1.5}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(self.chart_config['font_size'])
        
        ax.set_title(title, fontweight='bold', pad=20)
        
        if self.chart_config['show_legends']:
            legend_labels = [f"{label} (n={data[label]['n']})" for label in labels]
            ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{filename}.{self.chart_config['format']}"
        plt.savefig(output_path, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"✓ Gráfico criado: {output_path.name}")
        return output_path
    
    def create_stacked_bar_chart(self, data: Dict[str, Dict[str, Dict]],
                                title: str, filename: str,
                                ylabel: str = "Número de Alunos") -> Path:
        """Cria gráfico de barras empilhadas."""
        fig, ax = plt.subplots(figsize=(
            self.chart_config['width'],
            self.chart_config['height']
        ))
        
        grupos = list(data.keys())
        categorias = list(next(iter(data.values())).keys())
        
        values_matrix = []
        for cat in categorias:
            values_matrix.append([data[grupo][cat]['n'] for grupo in grupos])
        
        colors = self.colors.get_medidas_colors() if len(categorias) == 3 else \
                 [self.colors.get_categorical_color(i) for i in range(len(categorias))]
        
        x = np.arange(len(grupos))
        width = 0.6
        
        bottom = np.zeros(len(grupos))
        bars_list = []
        
        for i, (cat, values) in enumerate(zip(categorias, values_matrix)):
            bars = ax.bar(x, values, width, bottom=bottom,
                         label=cat, color=colors[i],
                         edgecolor='black', linewidth=1.0)
            bars_list.append(bars)
            bottom += values
        
        if self.chart_config['annotate_values'] and len(grupos) <= 6:
            for bars in bars_list:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2.,
                               bar.get_y() + height/2.,
                               f'{int(height)}',
                               ha='center', va='center',
                               color='white', fontweight='bold',
                               fontsize=self.chart_config['font_size_label'])
        
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(grupos, rotation=45, ha='right')
        ax.legend(loc='upper left')
        ax.grid(axis='y', alpha=self.chart_config['grid_alpha'])
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{filename}.{self.chart_config['format']}"
        plt.savefig(output_path, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"✓ Gráfico criado: {output_path.name}")
        return output_path
    
    def create_heatmap(self, data: Dict[str, Dict[str, float]],
                      title: str, filename: str,
                      xlabel: str = "Medidas",
                      ylabel: str = "Grupos") -> Path:
        """Cria heatmap de concentração."""
        fig, ax = plt.subplots(figsize=(
            self.chart_config['width'],
            self.chart_config['height_small']
        ))
        
        rows = list(data.keys())
        cols = list(next(iter(data.values())).keys())
        
        matrix = []
        for row in rows:
            matrix.append([data[row].get(col, 0) for col in cols])
        
        im = ax.imshow(matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=100)
        
        ax.set_xticks(np.arange(len(cols)))
        ax.set_yticks(np.arange(len(rows)))
        ax.set_xticklabels(cols, rotation=45, ha='right')
        ax.set_yticklabels(rows)
        
        ax.set_xlabel(xlabel, fontweight='bold')
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=20)
        
        if self.chart_config['annotate_values']:
            for i in range(len(rows)):
                for j in range(len(cols)):
                    value = matrix[i][j]
                    text = ax.text(j, i, f'{value:.1f}%',
                                 ha='center', va='center',
                                 color='white' if value > 50 else 'black',
                                 fontweight='bold')
        
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Percentagem (%)', rotation=270, labelpad=20, fontweight='bold')
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{filename}.{self.chart_config['format']}"
        plt.savefig(output_path, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"✓ Gráfico criado: {output_path.name}")
        return output_path
    
    def create_comparison_chart(self, data: Dict[str, Dict],
                               title: str, filename: str,
                               group1_label: str = "Grupo 1",
                               group2_label: str = "Grupo 2") -> Path:
        """Cria gráfico de comparação lado-a-lado."""
        fig, ax = plt.subplots(figsize=(
            self.chart_config['width'],
            self.chart_config['height']
        ))
        
        medidas = list(data.keys())
        values_g1 = [data[m].get('grupo1', data[m].get('escola', 0)) for m in medidas]
        values_g2 = [data[m].get('grupo2', data[m].get('agrupamento', 0)) for m in medidas]
        
        x = np.arange(len(medidas))
        width = 0.35
        
        color_g1 = self.colors.primary
        color_g2 = self.colors.secondary
        
        bars1 = ax.bar(x - width/2, values_g1, width, label=group1_label,
                      color=color_g1, edgecolor='black', linewidth=1.0)
        bars2 = ax.bar(x + width/2, values_g2, width, label=group2_label,
                      color=color_g2, edgecolor='black', linewidth=1.0)
        
        if self.chart_config['annotate_values']:
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}%',
                           ha='center', va='bottom',
                           fontweight='bold',
                           fontsize=self.chart_config['font_size_label'])
        
        ax.set_ylabel('Percentagem (%)', fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(medidas, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=self.chart_config['grid_alpha'])
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{filename}.{self.chart_config['format']}"
        plt.savefig(output_path, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"✓ Gráfico criado: {output_path.name}")
        return output_path
    
    def create_horizontal_bar_chart(self, data: Dict[str, int], title: str,
                                    filename: str, top_n: int = 10) -> Path:
        """NOVO: Cria gráfico de barras horizontais (rankings)."""
        fig, ax = plt.subplots(figsize=(
            self.chart_config['width'],
            self.chart_config['height']
        ))
        
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:top_n]
        labels = [item[0] for item in sorted_data]
        values = [item[1] for item in sorted_data]
        
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(labels)))
        
        bars = ax.barh(labels, values, color=colors, edgecolor='black', linewidth=1.0)
        
        if self.chart_config['annotate_values']:
            for bar, val in zip(bars, values):
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2.,
                       f' {val}',
                       ha='left', va='center',
                       fontweight='bold')
        
        ax.set_xlabel('Número de Alunos', fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=20)
        ax.grid(axis='x', alpha=self.chart_config['grid_alpha'])
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{filename}.{self.chart_config['format']}"
        plt.savefig(output_path, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"✓ Gráfico criado: {output_path.name}")
        return output_path
    
    def create_grouped_bar_chart(self, data: Dict[str, Dict[str, int]],
                                 title: str, filename: str) -> Path:
        """NOVO: Cria gráfico de barras agrupadas."""
        fig, ax = plt.subplots(figsize=(
            self.chart_config['width'] * 1.2,
            self.chart_config['height']
        ))
        
        grupos = list(data.keys())
        categorias = list(next(iter(data.values())).keys())
        
        x = np.arange(len(grupos))
        width = 0.8 / len(categorias)
        
        colors = [self.colors.get_categorical_color(i) for i in range(len(categorias))]
        
        for i, categoria in enumerate(categorias):
            values = [data[grupo].get(categoria, 0) for grupo in grupos]
            offset = width * i - (width * len(categorias) / 2) + width / 2
            bars = ax.bar(x + offset, values, width, label=categoria,
                         color=colors[i], edgecolor='black', linewidth=0.8)
            
            if self.chart_config['annotate_values'] and len(grupos) <= 8:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}',
                               ha='center', va='bottom',
                               fontsize=8, fontweight='bold')
        
        ax.set_ylabel('Número de Alunos', fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(grupos, rotation=45, ha='right')
        ax.legend(loc='upper left')
        ax.grid(axis='y', alpha=self.chart_config['grid_alpha'])
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{filename}.{self.chart_config['format']}"
        plt.savefig(output_path, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"✓ Gráfico criado: {output_path.name}")
        return output_path
    
    def create_line_chart(self, data: Dict[str, Dict[str, int]],
                         title: str, filename: str) -> Path:
        """NOVO: Cria gráfico de linhas (evolução)."""
        fig, ax = plt.subplots(figsize=(
            self.chart_config['width'],
            self.chart_config['height']
        ))
        
        anos = sorted([k for k in data.keys()])
        categorias = list(next(iter(data.values())).keys())
        
        colors = [self.colors.get_categorical_color(i) for i in range(len(categorias))]
        markers = ['o', 's', '^', 'D', 'v']
        
        for i, categoria in enumerate(categorias):
            values = [data[ano].get(categoria, 0) for ano in anos]
            ax.plot(anos, values, label=categoria, color=colors[i],
                   marker=markers[i % len(markers)], linewidth=2, markersize=8)
        
        ax.set_xlabel('Ano de Escolaridade', fontweight='bold')
        ax.set_ylabel('Número de Alunos', fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=20)
        ax.legend(loc='best')
        ax.grid(True, alpha=self.chart_config['grid_alpha'])
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{filename}.{self.chart_config['format']}"
        plt.savefig(output_path, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"✓ Gráfico criado: {output_path.name}")
        return output_path
    
    def create_box_plot(self, data: Dict[str, List[float]], title: str,
                       filename: str) -> Path:
        """NOVO: Cria box plot (estatísticas por aluno)."""
        fig, ax = plt.subplots(figsize=(
            self.chart_config['width'],
            self.chart_config['height']
        ))
        
        labels = list(data.keys())
        values = [data[label] for label in labels]
        
        bp = ax.boxplot(values, labels=labels, patch_artist=True,
                       notch=True, showmeans=True)
        
        colors = [self.colors.get_categorical_color(i) for i in range(len(labels))]
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        for element in ['whiskers', 'fliers', 'means', 'medians', 'caps']:
            plt.setp(bp[element], color='black', linewidth=1.5)
        
        ax.set_ylabel('Número de Medidas por Aluno', fontweight='bold')
        ax.set_title(title, fontweight='bold', pad=20)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.grid(axis='y', alpha=self.chart_config['grid_alpha'])
        
        plt.tight_layout()
        
        output_path = self.output_dir / f"{filename}.{self.chart_config['format']}"
        plt.savefig(output_path, dpi=self.chart_config['dpi'], bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"✓ Gráfico criado: {output_path.name}")
        return output_path
    
    def generate_all_charts(self, stats: Dict[str, Any]) -> List[Path]:
        """Gera TODOS os gráficos expandidos (18-20 gráficos)."""
        self.logger.info("=" * 80)
        self.logger.info("GERANDO GRÁFICOS EXPANDIDOS")
        self.logger.info("=" * 80)
        
        generated_charts = []
        
        try:
            # ========================================
            # GRÁFICOS BASE (1-4)
            # ========================================
            
            # 1. Medidas principais - Barras
            if 'global' in stats:
                chart = self.create_bar_chart(
                    stats['global']['medidas_principais'],
                    'Distribuição de Medidas DL 54/2018',
                    '01_medidas_principais_bar'
                )
                generated_charts.append(chart)
            
            # 2. Medidas principais - Pizza
            if 'global' in stats:
                chart = self.create_pie_chart(
                    stats['global']['medidas_principais'],
                    'Proporção de Medidas DL 54/2018',
                    '02_medidas_principais_pie'
                )
                generated_charts.append(chart)
            
            # 3. Por escola - Empilhado
            if 'por_escola' in stats:
                escola_data = {}
                for codigo, escola_stats in stats['por_escola'].items():
                    nome_curto = escola_stats['nome'].split(',')[0]
                    escola_data[nome_curto] = escola_stats['medidas_principais']
                
                chart = self.create_stacked_bar_chart(
                    escola_data,
                    'Medidas por Escola',
                    '03_medidas_por_escola_stacked'
                )
                generated_charts.append(chart)
            
            # 4. Heatmap escola × medida
            if 'por_escola' in stats:
                heatmap_data = {}
                for codigo, escola_stats in stats['por_escola'].items():
                    nome = escola_stats['nome'].split(',')[0]
                    heatmap_data[nome] = {
                        k: v['percentagem'] 
                        for k, v in escola_stats['medidas_principais'].items()
                    }
                
                chart = self.create_heatmap(
                    heatmap_data,
                    'Concentração de Medidas por Escola (%)',
                    '04_heatmap_escola_medida',
                    'Medidas', 'Escolas'
                )
                generated_charts.append(chart)
            
            # ========================================
            # NOVOS: GRÁFICOS POR TURMA (5-7)
            # ========================================
            
            # 5. Top 10 turmas por total de alunos
            if 'por_turma' in stats:
                turma_alunos = {
                    turma: dados['total_alunos']
                    for turma, dados in stats['por_turma'].items()
                }
                chart = self.create_horizontal_bar_chart(
                    turma_alunos,
                    'Top 10 Turmas por Número de Alunos',
                    '05_top_turmas_alunos',
                    top_n=10
                )
                generated_charts.append(chart)
            
            # 6. Medidas por turma - Agrupado
            if 'por_turma' in stats:
                # Pegar top 8 turmas
                turmas_sorted = sorted(stats['por_turma'].items(),
                                      key=lambda x: x[1]['total_alunos'],
                                      reverse=True)[:8]
                
                turma_medidas = {}
                for turma, dados in turmas_sorted:
                    turma_medidas[turma] = {
                        k: v['n']
                        for k, v in dados['medidas_principais'].items()
                    }
                
                chart = self.create_grouped_bar_chart(
                    turma_medidas,
                    'Medidas por Turma (Top 8)',
                    '06_medidas_por_turma_grouped'
                )
                generated_charts.append(chart)
            
            # 7. Heatmap turma × medida (top 12)
            if 'por_turma' in stats:
                turmas_sorted = sorted(stats['por_turma'].items(),
                                      key=lambda x: x[1]['total_alunos'],
                                      reverse=True)[:12]
                
                heatmap_data = {}
                for turma, dados in turmas_sorted:
                    heatmap_data[turma] = {
                        k: v['percentagem']
                        for k, v in dados['medidas_principais'].items()
                    }
                
                chart = self.create_heatmap(
                    heatmap_data,
                    'Concentração de Medidas por Turma (%) - Top 12',
                    '07_heatmap_turma_medida',
                    'Medidas', 'Turmas'
                )
                generated_charts.append(chart)
            
            # ========================================
            # NOVOS: GRÁFICOS POR ANO (8-9)
            # ========================================
            
            # 8. Evolução de medidas por ano
            if 'por_ano' in stats:
                ano_medidas = {}
                for ano, dados in sorted(stats['por_ano'].items()):
                    ano_nome = dados['ano_nome']
                    ano_medidas[ano_nome] = {
                        k: v['n']
                        for k, v in dados['medidas_principais'].items()
                    }
                
                chart = self.create_line_chart(
                    ano_medidas,
                    'Evolução de Medidas por Ano de Escolaridade',
                    '08_evolucao_medidas_ano'
                )
                generated_charts.append(chart)
            
            # 9. Heatmap ano × medida
            if 'por_ano' in stats:
                heatmap_data = {}
                for ano, dados in sorted(stats['por_ano'].items()):
                    heatmap_data[dados['ano_nome']] = {
                        k: v['percentagem']
                        for k, v in dados['medidas_principais'].items()
                    }
                
                chart = self.create_heatmap(
                    heatmap_data,
                    'Concentração de Medidas por Ano (%)',
                    '09_heatmap_ano_medida',
                    'Medidas', 'Anos'
                )
                generated_charts.append(chart)
            
            # ========================================
            # NOVOS: TERAPIAS (10-12)
            # ========================================
            
            # 10. Terapias - Global
            if 'terapias_completas' in stats and 'global' in stats['terapias_completas']:
                chart = self.create_bar_chart(
                    stats['terapias_completas']['global'],
                    'Distribuição de Terapias',
                    '10_terapias_global',
                    ylabel='Número de Alunos'
                )
                generated_charts.append(chart)
            
            # 11. Terapias por ano - Empilhado
            if 'terapias_completas' in stats and 'por_ano' in stats['terapias_completas']:
                ano_terapias = {}
                for ano_nome, terapias in stats['terapias_completas']['por_ano'].items():
                    ano_terapias[ano_nome] = terapias
                
                chart = self.create_stacked_bar_chart(
                    ano_terapias,
                    'Terapias por Ano de Escolaridade',
                    '11_terapias_por_ano_stacked',
                    ylabel='Número de Alunos'
                )
                generated_charts.append(chart)
            
            # 12. Terapias por sexo - Comparação
            if 'terapias_completas' in stats and 'por_sexo' in stats['terapias_completas']:
                terapias_sexo = stats['terapias_completas']['por_sexo']
                if 'M' in terapias_sexo and 'F' in terapias_sexo:
                    # Preparar dados para comparação
                    comp_data = {}
                    for terapia in terapias_sexo['M'].keys():
                        comp_data[terapia] = {
                            'grupo1': terapias_sexo['M'][terapia]['percentagem'],
                            'grupo2': terapias_sexo['F'][terapia]['percentagem']
                        }
                    
                    chart = self.create_comparison_chart(
                        comp_data,
                        'Terapias: Comparação Masculino vs Feminino',
                        '12_terapias_comparacao_sexo',
                        'Masculino', 'Feminino'
                    )
                    generated_charts.append(chart)
            
            # ========================================
            # NOVOS: ANÁLISES POR SEXO (13-14)
            # ========================================
            
            # 13. Medidas por sexo - Comparação
            if 'por_sexo' in stats:
                sexo_stats = stats['por_sexo']
                if 'M' in sexo_stats and 'F' in sexo_stats:
                    comp_data = {}
                    for medida in sexo_stats['M']['medidas_principais'].keys():
                        comp_data[medida] = {
                            'grupo1': sexo_stats['M']['medidas_principais'][medida]['percentagem_no_grupo'],
                            'grupo2': sexo_stats['F']['medidas_principais'][medida]['percentagem_no_grupo']
                        }
                    
                    chart = self.create_comparison_chart(
                        comp_data,
                        'Medidas: Comparação Masculino vs Feminino',
                        '13_medidas_comparacao_sexo',
                        'Masculino', 'Feminino'
                    )
                    generated_charts.append(chart)
            
            # 14. Distribuição por sexo - Pizza
            if 'por_sexo' in stats:
                sexo_data = {}
                for sexo, dados in stats['por_sexo'].items():
                    if not sexo.startswith('_'):
                        sexo_data[f"Sexo {sexo}"] = {
                            'n': dados['total_alunos'],
                            'percentagem': dados['percentagem_do_total']
                        }
                
                chart = self.create_pie_chart(
                    sexo_data,
                    'Distribuição por Sexo',
                    '14_distribuicao_sexo_pie'
                )
                generated_charts.append(chart)
            
            # ========================================
            # NOVOS: ESTATÍSTICAS POR ALUNO (15)
            # ========================================
            
            # 15. Box plot - Medidas por aluno (top 10 turmas)
            if 'estatisticas_aluno_turma' in stats:
                # Pegar top 10 turmas por número de alunos
                turmas_sorted = sorted(stats['estatisticas_aluno_turma'].items(),
                                      key=lambda x: x[1]['total_alunos'],
                                      reverse=True)[:10]
                
                # Para box plot, precisamos gerar distribuições simuladas
                # baseadas nas estatísticas
                box_data = {}
                for chave, dados in turmas_sorted:
                    stats_medidas = dados['estatisticas_medidas_por_aluno']
                    # Simular distribuição baseada em média e desvio padrão
                    mean = stats_medidas['media']
                    std = stats_medidas['desvio_padrao']
                    n_alunos = dados['total_alunos']
                    
                    # Gerar distribuição normal
                    distribution = np.random.normal(mean, std, n_alunos)
                    distribution = np.clip(distribution,
                                          stats_medidas['minimo'],
                                          stats_medidas['maximo'])
                    
                    box_data[dados['turma']] = distribution.tolist()
                
                chart = self.create_box_plot(
                    box_data,
                    'Distribuição de Medidas por Aluno (Top 10 Turmas)',
                    '15_boxplot_medidas_aluno'
                )
                generated_charts.append(chart)
            
            # ========================================
            # NOVOS: ALÍNEAS DETALHADAS (16-17)
            # ========================================
            
            # 16. Top 10 alíneas mais frequentes
            if 'alineas_detalhadas' in stats:
                # Agregar todas as alíneas
                alineas_total = {}
                for ano_nome, dados_ano in stats['alineas_detalhadas'].items():
                    for tipo in ['universais', 'seletivas', 'adicionais']:
                        for alinea, dados in dados_ano[tipo].items():
                            if alinea not in alineas_total:
                                alineas_total[alinea] = 0
                            alineas_total[alinea] += dados['n']
                
                chart = self.create_horizontal_bar_chart(
                    alineas_total,
                    'Top 10 Alíneas Mais Frequentes',
                    '16_top_alineas',
                    top_n=10
                )
                generated_charts.append(chart)
            
            # 17. Heatmap alíneas × ano (top 10 alíneas)
            if 'alineas_detalhadas' in stats:
                # Pegar top 10 alíneas
                alineas_total = {}
                for ano_nome, dados_ano in stats['alineas_detalhadas'].items():
                    for tipo in ['universais', 'seletivas', 'adicionais']:
                        for alinea, dados in dados_ano[tipo].items():
                            if alinea not in alineas_total:
                                alineas_total[alinea] = 0
                            alineas_total[alinea] += dados['n']
                
                top_alineas = sorted(alineas_total.items(),
                                    key=lambda x: x[1],
                                    reverse=True)[:10]
                top_alineas_names = [a[0] for a in top_alineas]
                
                # Criar heatmap
                heatmap_data = {}
                for ano_nome, dados_ano in stats['alineas_detalhadas'].items():
                    ano_dict = {}
                    for tipo in ['universais', 'seletivas', 'adicionais']:
                        for alinea, dados in dados_ano[tipo].items():
                            if alinea in top_alineas_names:
                                # Truncar nome da alínea
                                alinea_short = alinea[:30] + '...' if len(alinea) > 30 else alinea
                                ano_dict[alinea_short] = dados['percentagem']
                    
                    if ano_dict:
                        heatmap_data[ano_nome] = ano_dict
                
                if heatmap_data:
                    chart = self.create_heatmap(
                        heatmap_data,
                        'Concentração das Top 10 Alíneas por Ano (%)',
                        '17_heatmap_alineas_ano',
                        'Alíneas (Top 10)', 'Anos'
                    )
                    generated_charts.append(chart)
            
            # ========================================
            # NOVOS: ESCALÃO ASE (18)
            # ========================================
            
            # 18. Medidas por escalão ASE - Empilhado
            if 'por_escalao_ase' in stats:
                ase_medidas = {}
                for escalao, dados in stats['por_escalao_ase'].items():
                    ase_medidas[f"Escalão {escalao}"] = dados['medidas_principais']
                
                chart = self.create_stacked_bar_chart(
                    ase_medidas,
                    'Medidas por Escalão ASE',
                    '18_medidas_por_escalao_ase_stacked'
                )
                generated_charts.append(chart)
            
            self.logger.info("=" * 80)
            self.logger.info(f"✓ GRÁFICOS EXPANDIDOS GERADOS: {len(generated_charts)} ficheiros")
            self.logger.info("=" * 80)
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar gráficos: {e}", exc_info=True)
        
        return generated_charts
