const API_BASE = "http://127.0.0.1:8000";

const el = {
  riskScore: document.getElementById("risk-score"),
  riskLevel: document.getElementById("risk-level"),
  recommendation: document.getElementById("recommendation"),
  tokenPrice: document.getElementById("token-price"),
  volume: document.getElementById("volume"),
  liquidity: document.getElementById("liquidity"),
  alerts: document.getElementById("alerts"),
};

function fmt(n) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(n);
}

async function loadSnapshot() {
  const res = await fetch(`${API_BASE}/api/snapshot`);
  const data = await res.json();
  el.riskScore.textContent = data.risk_score;
  el.riskLevel.textContent = data.risk_level.toUpperCase();
  el.recommendation.textContent = data.recommendation.toUpperCase();
  el.tokenPrice.textContent = `$${data.token_price}`;
  el.volume.textContent = `$${fmt(data.volume_24h)}`;
  el.liquidity.textContent = `$${fmt(data.liquidity)}`;
}

async function loadAlerts() {
  const res = await fetch(`${API_BASE}/api/alerts`);
  const data = await res.json();
  el.alerts.innerHTML = "";
  if (!data.length) {
    const li = document.createElement("li");
    li.textContent = "No medium/high alerts yet.";
    el.alerts.appendChild(li);
    return;
  }

  data.slice(0, 10).forEach((alert) => {
    const li = document.createElement("li");
    li.textContent = `[${alert.risk_level.toUpperCase()}] score=${alert.risk_score}, rec=${alert.recommendation.toUpperCase()}, tx=${alert.on_chain_txn}`;
    el.alerts.appendChild(li);
  });
}

async function refresh() {
  try {
    await Promise.all([loadSnapshot(), loadAlerts()]);
  } catch (err) {
    console.error("Dashboard refresh failed:", err);
  }
}

refresh();
setInterval(refresh, 5000);
