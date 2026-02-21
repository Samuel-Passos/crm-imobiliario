import { useEffect, useState } from 'react'
import { supabase } from '../../lib/supabase'
import type { Profile, Role } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

const ROLES: Role[] = ['admin', 'corretor', 'secretario', 'cliente']
const ROLE_LABELS: Record<Role, string> = {
    admin: '👑 Admin', corretor: '🏠 Corretor',
    secretario: '📋 Secretário', cliente: '👤 Cliente'
}

export function UsersPage() {
    const [users, setUsers] = useState<Profile[]>([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState<string | null>(null)

    const fetchUsers = async () => {
        const { data, error } = await supabase.from('profiles').select('*').order('criado_em', { ascending: false })
        if (!error && data) setUsers(data as Profile[])
        setLoading(false)
    }

    useEffect(() => { fetchUsers() }, [])

    const changeRole = async (userId: string, newRole: Role) => {
        setSaving(userId)
        const { error } = await supabase.from('profiles').update({ role: newRole }).eq('user_id', userId)
        setSaving(null)
        if (error) toast.error('Erro ao alterar role.')
        else {
            toast.success('Role atualizado!')
            setUsers(u => u.map(p => p.user_id === userId ? { ...p, role: newRole } : p))
        }
    }

    if (loading) {
        return <div className="loading-screen"><div className="spinner" /></div>
    }

    return (
        <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Gerenciar Usuários</h1>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.9rem' }}>
                {users.length} usuários cadastrados
            </p>

            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <table className="table">
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Email</th>
                            <th>Role</th>
                            <th>Cadastrado em</th>
                            <th>Ação</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(u => (
                            <tr key={u.id}>
                                <td style={{ fontWeight: 500 }}>{u.nome_completo || '—'}</td>
                                <td style={{ color: 'var(--text-secondary)', fontSize: '0.87rem' }}>{u.email}</td>
                                <td><span className={`badge badge-${u.role}`}>{ROLE_LABELS[u.role]}</span></td>
                                <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                                    {new Date(u.criado_em).toLocaleDateString('pt-BR')}
                                </td>
                                <td>
                                    <select
                                        className="form-select"
                                        style={{ width: 150 }}
                                        value={u.role}
                                        disabled={saving === u.user_id}
                                        onChange={e => changeRole(u.user_id, e.target.value as Role)}
                                    >
                                        {ROLES.map(r => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
                                    </select>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
