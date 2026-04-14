import { useEffect, useState } from "react";
import { api } from "../api";

const STATUS_LABEL = { draft: "Brouillon", confirmed: "Confirmée", cancelled: "Annulée" };
const STATUS_COLOR = {
  draft: { background: "#fef9c3", color: "#854d0e" },
  confirmed: { background: "#d1fae5", color: "#065f46" },
  cancelled: { background: "#fee2e2", color: "#991b1b" },
};

const s = {
  root: { display: "flex", flexDirection: "column", gap: 12 },
  card: {
    background: "#fff",
    border: "1px solid #eee",
    borderRadius: 10,
    padding: "14px 16px",
    boxShadow: "0 1px 3px rgba(0,0,0,.05)",
  },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  id: { fontWeight: 700 },
  meta: { fontSize: "0.82rem", color: "#777", marginTop: 2 },
  badge: (status) => ({
    fontSize: "0.72rem",
    padding: "3px 9px",
    borderRadius: 20,
    fontWeight: 600,
    flexShrink: 0,
    ...STATUS_COLOR[status],
  }),
  total: { fontWeight: 800, fontSize: "1rem" },
  items: { marginTop: 10, borderTop: "1px solid #f0f0f0", paddingTop: 10, display: "flex", flexDirection: "column", gap: 4 },
  item: { fontSize: "0.82rem", color: "#444", display: "flex", justifyContent: "space-between" },
  empty: { color: "#999", textAlign: "center", padding: 48 },
  error: { color: "#dc2626", padding: 12, background: "#fef2f2", borderRadius: 8 },
};

function formatDate(iso) {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" });
}

export default function OrderList({ refreshKey }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api.getOrders()
      .then((data) => setOrders(Array.isArray(data) ? data : data.results ?? []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [refreshKey]);

  if (loading) return <p style={s.empty}>Chargement…</p>;
  if (error) return <p style={s.error}>⚠ {error}</p>;
  if (orders.length === 0) return <p style={s.empty}>Aucune commande.</p>;

  return (
    <div style={s.root}>
      {orders.map((o) => (
        <div key={o.id} style={s.card}>
          <div style={s.header}>
            <div>
              <div style={s.id}>Commande #{o.id}</div>
              <div style={s.meta}>Client #{o.customer_id} · {formatDate(o.created_at)}</div>
            </div>
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <span style={s.total}>{parseFloat(o.total_amount).toFixed(2)} €</span>
              <span style={s.badge(o.status)}>{STATUS_LABEL[o.status] ?? o.status}</span>
            </div>
          </div>
          {o.items?.length > 0 && (
            <div style={s.items}>
              {o.items.map((item, i) => (
                <div key={i} style={s.item}>
                  <span>{item.product_name} × {item.quantity}</span>
                  <span>{parseFloat(item.line_total).toFixed(2)} €</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
