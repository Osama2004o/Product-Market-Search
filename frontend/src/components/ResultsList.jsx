import ResultCard from "./ResultCard";

function SkeletonCard() {
  return (
    <div className="result-card skeleton">
      <div className="skeleton-image shimmer" />
      <div className="skeleton-body">
        <div className="skeleton-line short shimmer" />
        <div className="skeleton-line long shimmer" />
        <div className="skeleton-line medium shimmer" />
      </div>
    </div>
  );
}

export default function ResultsList({ results, isLoading, error, hasSearched }) {
  if (error) {
    return (
      <div className="results-message error-message">
        <span className="error-icon">⚠️</span>
        <p>{error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="results-container">
        <div className="loading-header">
          <div className="pulse-dot" />
          <p>Searching Amazon, Noon & Jumia...</p>
        </div>
        <div className="results-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (hasSearched && results.length === 0) {
    return (
      <div className="results-message empty-message">
        <span className="empty-icon">🔍</span>
        <p>No products found. Try a different search term.</p>
      </div>
    );
  }

  if (!hasSearched) return null;

  return (
    <div className="results-container">
      <div className="results-header">
        <h2>{results.length} product{results.length !== 1 ? "s" : ""} found</h2>
        <span className="results-subtitle">Ranked by best value (price vs. rating)</span>
      </div>
      <div className="results-grid">
        {results.map((product, i) => (
          <ResultCard key={`${product.site}-${product.url}-${i}`} product={product} index={i} />
        ))}
      </div>
    </div>
  );
}
