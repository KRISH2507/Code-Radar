'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useUser } from '@/context/user-context'
import { getAdminUsers, updateUserPlan, AdminUser } from '@/lib/api'
import { ShieldCheck, RefreshCw, Users } from 'lucide-react'

export default function AdminPage() {
    const { user, loading } = useUser()
    const router = useRouter()

    const [users, setUsers] = useState<AdminUser[]>([])
    const [total, setTotal] = useState(0)
    const [fetching, setFetching] = useState(true)
    const [updatingId, setUpdatingId] = useState<number | null>(null)
    const [toastMsg, setToastMsg] = useState('')

    // ── Guard: redirect non-admins ───────────────────────────────────────────
    useEffect(() => {
        if (!loading && (!user || user.role !== 'admin')) {
            router.replace('/dashboard')
        }
    }, [user, loading, router])

    const fetchUsers = useCallback(async () => {
        setFetching(true)
        const res = await getAdminUsers()
        if (res.data) {
            setUsers(res.data.users)
            setTotal(res.data.total)
        }
        setFetching(false)
    }, [])

    useEffect(() => {
        if (user?.role === 'admin') fetchUsers()
    }, [user, fetchUsers])

    const handlePlanToggle = async (targetUser: AdminUser) => {
        const newPlan = targetUser.plan === 'free' ? 'pro' : 'free'
        setUpdatingId(targetUser.id)
        const res = await updateUserPlan(targetUser.id, newPlan)
        if (!res.error) {
            setUsers(prev =>
                prev.map(u => u.id === targetUser.id ? { ...u, plan: newPlan } : u)
            )
            setToastMsg(`${targetUser.email} → ${newPlan.toUpperCase()}`)
            setTimeout(() => setToastMsg(''), 3000)
        }
        setUpdatingId(null)
    }

    if (loading || !user) return null

    // ── Render ───────────────────────────────────────────────────────────────
    return (
        <div style={{
            minHeight: '100vh',
            background: 'var(--background, #0f172a)',
            padding: '2rem',
            fontFamily: 'inherit',
        }}>
            {/* Toast */}
            {toastMsg && (
                <div style={{
                    position: 'fixed', top: 20, right: 20, zIndex: 999,
                    background: '#14532d', border: '1px solid #16a34a',
                    color: '#86efac', borderRadius: 8, padding: '10px 18px',
                    fontSize: 13, fontWeight: 600, boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                }}>
                    ✓ Updated: {toastMsg}
                </div>
            )}

            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                        width: 40, height: 40, borderRadius: 10,
                        background: 'linear-gradient(135deg, #f59e0b33, #d9770611)',
                        border: '1px solid #f59e0b44',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                        <ShieldCheck size={20} color="#f59e0b" />
                    </div>
                    <div>
                        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#f1f5f9' }}>Admin Panel</h1>
                        <p style={{ margin: 0, fontSize: 13, color: '#64748b' }}>
                            {total} user{total !== 1 ? 's' : ''} total
                        </p>
                    </div>
                </div>

                <button
                    onClick={fetchUsers}
                    disabled={fetching}
                    style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        padding: '8px 16px', borderRadius: 8,
                        background: '#1e293b', border: '1px solid #334155',
                        color: '#94a3b8', cursor: 'pointer', fontSize: 13,
                        opacity: fetching ? 0.5 : 1,
                    }}
                >
                    <RefreshCw size={14} style={{ animation: fetching ? 'spin 1s linear infinite' : 'none' }} />
                    Refresh
                </button>
            </div>

            {/* Stats row */}
            <div style={{ display: 'flex', gap: 12, marginBottom: '1.5rem' }}>
                {[
                    { label: 'Total Users', value: total, color: '#3b82f6' },
                    { label: 'Pro Users', value: users.filter(u => u.plan === 'pro').length, color: '#f59e0b' },
                    { label: 'Free Users', value: users.filter(u => u.plan === 'free').length, color: '#64748b' },
                ].map(stat => (
                    <div key={stat.label} style={{
                        flex: 1, padding: '16px 20px', borderRadius: 12,
                        background: '#1e293b', border: '1px solid #334155',
                    }}>
                        <p style={{ margin: 0, fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                            {stat.label}
                        </p>
                        <p style={{ margin: '4px 0 0', fontSize: 26, fontWeight: 800, color: stat.color }}>
                            {stat.value}
                        </p>
                    </div>
                ))}
            </div>

            {/* Table */}
            <div style={{
                background: '#1e293b', borderRadius: 14,
                border: '1px solid #334155', overflow: 'hidden',
            }}>
                {/* Table header */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr 120px 100px 120px',
                    padding: '12px 20px',
                    borderBottom: '1px solid #334155',
                    fontSize: 11, fontWeight: 700,
                    color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em',
                }}>
                    <span>User</span>
                    <span>Email</span>
                    <span>Plan</span>
                    <span>Scans</span>
                    <span>Action</span>
                </div>

                {fetching ? (
                    <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
                        <Users size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
                        <p>Loading users…</p>
                    </div>
                ) : users.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
                        <Users size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
                        <p>No users found.</p>
                    </div>
                ) : (
                    users.map((u, i) => (
                        <div
                            key={u.id}
                            style={{
                                display: 'grid',
                                gridTemplateColumns: '1fr 1fr 120px 100px 120px',
                                padding: '14px 20px',
                                alignItems: 'center',
                                borderBottom: i < users.length - 1 ? '1px solid #1e293b88' : 'none',
                                background: i % 2 === 0 ? 'transparent' : '#ffffff04',
                                transition: 'background 0.15s',
                            }}
                        >
                            {/* Name */}
                            <div>
                                <p style={{ margin: 0, fontWeight: 600, color: '#e2e8f0', fontSize: 14 }}>
                                    {u.name ?? '—'}
                                </p>
                                <p style={{ margin: 0, fontSize: 11, color: '#64748b' }}>ID #{u.id}</p>
                            </div>

                            {/* Email */}
                            <p style={{ margin: 0, fontSize: 13, color: '#94a3b8' }}>{u.email}</p>

                            {/* Plan Badge */}
                            <span style={{
                                display: 'inline-flex', alignItems: 'center',
                                padding: '3px 10px', borderRadius: 9999,
                                fontSize: 11, fontWeight: 700, letterSpacing: '0.06em',
                                textTransform: 'uppercase', border: '1px solid',
                                ...(u.plan === 'pro'
                                    ? { background: '#f59e0b22', borderColor: '#f59e0b66', color: '#f59e0b' }
                                    : { background: '#3b82f622', borderColor: '#3b82f666', color: '#60a5fa' }),
                            }}>
                                {u.plan === 'pro' ? '⚡ Pro' : 'Free'}
                            </span>

                            {/* Scan count */}
                            <p style={{ margin: 0, fontSize: 14, color: '#94a3b8' }}>
                                {u.scan_count} <span style={{ fontSize: 11, color: '#475569' }}>this mo.</span>
                            </p>

                            {/* Toggle button */}
                            <button
                                onClick={() => handlePlanToggle(u)}
                                disabled={updatingId === u.id}
                                style={{
                                    padding: '6px 14px', borderRadius: 7, fontSize: 12, fontWeight: 600,
                                    border: '1px solid',
                                    cursor: updatingId === u.id ? 'wait' : 'pointer',
                                    opacity: updatingId === u.id ? 0.6 : 1,
                                    transition: 'all 0.15s',
                                    ...(u.plan === 'free'
                                        ? { background: '#f59e0b22', borderColor: '#f59e0b66', color: '#f59e0b' }
                                        : { background: '#ef444422', borderColor: '#ef444466', color: '#f87171' }),
                                }}
                            >
                                {updatingId === u.id
                                    ? '…'
                                    : u.plan === 'free' ? '↑ Upgrade' : '↓ Downgrade'}
                            </button>
                        </div>
                    ))
                )}
            </div>

            {/* Keyframe for spinner */}
            <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
        </div>
    )
}
