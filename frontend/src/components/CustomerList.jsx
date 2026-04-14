import { useEffect, useState } from "react";
import { api } from "../api";

const s = {
  root: { display: "flex", flexDirection: "column", gap: 12 },
  toolbar: { display: "flex", gap: 10, alignItems: "center" },
  search: {
    flex: 1,
    padding: "10px 14px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: "0.9rem",
    outline: "none",
  },
  searchBtn: {
    padding: "10px 16px",
    background: "#1a1a1a",
    color: "#fff",
    borderRadius: 8,
    fontSize: "0.85rem",
  },
  clearBtn: {
    padding: "10px 12px",
    background: "#f0f0f0",
    color: "#555",
    borderRadius: 8,
    fontSize: "0.85rem",
  },
  card: {
    background: "#fff",
    border: "1px solid #eee",
    borderRadius: 10,
    padding: "14px 16px",
    cursor: "pointer",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    boxShadow: "0 1px 3px rgba(0,0,0,.05)",
    transition: "box-shadow 0.15s",
  },
  name: { fontWeight: 600 },
  meta: { fontSize: "0.82rem", color: "#777", marginTop: 3 },
  badge: (active) => ({
    fontSize: "0.72rem",
    padding: "3px 9px",
    borderRadius: 20,
    background: active ? "#d1fae5" : "#fee2e2",
    color: active ? "#065f46" : "#991b1b",
    fontWeight: 600,
    flexShrink: 0,
  }),
  empty: { color: "#999", textAlign: "center", padding: 48 },
  error: { color: "#dc2626", padding: 12, background: "#fef2f2", borderRadius: 8 },
};

export default function CustomerList({ onSelect }) {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  function load(email = "") {
    setLoading(true);
    setError(null);
    api.getCustomers(email)
      .then(setCustomers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  function handleSearch(e) {
    e.preventDefault();
    setQuery(search);
    load(search);
  }

  function handleClear() {
    setSearch("");
    setQuery("");
    load();
  }

  return (
    <div style={s.root}>
      <form style={s.toolbar} onSubmit={handleSearch}>
        <input
          style={s.search}
          placeholder="Rechercher par email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit" style={s.searchBtn}>Rechercher</button>
        {query && <button type="button" style={s.clearBtn} onClick={handleClear}>✕</button>}
      </form>

      {loading ? (
        <p style={s.empty}>Chargement…</p>
      ) : error ? (
        <p style={s.error}>⚠ {error}</p>
      ) : customers.length === 0 ? (
        <p style={s.empty}>Aucun client trouvé.</p>
      ) : (
        customers.map((c) => (
          <div key={c.id} style={s.card} onClick={() => onSelect(c.id)}>
            <div>
              <div style={s.name}>{c.first_name} {c.last_name}</div>
              <div style={s.meta}>{c.email} · {c.phone}</div>
            </div>
            <span style={s.badge(c.is_active)}>{c.is_active ? "Actif" : "Inactif"}</span>
          </div>
        ))
      )}
    </div>
  );
}
