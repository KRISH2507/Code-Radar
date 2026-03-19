'use client'

import React, { useState, useEffect } from 'react'
import { createOrder, verifyPayment } from '@/lib/api'
import { useUser } from '@/context/user-context'

interface Props {
    onClose: () => void
}

type Stage = 'idle' | 'creating' | 'processing' | 'success' | 'error'

export default function UpgradeModal({ onClose }: Props) {
    const { refreshUser } = useUser()
    const [stage, setStage] = useState<Stage>('idle')
    const [errorMsg, setErrorMsg] = useState('')

    // Lock body scroll
    useEffect(() => {
        document.body.style.overflow = 'hidden'
        return () => { document.body.style.overflow = '' }
    }, [])

    const handleUpgrade = async () => {
        setStage('creating')
        setErrorMsg('')

        const orderRes = await createOrder()
        if (orderRes.error || !orderRes.data) {
            setStage('error')
            setErrorMsg(orderRes.error ?? 'Failed to create payment order.')
            return
        }

        const { order_id, amount, currency, key_id } = orderRes.data

        // Dynamically load Razorpay checkout script
        await new Promise<void>((resolve, reject) => {
            if ((window as any).Razorpay) { resolve(); return }
            const script = document.createElement('script')
            script.src = 'https://checkout.razorpay.com/v1/checkout.js'
            script.onload = () => resolve()
            script.onerror = () => reject(new Error('Failed to load Razorpay script'))
            document.body.appendChild(script)
        }).catch(() => {
            setStage('error')
            setErrorMsg('Could not load payment gateway. Please check your internet connection.')
            return
        })

        setStage('processing')

        const options = {
            key: key_id,
            amount,
            currency,
            name: 'Code Radar',
            description: 'Pro Plan – Unlimited Scans',
            order_id,
            handler: async (response: {
                razorpay_order_id: string
                razorpay_payment_id: string
                razorpay_signature: string
            }) => {
                const verifyRes = await verifyPayment({
                    razorpay_order_id: response.razorpay_order_id,
                    razorpay_payment_id: response.razorpay_payment_id,
                    razorpay_signature: response.razorpay_signature,
                })

                if (verifyRes.error) {
                    setStage('error')
                    setErrorMsg(verifyRes.error)
                } else {
                    await refreshUser()
                    setStage('success')
                }
            },
            modal: {
                ondismiss: () => {
                    setStage('idle')
                },
            },
            theme: { color: '#f59e0b' },
        }

        const rzp = new (window as any).Razorpay(options)
        rzp.open()
    }

    // ── Overlay ────────────────────────────────────────────────────────────────
    return (
        <div
            onClick={onClose}
            style={{
                position: 'fixed', inset: 0, zIndex: 1000,
                background: 'rgba(0,0,0,0.7)',
                backdropFilter: 'blur(4px)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
        >
            <div
                onClick={e => e.stopPropagation()}
                style={{
                    background: 'linear-gradient(135deg, #0f172a, #1e293b)',
                    border: '1px solid #334155',
                    borderRadius: 16,
                    padding: '2rem',
                    width: '100%',
                    maxWidth: 440,
                    boxShadow: '0 25px 60px rgba(0,0,0,0.6)',
                    position: 'relative',
                }}
            >
                {/* Close button */}
                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute', top: 16, right: 16,
                        background: 'transparent', border: 'none',
                        color: '#64748b', fontSize: 18, cursor: 'pointer',
                    }}
                >
                    ✕
                </button>

                {stage === 'success' ? (
                    /* ── Success state ── */
                    <div style={{ textAlign: 'center', padding: '1rem 0' }}>
                        <div style={{ fontSize: 48, marginBottom: 12 }}>🎉</div>
                        <h2 style={{ color: '#f59e0b', fontWeight: 700, fontSize: 22, marginBottom: 8 }}>
                            Welcome to Pro!
                        </h2>
                        <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 24 }}>
                            You now have unlimited scans. Enjoy Code Radar Pro!
                        </p>
                        <button
                            onClick={onClose}
                            style={{
                                padding: '10px 28px', borderRadius: 8,
                                background: 'linear-gradient(135deg, #f59e0b, #d97706)',
                                border: 'none', color: '#0f172a',
                                fontWeight: 700, fontSize: 14, cursor: 'pointer',
                            }}
                        >
                            Start Scanning
                        </button>
                    </div>
                ) : (
                    /* ── Default / error state ── */
                    <>
                        {/* Header */}
                        <div style={{ marginBottom: '1.5rem' }}>
                            <div style={{ fontSize: 32, marginBottom: 8 }}>⚡</div>
                            <h2 style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 22, margin: 0 }}>
                                Upgrade to Pro
                            </h2>
                            <p style={{ color: '#94a3b8', fontSize: 14, marginTop: 6, marginBottom: 0 }}>
                                Unlock unlimited scans and all future Pro features.
                            </p>
                        </div>

                        {/* Feature list */}
                        <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 1.5rem', display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {[
                                '✅  Unlimited scans per month',
                                '✅  Priority queue for scans',
                                '✅  All future Pro features',
                                '✅  Email support',
                            ].map(f => (
                                <li key={f} style={{ color: '#cbd5e1', fontSize: 14 }}>{f}</li>
                            ))}
                        </ul>

                        {/* Price */}
                        <div
                            style={{
                                padding: '1rem',
                                borderRadius: 10,
                                background: '#0f172a',
                                border: '1px solid #334155',
                                textAlign: 'center',
                                marginBottom: '1.5rem',
                            }}
                        >
                            <span style={{ color: '#f59e0b', fontSize: 32, fontWeight: 800 }}>₹999</span>
                            <span style={{ color: '#64748b', fontSize: 14 }}> / month</span>
                        </div>

                        {/* Error */}
                        {stage === 'error' && (
                            <div
                                style={{
                                    padding: '10px 14px', borderRadius: 8,
                                    background: '#7f1d1d33', border: '1px solid #ef444466',
                                    color: '#fca5a5', fontSize: 13, marginBottom: '1rem',
                                }}
                            >
                                {errorMsg}
                            </div>
                        )}

                        {/* CTA */}
                        <button
                            onClick={handleUpgrade}
                            disabled={stage === 'creating' || stage === 'processing'}
                            style={{
                                width: '100%', padding: '12px 0', borderRadius: 8,
                                background: 'linear-gradient(135deg, #f59e0b, #d97706)',
                                border: 'none', color: '#0f172a',
                                fontWeight: 700, fontSize: 15, cursor: 'pointer',
                                opacity: (stage === 'creating' || stage === 'processing') ? 0.7 : 1,
                                transition: 'opacity 0.15s',
                            }}
                        >
                            {stage === 'creating'
                                ? 'Creating order…'
                                : stage === 'processing'
                                    ? 'Processing…'
                                    : 'Pay ₹999 / month'}
                        </button>

                        <p style={{ color: '#475569', fontSize: 11, textAlign: 'center', marginTop: 10 }}>
                            Secured by Razorpay · Cancel anytime
                        </p>
                    </>
                )}
            </div>
        </div>
    )
}
