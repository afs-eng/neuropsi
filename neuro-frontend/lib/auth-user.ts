export interface AuthUser {
  username?: string;
  full_name?: string;
  display_name?: string;
  role?: string;
  specialty?: string;
  sex?: string;
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") {
    return null;
  }

  const savedUser = localStorage.getItem("user");
  if (!savedUser) {
    return null;
  }

  try {
    const parsed = JSON.parse(savedUser);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}
