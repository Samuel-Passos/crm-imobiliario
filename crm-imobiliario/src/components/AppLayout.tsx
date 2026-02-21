import { Sidebar } from './Sidebar'
import { BottomNav } from './BottomNav'
import { useDeviceType } from '../hooks/useDeviceType'

export function AppLayout({ children }: { children: React.ReactNode }) {
    const device = useDeviceType()
    const isMobile = device === 'mobile'

    return (
        <div className="app-layout">
            <Sidebar />
            <main
                className="main-content"
                style={{
                    marginLeft: isMobile ? 0 : undefined,
                    paddingBottom: isMobile ? '80px' : undefined,
                }}
            >
                {children}
            </main>
            {isMobile && <BottomNav />}
        </div>
    )
}
