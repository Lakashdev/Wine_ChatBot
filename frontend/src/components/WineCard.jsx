import React, { useState } from "react";
import "./WineCard.css";

const NO_IMG =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200">
       <rect width="100%" height="100%" fill="#f3f4f6"/>
       <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
             font-family="Arial" font-size="16" fill="#9aa0a6">No Image</text>
     </svg>`
  );

function toChips(s) {
  if (!s) return [];
  return s
    .split("|")
    .map(x => x.trim())
    .filter(Boolean)
    .slice(0, 8); // cap how many we show
}

const ChipRow = ({ label, value }) => {
  const chips = toChips(value);
  if (!chips.length) return null;
  return (
    <div className="wc-row">
      <span className="wc-label">{label}</span>
      <div className="wc-chips">
        {chips.map((c, i) => (
          <span key={i} className="wc-chip">{c}</span>
        ))}
      </div>
    </div>
  );
};

export default function WineCard({ wine }) {
  const [imgSrc, setImgSrc] = useState(wine.image || NO_IMG);
  console.log(imgSrc, wine.image);

  return (
    <article className="wc-card">
      <div className="wc-media">
        <img
          src={imgSrc}
          alt={wine.title || "Wine image"}
          loading="lazy"
          onError={() => setImgSrc(NO_IMG)}
        />
      </div>

      <div className="wc-body">
        <h3 className="wc-title" title={wine.title || ""}>
          {wine.title || "Unnamed wine"}
        </h3>

        <div className="wc-badges">
          {wine.region ? <span className="wc-badge">{wine.region}</span> : null}
          {wine.type ? <span className="wc-badge wc-badge--muted">{wine.type}</span> : null}
        </div>

        {wine.profile ? (
          <p className="wc-profile" title={wine.profile}>{wine.profile}</p>
        ) : null}

        <ChipRow label="Aromas" value={wine.aromas} />
        <ChipRow label="Pairs with" value={wine.pairing} />

        {(wine.price || wine.alcohol) && (
          <div className="wc-stats">
            {wine.price ? <span>💲 {String(wine.price).replace(/\.0$/, "")}</span> : <span />}
            {wine.alcohol ? <span>🍷 {wine.alcohol}</span> : null}
          </div>
        )}

        <div className="wc-actions">
          {wine.permalink ? (
            <a className="wc-btn" href={wine.permalink} target="_blank" rel="noreferrer">
              Buy
            </a>
          ) : (
            <button className="wc-btn wc-btn--muted" disabled>No link</button>
          )}
        </div>
      </div>
    </article>
  );
}
