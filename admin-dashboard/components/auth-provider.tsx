"use client";
import {createContext,useContext,useEffect,useState} from "react";
import {usePathname,useRouter} from "next/navigation";
import {API_BASE} from "@/lib/api";
type User={id:string;email:string;first_name:string;last_name:string;platform_role:string;memberships:{estate_id:string;role:string;status:string}[]};
type Auth={user:User|null;ready:boolean;signOut:()=>void};
const Context=createContext<Auth>({user:null,ready:false,signOut:()=>{}});
export const useAuth=()=>useContext(Context);
export function AuthProvider({children}:{children:React.ReactNode}){const[user,setUser]=useState<User|null>(null);const[ready,setReady]=useState(false);const pathname=usePathname();const router=useRouter();useEffect(()=>{if(pathname==="/login"){setReady(true);return;}const access=sessionStorage.getItem("estate_access_token");if(!access){router.replace("/login");setReady(true);return;}fetch(`${API_BASE}/auth/me/`,{headers:{Authorization:`Bearer ${access}`},cache:"no-store"}).then(r=>{if(!r.ok)throw new Error("Session expired");return r.json();}).then((data:User)=>setUser(data)).catch(()=>{sessionStorage.removeItem("estate_access_token");sessionStorage.removeItem("estate_refresh_token");router.replace("/login");}).finally(()=>setReady(true));},[pathname,router]);const signOut=()=>{sessionStorage.removeItem("estate_access_token");sessionStorage.removeItem("estate_refresh_token");setUser(null);router.replace("/login");};return <Context.Provider value={{user,ready,signOut}}>{children}</Context.Provider>;}
