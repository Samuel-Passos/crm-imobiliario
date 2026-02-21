import { useState } from 'react'
import { supabase } from '../../lib/supabase'
import type { ImovelKanban } from '../kanban/types'
import { KanbanCard } from '../kanban/KanbanCard'
import toast from 'react-hot-toast'

export function PesquisaPage() {
    const [busca, setBusca] = useState('')
    const [loading, setLoading] = useState(false)
    const [resultado, setResultado] = useState<ImovelKanban | null>(null)
    const [searched, setSearched] = useState(false)

    async function handleSearch(e: React.FormEvent) {
        e.preventDefault()
        if (!busca.trim()) return

        setLoading(true)
        setSearched(true)
        setResultado(null)

        // Extrai apenas os números da busca (caso o usuário cole uma URL ou o ID direto)
        const match = busca.match(/(\d+)/)
        const id = match ? match[1] : null

        if (!id) {
            toast.error('Não foi possível identificar um ID na busca.')
            setLoading(false)
            return
        }

        // Tenta buscar por ad_id ou list_id
        const { data, error } = await supabase
            .from('imoveis')
            .select(`
        id, list_id, titulo, url, preco, preco_str,
        tipo_imovel, subtipo, tipo_negocio, area_m2,
        quartos, banheiros, vagas, suites,
        rua, numero, complemento, bairro, cidade, estado, cep,
        em_condominio, nome_condominio, bloco, numero_apartamento,
        latitude, longitude,
        vendedor_nome, telefone, telefone_mascara, vendedor_whatsapp,
        ad_id, foto_capa, fotos,
        vendedor_chat_ativo, vendedor_email, autorizado, comissao_pct,
        area_construida_m2, area_terreno_m2, salas, tem_cozinha,
        outras_caracteristicas, descricao,
        condominio, condominio_str, iptu, iptu_str,
        aceita_permuta, notas_corretor, historico_kanban,
        kanban_coluna_id, kanban_ordem, corretor_id
      `)
            .or(`ad_id.eq.${id},list_id.eq.${id}`)
            .eq('ativo', true)
            .limit(1)
            .single()

        setLoading(false)

        if (error) {
            if (error.code === 'PGRST116') {
                // Not found
                setResultado(null)
            } else {
                toast.error('Erro ao buscar imóvel: ' + error.message)
            }
        } else if (data) {
            setResultado(data as ImovelKanban)
        }
    }

    function handleUpdate(updatedParams: Partial<ImovelKanban>) {
        setResultado(prev => prev ? { ...prev, ...updatedParams } : null)
    }

    return (
        <div style={{ padding: '1.5rem', maxWidth: 800, margin: '0 auto', width: '100%' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.2rem' }}>Pesquisar Imóvel</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '2rem' }}>
                Cole o ID do anúncio ou o link completo da OLX para verificar se já está no banco.
            </p>

            <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem' }}>
                <input
                    type="text"
                    className="form-input"
                    placeholder="Ex: 1474713058 ou https://sp.olx.com.br/..."
                    value={busca}
                    onChange={e => setBusca(e.target.value)}
                    style={{ flex: 1, padding: '0.8rem 1rem', fontSize: '1rem' }}
                    autoFocus
                />
                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading || !busca.trim()}
                    style={{ width: 'auto', padding: '0.8rem 1.5rem', fontSize: '1rem' }}
                >
                    {loading ? <span className="spinner" /> : '🔍 Buscar'}
                </button>
            </form>

            {searched && !loading && (
                <div style={{ marginTop: '2rem' }}>
                    {resultado ? (
                        <div>
                            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--success)' }}>
                                ✅ Imóvel encontrado no banco de dados!
                            </h2>
                            <div style={{ maxWidth: 350 }}>
                                <KanbanCard imovel={resultado} onUpdate={handleUpdate} />
                            </div>
                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', padding: '3rem 1rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border)' }}>
                            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>😕</div>
                            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                                Imóvel não encontrado
                            </h3>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                                Não localizamos nenhum imóvel com esse ID ativo no banco de dados.<br />
                                Verifique se o ID ou Link estão corretos.
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
