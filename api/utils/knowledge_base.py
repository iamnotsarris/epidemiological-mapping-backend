CONHECIMENTO_BASE = """
# Sobre a Plataforma EPI-DATA
O EPI-DATA é um sistema de mapeamento epidemiológico setorial e dashboard de saúde pública desenvolvido para a Secretaria de Saúde de Floriano, Piauí. O principal objetivo é acompanhar a evolução de casos, monitorar focos de endemias e mapear as zonas de abrangência das Unidades Básicas de Saúde (UBSs), fornecendo suporte à decisão para o controle de surtos e vetores em tempo real.

# Funcionalidades e Agravos Monitorados
A plataforma possui Dashboards interativos e Mapas de Calor Georreferenciados para 11 agravos: Dengue, Tuberculose, Sífilis, Doença de Chagas, Violência Doméstica, Hanseníase, Hepatite, Acidentes com Animais Peçonhentos, Intoxicação, Leishmaniose e AIDS Adulto. Cada painel traz KPIs (Total de Casos, Casos em Alerta), curvas epidêmicas, perfil demográfico e distribuição territorial.

# Como o Assistente Deve Responder
A IA explica como os dados são organizados, como ler os mapas de densidade, o que significam os KPIs e como navegar na interface. Sempre que o usuário perguntar "quantos casos", "ranking", "por bairro", "por UBS", "série histórica" ou "por agravo", o assistente deve acionar a ferramenta apropriada em vez de chutar. A IA NÃO fornece diagnósticos médicos, apenas dados agregados da plataforma.

# Ficha Técnica por Agravo

## Dengue
- Transmissão: vetorial (Aedes aegypti).
- Fonte dos dados: SINAN Dengue.
- Campos disponíveis: data_notificacao, data_pri_sintoma, data_nascimento, classi_fin (classificação final), cs_sexo, hospital, endereco (com bairro extraível), id_agravo, id_unidade.
- Filtros suportados: ano, bairro (via parsing do endereço), sexo, classificação final, UBS.
- Análises típicas: ranking de bairros com mais casos, curva por mês, perfil por sexo/faixa etária, classificação final (Dengue, Dengue com sinais de alarme, Dengue grave).

## Tuberculose
- Transmissão: aerossóis (Mycobacterium tuberculosis).
- Fonte: SINAN Tuberculose.
- Campos disponíveis: nu_notific, ano_notific, id_unidade, nm_ubs.
- Filtros suportados: ano, UBS.
- Análises típicas: casos por ano, casos por UBS, série histórica. NÃO suporta filtro por bairro/sexo no modelo atual.

## Sífilis
- Transmissão: sexual e vertical (congênita).
- Fonte: SINAN Sífilis.
- Campos disponíveis: nu_notific, dt_notific, ano_notific, id_agravo, id_unidade, un_saude, nm_ubs, mu_residen, nm_pacient.
- Filtros suportados: ano, UBS, município de residência, agravo (sífilis adquirida, gestante, congênita).
- Análises típicas: casos por ano, distribuição por agravo (adquirida/gestante/congênita), casos por UBS.

## Doença de Chagas
- Transmissão: vetorial (Triatoma) e oral.
- Fonte: SINAN Chagas.
- Campos disponíveis: nu_notific, ano_notific, id_unidade, nm_ubs.
- Filtros suportados: ano, UBS.
- Análises típicas: casos por ano, série histórica, casos por UBS.

## Violência Doméstica
- Definição: notificações de violência interpessoal/autoprovocada.
- Fonte: SINAN Violência.
- Campos disponíveis: nu_notific, ano_notific, id_unidade, nm_ubs.
- Filtros suportados: ano, UBS.
- Análises típicas: casos por ano, por UBS, série histórica. Dados sigilosos — suporte humano apenas para detalhamento.

## Hanseníase
- Transmissão: contato prolongado (Mycobacterium leprae).
- Fonte: SINAN Hanseníase.
- Campos: nu_notific, ano_notific, id_unidade, nm_ubs.
- Filtros: ano, UBS.
- Análises: casos por ano, por UBS, série histórica.

## Hepatite
- Transmissão: viral (A, B, C, D, E), fecal-oral ou sanguínea/sexual.
- Fonte: SINAN Hepatites Virais.
- Campos: nu_notific, ano_notific, id_unidade, nm_ubs.
- Filtros: ano, UBS.
- Análises: casos por ano, por UBS.

## Acidentes com Animais Peçonhentos
- Definição: picadas/acidentes com serpentes, escorpiões, aranhas, abelhas, etc.
- Fonte: SINAN Animais Peçonhentos.
- Campos: nu_notific, ano_notific, id_unidade, nm_ubs, hospital.
- Filtros: ano, UBS, hospital de atendimento.
- Análises: casos por ano, por hospital, por UBS.

## Intoxicação Exógena
- Definição: intoxicações por agentes químicos, medicamentos, agrotóxicos, etc.
- Fonte: SINAN Intoxicação Exógena.
- Campos: nu_notific, ano_notific, id_unidade.
- Filtros: ano, UBS.
- Análises: casos por ano, série histórica.

## Leishmaniose
- Transmissão: vetorial (flebotomíneos). Formas: tegumentar e visceral.
- Fonte: SINAN Leishmaniose.
- Campos: nu_notific, ano_notific, id_unidade.
- Filtros: ano, UBS.
- Análises: casos por ano, série histórica.

## AIDS Adulto
- Transmissão: sexual, sanguínea, vertical.
- Fonte: SINAN AIDS Adulto.
- Campos: nu_notific, ano_notific, id_unidade.
- Filtros: ano, UBS.
- Análises: casos por ano, série histórica.

# Cobertura Vacinal
A plataforma também armazena dados de cobertura vacinal por ano e imunobiológico (BCG, Rotavírus, etc.), com percentual de cobertura e meta ótima (90% para Rotavírus, 95% para as demais). Use a ferramenta `cobertura_vacinal` para consultas sobre vacinação.

# Importação de Dados DBF
O sistema importa arquivos DBF do SINAN, além de arquivos xlsx do excel e arquivos cvs. O nome do arquivo identifica a doença (ex: 'deng' → Dengue, 'tubercu' → Tuberculose, 'sifi' → Sífilis). Datas inválidas (30/12/1899) são ignoradas e endereços são concatenados (Logradouro, Número, Complemento, Bairro, CEP).

# Suporte Humano
Para acessos restritos, inconsistências graves no DBF, falhas de banco ou assuntos sigilosos, acionar: vigilanciafloriano@gmail.com
"""