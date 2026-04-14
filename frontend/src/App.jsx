import { useState } from "react";
import CustomerDetail from "./components/CustomerDetail";
import CustomerForm from "./components/CustomerForm";
import CustomerList from "./components/CustomerList";

const s = {
  header: {
    background: "#1a1a1a",
    color: "#fff",
    padding: "0 24px",
    height: 56,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    position: "sticky",
    top: 0,
    zIndex: 10,
  },
  logo: { fontWeight: 800, fontSize: "1.1rem", letterSpacing: "-0.02em" },
  newBtn: {
    padding: "7px 14px",
    background: "#fff",
    color: "#1a1a1a",
    borderRadius: 6,
    fontWeight: 600,
    fontSize: "0.8rem",
  },
  main: { padding: 24, maxWidth: 820, margin: "0 auto" },
};

export default function App() {
  const [selectedId, setSelectedId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  function onCreated() {
    setShowForm(false);
    setRefreshKey((k) => k + 1);
  }

  return (
    <>
      <header style={s.header}>
        <span style={s.logo} onClick={() => { setSelectedId(null); setShowForm(false); }} role="button" tabIndex={0} style={{ ...s.logo, cursor: "pointer" }}>
          Customer Service
        </span>
        <button style={s.newBtn} onClick={() => { setSelectedId(null); setShowForm(true); }}>
          + Nouveau client
        </button>
      </header>

      <main style={s.main}>
        {showForm ? (
          <CustomerForm onCreated={onCreated} onCancel={() => setShowForm(false)} />
        ) : selectedId ? (
          <CustomerDetail id={selectedId} onBack={() => setSelectedId(null)} />
        ) : (
          <CustomerList key={refreshKey} onSelect={setSelectedId} />
        )}
      </main>
    </>
  );
}
