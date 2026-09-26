"use client";

import { useState } from "react";
import { loginUser, registerUser } from "../../services/routeApi";
import type { UserProfile } from "../../types/route";

interface LoginPageProps {
  onLoginSuccess: (user: UserProfile) => void;
}

export function SafeRouteLogo({ className = "w-12 h-12" }: { className?: string }) {
  return (
    <div
      className={`relative flex items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-500 shadow-xl shadow-emerald-500/20 ${className}`}
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="w-3/5 h-3/5 text-white drop-shadow"
      >
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <path d="m9 12 2 2 4-4" />
      </svg>
    </div>
  );
}

export default function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [trustedContactName, setTrustedContactName] = useState("");
  const [trustedContactPhone, setTrustedContactPhone] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isLogin) {
        const res = await loginUser(email.trim(), password);
        onLoginSuccess(res.user);
      } else {
        if (!name.trim()) {
          setError("Please enter your full name.");
          setLoading(false);
          return;
        }
        if (password.length < 6) {
          setError("Password must be at least 6 characters.");
          setLoading(false);
          return;
        }
        const res = await registerUser(email.trim(), password, name.trim());
        onLoginSuccess(res.user);
      }
    } catch (err: any) {
      const msg = err.message || "";
      if (isLogin) {
        if (msg.includes("connect")) {
          setError("Unable to connect to SafeRoute server. Please ensure the backend is running on port 8000.");
        } else {
          setError("Invalid credentials");
        }
      } else {
        // Create account
        if (msg.includes("connect")) {
          setError("Unable to connect to SafeRoute server. Please ensure the backend is running on port 8000.");
        } else if (msg.toLowerCase().includes("already exists")) {
          setError("An account with this email already exists.");
        } else {
          setError(msg || "Registration failed. Please check your details.");
        }
      }
    } finally {
      setLoading(false);
    }
  };

  // Quick 1-click Demo Login
  const handleDemoLogin = async () => {
    setError("");
    setLoading(true);
    const demoEmail = "demo@saferoute.chennai";
    const demoPass = "SafeRoute2026!";
    const demoName = "Chennai Traveler";

    try {
      try {
        const res = await loginUser(demoEmail, demoPass);
        onLoginSuccess(res.user);
        return;
      } catch (e: any) {
        if (e.message?.includes("connect")) {
          throw e;
        }
        // If demo user doesn't exist yet, auto-register
        const res = await registerUser(demoEmail, demoPass, demoName);
        onLoginSuccess(res.user);
      }
    } catch (err: any) {
      if (err.message?.includes("connect")) {
        setError("Unable to connect to SafeRoute server. Please ensure the backend is running on port 8000.");
      } else {
        setError("Invalid credentials");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen w-full items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 p-4 text-slate-100 overflow-hidden">
      {/* Decorative ambient background glows */}
      <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-emerald-500/15 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-teal-500/15 blur-3xl" />

      <div className="relative w-full max-w-md rounded-3xl border border-white/10 bg-slate-900/80 p-8 shadow-2xl backdrop-blur-2xl">
        {/* Header with Logo */}
        <div className="flex flex-col items-center text-center">
          <SafeRouteLogo className="w-16 h-16 mb-4" />
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            SafeRoute
          </h1>
          <p className="mt-2 text-xs font-medium text-emerald-400 max-w-xs leading-relaxed">
            Smart, Time-Aware Safe Route Prediction & Real-Time Navigation for Women in Chennai
          </p>
        </div>

        {/* Auth Tab Switcher */}
        <div className="mt-8 flex rounded-2xl bg-slate-800/80 p-1 border border-white/5">
          <button
            type="button"
            onClick={() => {
              setIsLogin(true);
              setError("");
            }}
            className={`flex-1 rounded-xl py-2 text-xs font-bold transition-all ${
              isLogin
                ? "bg-emerald-600 text-white shadow-lg shadow-emerald-600/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setIsLogin(false);
              setError("");
            }}
            className={`flex-1 rounded-xl py-2 text-xs font-bold transition-all ${
              !isLogin
                ? "bg-emerald-600 text-white shadow-lg shadow-emerald-600/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/15 p-3 text-xs text-red-200 font-semibold flex items-center gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Full Name
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
                className="w-full rounded-xl border border-white/10 bg-slate-800/90 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={isLogin ? "Enter your registered email id" : "Enter your email id"}
              className="w-full rounded-xl border border-white/10 bg-slate-800/90 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full rounded-xl border border-white/10 bg-slate-800/90 px-3.5 py-2.5 pr-10 text-xs text-white placeholder-slate-500 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-emerald-400 transition focus:outline-none"
                title={showPassword ? "Hide password" : "Show password"}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="w-4 h-4"
                  >
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="w-4 h-4"
                  >
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 py-3 text-xs font-bold text-white shadow-lg shadow-emerald-600/30 transition hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50"
          >
            {loading ? "Authenticating..." : isLogin ? "Sign In to SafeRoute" : "Create Account"}
          </button>
        </form>

        {/* Quick Demo Access Button */}
        <div className="mt-5 border-t border-white/10 pt-4">
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 py-2.5 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-500/20"
          >
            <span>⚡</span> Quick Demo Sign In (1-Click)
          </button>
        </div>

        {/* Feature Badges */}
        <div className="mt-6 grid grid-cols-2 gap-2 text-[10px] text-slate-400 border-t border-white/5 pt-4">
          <div className="flex items-center gap-1.5">
            <span className="text-emerald-400">🛡️</span> 35-Feature ML Risk
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-teal-400">🌙</span> Time Vulnerability
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-purple-400">🧬</span> Personal Digital Twin
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-blue-400">📍</span> Live GPS Re-Routing
          </div>
        </div>
      </div>
    </div>
  );
}

