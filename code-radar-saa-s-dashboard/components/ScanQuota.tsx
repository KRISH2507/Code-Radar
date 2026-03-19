'use client'

import React, { useState } from 'react'
import { useUser } from '@/context/user-context'
import UpgradeModal from './UpgradeModal'

const FREE_LIMIT = 3

export default function ScanQuota() {
    const { user } = useUser()
    const [showUpgrade, setShowUpgrade] = useState(false)

    if (!user || user.plan === 'pro') return null

    const used = user.scan_count
    const remaining = Math.max(FREE_LIMIT - used, 0)
    const pct = Math.min((used / FREE_LIMIT) * 100, 100)
    const exhausted = remaining === 0

    return (
        <>
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '6px 12px',
                    borderRadius: '10px',
                    background: exhausted ? '#7f1d1d22' : '#1e293b',
                    border: `1px solid ${exhausted ? '#ef444466' : '#334155'}`,
                    fontSize: '12px',
                    color: exhausted ? '#fca5a5' : '#94a3b8',
                }}
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', minWidth: 120 }}>
                    <span style={{ fontWeight: 600, color: exhausted ? '#fca5a5' : '#e2e8f0' }}>
                        {exhausted ? '🚫 Scan limit reached' : `${remaining} scan${remaining !== 1 ? 's' : ''} left`}
                    </span>
                    {/* Progress bar */}
                    <div
                        style={{
                            height: 4,
                            borderRadius: 4,
                            background: '#1e293b',
                            border: '1px solid #334155',
                            overflow: 'hidden',
                            width: '100%',
                        }}
                    >
                        <div
                            style={{
                                height: '100%',
                                width: `${pct}%`,
                                borderRadius: 4,
                                background: exhausted
                                    ? 'linear-gradient(90deg, #ef4444, #dc2626)'
                                    : pct >= 66
                                        ? 'linear-gradient(90deg, #f59e0b, #d97706)'
                                        : 'linear-gradient(90deg, #3b82f6, #2563eb)',
                                transition: 'width 0.4s ease',
                            }}
                        />
                    </div>
                    <span style={{ fontSize: 10, color: '#64748b' }}>
                        {used} / {FREE_LIMIT} this month
                    </span>
                </div>

                <button
                    onClick={() => setShowUpgrade(true)}
                    style={{
                        padding: '4px 10px',
                        borderRadius: 6,
                        fontSize: 11,
                        fontWeight: 700,
                        border: '1px solid #f59e0b88',
                        background: 'linear-gradient(135deg, #f59e0b22, #d9770611)',
                        color: '#f59e0b',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                        transition: 'all 0.15s',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'linear-gradient(135deg, #f59e0b44, #d9770633)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'linear-gradient(135deg, #f59e0b22, #d9770611)')}
                >
                    Upgrade ↑
                </button>
            </div>

            {showUpgrade && <UpgradeModal onClose={() => setShowUpgrade(false)} />}
        </>
    )
}
