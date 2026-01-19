#!/usr/bin/env python3
"""
config.py - Gestão Centralizada de Configuração
Sistema de Análise Estatística DL 54/2018 v2.0

Este módulo gere todas as configurações do sistema de forma centralizada,
proporcionando acesso fácil e validado a todos os parâmetros.

Autor: Sistema de Qualidade de Dados Educacionais
"""

import configparser
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class ConfigurationError(Exception):
    """Exceção para erros de configuração"""
    pass


class ColorPalette:
    """Paleta de cores WebSafe com alto contraste"""

    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self._load_colors()

    def _load_colors(self):
        """Carrega paleta de cores da configuração"""
        # Cores principais
        self.primary = self._get_color('GRAFICOS', 'COLOR_PRIMARY', '#003366')
        self.secondary = self._get_color('GRAFICOS', 'COLOR_SECONDARY', '#006699')
        self.success = self._get_color('GRAFICOS', 'COLOR_SUCCESS', '#009933')
        self.warning = self._get_color('GRAFICOS', 'COLOR_WARNING', '#FF9900')
        self.danger = self._get_color('GRAFICOS', 'COLOR_DANGER', '#CC0000')
        self.info = self._get_color('GRAFICOS', 'COLOR_INFO', '#0099CC')

        # Paleta categórica
        palette_str = self.config.get('GRAFICOS', 'COLOR_PALETTE',
                                      fallback='#003366,#CC0000,#009933,#FF9900')
        self.categorical = [c.strip() for c in palette_str.split(',')]

        # Cores para medidas DL 54/2018
        self.medidas_universais = self._get_color('GRAFICOS', 'COLOR_MEDIDAS_UNIVERSAIS', '#0099CC')
        self.medidas_seletivas = self._get_color('GRAFICOS', 'COLOR_MEDIDAS_SELETIVAS', '#FF9900')
        self.medidas_adicionais = self._get_color('GRAFICOS', 'COLOR_MEDIDAS_ADICIONAIS', '#CC0000')

        # Cores para heatmap
        self.heatmap_low = self._get_color('CORES_HEATMAP', 'COLOR_LOW', '#009933')
        self.heatmap_mid = self._get_color('CORES_HEATMAP', 'COLOR_MID', '#FFFF00')
        self.heatmap_high = self._get_color('CORES_HEATMAP', 'COLOR_HIGH', '#CC0000')

    def _get_color(self, section: str, key: str, fallback: str) -> str:
        """Obtém cor com fallback"""
        return self.config.get(section, key, fallback=fallback)

    def get_medidas_colors(self) -> List[str]:
        """Retorna cores para os três tipos de medidas"""
        return [
            self.medidas_universais,
            self.medidas_seletivas,
            self.medidas_adicionais
        ]

    def get_heatmap_colors(self) -> List[str]:
        """Retorna cores para heatmap"""
        return [self.heatmap_low, self.heatmap_mid, self.heatmap_high]

    def get_categorical_color(self, index: int) -> str:
        """Retorna cor categórica pelo índice (com wrap-around)"""
        return self.categorical[index % len(self.categorical)]


class ConfigManager:
    """
    Gestor centralizado de configuração com validação e acesso otimizado.

    Responsabilidades:
    - Carregar e validar ficheiro de configuração
    - Fornecer acesso tipo-seguro aos parâmetros
    - Gerir paleta de cores
    - Validar estrutura de configuração
    """

    def __init__(self, config_path: str = 'config/config.ini'):
        """
        Inicializa o gestor de configuração.

        Args:
            config_path: Caminho para o ficheiro de configuração

        Raises:
            ConfigurationError: Se o ficheiro não existe ou é inválido
        """
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()

        # Carregar configuração
        self._load_config()

        # Validar configuração
        self._validate_config()

        # Inicializar paleta de cores
        self.colors = ColorPalette(self.config)

        # Cache para valores frequentemente acedidos
        self._cache: Dict[str, Any] = {}

    def _load_config(self):
        """Carrega ficheiro de configuração"""
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Ficheiro de configuração não encontrado: {self.config_path}"
            )

        try:
            self.config.read(self.config_path, encoding='utf-8')
        except Exception as e:
            raise ConfigurationError(f"Erro ao ler configuração: {e}")

    def _validate_config(self):
        """Valida estrutura da configuração"""
        required_sections = [
            'IO', 'ESCOLAS', 'COLUNAS_DL54', 'RELATORIOS',
            'GRAFICOS', 'LOGGING', 'ANALISE_ESTATISTICA'
        ]

        missing_sections = [s for s in required_sections if s not in self.config]

        if missing_sections:
            raise ConfigurationError(
                f"Secções em falta na configuração: {', '.join(missing_sections)}"
            )

    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """Obtém valor string"""
        return self.config.get(section, key, fallback=fallback)

    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """Obtém valor inteiro"""
        try:
            return self.config.getint(section, key)
        except (ValueError, configparser.NoOptionError):
            return fallback

    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Obtém valor float"""
        try:
            return self.config.getfloat(section, key)
        except (ValueError, configparser.NoOptionError):
            return fallback

    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """Obtém valor booleano"""
        try:
            return self.config.getboolean(section, key)
        except (ValueError, configparser.NoOptionError):
            return fallback

    def get_escola_mapping(self) -> Dict[int, str]:
        """
        Retorna mapeamento de códigos de escola para nomes.

        Returns:
            Dicionário {codigo: nome}
        """
        cache_key = 'escola_mapping'

        if cache_key not in self._cache:
            mapping = {}
            for k, v in self.config['ESCOLAS'].items():
                if k.isdigit():
                    mapping[int(k)] = v
            self._cache[cache_key] = mapping

        return self._cache[cache_key]

    def get_column_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Retorna todos os mapeamentos de colunas DL 54/2018.

        Returns:
            Dicionário organizado por tipo de medida
        """
        cache_key = 'column_mappings'

        if cache_key not in self._cache:
            cfg = self.config['COLUNAS_DL54']

            mappings = {
                'principais': {
                    'Medidas Universais': cfg['MEDIDAS_UNIVERSAIS'],
                    'Medidas Seletivas': cfg['MEDIDAS_SELETIVAS'],
                    'Medidas Adicionais': cfg['MEDIDAS_ADICIONAIS']
                },
                'universais': {
                    'a) Diferenciação Pedagógica': cfg['MU_DIFERENCIACAO'],
                    'b) Acomodações Curriculares': cfg['MU_ACOMODACOES'],
                    'c) Enriquecimento Curricular': cfg['MU_ENRIQUECIMENTO'],
                    'd) Promoção Comportamento Pró-social': cfg['MU_PROMOCAO_PROSOCIAL'],
                    'e) Intervenção Foco Académico': cfg['MU_INTERVENCAO_FOCO']
                },
                'seletivas': {
                    'a) Percursos Diferenciados': cfg['MS_PERCURSOS_DIFERENCIADOS'],
                    'b) ACNS': cfg['MS_ACNS'],
                    'c) Apoio Psicopedagógico': cfg['MS_APOIO_PSICOPEDAGOGICO'],
                    'd) Antecipação e Reforço': cfg['MS_ANTECIPACAO_REFORCO'],
                    'e) Apoio Tutorial': cfg['MS_APOIO_TUTORIAL']
                },
                'adicionais': {
                    'a) Frequência por Disciplinas': cfg['MA_FREQUENCIA_POR_DISCIPLINAS'],
                    'b) ACS': cfg['MA_ACS'],
                    'c) PIT': cfg['MA_PIT'],
                    'd) Metodologias Ensino Estruturado': cfg['MA_METODOLOGIAS_ENSINO'],
                    'e) Competências Autonomia': cfg['MA_COMPETENCIAS_AUTONOMIA']
                },
                'art28': self._get_art28_mappings(cfg)
            }

            self._cache[cache_key] = mappings

        return self._cache[cache_key]

    def _get_art28_mappings(self, cfg: configparser.SectionProxy) -> Dict[str, str]:
        """Obtém mapeamentos do Art. 28º"""
        return {
            'a) Diversificação Instrumentos': cfg['ART28_DIVERSIFICACAO_INSTRUMENTOS'],
            'b) Enunciados Acessíveis': cfg['ART28_ENUNCIADOS_ACESSIVEIS'],
            'c) Interpretação LGP': cfg['ART28_INTERPRETACAO_LGP'],
            'd) Produtos de Apoio': cfg['ART28_PRODUTOS_APOIO'],
            'e) Tempo Suplementar': cfg['ART28_TEMPO_SUPLEMENTAR'],
            'f) Transcrição Respostas': cfg['ART28_TRANSCRICAO'],
            'g) Leitura de Enunciados': cfg['ART28_LEITURA_ENUNCIADOS'],
            'h) Sala Separada': cfg['ART28_SALA_SEPARADA'],
            'i) Pausas Vigiadas': cfg['ART28_PAUSAS_VIGIADAS'],
            'j) Código de Cores': cfg['ART28_CODIGO_CORES']
        }

    def get_grouping_columns(self) -> Dict[str, str]:
        """
        Retorna colunas para agrupamento.

        Returns:
            Dicionário {nome_logico: nome_coluna}
        """
        cfg = self.config['COLUNAS_DL54']

        return {
            'escola': cfg['COLUNA_ESCOLA'],
            'ano': cfg['COLUNA_ANO'],
            'turma': cfg['COLUNA_TURMA'],
            'sexo': cfg['COLUNA_SEXO'],
            'idade': cfg['COLUNA_IDADE'],
            'escalao_ase': cfg['COLUNA_ESCALAO_ASE']
        }

    def get_therapy_columns(self) -> Dict[str, str]:
        """Retorna colunas de terapias"""
        cfg = self.config['COLUNAS_DL54']

        return {
            'terapias': cfg['COLUNA_TERAPIAS'],
            'terapia_fala': cfg['COLUNA_TERAPIA_FALA'],
            'terapia_ocupacional': cfg['COLUNA_TERAPIA_OCUPACIONAL'],
            'psicomotricidade': cfg['COLUNA_PSICOMOTRICIDADE'],
            'fisioterapia': cfg['COLUNA_FISIOTERAPIA'],
            'psicologia': cfg['COLUNA_PSICOLOGIA']
        }

    def get_analysis_config(self) -> Dict[str, bool]:
        """Retorna configuração de análises a realizar"""
        section = 'ANALISE_ESTATISTICA'

        return {
            'detailed_stats': self.getboolean(section, 'DETAILED_STATS', True),
            'percentages': self.getboolean(section, 'CALCULATE_PERCENTAGES', True),
            'ratios': self.getboolean(section, 'CALCULATE_RATIOS', True),
            'trends': self.getboolean(section, 'CALCULATE_TRENDS', True),
            'group_by_escola': self.getboolean(section, 'GROUP_BY_ESCOLA', True),
            'group_by_ano': self.getboolean(section, 'GROUP_BY_ANO', True),
            'group_by_turma': self.getboolean(section, 'GROUP_BY_TURMA', False),
            'group_by_sexo': self.getboolean(section, 'GROUP_BY_SEXO', True),
            'group_by_idade': self.getboolean(section, 'GROUP_BY_IDADE', True),
            'group_by_escalao': self.getboolean(section, 'GROUP_BY_ESCALAO_ASE', True),
            'correlations': self.getboolean(section, 'INCLUDE_CORRELATIONS', True),
            'comparisons': self.getboolean(section, 'INCLUDE_COMPARISONS', True),
            'rankings': self.getboolean(section, 'INCLUDE_RANKINGS', True),
            'terapias': self.getboolean(section, 'INCLUDE_TERAPIAS', True),
            'cross_analysis': self.getboolean(section, 'INCLUDE_CROSS_ANALYSIS', True),
            'age_distribution': self.getboolean(section, 'ANALYZE_AGE_DISTRIBUTION', True),
            'gender_distribution': self.getboolean(section, 'ANALYZE_GENDER_DISTRIBUTION', True),
            'socioeconomic': self.getboolean(section, 'ANALYZE_SOCIOECONOMIC', True)
        }

    def get_chart_config(self) -> Dict[str, Any]:
        """Retorna configuração de gráficos"""
        section = 'GRAFICOS'

        return {
            'generate': self.getboolean(section, 'GENERATE_CHARTS', True),
            'dpi': self.getint(section, 'CHART_DPI', 150),
            'format': self.get(section, 'CHART_FORMAT', 'png'),
            'width': self.getfloat(section, 'CHART_WIDTH', 12),
            'height': self.getfloat(section, 'CHART_HEIGHT', 7),
            'width_small': self.getfloat(section, 'CHART_WIDTH_SMALL', 8),
            'height_small': self.getfloat(section, 'CHART_HEIGHT_SMALL', 6),
            'style': self.get(section, 'CHART_STYLE', 'seaborn-v0_8-darkgrid'),
            'font_size': self.getint(section, 'FONT_SIZE', 11),
            'font_size_title': self.getint(section, 'FONT_SIZE_TITLE', 14),
            'font_size_label': self.getint(section, 'FONT_SIZE_LABEL', 10),
            'font_family': self.get(section, 'FONT_FAMILY', 'Arial'),
            'high_contrast': self.getboolean(section, 'USE_HIGH_CONTRAST', True),
            'annotate_values': self.getboolean(section, 'ANNOTATE_VALUES', True),
            'show_percentages': self.getboolean(section, 'SHOW_PERCENTAGES', True),
            'show_legends': self.getboolean(section, 'SHOW_LEGENDS', True),
            'grid_alpha': self.getfloat(section, 'GRID_ALPHA', 0.3),
            'types': {
                'bar': self.getboolean(section, 'GENERATE_BAR_CHARTS', True),
                'pie': self.getboolean(section, 'GENERATE_PIE_CHARTS', True),
                'stacked': self.getboolean(section, 'GENERATE_STACKED_CHARTS', True),
                'heatmap': self.getboolean(section, 'GENERATE_HEATMAPS', True),
                'comparison': self.getboolean(section, 'GENERATE_COMPARISON_CHARTS', True),
                'trend': self.getboolean(section, 'GENERATE_TREND_CHARTS', True),
                'distribution': self.getboolean(section, 'GENERATE_DISTRIBUTION_CHARTS', True)
            }
        }

    def get_report_config(self) -> Dict[str, Any]:
        """Retorna configuração de relatórios"""
        section = 'RELATORIOS'

        return {
            'generate_docx': self.getboolean(section, 'GENERATE_DOCX', True),
            'generate_xlsx': self.getboolean(section, 'GENERATE_XLSX', True),
            'generate_pdf': self.getboolean(section, 'GENERATE_PDF', False),
            'docx_filename': self.get(section, 'DOCX_FILENAME', 'Relatorio_DL54.docx'),
            'xlsx_filename': self.get(section, 'XLSX_FILENAME', 'Analise_DL54.xlsx'),
            'pdf_filename': self.get(section, 'PDF_FILENAME', 'Relatorio_DL54.pdf'),
            'executive_summary': self.getboolean(section, 'INCLUDE_EXECUTIVE_SUMMARY', True),
            'detailed_analysis': self.getboolean(section, 'INCLUDE_DETAILED_ANALYSIS', True),
            'charts': self.getboolean(section, 'INCLUDE_CHARTS', True),
            'raw_data_sample': self.getboolean(section, 'INCLUDE_RAW_DATA_SAMPLE', True),
            'raw_data_max_rows': self.getint(section, 'RAW_DATA_MAX_ROWS', 1000),
            'freeze_panes': self.getboolean(section, 'EXCEL_FREEZE_PANES', True),
            'auto_filter': self.getboolean(section, 'EXCEL_AUTO_FILTER', True),
            'conditional_formatting': self.getboolean(section, 'EXCEL_CONDITIONAL_FORMATTING', True)
        }

    def get_personalization(self) -> Dict[str, str]:
        """Retorna configurações de personalização"""
        section = 'PERSONALIZACAO'

        return {
            'organization': self.get(section, 'ORGANIZATION_NAME', ''),
            'title': self.get(section, 'REPORT_TITLE', 'Análise Estatística DL 54/2018'),
            'subtitle': self.get(section, 'REPORT_SUBTITLE', ''),
            'author': self.get(section, 'REPORT_AUTHOR', ''),
            'version': self.get(section, 'REPORT_VERSION', '2.0')
        }

    def __repr__(self) -> str:
        """Representação string do objeto"""
        return f"ConfigManager(config_path='{self.config_path}')"


def setup_logging(config: ConfigManager) -> logging.Logger:
    """
    Configura sistema de logging baseado na configuração.

    Args:
        config: Instância do ConfigManager

    Returns:
        Logger configurado
    """
    from datetime import datetime

    # Criar diretório de output se não existir
    output_dir = Path(config.get('IO', 'OUTPUT_DIR'))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Configurações de logging
    log_file = output_dir / config.get('LOGGING', 'LOG_FILE')
    log_level = getattr(logging, config.get('LOGGING', 'LOG_LEVEL', 'INFO'))
    log_format = config.get('LOGGING', 'LOG_FORMAT')
    log_mode = config.get('LOGGING', 'LOG_MODE', 'a')

    # Handlers
    handlers = []

    if config.getboolean('LOGGING', 'LOG_TO_FILE', True):
        handlers.append(
            logging.FileHandler(log_file, mode=log_mode, encoding='utf-8')
        )

    if config.getboolean('LOGGING', 'LOG_TO_CONSOLE', True):
        handlers.append(logging.StreamHandler())

    # Configurar logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )

    logger = logging.getLogger('DL54')

    # Log inicial
    logger.info("=" * 80)
    logger.info("SISTEMA DE ANÁLISE ESTATÍSTICA - DL 54/2018 v2.0")
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    return logger