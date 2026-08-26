import { MapContainer, TileLayer, Marker, Popup, Tooltip, useMap, useMapEvents, GeoJSON } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import MarkerClusterGroup from 'react-leaflet-cluster'
import { useEffect, useState, useMemo, useRef } from 'react'

// Fix ícones Leaflet usando CDN (Solução definitiva para problemas de path)
const DefaultIcon = L.icon({
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
})
L.Marker.prototype.options.icon = DefaultIcon

interface MapPoint {
    id: string | number
    lat: number
    lng: number
    popupContent?: React.ReactNode
    onMarkerClick?: () => void
    category?: 'autorizados' | 'funil' | 'mercado'
}

const createCustomIcon = (category?: 'autorizados' | 'funil' | 'mercado') => {
    let color = '#3b82f6' // Azul padrão (mercado)
    if (category === 'autorizados') color = '#ef4444' // Vermelho
    if (category === 'funil') color = '#f97316' // Laranja

    const svgIcon = `
        <svg viewBox="0 0 24 24" fill="${color}" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
            <circle cx="12" cy="10" r="3" fill="white"></circle>
        </svg>
    `

    return L.divIcon({
        html: `<div style="width: 32px; height: 32px; filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.3)); transform: translate(-16px, -32px);">${svgIcon}</div>`,
        className: 'custom-map-icon',
        iconSize: [0, 0], // Evita que o leaflet adicione estilos de tamanho que quebrem
    })
}

// Pré-instanciar os ícones para evitar Memory Leaks e recriação em cada render do React (Crash do Browser)
const CATEGORY_ICONS = {
    autorizados: createCustomIcon('autorizados'),
    funil: createCustomIcon('funil'),
    mercado: createCustomIcon('mercado'),
    default: DefaultIcon
}

interface MapViewProps {
    points: MapPoint[]
    height?: string | number
    useClustering?: boolean
    onBoundsChange?: (bounds: L.LatLngBounds) => void
}

// GeoJSON cacheado em nível de módulo — carregado uma única vez e compartilhado entre
// todas as instâncias do MapView. Evita re-fetch e re-parse a cada remontagem.
let cachedGeoJson: any = null

// MapEventHandler fora do MapView para evitar re-declaração a cada render
function MapEventHandler({ onBoundsChange }: { onBoundsChange?: (b: L.LatLngBounds) => void }) {
    const map = useMapEvents({
        moveend: () => { if (onBoundsChange) onBoundsChange(map.getBounds()) },
        zoomend: () => { if (onBoundsChange) onBoundsChange(map.getBounds()) },
    })

    useEffect(() => {
        if (onBoundsChange && map) onBoundsChange(map.getBounds())
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [map])

    return null
}

function ChangeView({ points }: { points: MapPoint[] }) {
    const map = useMap()
    const hasCenteredRef = useRef(false)

    useEffect(() => {
        // Só centraliza automaticamente se ainda não centrou ou se a quantidade de pontos mudou
        if (points.length > 0 && !hasCenteredRef.current) {
            const bounds = L.latLngBounds(points.map(p => [p.lat, p.lng]))
            if (bounds.isValid()) {
                map.fitBounds(bounds, { padding: [50, 50], maxZoom: 18 })
                hasCenteredRef.current = true
            }
        }
        
        // Se os pontos zerarem, marcamos como não centrado para a próxima carga
        if (points.length === 0) {
            hasCenteredRef.current = false
        }
    }, [map, points])

    return null
}

export function MapView({ points, height = '100%', useClustering = true, onBoundsChange }: MapViewProps) {
    const centroPadrao: [number, number] = [-23.1794, -45.8869]


    const [geoJsonData, setGeoJsonData] = useState<any>(cachedGeoJson)

    useEffect(() => {
        if (cachedGeoJson) return // já carregado por instância anterior
        fetch('/sjc_bairros.geojson')
            .then(res => res.json())
            .then(data => {
                cachedGeoJson = data  // salva no cache de módulo
                setGeoJsonData(data)
            })
            .catch(err => console.error('Erro ao carregar bairros', err))
    }, [])

    const geoJsonStyle = {
        color: 'var(--m3-primary)',
        weight: 1,
        opacity: 0.4,
        fillColor: 'var(--m3-primary)',
        fillOpacity: 0.03
    }

    const onEachFeature = (feature: any, layer: any) => {
        if (feature.properties?.name) {
            layer.bindTooltip(feature.properties.name, { sticky: true, className: 'bairro-tooltip' })
        }
        layer.on({
            mouseover: (e: any) => {
                e.target.setStyle({ weight: 2, color: 'var(--m3-primary)', fillOpacity: 0.1 })
                e.target.bringToFront()
            },
            mouseout: (e: any) => e.target.setStyle(geoJsonStyle)
        })
    }


    return (
        <div style={{ height, width: '100%', borderRadius: 'var(--m3-radius-xl)', overflow: 'hidden', border: '1px solid var(--m3-outline-variant)' }}>
            <MapContainer
                center={centroPadrao}
                zoom={13}
                style={{ height: '100%', width: '100%' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <MapEventHandler onBoundsChange={onBoundsChange} />
                <ChangeView points={points} />


                {geoJsonData && (
                    <GeoJSON
                        data={geoJsonData}
                        style={geoJsonStyle}
                        onEachFeature={onEachFeature}
                    />
                )}

                {useClustering ? (
                    <MarkerClusterGroup chunkedLoading>
                        {points.map(p => (
                            <Marker
                                key={p.id}
                                position={[p.lat, p.lng]}
                                icon={p.category ? CATEGORY_ICONS[p.category] : CATEGORY_ICONS.default}
                                eventHandlers={{
                                    click: () => { if (p.onMarkerClick) p.onMarkerClick() }
                                }}
                            >
                                {p.popupContent && <Popup>{p.popupContent}</Popup>}
                            </Marker>
                        ))}
                    </MarkerClusterGroup>
                ) : (
                    points.map(p => (
                        <Marker
                            key={p.id}
                            position={[p.lat, p.lng]}
                            icon={p.category ? CATEGORY_ICONS[p.category] : CATEGORY_ICONS.default}
                            eventHandlers={{
                                click: () => { if (p.onMarkerClick) p.onMarkerClick() }
                            }}
                        >
                            {p.popupContent && !p.onMarkerClick && (
                                <Popup>{p.popupContent}</Popup>
                            )}
                        </Marker>
                    ))
                )}
            </MapContainer>
        </div>
    )
}
