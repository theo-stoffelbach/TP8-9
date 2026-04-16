import { useEffect, useState } from "react";
import { api } from "../api";

const PAGE_SIZE = 20;

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
  pagination: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    marginTop: 4,
  },
  pageBtn: (disabled) => ({
    padding: "7px 14px",
    borderRadius: 8,
    fontSize: "0.85rem",
    background: disabled ? "#f0f0f0" : "#1a1a1a",
    color: disabled ? "#aaa" : "#fff",
    cursor: disabled ? "not-allowed" : "pointer",
    border: "none",
  }),
  pageInfo: { fontSize: "0.85rem", color: "#555", minWidth: 100, textAlign: "center" },
};

export default function CustomerList({ onSelect }) {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  function load(email = "", targetPage = 1) {
    setLoading(true);
    setError(null);
    api.getCustomers({ email, page: targetPage, pageSize: PAGE_SIZE })
      .then((data) => {
        setCustomers(data.results);
        setTotal(data.count);
        setTotalPages(data.total_pages);
        setPage(targetPage);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  function handleSearch(e) {
    e.preventDefault();
    setQuery(search);
    load(search, 1);
  }

  function handleClear() {
    setSearch("");
    setQuery("");
    load("", 1);
  }

  function goTo(targetPage) {
    load(query, targetPage);
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
        <>
          {customers.map((c) => (
            <div key={c.id} style={s.card} onClick={() => onSelect(c.id)}>
              <div>
                <div style={s.name}>{c.first_name} {c.last_name}</div>
                <div style={s.meta}>{c.email} · {c.phone}</div>
              </div>
              <span style={s.badge(c.is_active)}>{c.is_active ? "Actif" : "Inactif"}</span>
            </div>
          ))}

          <div style={s.pagination}>
            <button
              style={s.pageBtn(page <= 1)}
              disabled={page <= 1}
              onClick={() => goTo(page - 1)}
            >
              ← Précédent
            </button>
            <span style={s.pageInfo}>
              Page {page} / {totalPages}
              <br />
              <span style={{ fontSize: "0.75rem", color: "#999" }}>{total} client{total > 1 ? "s" : ""}</span>
            </span>
            <button
              style={s.pageBtn(page >= totalPages)}
              disabled={page >= totalPages}
              onClick={() => goTo(page + 1)}
            >
              Suivant →
            </button>
          </div>
        </>
      )}
    </div>
  );
}
