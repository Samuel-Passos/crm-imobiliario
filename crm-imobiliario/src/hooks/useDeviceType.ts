import { useState, useEffect } from 'react'

export type DeviceType = 'mobile' | 'tablet' | 'desktop'

const BREAKPOINTS = {
    mobile: 768,
    tablet: 1024,
}

function getDeviceType(): DeviceType {
    const width = window.innerWidth
    if (width < BREAKPOINTS.mobile) return 'mobile'
    if (width < BREAKPOINTS.tablet) return 'tablet'
    return 'desktop'
}

export function useDeviceType(): DeviceType {
    const [device, setDevice] = useState<DeviceType>(getDeviceType)

    useEffect(() => {
        const handler = () => setDevice(getDeviceType())
        const mediaQueryMobile = window.matchMedia(`(max-width: ${BREAKPOINTS.mobile - 1}px)`)
        const mediaQueryTablet = window.matchMedia(`(max-width: ${BREAKPOINTS.tablet - 1}px)`)

        mediaQueryMobile.addEventListener('change', handler)
        mediaQueryTablet.addEventListener('change', handler)

        return () => {
            mediaQueryMobile.removeEventListener('change', handler)
            mediaQueryTablet.removeEventListener('change', handler)
        }
    }, [])

    return device
}

export function useIsMobile(): boolean {
    return useDeviceType() === 'mobile'
}

export function useIsTablet(): boolean {
    return useDeviceType() === 'tablet'
}

export function useIsDesktop(): boolean {
    return useDeviceType() === 'desktop'
}
