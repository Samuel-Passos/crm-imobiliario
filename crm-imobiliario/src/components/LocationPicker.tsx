import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import { useState, useEffect } from 'react'

// Fix ícones Leaflet
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

const DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
})

interface LocationPickerProps {
    initialLat?: number | null
    initialLng?: number | null
    onLocationSelected: (data: { lat: number; lng: number; address?: any }) => void
}

function MapEvents({ onClick }: { onClick: (lat: number, lng: number) => void }) {
    useMapEvents({
        click(e) {
            onClick(e.latlng.lat, e.latlng.lng)
        },
    })
    return null
}

function AutoCenter({ pos }: { pos: [number, number] }) {
    const map = useMap()
    useEffect(() => {
        if (pos[0] !== 0) {
            map.setView(pos, map.getZoom())
        }
    }, [pos, map])
    return null
}

export function LocationPicker({ initialLat, initialLng, onLocationSelected }: LocationPickerProps) {
    const [pos, setPos] = useState<[number, number]>([initialLat || -23.5505, initialLng || -46.6333])
    const [loading, setLoading] = useState(false)

    async function handleReverseGeocode(lat: number, lng: number) {
        setLoading(true)
        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`, {
                headers: { 'User-Agent': 'CRM-Imobiliario-App-Samuel' }
            })
            const data = await res.json()
            onLocationSelected({ lat, lng, address: data.address })
        } catch (e) {
            console.error('Erro reverse geocode:', e)
            onLocationSelected({ lat, lng })
        } finally {
            setLoading(false)
        }
    }

    const handleClick = (lat: number, lng: number) => {
        setPos([lat, lng])
        handleReverseGeocode(lat, lng)
    }

    return (
        <div style={{ position: 'relative', height: '300px', width: '100%', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border)', marginBottom: '1rem' }}>
            <MapContainer
                center={pos}
                zoom={15}
                style={{ height: '100%', width: '100%' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapEvents onClick={handleClick} />
                <AutoCenter pos={pos} />
                <Marker position={pos} icon={DefaultIcon} />
            </MapContainer>

            {loading && (
                <div style={{ position: 'absolute', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '0.8rem', fontWeight: 600 }}>
                    <span className="spinner" style={{ marginRight: '0.5rem' }} /> Buscando endereço...
                </div>
            )}

            <div style={{ position: 'absolute', bottom: 10, left: 10, right: 10, zIndex: 1000, background: 'var(--bg-card)', padding: '0.5rem', borderRadius: 4, fontSize: '0.75rem', border: '1px solid var(--border)', boxShadow: '0 4px 12px rgba(0,0,0,0.2)' }}>
                📍 Clique no mapa para posicionar o pin e preencher o endereço automaticamente.
            </div>
        </div>
    )
}
