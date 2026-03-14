import { MapContainer, TileLayer, Marker, Popup, Tooltip, useMap, useMapEvents, GeoJSON } from 'react-leaflet'
import L from 'leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import { useEffect, useState } from 'react'

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
    popupContent?: React.ReactNode
    tooltipContent?: React.ReactNode
    onMarkerClick?: () => void
}

interface MapViewProps {
    points: MapPoint[]
    height?: string | number
    useClustering?: boolean
    onBoundsChange?: (bounds: L.LatLngBounds) => void
}

function ChangeView({ points }: { points: MapPoint[] }) {
    const map = useMap()

    useEffect(() => {
        if (points.length > 0 && !map.hasLayer(L.polygon([]))) {
            const bounds = L.latLngBounds(points.map(p => [p.lat, p.lng]))
            if (bounds.isValid()) {
                map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 })
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [map])

    return null
}


export function MapView({ points, height = '100%', useClustering = true, onBoundsChange }: MapViewProps) {
    const centroPadrao: [number, number] = [-23.1867, -45.8854]

    const MapEventHandler = () => {
        const map = useMapEvents({
            moveend: () => { if (onBoundsChange) onBoundsChange(map.getBounds()) },
            zoomend: () => { if (onBoundsChange) onBoundsChange(map.getBounds()) }
        })

        useEffect(() => {
            if (onBoundsChange && map) {
                setTimeout(() => onBoundsChange(map.getBounds()), 500)
            }
        }, [map, onBoundsChange])

        return null
    }

    const [geoJsonData, setGeoJsonData] = useState<any>(null)

    useEffect(() => {
        fetch('/sjc_bairros.geojson')
            .then(res => res.json())
            .then(data => setGeoJsonData(data))
            .catch(err => console.error("Erro ao carregar bairros", err))
    }, [])

    const geoJsonStyle = {
        color: 'var(--brand-500)',
        weight: 1,
        opacity: 0.6,
        fillColor: 'var(--brand-500)',
        fillOpacity: 0.05
    }

    const onEachFeature = (feature: any, layer: any) => {
        if (feature.properties?.name) {
            layer.bindTooltip(feature.properties.name, { sticky: true, className: 'bairro-tooltip' })
        }
        layer.on({
            mouseover: (e: any) => {
                e.target.setStyle({ weight: 2, color: 'var(--brand-600)', fillOpacity: 0.2 })
                e.target.bringToFront()
            },
            mouseout: (e: any) => e.target.setStyle(geoJsonStyle)
        })
    }

    const Markers = () => (
        <>
            {points.map(p => (
                <Marker
                    key={p.id}
                    position={[p.lat, p.lng]}
                    icon={DefaultIcon}
                    eventHandlers={{
                        click: () => { if (p.onMarkerClick) p.onMarkerClick() }
                    }}
                >
                    {/* Tooltip: card de resumo ao passar o mouse */}
                    {p.tooltipContent && (
                        <Tooltip
                            direction="top"
                            offset={[0, -38]}
                            opacity={1}
                            sticky={false}
                            className="map-pin-tooltip"
                        >
                            {p.tooltipContent}
                        </Tooltip>
                    )}

                    {/* Popup: fallback quando não há onMarkerClick */}
                    {p.popupContent && !p.onMarkerClick && (
                        <Popup>{p.popupContent}</Popup>
                    )}
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

                <MapEventHandler />
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
                        <Markers />
                    </MarkerClusterGroup>
                ) : (
                    <Markers />
                )}
            </MapContainer>
        </div>
    )
}
