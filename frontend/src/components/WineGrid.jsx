import React from "react";
import WineCard from "./WineCard";
import "./WineGrid.css";

export default function WineGrid({ wines }) {
  if (!wines?.length) return null;
  return (
    <div className="wg-grid">
      {wines.map((w, i) => <WineCard wine={w} key={i} />)}
    </div>
  );
}
 


