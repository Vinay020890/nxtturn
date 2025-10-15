// C:\Users\Vinay\Project\frontend\src/types/index.ts
// This is the updated single source of truth for all major data shapes.

// --- Core User Types (Unchanged) ---
export interface User {
  id: number
  pk: number
  username: string
  email: string
  first_name: string
  last_name: string
}

export interface CurrentUser extends User {
  profile_picture: string | null
}

// --- Profile Section Types (Unchanged) ---
export interface Education {
  id: number
  school: string
  degree: string | null
  field_of_study: string | null
  start_date: string
  end_date: string | null
  description: string | null
}

export interface Experience {
  id: number
  title: string
  company: string
  location: string | null
  start_date: string
  end_date: string | null
  is_current: boolean
  description: string | null
}

export interface Skill {
  id: number
  name: string
}

// --- UPDATED: The Main UserProfile Type ---
export interface UserProfile {
  user: User

  // --- ADDED AS PER OUR PLAN ---
  display_name: string | null
  headline: string | null
  // --- END OF ADDITION ---

  bio: string | null
  location: string | null
  resume: string | null
  linkedin_url: string | null
  portfolio_url: string | null
  picture: string | null
  updated_at: string

  is_followed_by_request_user: boolean

  relationship_status: {
    connection_status: 'not_connected' | 'request_sent' | 'request_received' | 'connected' | 'self'
  } | null

  skills: Skill[]
  education: Education[]
  experience: Experience[]
  interests: string[]
}

// --- UPDATED: The Payload for Profile Updates ---
export type ProfileUpdatePayload = {
  // --- ADDED AS PER OUR PLAN ---
  display_name?: string | null
  headline?: string | null
  // --- END OF ADDITION ---

  bio?: string | null
  location?: string | null
  linkedin_url?: string | null
  portfolio_url?: string | null
  interests?: string[]
}

// --- Post-Related Types (Preserved from your original file) ---
export interface PostAuthor {
  id: number
  username: string
  first_name: string
  last_name: string
  picture: string | null
}

export interface PostMedia {
  id: number
  media_type: 'image' | 'video'
  file_url: string
}

export interface PollOption {
  id: number
  text: string
  vote_count: number
}

export interface Poll {
  id: number
  question: string
  options: PollOption[]
  total_votes: number
  user_vote: number | null
}

export interface Post {
  id: number
  post_type: string
  author: PostAuthor
  created_at: string
  updated_at: string
  title: string | null
  content: string | null
  media: PostMedia[]
  poll: Poll | null
  like_count: number
  comment_count?: number
  is_liked_by_user: boolean
  content_type_id: number
  object_id: number
  isLiking?: boolean
  isDeleting?: boolean
  isUpdating?: boolean
  group: { id: number; name: string; slug: string } | null
  is_saved: boolean
}
