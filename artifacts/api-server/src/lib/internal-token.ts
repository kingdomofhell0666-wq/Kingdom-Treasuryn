import crypto from "crypto";

/**
 * Derive a deterministic internal API token from SESSION_SECRET.
 * The bot derives the same token using the same formula in Python.
 * Formula: sha256(SESSION_SECRET + ':internal')
 */
export function getInternalToken(): string {
  const secret = process.env["SESSION_SECRET"] ?? "dev-secret-change-me";
  return crypto.createHash("sha256").update(`${secret}:internal`).digest("hex");
}
