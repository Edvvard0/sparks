import { useEffect, useRef } from 'react'
import { useIsConnectionRestored, useTonConnectUI, useTonWallet } from '@tonconnect/ui-react'
import { tonProofService } from '../lib/ton-proof'
import { useApp } from '../context/AppContext'
import { showError } from '../lib/toast'

const payloadTTLMS = 1000 * 60 * 20 // 20 минут

export function useTonAuth() {
  const { setWalletAddress, setUser, updateUser, user, wallet_address } = useApp()
  const isConnectionRestored = useIsConnectionRestored()
  const wallet = useTonWallet()
  const [tonConnectUI] = useTonConnectUI()
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>()
  const hasProcessedProofRef = useRef<string | null>(null) // Отслеживаем обработанные proof
  const disconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null) // Для отслеживания отключения

  // Устанавливаем параметры подключения с tonProof ДО подключения кошелька
  // Это должно быть ВСЕГДА когда кошелек не подключен
  useEffect(() => {
    if (!isConnectionRestored || !tonConnectUI) {
      return
    }

    // Если кошелек уже подключен, не устанавливаем параметры
    if (wallet) {
      // Очищаем интервал если кошелек подключен
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = undefined
      }
      return
    }

    // Очищаем предыдущий интервал
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = undefined
    }

    // Кошелек не подключен - генерируем payload для подключения
    const refreshPayload = async () => {
      try {
        console.log('Generating payload for TON Connect...')
        tonConnectUI.setConnectRequestParameters({ state: 'loading' })

        const payload = await tonProofService.generatePayload()
        if (!payload) {
          console.warn('Failed to generate payload')
          tonConnectUI.setConnectRequestParameters(null)
        } else {
          console.log('Payload generated, setting connect parameters:', payload)
          tonConnectUI.setConnectRequestParameters({
            state: 'ready',
            value: payload
          })
        }
      } catch (error) {
        console.error('Error refreshing payload:', error)
        tonConnectUI.setConnectRequestParameters(null)
      }
    }

    // Генерируем payload сразу при монтировании
    refreshPayload()
    // Обновляем payload каждые 20 минут
    intervalRef.current = setInterval(refreshPayload, payloadTTLMS)
    
    // Cleanup при размонтировании или изменении зависимостей
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = undefined
      }
    }
  }, [isConnectionRestored, tonConnectUI, wallet])

  // Обрабатываем подключение кошелька и проверку proof
  useEffect(() => {
    if (!isConnectionRestored || !tonConnectUI || !wallet) {
      return
    }

    console.log('Processing wallet connection:', {
      address: wallet.account?.address,
      hasConnectItems: !!wallet.connectItems,
      connectItemsKeys: wallet.connectItems ? Object.keys(wallet.connectItems) : [],
      tonProof: wallet.connectItems?.tonProof ? 'present' : 'missing'
    })

    // Кошелек подключен - проверяем proof
    if (wallet.connectItems?.tonProof) {
      // Проверяем, есть ли ошибка в proof
      if ('error' in wallet.connectItems.tonProof) {
        console.error('TON Proof error:', wallet.connectItems.tonProof.error)
        // Ошибка в proof - отключаем кошелек
        tonConnectUI.disconnect()
        setWalletAddress(null)
        setUser(null)
        localStorage.removeItem('wallet_address')
        return
      }

      // Проверяем что proof доступен
      if (!('proof' in wallet.connectItems.tonProof)) {
        return
      }
      const proofPayload = wallet.connectItems.tonProof.proof.payload
      
      // Проверяем, не обрабатывали ли мы уже этот proof
      if (hasProcessedProofRef.current === proofPayload) {
        console.log('Proof already processed, skipping:', proofPayload)
        return
      }
      
      hasProcessedProofRef.current = proofPayload
      console.log('Processing new proof:', proofPayload)
      
      const handleProof = async () => {
        try {
          console.log('Checking proof for wallet:', wallet.account.address)
          if (!wallet.connectItems?.tonProof || 'error' in wallet.connectItems.tonProof) {
            console.warn('No valid proof found')
            return
          }
          const proof = wallet.connectItems.tonProof
          // Проверяем что это успешный ответ с proof
          if (!('proof' in proof)) {
            console.warn('Proof is not available')
            return
          }
          // Типизируем как TonProofItemReplySuccess и передаем весь proof объект
          const successProof = proof as any
          const result = await tonProofService.checkProof(
            successProof.proof as any,
            wallet.account
          )

          console.log('Proof check result:', result)

          if (result && result.success) {
            // TON Proof проверен успешно
            // Устанавливаем wallet_address в контекст и localStorage
            setWalletAddress(wallet.account.address)
            localStorage.setItem('wallet_address', wallet.account.address)
            
            if (result.user) {
              // Пользователь найден - wallet_address уже обновлен на бэкенде
              console.log('User found, wallet address updated:', result.user)
              
              // Сохраняем tg_id в localStorage если он есть (для быстрого доступа)
              if (result.user.tg_id) {
                localStorage.setItem('tg_id', result.user.tg_id.toString())
              }
              
              // Устанавливаем пользователя в контекст
              setUser(result.user)
              
              // Обновляем баланс и другие данные пользователя
              await updateUser()
              
              console.log('User wallet address updated successfully')
            } else {
              // Пользователь не найден - это нормально
              // Пользователь должен быть зарегистрирован через /register после онбординга
              // Сохраняем wallet_address для использования при регистрации
              console.log('User not found - wallet_address saved for registration')
              setWalletAddress(wallet.account.address)
              localStorage.setItem('wallet_address', wallet.account.address)
              // НЕ создаем пользователя автоматически - он должен пройти регистрацию через онбординг
            }
          } else {
            // Ошибка авторизации
            console.error('Proof check failed:', result)
            const errorMessage = result?.message || 'Ошибка авторизации. Попробуйте другой кошелек.'
            console.error('Proof check error details:', {
              result,
              walletAddress: wallet.account.address,
              proofPayload: proofPayload
            })
            showError(errorMessage)
            await tonConnectUI.disconnect()
            setWalletAddress(null)
            setUser(null)
            localStorage.removeItem('wallet_address')
            hasProcessedProofRef.current = null
          }
        } catch (error: any) {
          console.error('Error handling proof:', error)
          console.error('Error details:', {
            error,
            message: error?.message,
            response: error?.response?.data,
            status: error?.response?.status,
            walletAddress: wallet.account?.address
          })
          
          // Определяем более понятное сообщение об ошибке
          let errorMessage = 'Ошибка при проверке авторизации.'
          if (error?.response?.data?.detail) {
            errorMessage = error.response.data.detail
          } else if (error?.message) {
            errorMessage = error.message
          } else if (error?.response?.status === 401) {
            errorMessage = 'Ошибка авторизации. Проверьте подключение кошелька и попробуйте снова.'
          } else if (error?.response?.status === 404) {
            errorMessage = 'Сервис авторизации недоступен. Попробуйте позже.'
          }
          
          showError(errorMessage)
          await tonConnectUI.disconnect()
          setWalletAddress(null)
          setUser(null)
          localStorage.removeItem('wallet_address')
          hasProcessedProofRef.current = null
        }
      }

      handleProof()
    } else {
      // Proof не получен - кошелек подключен БЕЗ proof
      // Это может быть восстановленное соединение из старой сессии
      console.warn('Wallet connected without TON Proof. Checking if user exists...')
      console.log('Wallet state:', {
        address: wallet.account?.address,
        chain: wallet.account?.chain,
        hasConnectItems: !!wallet.connectItems,
        connectItemsKeys: wallet.connectItems ? Object.keys(wallet.connectItems) : []
      })
      
      // Устанавливаем адрес кошелька
      if (wallet.account?.address) {
        const currentAddress = wallet.account.address
        const storedAddress = localStorage.getItem('wallet_address')
        
        if (currentAddress !== storedAddress) {
          console.log('Setting wallet address:', currentAddress)
          setWalletAddress(currentAddress)
          localStorage.setItem('wallet_address', currentAddress)
        }
      }
      
      // Проверяем, есть ли пользователь в БД по wallet_address
      // Если пользователь найден, не отключаем кошелек
      const checkUserAndHandle = async () => {
        try {
          // НЕ вызываем updateUser здесь - он уже будет вызван автоматически через useEffect в AppContext
          // когда wallet_address установится в контексте
          
          // Проверяем, появился ли proof во время проверки
          if (wallet.connectItems?.tonProof) {
            console.log('Proof received during user check, canceling disconnect')
            if (disconnectTimeoutRef.current) {
              clearTimeout(disconnectTimeoutRef.current)
              disconnectTimeoutRef.current = null
            }
            return
          }
          
          // Если пользователь найден (установлен в контекст через updateUser), не отключаем
          // Проверяем через небольшую задержку, чтобы дать время на обновление состояния
          setTimeout(() => {
            if (user) {
              console.log('User found, keeping wallet connected')
              if (disconnectTimeoutRef.current) {
                clearTimeout(disconnectTimeoutRef.current)
                disconnectTimeoutRef.current = null
              }
            } else {
              // Пользователь не найден - отключаем кошелек
              console.log('User not found, disconnecting wallet...')
              tonConnectUI.disconnect().then(() => {
                setWalletAddress(null)
                setUser(null)
                localStorage.removeItem('wallet_address')
                hasProcessedProofRef.current = null
              }).catch((error) => {
                console.error('Error disconnecting wallet:', error)
              }).finally(() => {
                if (disconnectTimeoutRef.current) {
                  clearTimeout(disconnectTimeoutRef.current)
                  disconnectTimeoutRef.current = null
                }
              })
            }
          }, 1000) // Даем 1 секунду на обновление состояния
        } catch (error) {
          console.error('Error checking user:', error)
          // Ошибка при проверке - отключаем кошелек
          console.log('Error checking user, disconnecting wallet...')
          tonConnectUI.disconnect().then(() => {
            setWalletAddress(null)
            setUser(null)
            localStorage.removeItem('wallet_address')
            hasProcessedProofRef.current = null
          }).catch((disconnectError) => {
            console.error('Error disconnecting wallet:', disconnectError)
          }).finally(() => {
            if (disconnectTimeoutRef.current) {
              clearTimeout(disconnectTimeoutRef.current)
              disconnectTimeoutRef.current = null
            }
          })
        }
      }
      
      // Сразу проверяем пользователя
      checkUserAndHandle()
      
      // Отключаем кошелек только если proof не придет в течение 5 секунд
      // И только если пользователь не найден
      // Используем useRef для отслеживания, чтобы не отключать несколько раз
      if (!disconnectTimeoutRef.current) {
        disconnectTimeoutRef.current = setTimeout(() => {
          // Проверяем еще раз, не появился ли proof
          if (wallet.connectItems?.tonProof) {
            console.log('Proof received during wait, canceling disconnect')
            disconnectTimeoutRef.current = null
            return
          }
          
          // Проверяем пользователя еще раз перед отключением
          checkUserAndHandle()
        }, 5000) // Даем 5 секунд на получение proof или проверку пользователя
      }
    }
  }, [wallet, isConnectionRestored, tonConnectUI, setWalletAddress, setUser, updateUser, user])

  // Cleanup при размонтировании
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
      if (disconnectTimeoutRef.current) {
        clearTimeout(disconnectTimeoutRef.current)
      }
    }
  }, [])
  
  // Сброс флага отключения при отключении кошелька
  useEffect(() => {
    if (!wallet && disconnectTimeoutRef.current) {
      clearTimeout(disconnectTimeoutRef.current)
      disconnectTimeoutRef.current = null
    }
  }, [wallet])
  
  // Отменяем отключение кошелька, если пользователь найден
  useEffect(() => {
    if (user && disconnectTimeoutRef.current && wallet && !wallet.connectItems?.tonProof) {
      console.log('User found, canceling wallet disconnect')
      clearTimeout(disconnectTimeoutRef.current)
      disconnectTimeoutRef.current = null
    }
  }, [user, wallet])
  
  // Обработка отключения кошелька (когда wallet становится null)
  useEffect(() => {
    if (!wallet && wallet_address) {
      // Кошелек отключен - очищаем wallet_address
      console.log('Wallet disconnected, clearing wallet_address')
      setWalletAddress(null)
      localStorage.removeItem('wallet_address')
      
      // Обновляем данные пользователя
      updateUser().catch((error) => {
        console.error('Error updating user after wallet disconnect:', error)
      })
    }
  }, [wallet, wallet_address, setWalletAddress, updateUser])
}

