/**
 * API client for Product Market Search backend.
 */

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

export async function searchProducts(query) {
  const response = await fetch(`${API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Search failed (${response.status})`);
  }

  return response.json();
}
