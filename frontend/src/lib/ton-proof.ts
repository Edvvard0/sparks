import { Account, ConnectAdditionalRequest, TonProofItemReplySuccess } from '@tonconnect/ui-react'
import apiClient from './api'
import { User } from '../context/AppContext'

class TonProofService {
  async generatePayload(): Promise<ConnectAdditionalRequest | undefined> {
    try {
      console.log('[TON Proof] Generating payload...')
      const response = await apiClient.post<{ payload: string }>(
        '/auth/ton-proof/generate',
        {},
        {
          timeout: 10000
        }
      )
      console.log('[TON Proof] Payload generated:', response.data.payload)
      console.log('[TON Proof] Payload length:', response.data.payload?.length)
      return { tonProof: response.data.payload }
    } catch (e: any) {
      console.error('[TON Proof] Error generating payload:', e)
      console.error('[TON Proof] Error details:', {
        message: e?.message,
        response: e?.response?.data,
        status: e?.response?.status,
        statusText: e?.response?.statusText
      })
      return undefined
    }
  }

  async checkProof(
    proof: TonProofItemReplySuccess['proof'],
    account: Account
  ): Promise<{ success: boolean; user: User | null; token?: string; message?: string } | null> {
    try {
      const requestBody = {
        address: account.address,
        network: account.chain,
        proof: {
          ...proof,
          state_init: account.walletStateInit
        }
      }

      // Получаем tg_id из localStorage для передачи в заголовке
      const tgId = localStorage.getItem('tg_id')
      const headers: Record<string, string> = {}
      if (tgId) {
        headers['X-Telegram-User-ID'] = tgId
      }

      console.log('[TON Proof] Checking proof for address:', account.address)
      console.log('[TON Proof] Proof payload:', proof.payload)
      console.log('[TON Proof] Proof timestamp:', proof.timestamp)
      console.log('[TON Proof] Proof signature:', proof.signature ? `${proof.signature.substring(0, 20)}...` : 'missing')
      console.log('[TON Proof] tg_id from localStorage:', tgId)
      console.log('[TON Proof] Request body:', {
        address: requestBody.address,
        network: requestBody.network,
        proofPayload: requestBody.proof.payload,
        hasSignature: !!requestBody.proof.signature,
        hasTimestamp: !!requestBody.proof.timestamp
      })
      
      const response = await apiClient.post<{
        success: boolean
        user: User | null
        token?: string
        message?: string
      }>('/auth/ton-proof/check', requestBody, {
        timeout: 15000,
        headers
      })

      console.log('[TON Proof] Proof check result:', response.data)
      return response.data
    } catch (e: any) {
      console.error('[TON Proof] Error checking proof:', e)
      console.error('[TON Proof] Error details:', {
        message: e?.message,
        response: e?.response?.data,
        status: e?.response?.status,
        statusText: e?.response?.statusText,
        proofPayload: proof?.payload
      })
      return null
    }
  }
}

export const tonProofService = new TonProofService()

