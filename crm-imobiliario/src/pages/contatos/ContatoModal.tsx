import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import type { Contato, TipoContato } from './types'
import { TIPO_CONTATO_LABELS } from './types'
import toast from 'react-hot-toast'

interface Props {
    contato?: Contato | null          // null = novo contato
    onClose: () => void
    onSaved: (c: Contato) => void
}

const TIPOS: TipoContato[] = ['proprietario', 'inquilino', 'comprador', 'parceiro', 'outro']



export function ContatoModal({ contato, onClose, onSaved }: Props) {
    const isNew = !contato

    const [nome, setNome] = useState(contato?.nome_completo || '')
    const [telefone, setTelefone] = useState(contato?.telefone || '')
    const [whatsapp, setWhatsapp] = useState(contato?.whatsapp || '')
    const [email, setEmail] = useState(contato?.email || '')
    const [tipo, setTipo] = useState<TipoContato>(contato?.tipo_contato || 'outro')

    const [cep, setCep] = useState(contato?.cep || '')
    const [logradouro, setLogradouro] = useState(contato?.logradouro || '')
    const [numero, setNumero] = useState(contato?.numero || '')
    const [complemento, setComplemento] = useState(contato?.complemento || '')
    const [bairro, setBairro] = useState(contato?.bairro || '')
    const [cidade, setCidade] = useState(contato?.cidade || '')
    const [estado, setEstado] = useState(contato?.estado || '')

    const [emCond, setEmCond] = useState(contato?.em_condominio || false)
    const [nomeCond, setNomeCond] = useState(contato?.nome_condominio || '')
    const [bloco, setBloco] = useState(contato?.bloco || '')
    const [apartamento, setApartamento] = useState(contato?.apartamento || '')

    const [notas, setNotas] = useState(contato?.notas || '')
    const [cpf, setCpf] = useState(contato?.cpf || '')
    const [rg, setRg] = useState(contato?.rg || '')
    const [dataNasc, setDataNasc] = useState(contato?.data_nascimento || '')
    const [estadoCivil, setEstadoCivil] = useState(contato?.estado_civil || '')
    const [origem, setOrigem] = useState(contato?.origem || '')
    const [saving, setSaving] = useState(false)
    const [buscandoCep, setBuscandoCep] = useState(false)

    // Fechar com Escape
    useEffect(() => {
        const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', h)
        return () => window.removeEventListener('keydown', h)
    }, [onClose])

    // Buscar CEP via ViaCEP
    async function buscarCep(v: string) {
        const apenas = v.replace(/\D/g, '')
        setCep(v)
        if (apenas.length !== 8) return
        setBuscandoCep(true)
        try {
            const res = await fetch(`https://viacep.com.br/ws/${apenas}/json/`)
            const data = await res.json()
            if (!data.erro) {
                setLogradouro(data.logradouro || '')
                setBairro(data.bairro || '')
                setCidade(data.localidade || '')
                setEstado(data.uf || '')
            } else {
                toast.error('CEP não encontrado')
            }
        } catch {
            toast.error('Erro ao buscar CEP')
        } finally {
            setBuscandoCep(false)
        }
    }

    async function handleSalvar(e: React.FormEvent) {
        e.preventDefault()
        if (!nome.trim()) { toast.error('Nome obrigatório'); return }
        setSaving(true)

        const payload = {
            nome_completo: nome.trim(),
            telefone: telefone || null,
            whatsapp: whatsapp || null,
            email: email || null,
            tipo_contato: tipo,
            cep: cep || null,
            logradouro: logradouro || null,
            numero: numero || null,
            complemento: complemento || null,
            bairro: bairro || null,
            cidade: cidade || null,
            estado: estado || null,
            em_condominio: emCond,
            nome_condominio: emCond ? nomeCond || null : null,
            bloco: emCond ? bloco || null : null,
            apartamento: emCond ? apartamento || null : null,
            notas: notas || null,
            cpf: cpf || null,
            rg: rg || null,
            data_nascimento: dataNasc || null,
            estado_civil: estadoCivil || null,
            origem: origem || null,
        }

        let result: Contato | null = null
        if (isNew) {
            const { data, error } = await supabase.from('contatos').insert(payload).select().single()
            if (error) { toast.error('Erro: ' + error.message); setSaving(false); return }
            result = data as Contato
        } else {
            const { data, error } = await supabase.from('contatos').update(payload).eq('id', contato!.id).select().single()
            if (error) { toast.error('Erro: ' + error.message); setSaving(false); return }
            result = data as Contato
        }

        setSaving(false)
        toast.success(isNew ? '✅ Contato criado!' : '✅ Contato atualizado!')
        onSaved(result!)
        onClose()
    }

    const inp = { className: 'form-input' }

    return (
        <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
            <div className="modal" style={{ maxWidth: 640 }}>
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                    <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                        {isNew ? '➕ Novo Contato' : `✏️ Editar — ${contato!.nome_completo}`}
                    </h2>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}>✕</button>
                </div>

                <form onSubmit={handleSalvar}>
                    {/* Dados pessoais */}
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                        Dados pessoais
                    </div>

                    <div className="form-group">
                        <label className="form-label">Nome completo *</label>
                        <input {...inp} value={nome} onChange={e => setNome(e.target.value)} placeholder="João da Silva" required />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Tipo de contato</label>
                        <select className="form-select" value={tipo} onChange={e => setTipo(e.target.value as TipoContato)}>
                            {TIPOS.map(t => <option key={t} value={t}>{TIPO_CONTATO_LABELS[t]}</option>)}
                        </select>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Telefone</label>
                            <input {...inp} value={telefone} onChange={e => setTelefone(e.target.value)} placeholder="(11) 99999-9999" />
                        </div>
                        <div className="form-group">
                            <label className="form-label">WhatsApp</label>
                            <input {...inp} value={whatsapp} onChange={e => setWhatsapp(e.target.value)} placeholder="(11) 99999-9999" />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">E-mail</label>
                        <input {...inp} type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="email@exemplo.com" />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">CPF</label>
                            <input {...inp} value={cpf} onChange={e => setCpf(e.target.value)} placeholder="000.000.000-00" maxLength={14} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">RG</label>
                            <input {...inp} value={rg} onChange={e => setRg(e.target.value)} placeholder="00.000.000-0" />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Data de nascimento</label>
                            <input {...inp} type="date" value={dataNasc} onChange={e => setDataNasc(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Estado civil</label>
                            <select className="form-select" value={estadoCivil} onChange={e => setEstadoCivil(e.target.value)}>
                                <option value="">Não informado</option>
                                <option value="solteiro">Solteiro(a)</option>
                                <option value="casado">Casado(a)</option>
                                <option value="divorciado">Divorciado(a)</option>
                                <option value="viuvo">Viúvo(a)</option>
                                <option value="outro">Outro</option>
                            </select>
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Origem do contato</label>
                        <input {...inp} value={origem} onChange={e => setOrigem(e.target.value)} placeholder="OLX, Indicação, Site..." />
                    </div>

                    {/* Endereço */}
                    <div style={{ borderTop: '1px solid var(--border)', margin: '1.25rem 0', paddingTop: '1rem' }}>
                        <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                            Endereço {buscandoCep && <span style={{ color: 'var(--brand-500)', fontWeight: 400 }}>Buscando CEP...</span>}
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">CEP</label>
                            <input {...inp} value={cep} onChange={e => buscarCep(e.target.value)} placeholder="00000-000" maxLength={9} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Estado (UF)</label>
                            <input {...inp} value={estado} onChange={e => setEstado(e.target.value)} maxLength={2} placeholder="SP" />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Logradouro (Rua / Avenida)</label>
                        <input {...inp} value={logradouro} onChange={e => setLogradouro(e.target.value)} placeholder="Rua das Flores" />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Número</label>
                            <input {...inp} value={numero} onChange={e => setNumero(e.target.value)} placeholder="123" />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Complemento</label>
                            <input {...inp} value={complemento} onChange={e => setComplemento(e.target.value)} placeholder="Apto, sala..." />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Bairro</label>
                            <input {...inp} value={bairro} onChange={e => setBairro(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Cidade</label>
                            <input {...inp} value={cidade} onChange={e => setCidade(e.target.value)} />
                        </div>
                    </div>

                    {/* Condomínio */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', margin: '0.5rem 0 1rem' }}>
                        <input type="checkbox" id="emCond" checked={emCond} onChange={e => setEmCond(e.target.checked)}
                            style={{ width: 16, height: 16, accentColor: 'var(--brand-500)', cursor: 'pointer' }} />
                        <label htmlFor="emCond" style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                            Em condomínio
                        </label>
                    </div>

                    {emCond && (
                        <>
                            <div className="form-group">
                                <label className="form-label">Nome do Condomínio</label>
                                <input {...inp} value={nomeCond} onChange={e => setNomeCond(e.target.value)} />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label className="form-label">Bloco</label>
                                    <input {...inp} value={bloco} onChange={e => setBloco(e.target.value)} placeholder="A" />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Apartamento</label>
                                    <input {...inp} value={apartamento} onChange={e => setApartamento(e.target.value)} placeholder="101" />
                                </div>
                            </div>
                        </>
                    )}

                    {/* Notas */}
                    <div style={{ borderTop: '1px solid var(--border)', margin: '1.25rem 0 0.75rem', paddingTop: '1rem' }}>
                        <label className="form-label">Notas</label>
                        <textarea className="form-input" value={notas} onChange={e => setNotas(e.target.value)}
                            rows={3} placeholder="Observações sobre o contato..."
                            style={{ resize: 'vertical', fontFamily: 'Inter, sans-serif' }} />
                    </div>

                    {/* Botões */}
                    <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                        <button type="submit" className="btn btn-primary" disabled={saving} style={{ width: 'auto' }}>
                            {saving ? <><span className="spinner" /> Salvando...</> : isNew ? '➕ Criar contato' : '💾 Salvar'}
                        </button>
                        <button type="button" className="btn btn-danger" onClick={onClose} style={{ width: 'auto', padding: '0.8rem 1.25rem' }}>
                            Cancelar
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
