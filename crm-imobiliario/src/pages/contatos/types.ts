// Tipos do módulo de Contatos

export type TipoContato = 'proprietario' | 'inquilino' | 'comprador' | 'parceiro' | 'outro'

export interface Contato {
    id: string
    nome_completo: string
    telefone: string | null
    whatsapp: string | null
    email: string | null
    tipo_contato: TipoContato
    // Endereço
    cep: string | null
    logradouro: string | null
    numero: string | null
    complemento: string | null
    bairro: string | null
    cidade: string | null
    estado: string | null
    // Condomínio
    em_condominio: boolean
    nome_condominio: string | null
    bloco: string | null
    apartamento: string | null
    // Geo
    latitude: number | null
    longitude: number | null
    // Dados pessoais extras
    cpf: string | null
    rg: string | null
    data_nascimento: string | null    // ISO date: 'YYYY-MM-DD'
    estado_civil: string | null       // solteiro, casado, divorciado, viúvo, outro
    // Extras
    origem: string | null             // OLX, Indicação, Site, etc.
    vinculo_imovel_id: string | null
    notas: string | null
    criado_em: string
    atualizado_em: string
}

export const TIPO_CONTATO_LABELS: Record<TipoContato, string> = {
    proprietario: '🏠 Proprietário',
    inquilino: '🔑 Inquilino',
    comprador: '💰 Comprador',
    parceiro: '🤝 Parceiro',
    outro: '👤 Outro',
}

export const TIPO_CONTATO_CORES: Record<TipoContato, string> = {
    proprietario: 'var(--gold-400)',
    inquilino: '#a78bfa',
    comprador: 'var(--success)',
    parceiro: 'var(--brand-500)',
    outro: 'var(--text-muted)',
}
