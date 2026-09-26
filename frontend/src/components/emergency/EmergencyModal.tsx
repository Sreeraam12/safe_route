"use client";

import React, { useEffect, useState } from "react";

function getApiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

function getSOSHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("saferoute_token") || localStorage.getItem("token")
      : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = "Bearer " + token;
  return headers;
}

export interface EmergencyModalProps {
  isOpen: boolean;
  onClose: () => void;
  user?: { name?: string; email?: string } | null;
}

export default function EmergencyModal({ isOpen, onClose, user }: EmergencyModalProps) {
  const [contacts, setContacts] = useState<any[]>([]);
  const [sosHistory, setSosHistory] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"contacts" | "history">("contacts");

  // New contact form state
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [relationship, setRelationship] = useState("Family");

  // Edit contact state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editRelationship, setEditRelationship] = useState("Family");

  const loadData = async () => {
    try {
      const base = getApiBase();
      const [cRes, hRes] = await Promise.all([
        fetch(`${base}/api/emergency/contacts`, { headers: getSOSHeaders() }),
        fetch(`${base}/api/sos/history`, { headers: getSOSHeaders() }),
      ]);
      if (cRes.ok) {
        const cData = await cRes.json();
        setContacts(cData.contacts || cData.items || []);
      }
      if (hRes.ok) {
        const hData = await hRes.json();
        setSosHistory(hData.sos_events || hData.items || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (isOpen) loadData();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanPhone = phone.trim();
    if (!name.trim() || !cleanPhone) return;
    if (!/^\d{10}$/.test(cleanPhone)) {
      setPhoneError("Phone number must be exactly 10 digits (0-9 only).");
      return;
    }
    setPhoneError(null);
    try {
      const res = await fetch(`${getApiBase()}/api/emergency/contacts`, {
        method: "POST",
        headers: getSOSHeaders(),
        body: JSON.stringify({
          contact_name: name,
          phone_number: phone,
          relationship,
          is_primary: contacts.length === 0,
        }),
      });
      if (res.ok) {
        setName("");
        setPhone("");
        loadData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const startEdit = (c: any) => {
    setEditingId(c.contact_id || c.id);
    setEditName(c.contact_name || c.name || "");
    setEditPhone(c.phone_number || "");
    setEditRelationship(c.relationship || "Family");
  };

  const handleSaveEdit = async (id: string) => {
    const cleanEditPhone = editPhone.trim();
    if (!/^\d{10}$/.test(cleanEditPhone)) {
      setPhoneError("Phone number must be exactly 10 digits (0-9 only).");
      return;
    }
    setPhoneError(null);
    try {
      const res = await fetch(`${getApiBase()}/api/emergency/contacts/${id}`, {
        method: "PATCH",
        headers: getSOSHeaders(),
        body: JSON.stringify({
          contact_name: editName,
          phone_number: editPhone,
          relationship: editRelationship,
        }),
      });
      if (res.ok) {
        setEditingId(null);
        loadData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteContact = async (id: string) => {
    try {
      await fetch(`${getApiBase()}/api/emergency/contacts/${id}`, {
        method: "DELETE",
        headers: getSOSHeaders(),
      });
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full overflow-hidden border border-gray-100">
        {/* Profile & Emergency Header */}
        <div className="bg-gradient-to-r from-slate-900 via-red-950 to-red-900 text-white px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-11 w-11 rounded-2xl bg-red-600 flex items-center justify-center text-lg font-extrabold shadow-md">
              {user?.name ? user.name.charAt(0).toUpperCase() : "🛡️"}
            </div>
            <div>
              <h2 className="text-base font-extrabold flex items-center gap-2">
                <span>{user?.name || "SafeRoute User"}</span>
                <span className="text-[10px] bg-red-500/30 border border-red-400/40 px-2 py-0.5 rounded-full uppercase tracking-wider">
                  Profile & SOS Contacts
                </span>
              </h2>
              <p className="text-xs text-red-100/90 mt-0.5">
                {user?.email || "Manage your Trusted Emergency Contacts & SOS Logs"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white text-xl font-bold h-8 w-8 flex items-center justify-center rounded-full hover:bg-white/10"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 bg-gray-50">
          <button
            onClick={() => setActiveTab("contacts")}
            className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider transition ${
              activeTab === "contacts"
                ? "border-b-2 border-red-600 text-red-600 bg-white"
                : "text-gray-500 hover:text-gray-800"
            }`}
          >
            👥 Trusted Contacts ({contacts.length})
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider transition ${
              activeTab === "history"
                ? "border-b-2 border-red-600 text-red-600 bg-white"
                : "text-gray-500 hover:text-gray-800"
            }`}
          >
            🚨 SOS Event History ({sosHistory.length})
          </button>
        </div>

        <div className="p-6 max-h-[72vh] overflow-y-auto">
          {activeTab === "contacts" ? (
            <div className="space-y-4">
              {/* Add New Contact Form */}
              <form onSubmit={handleAddContact} className="bg-red-50/70 p-4 rounded-2xl border border-red-100 space-y-3">
                <div className="text-xs font-extrabold text-red-900 uppercase tracking-wide">
                  + Add Trusted Emergency Contact
                </div>
                {phoneError && (
                  <div className="text-xs font-bold text-red-600 bg-red-100/90 border border-red-300 rounded-lg px-3 py-1.5">
                    ?? {phoneError}
                  </div>
                )}
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Contact Name (e.g., Mom)"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="text-xs p-2.5 border border-gray-300 rounded-xl text-gray-900 bg-white focus:outline-none focus:border-red-500"
                    required
                  />
                  <input
                    type="text"
                    placeholder="10-digit mobile (e.g. 9876543210)"
                    value={phone}
                    maxLength={10}
                    pattern="\d{10}"
                    title="Please enter exactly 10 digits (0-9)"
                    onChange={(e) => {
                      const digitsOnly = e.target.value.replace(/\D/g, "").slice(0, 10);
                      setPhone(digitsOnly);
                      if (phoneError) setPhoneError(null);
                    }}
                    className="text-xs p-2.5 border border-gray-300 rounded-xl text-gray-900 bg-white focus:outline-none focus:border-red-500"
                    required
                  />
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={relationship}
                    onChange={(e) => setRelationship(e.target.value)}
                    className="text-xs p-2.5 border border-gray-300 rounded-xl bg-white text-gray-900 flex-1"
                  >
                    <option value="Family">Family</option>
                    <option value="Parent">Parent</option>
                    <option value="Spouse">Spouse</option>
                    <option value="Friend">Friend</option>
                    <option value="Guardian">Guardian</option>
                  </select>
                  <button
                    type="submit"
                    className="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-4 py-2.5 rounded-xl transition shadow-sm"
                  >
                    Save Contact
                  </button>
                </div>
              </form>

              {/* Contacts List with Edit & Delete */}
              <div className="space-y-2.5">
                {contacts.length === 0 ? (
                  <p className="text-xs text-gray-500 text-center py-6 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
                    No trusted contacts added yet. Add a contact above so they are automatically alerted when you press SOS during navigation.
                  </p>
                ) : (
                  contacts.map((c) => {
                    const cid = c.contact_id || c.id;
                    const isEditing = editingId === cid;
                    return (
                      <div
                        key={cid}
                        className="p-3.5 bg-gray-50 rounded-2xl border border-gray-200 transition"
                      >
                        {isEditing ? (
                          <div className="space-y-2">
                            <div className="grid grid-cols-2 gap-2">
                              <input
                                type="text"
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                                className="text-xs p-2 border border-gray-300 rounded-lg text-gray-900 bg-white"
                              />
                              <input
                                type="text"
                                value={editPhone}
                                maxLength={10}
                                placeholder="10 digits"
                                onChange={(e) => setEditPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
                                className="text-xs p-2 border border-gray-300 rounded-lg text-gray-900 bg-white"
                              />
                            </div>
                            <div className="flex items-center justify-between gap-2">
                              <select
                                value={editRelationship}
                                onChange={(e) => setEditRelationship(e.target.value)}
                                className="text-xs p-2 border border-gray-300 rounded-lg bg-white text-gray-900 flex-1"
                              >
                                <option value="Family">Family</option>
                                <option value="Parent">Parent</option>
                                <option value="Spouse">Spouse</option>
                                <option value="Friend">Friend</option>
                                <option value="Guardian">Guardian</option>
                              </select>
                              <button
                                onClick={() => handleSaveEdit(cid)}
                                className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg"
                              >
                                Save
                              </button>
                              <button
                                onClick={() => setEditingId(null)}
                                className="bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs font-semibold px-3 py-1.5 rounded-lg"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-sm font-bold text-gray-900 flex items-center gap-1.5">
                                <span>{c.contact_name || c.name}</span>
                                <span className="text-[11px] font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-100">
                                  {c.relationship || "Family"}
                                </span>
                                {c.contact_user_id && (
                                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                                    SafeRoute User
                                  </span>
                                )}
                              </div>
                              <div className="text-xs text-gray-600 mt-0.5 font-medium">
                                📞 {c.phone_number}
                              </div>
                            </div>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => startEdit(c)}
                                className="text-xs text-blue-600 hover:bg-blue-50 font-semibold px-2.5 py-1.5 rounded-lg transition"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleDeleteContact(cid)}
                                className="text-xs text-red-600 hover:bg-red-50 font-semibold px-2.5 py-1.5 rounded-lg transition"
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {sosHistory.length === 0 ? (
                <p className="text-xs text-gray-500 text-center py-6">
                  No SOS emergencies triggered yet.
                </p>
              ) : (
                sosHistory.map((ev) => (
                  <div
                    key={ev.sos_id || ev.id}
                    className="p-3.5 rounded-2xl border border-gray-200 bg-gray-50 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-bold text-gray-900">
                        🚨 SOS #{String(ev.sos_id || ev.id).slice(0, 8)} ? {ev.road_name || "Chennai Route"}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        Coords: {Number(ev.latitude ?? ev.latest_lat).toFixed(4)}, {Number(ev.longitude ?? ev.latest_lon).toFixed(4)}
                      </div>
                      {ev.nearest_police_station_name && (
                        <div className="text-[11px] text-red-600 font-semibold mt-0.5">
                          🚓 {ev.nearest_police_station_name} ({ev.nearest_police_station_distance_km} km)
                        </div>
                      )}
                      <div className="text-[11px] text-gray-400 mt-0.5">
                        Triggered: {ev.triggered_at || ev.created_at}
                      </div>
                    </div>
                    <span
                      className={`text-xs font-bold px-2.5 py-1 rounded-full uppercase ${
                        ev.status === "ACTIVE" || ev.status === "active"
                          ? "bg-red-100 text-red-700"
                          : "bg-emerald-100 text-emerald-700"
                      }`}
                    >
                      {ev.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
