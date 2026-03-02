import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import type { Contato } from './types'
import { TIPO_CONTATO_LABELS, TIPO_CONTATO_CORES } from './types'
import { useEffect } from 'react'

// Fix para ícone padrão do Leaflet que as vezes quebra caminhos no build/Vite
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

const DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
})

interface Props {
    contatos: Contato[]
    onEditar: (c: Contato) => void
}

// Componente para ajustar o zoom e centro quando mudar os contatos
function ChangeView({ contacts }: { contacts: Contato[] }) {
    const map = useMap()

    useEffect(() => {
        const withCoords = contacts.filter(c => c.latitude && c.longitude)
        if (withCoords.length > 0) {
            const bounds = L.latLngBounds(withCoords.map(c => [c.latitude!, c.longitude!]))
            map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 })
        }
    }, [contacts, map])

    return null
}

export function ContatosMapa({ contatos, onEditar }: Props) {
    const contatosComCoords = contatos.filter(c => c.latitude && c.longitude)

    const centroPadrao: [number, number] = [-23.5505, -46.6333] // São Paulo

    return (
        <div style={{ height: 'calc(100vh - 250px)', minHeight: 400, borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border)' }}>
            <MapContainer
                center={centroPadrao}
                zoom={12}
                style={{ height: '100%', width: '100%' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <ChangeView contacts={contatosComCoords} />

                {contatosComCoords.map(c => (
                    <Marker
                        key={c.id}
                        position={[c.latitude!, c.longitude!]}
                        icon={DefaultIcon}
                    >
                        <Popup>
                            <div style={{ color: '#333', minWidth: 150 }}>
                                <div style={{ fontWeight: 700, marginBottom: 4 }}>{c.nome_completo}</div>
                                <div style={{
                                    fontSize: '0.7rem',
                                    fontWeight: 600,
                                    color: TIPO_CONTATO_CORES[c.tipo_contato] || '#666',
                                    background: `${TIPO_CONTATO_CORES[c.tipo_contato] || '#666'}18`,
                                    padding: '2px 6px',
                                    borderRadius: 4,
                                    display: 'inline-block',
                                    marginBottom: 8
                                }}>
                                    {TIPO_CONTATO_LABELS[c.tipo_contato] || c.tipo_contato}
                                </div>
                                <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: 8 }}>
                                    📍 {[c.logradouro, c.numero, c.cidade].filter(Boolean).join(', ')}
                                </div>
                                <button
                                    onClick={() => onEditar(c)}
                                    style={{
                                        width: '100%',
                                        padding: '4px',
                                        fontSize: '0.8rem',
                                        cursor: 'pointer',
                                        background: 'var(--brand-500)',
                                        color: '#fff',
                                        border: 'none',
                                        borderRadius: 4
                                    }}
                                >
                                    Editar Contato
                                </button>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    )
}
