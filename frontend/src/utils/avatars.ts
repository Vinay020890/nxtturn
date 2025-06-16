// This function takes a user's picture URL and their first name.
// It returns the real picture URL if it exists, otherwise it creates a placeholder.
export function getAvatarUrl(pictureUrl: string | null | undefined, firstName: string | undefined, lastName: string | undefined): string {
  
  // If a real picture URL is provided, use it.
  if (pictureUrl) {
    return pictureUrl;
  }

  // If no picture, create a name for the placeholder.
  // Use first and last name, or just "User" if names are missing.
  const name = (firstName && lastName) ? `${firstName}+${lastName}` : 'User';

  // Return the URL for the placeholder avatar.
  return `https://api.dicebear.com/8.x/rings/svg?seed=${name}`;
}