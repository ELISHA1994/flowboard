/**
 * In-memory token storage for access tokens.
 * Refresh tokens are stored in HttpOnly cookies.
 */
class TokenStorage {
  private static instance: TokenStorage;
  private accessToken: string | null = null;
  private tokenExpiry: Date | null = null;

  private constructor() {}

  static getInstance(): TokenStorage {
    if (!TokenStorage.instance) {
      TokenStorage.instance = new TokenStorage();
    }
    return TokenStorage.instance;
  }

  setAccessToken(token: string, expiresIn: number): void {
    this.accessToken = token;
    // Calculate expiry time (expiresIn is in seconds)
    this.tokenExpiry = new Date(Date.now() + expiresIn * 1000);
  }

  getAccessToken(): string | null {
    // Check if token is expired
    if (this.tokenExpiry && new Date() >= this.tokenExpiry) {
      this.clearAccessToken();
      return null;
    }
    return this.accessToken;
  }

  clearAccessToken(): void {
    this.accessToken = null;
    this.tokenExpiry = null;
  }

  isTokenExpired(): boolean {
    if (!this.tokenExpiry) return true;
    return new Date() >= this.tokenExpiry;
  }

  getTokenExpiry(): Date | null {
    return this.tokenExpiry;
  }
}

export const tokenStorage = TokenStorage.getInstance();
