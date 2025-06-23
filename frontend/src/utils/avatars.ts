// src/utils/avatars.ts

// This safely gets the base URL from the environment variables.
// It strips the trailing '/api/' to get just the server's address.
const API_URL_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace('/api/', '');

/**
 * This function now takes a user's picture URL (which can be relative or absolute)
 * and returns a full, usable URL.
 * If no picture URL is provided, it creates a placeholder avatar URL.
 */
export function getAvatarUrl(
  pictureUrl: string | null | undefined, 
  firstName: string | undefined, 
  lastName: string | undefined
): string {
  
  // --- THIS IS THE NEW LOGIC ---
  // If a picture URL exists...
  if (pictureUrl) {
    // ...and it's already a full URL (like from Cloudinary), return it directly.
    if (pictureUrl.startsWith('http')) {
      return pictureUrl;
    }
    // ...otherwise, it's a local relative path, so prepend the backend base URL.
    return `${API_URL_BASE}${pictureUrl}`;
  }
  // --- END OF NEW LOGIC ---

  // If no picture URL was provided, create a placeholder.
  const name = (firstName && lastName) ? `${firstName}+${lastName}` : 'User';
  return `https://api.dicebear.com/8.x/rings/svg?seed=${name}`;
}

// Add this new function to the bottom of src/utils/avatars.ts

/**
 * A simpler utility for general media files that don't have a fallback.
 * It correctly constructs the full URL for local or production environments.
 * @param url The relative or absolute path from the API.
 * @returns The full, usable URL or an empty string if the input is invalid.
 */
export function buildMediaUrl(url: string | null | undefined): string {
  if (!url) {
    return ''; // Return an empty string to avoid broken image icons
  }
  
  if (url.startsWith('http')) {
    return url; // It's already a full URL (from Cloudinary)
  }
  
  // It's a local relative path, so prepend the backend base URL.
  return `${API_URL_BASE}${url}`;
}