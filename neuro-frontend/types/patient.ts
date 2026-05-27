export interface Patient {
  id: number
  full_name: string
  birth_date: string
  sex: string
  schooling?: string
  school_name?: string
  grade_year?: string
  mother_name?: string
  father_name?: string
  phone?: string
  email?: string | null
  city?: string
  state?: string
  notes?: string
  responsible_name?: string
  responsible_phone?: string
  created_at?: string
}
