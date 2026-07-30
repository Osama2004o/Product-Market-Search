const SITE_COLORS = {
  amazon: { bg: "#FF9900", text: "#111" },
  noon: { bg: "#F5D100", text: "#111" },
  jumia: { bg: "#F68B1E", text: "#fff" },
};

function StarRating({ rating }) {
  if (rating == null) return <span className="no-rating">No rating</span>;
  const full = Math.floor(rating);
  const half = rating - full >= 0.25;
  const empty = 5 - full - (half ? 1 : 0);

  return (
    <span className="stars" title={`${rating.toFixed(1)} / 5`}>
      {"★".repeat(full)}
      {half && "½"}
      {"☆".repeat(empty)}
      <span className="rating-num">{rating.toFixed(1)}</span>
    </span>
  );
}

export default function ResultCard({ product, index }) {
  const site = product.site?.toLowerCase() || "unknown";
  const colors = SITE_COLORS[site] || { bg: "#666", text: "#fff" };

  return (
    <div className="result-card" style={{ animationDelay: `${index * 0.07}s` }}>
      <div className="card-rank">#{product.rank || index + 1}</div>

      {product.image_url && (
        <div className="card-image">
          <img src={product.image_url} alt={product.title} loading="lazy" />
        </div>
      )}

      <div className="card-body">
        <div className="card-header">
          <span className="site-badge" style={{ background: colors.bg, color: colors.text }}>
            {site}
          </span>
          {product.score != null && (
            <span className="score-badge" title="Value score">
              ⚡ {product.score.toFixed(2)}
            </span>
          )}
        </div>

        <h3 className="card-title">{product.title}</h3>

        <div className="card-meta">
          <div className="card-price">
            {product.price != null ? (
              <>
                <span className="price-value">
                  {product.price.toLocaleString("en-EG", { minimumFractionDigits: 0 })}
                </span>
                <span className="price-currency">{product.currency || "EGP"}</span>
              </>
            ) : (
              <span className="no-price">Price unavailable</span>
            )}
          </div>

          <div className="card-rating">
            <StarRating rating={product.rating} />
            {product.review_count != null && (
              <span className="review-count">({product.review_count.toLocaleString()} reviews)</span>
            )}
          </div>
        </div>

        {product.justification && (
          <p className="card-justification">{product.justification}</p>
        )}

        {product.url && (
          <a className="card-link" href={product.url} target="_blank" rel="noopener noreferrer">
            View on {site} →
          </a>
        )}
      </div>
    </div>
  );
}
