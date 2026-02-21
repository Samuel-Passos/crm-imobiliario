import { useState, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../contexts/AuthContext'
import type { Profile } from '../contexts/AuthContext'

export function useProfile() {
    const { profile, updateProfile } = useAuth()
    const [saving, setSaving] = useState(false)

    const save = useCallback(async (data: Partial<Profile>) => {
        setSaving(true)
        const result = await updateProfile(data)
        setSaving(false)
        return result
    }, [updateProfile])

    const fetchByUserId = async (userId: string) => {
        const { data, error } = await supabase
            .from('profiles')
            .select('*')
            .eq('user_id', userId)
            .single()
        return { data, error }
    }

    return { profile, save, saving, fetchByUserId }
}
