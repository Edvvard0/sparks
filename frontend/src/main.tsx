import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import './lib/i18n'
import { AppProvider } from './context/AppContext'
import { TonConnectUIProvider } from '@tonconnect/ui-react'

// Получаем URL манифеста
const getManifestUrl = (): string => {
  if (typeof window === 'undefined') {
    return ''
  }
  // Используем полный URL для продакшена или localhost для разработки
  const origin = window.location.origin
  const manifestUrl = `${origin}/tonconnect-manifest.json`
  console.log('[TON Connect] Manifest URL:', manifestUrl)
  return manifestUrl
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <TonConnectUIProvider 
      manifestUrl={getManifestUrl()}
      language="ru"
      uiPreferences={{ theme: 'DARK' as any }}
      actionsConfiguration={{
        returnStrategy: 'back',
      }}
    >
      <AppProvider>
        <App />
      </AppProvider>
    </TonConnectUIProvider>
  </React.StrictMode>,
)
