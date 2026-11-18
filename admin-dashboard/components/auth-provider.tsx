"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

type User = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  platform_role: string;
  memberships: { estate_id: string; role: string; status: string }[];
};
type Auth = { user: User | null; ready: boolean; signOut: () => void };
const Context = createContext<Auth>({ user: null, ready: false, signOut: () => {} });
export const useAuth = () => useContext(Context);

async function loadCurrentUser(): Promise<User> {
  let response = await fetch("/api/bff/auth/me/", { credentials: "same-origin", cache: "no-store" });
  for (let attempt = 0; response.status === 409 && attempt < 3; attempt += 1) {
    await new Promise(resolve => setTimeout(resolve, 150 * (attempt + 1)));
    response = await fetch("/api/bff/auth/me/", { credentials: "same-origin", cache: "no-store" });
  }
  if (!response.ok) throw new Error("Session expired");
  return response.json() as Promise<User>;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    let active = true;
    if (pathname === "/login") {
      setReady(true);
      return () => { active = false; };
    }
    loadCurrentUser()
      .then(data => { if (active) setUser(data); })
      .catch(() => {
        if (active) {
          setUser(null);
          router.replace("/login");
        }
      })
      .finally(() => { if (active) setReady(true); });
    return () => { active = false; };
  }, [pathname, router]);

  const signOut = async () => {
    try {
      await fetch("/api/bff/auth/logout/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
    } finally {
      setUser(null);
      router.replace("/login");
    }
  };

  return <Context.Provider value={{ user, ready, signOut }}>{children}</Context.Provider>;
}
