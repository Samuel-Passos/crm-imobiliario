import type { FiltrosKanban } from './types'

interface KanbanFiltersProps {
    filtros: FiltrosKanban
    onChange: (f: FiltrosKanban) => void
    cidades: string[]
    tipos: string[]
}

export function KanbanFilters({ filtros, onChange, cidades, tipos }: KanbanFiltersProps) {
    const set = <K extends keyof FiltrosKanban>(key: K, value: FiltrosKanban[K]) =>
        onChange({ ...filtros, [key]: value })

    return (
        <div style={{
            display: 'flex', gap: '0.75rem', flexWrap: 'wrap',
            padding: '0.75rem 1rem', background: 'var(--bg-surface)',
            borderBottom: '1px solid var(--border)', alignItems: 'center'
        }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>FILTROS</span>

            <select className="form-select" style={{ width: 140 }}
                value={filtros.tipo_negocio} onChange={e => set('tipo_negocio', e.target.value as FiltrosKanban['tipo_negocio'])}>
                <option value="">Negócio (todos)</option>
                <option value="venda">💰 Venda</option>
                <option value="aluguel">🔑 Aluguel</option>
            </select>

            <select className="form-select" style={{ width: 160 }}
                value={filtros.tipo_imovel} onChange={e => set('tipo_imovel', e.target.value)}>
                <option value="">Tipo (todos)</option>
                {tipos.map(t => <option key={t} value={t}>{t}</option>)}
            </select>

            <select className="form-select" style={{ width: 150 }}
                value={filtros.cidade} onChange={e => set('cidade', e.target.value)}>
                <option value="">Cidade (todas)</option>
                {cidades.map(c => <option key={c} value={c}>{c}</option>)}
            </select>

            <select className="form-select" style={{ width: 160 }}
                value={filtros.aceita_permuta} onChange={e => set('aceita_permuta', e.target.value as FiltrosKanban['aceita_permuta'])}>
                <option value="">Permuta (todas)</option>
                <option value="aceita">🔄 Aceita</option>
                <option value="nao_aceita">🚫 Não aceita</option>
                <option value="nao_informado">❓ Não informado</option>
            </select>

            {(filtros.tipo_negocio || filtros.tipo_imovel || filtros.cidade || filtros.aceita_permuta) && (
                <button className="btn btn-ghost btn-sm"
                    onClick={() => onChange({ tipo_negocio: '', tipo_imovel: '', cidade: '', aceita_permuta: '' })}>
                    ✕ Limpar
                </button>
            )}
        </div>
    )
}
