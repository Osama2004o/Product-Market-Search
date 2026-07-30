import { useState } from "react";
import SearchBar from "./components/SearchBar";
import ResultsList from "./components/ResultsList";
import { searchProducts } from "./api/searchApi";
import "./index.css";

export default function App() {
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [warnings, setWarnings] = useState([]);

  const handleSearch = async (query) => {
    setIsLoading(true);
    setError(null);
    setWarnings([]);
    setHasSearched(true);

    try {
      const data = await searchProducts(query);
      setResults(data.results || []);
      setWarnings(data.warnings || []);
    } catch (err) {
      setError(err.message || "Something went wrong.");
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      {/* Animated background blobs */}
      <div className="bg-blob blob-1" />
      <div className="bg-blob blob-2" />
      <div className="bg-blob blob-3" />

      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">🔎</span>
          <h1>MarketLens</h1>
        </div>
        <p className="tagline">
          Compare prices across <strong>Amazon</strong>, <strong>Noon</strong> &amp; <strong>Jumia</strong> — find the best deal instantly.
        </p>
      </header>

      <main className="app-main">
        <SearchBar onSearch={handleSearch} isLoading={isLoading} />

        {warnings.length > 0 && (
          <div className="warnings-bar">
            {warnings.map((w, i) => (
              <span key={i} className="warning-item">⚠ {w}</span>
            ))}
          </div>
        )}

        <ResultsList
          results={results}
          isLoading={isLoading}
          error={error}
          hasSearched={hasSearched}
        />
      </main>

      <footer className="app-footer">
        <p>MarketLens — Powered by AI agents & live scraping</p>
      </footer>
    </div>
  );
}
