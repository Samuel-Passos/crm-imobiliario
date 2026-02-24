// Tipos compartilhados do Módulo Kanban

export interface KanbanColuna {
    id: string
    nome: string
    ordem: number
}

export interface CorretorInfo {
    id: string
    nome_completo: string
    telefone: string | null
}

export interface ImovelKanban {
    id: number
    ad_id: number | null              // ID do anúncio OLX — usado para montar chat_url
    list_id: number
    titulo: string
    url: string
    preco: number | null
    preco_str: string | null
    condominio: number | null
    condominio_str: string | null
    iptu: number | null
    iptu_str: string | null
    tipo_imovel: string | null
    subtipo: string | null
    tipo_negocio: string | null
    area_m2: number | null
    area_construida_m2: number | null
    area_terreno_m2: number | null
    quartos: number | null
    banheiros: number | null
    vagas: number | null
    suites: number | null
    salas: number | null
    tem_cozinha: boolean
    outras_caracteristicas: string | null
    descricao: string | null
    rua: string | null
    numero: string | null
    complemento: string | null
    bairro: string | null
    cidade: string | null
    estado: string | null
    cep: string | null
    em_condominio: boolean
    nome_condominio: string | null
    bloco: string | null
    numero_apartamento: string | null
    latitude: number | null
    longitude: number | null
    // Vendedor / Proprietário
    vendedor_nome: string | null
    vendedor_email: string | null
    vendedor_user_id: string | null
    vendedor_chat_ativo: boolean
    telefone_existe: boolean
    telefone: string | null
    telefone_mascara: string | null
    telefones_extraidos?: { nome: string | null; telefone: string; origem?: string }[]
    vendedor_whatsapp: boolean       // true = WA ativo (número é imovel.telefone)
    autorizado: boolean
    telefone_pesquisado?: boolean
    anuncio_expirado?: boolean
    comissao_pct: number | null
    // Fotos
    foto_capa: string | null
    fotos: string[] | null
    // CRM
    origem: string | null             // OLX, Indicação, Site, etc.
    aceita_permuta: 'aceita' | 'nao_aceita' | 'nao_informado'
    notas_corretor: string | null
    historico_kanban: Array<{ coluna: string; data: string }> | null
    kanban_coluna_id: string | null
    kanban_ordem: number
    // Corretor
    corretor_id: string | null
    corretor?: CorretorInfo | null
}

// Helpers
export function getChatUrl(imovel: ImovelKanban): string | null {
    if (!imovel.ad_id || !imovel.vendedor_chat_ativo) return null
    return `https://chat.olx.com.br/chat?adId=${imovel.ad_id}`
}

export interface FiltrosKanban {
    tipo_negocio: '' | 'venda' | 'aluguel'
    tipo_imovel: string
    cidade: string
    aceita_permuta: '' | 'aceita' | 'nao_aceita' | 'nao_informado'
    telefone_status: '' | 'com_telefone' | 'sem_telefone'
    ordenacao: '' | 'recente_antigo' | 'antigo_recente' | 'preco_maior' | 'preco_menor'
}
