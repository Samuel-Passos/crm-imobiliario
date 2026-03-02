import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import { useEffect } from 'react'

// Fix ícones Leaflet
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

const DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
})

interface MapPoint {
    id: string | number
    lat: number
    lng: number
    popupContent: React.ReactNode
}

interface MapViewProps {
    points: MapPoint[]
    height?: string | number
    useClustering?: boolean
}

function ChangeView({ points }: { points: MapPoint[] }) {
    const map = useMap()

    useEffect(() => {
        if (points.length > 0) {
            const bounds = L.latLngBounds(points.map(p => [p.lat, p.lng]))
            map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 })
        }
    }, [points, map])

    return null
}

export function MapView({ points, height = '100%', useClustering = true }: MapViewProps) {
    const centroPadrao: [number, number] = [-23.5505, -46.6333] // SP

    const Markers = () => (
        <>
            {points.map(p => (
                <Marker key={p.id} position={[p.lat, p.lng]} icon={DefaultIcon}>
                    <Popup>{p.popupContent}</Popup>
                </Marker>
            ))}
        </>
    )

    return (
        <div style={{ height, width: '100%', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border)' }}>
            <MapContainer
                center={centroPadrao}
                zoom={12}
                style={{ height: '100%', width: '100%' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <ChangeView points={points} />

                {useClustering ? (
                    <MarkerClusterGroup chunkedLoading>
                        <Markers />
                    </MarkerClusterGroup>
                ) : (
                    <Markers />
                )}
            </MapContainer>
        </div>
    )
}
