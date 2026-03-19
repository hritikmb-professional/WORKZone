"use client";
import { Sun, Moon, Bell, Search, LogOut } from "lucide-react";
import { useTheme } from "@/lib/theme";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Topbar({ title }: { title?: string }) {
  const { theme, toggle } = useTheme();
  const [search, setSearch] = useState("");
  const router = useRouter();

  const handleLogout = () => {
    localStorage.clear();
    router.push("/login");
  };

  return (
    <header style={{
      height: 56,
      background: "var(--surface)",
      borderBottom: "1px solid var(--border)",
      display: "flex",
      alignItems: "center",
      padding: "0 20px",
      gap: 12,
      flexShrink: 0,
    }}>
      {title && (
        <h1 style={{
          fontFamily: "var(--font-display)",
          fontWeight: 700,
          fontSize: 16,
          color: "var(--text-primary)",
          marginRight: "auto",
        }}>{title}</h1>
      )}

      {/* Search */}
      <div style={{
        display: "flex", alignItems: "center", gap: 8,
        background: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "6px 12px",
        flex: title ? "0 0 240px" : 1,
        marginLeft: title ? "auto" : 0,
      }}>
        <Search size={14} color="var(--text-muted)" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search meetings..."
          style={{
            background: "transparent",
            border: "none",
            outline: "none",
            fontSize: 13,
            color: "var(--text-primary)",
            width: "100%",
          }}
          onKeyDown={e => {
            if (e.key === "Enter" && search.trim()) {
              router.push(`/meetings?search=${encodeURIComponent(search)}`);
            }
          }}
        />
      </div>

      {/* Theme toggle */}
      <button onClick={toggle} style={{
        width: 36, height: 36, borderRadius: 8,
        background: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        display: "flex", alignItems: "center", justifyContent: "center",
        cursor: "pointer", color: "var(--text-secondary)",
        transition: "all 0.15s",
      }}>
        {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
      </button>

      {/* Notifications */}
      <button style={{
        width: 36, height: 36, borderRadius: 8,
        background: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        display: "flex", alignItems: "center", justifyContent: "center",
        cursor: "pointer", color: "var(--text-secondary)",
        position: "relative",
      }}>
        <Bell size={16} />
        <span style={{
          position: "absolute", top: 6, right: 6,
          width: 7, height: 7, borderRadius: "50%",
          background: "var(--danger)",
        }} />
      </button>

      {/* Logout */}
      <button onClick={handleLogout} style={{
        width: 36, height: 36, borderRadius: 8,
        background: "var(--bg-secondary)",
        border: "1px solid var(--border)",
        display: "flex", alignItems: "center", justifyContent: "center",
        cursor: "pointer", color: "var(--text-secondary)",
      }}>
        <LogOut size={16} />
      </button>
    </header>
  );
}
