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

export function isFemaleUser(user: AuthUser | null): boolean {
  return user?.sex === "F";
}

export function cleanProfessionalName(name?: string): string {
  return (name || "Profissional").replace(/^(Dr\.|Dra\.|Dr|Dra)\s*/i, "").trim() || "Profissional";
}

export function professionalTitle(user: AuthUser | null): "Dr." | "Dra." {
  return isFemaleUser(user) ? "Dra." : "Dr.";
}

export function professionalDisplayName(user: AuthUser | null, fallback = "Profissional"): string {
  if (!user) {
    return fallback;
  }

  const rawName = user.display_name || user.full_name || user.username || fallback;
  const firstName = cleanProfessionalName(rawName).split(/\s+/)[0];
  return `${professionalTitle(user)} ${firstName}`;
}

export function professionalSpecialty(user: AuthUser | null): string {
  if (user?.specialty) {
    return user.specialty.replace(/neuropsic[oó]log[oa]/i, isFemaleUser(user) ? "Neuropsicóloga" : "Neuropsicólogo");
  }

  return isFemaleUser(user) ? "Neuropsicóloga" : "Neuropsicólogo";
}
