/**
 * Validation utilities and constants for AFTR platform
 */

export const LIMITS = {
  INVITE_EXPIRATION_HOURS: 72,
  INITIAL_INVITE_QUOTA: 3,
  MIN_AGE: 18,
  DISPLAY_NAME_MIN: 3,
  DISPLAY_NAME_MAX: 30,
  CONFESSION_MIN: 10,
  CONFESSION_MAX: 2000,
  BIO_MAX: 280,
  COMMENT_MAX: 500,
} as const;

// Patterns to prevent doxxing and leaks
export const PII_PATTERNS = {
  // Common phone formats: 10 digits, with optional country code, dashes, spaces
  PHONE: /(\+?[0-9]{1,3}[-.\s]?)?(\(?[0-9]{2,4}\)?[-.\s]?)[0-9]{3,4}[-.\s]?[0-9]{3,4}/,
  // Standard email regex
  EMAIL: /[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/,
  // Common campus student roll/matriculation patterns
  CAMPUS_ID: /\b(20[1-2][0-9][A-Z]{2,4}[0-9]{4,6}|[0-9]{2}[A-Z]{2,4}[0-9]{3,5})\b/i,
};

export function containsPII(text: string): boolean {
  return (
    PII_PATTERNS.PHONE.test(text) ||
    PII_PATTERNS.EMAIL.test(text) ||
    PII_PATTERNS.CAMPUS_ID.test(text)
  );
}

export function validateAge(birthYear: number): { valid: boolean; reason?: string } {
  const currentYear = new Date().getFullYear();
  const calculatedAge = currentYear - birthYear;
  if (calculatedAge < LIMITS.MIN_AGE) {
    return {
      valid: false,
      reason: `You must be at least ${LIMITS.MIN_AGE} years of age to access AFTR.`,
    };
  }
  if (calculatedAge > 120) {
    return {
      valid: false,
      reason: "Invalid birth year provided.",
    };
  }
  return { valid: true };
}

export function validateDisplayName(name: string): { valid: boolean; reason?: string } {
  const trimmed = name.trim();
  if (trimmed.length < LIMITS.DISPLAY_NAME_MIN || trimmed.length > LIMITS.DISPLAY_NAME_MAX) {
    return {
      valid: false,
      reason: `Display name must be between ${LIMITS.DISPLAY_NAME_MIN} and ${LIMITS.DISPLAY_NAME_MAX} characters.`,
    };
  }
  if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
    return {
      valid: false,
      reason: "Display name may only contain alphanumeric characters, underscores, and hyphens.",
    };
  }
  return { valid: true };
}
