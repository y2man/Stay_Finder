import { useEffect, useRef, ReactNode } from "react";
import { motion, useMotionValue, useTransform, useSpring, animate, useInView, AnimatePresence } from "framer-motion";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { Moon, Sun, Star, BedDouble, Users, Heart, Home } from "lucide-react";
import { useStore, } from "./store"; import { assetUrl, type Property } from "./api";

export function Orbs() {
  const o = [["#7C3AED", "8%", "12%", 0], ["#38BDF8", "75%", "30%", 1.5], ["#F59E0B", "50%", "75%", 3]] as const;
  return <div aria-hidden className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
    {o.map(([c, l, t, d], i) => <motion.div key={i} className="absolute rounded-full blur-3xl opacity-40" style={{ background: c, left: l, top: t, width: 320, height: 320 }}
      animate={{ y: [0, -40, 0], x: [0, 30, 0] }} transition={{ duration: 9, repeat: Infinity, delay: d, ease: "easeInOut" }} />)}</div>;
}
export function Reveal({ children, d = 0 }: { children: ReactNode; d?: number }) {
  return <motion.div initial={{ opacity: 0, y: 40 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-60px" }} transition={{ duration: .6, delay: d }}>{children}</motion.div>;
}
export function Tilt({ children, className = "" }: { children: ReactNode; className?: string }) {
  const x = useMotionValue(0), y = useMotionValue(0);
  const rx = useTransform(y, [-.5, .5], [9, -9]), ry = useTransform(x, [-.5, .5], [-9, 9]);
  return <motion.div className={className} style={{ rotateX: rx, rotateY: ry, transformPerspective: 900 }} whileHover={{ scale: 1.02 }}
    onMouseMove={e => { const b = e.currentTarget.getBoundingClientRect(); x.set((e.clientX - b.left) / b.width - .5); y.set((e.clientY - b.top) / b.height - .5); }}
    onMouseLeave={() => { x.set(0); y.set(0); }}>{children}</motion.div>;
}
export function Magnetic({ children, className = "", ...p }: any) {
  const x = useSpring(0, { stiffness: 200, damping: 12 }), y = useSpring(0, { stiffness: 200, damping: 12 });
  return <motion.button {...p} className={"btn " + className} style={{ x, y }} whileTap={{ scale: .93, rotate: -2 }}
    onMouseMove={e => { const b = e.currentTarget.getBoundingClientRect(); x.set((e.clientX - b.left - b.width / 2) * .25); y.set((e.clientY - b.top - b.height / 2) * .25); }}
    onMouseLeave={() => { x.set(0); y.set(0); }}>{children}</motion.button>;
}
export function Counter({ to, suffix = "" }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null), v = useInView(ref, { once: true });
  useEffect(() => { if (v && ref.current) { const c = animate(0, to, { duration: 1.6, onUpdate: n => { ref.current!.textContent = Math.round(n).toLocaleString() + suffix; } }); return () => c.stop(); } }, [v]);
  return <span ref={ref}>0</span>;
}
export const Skeleton = ({ h = "h-72" }: { h?: string }) => <div className={`glass ${h} relative overflow-hidden`}><div className="shimmer absolute inset-0" /></div>;

export function PropertyCard({ p, list = false }: { p: Property; list?: boolean }) {
  const say = useStore(s => s.say);
  const save = async (e: any) => { e.preventDefault(); e.stopPropagation(); try { await (await import("./api")).api(`/favorites/${p.id}`, { method: "POST" }); say("Added to saved stays"); } catch (err) { say((err as Error).message); } };
  return <Tilt><Link to={`/property/${p.id}`} className={`glass glow overflow-hidden group block ${list ? "sm:flex" : ""}`}>
    <div className={`overflow-hidden relative ${list ? "sm:w-72 shrink-0" : ""}`}>
      <img src={assetUrl(p.image_url)} alt={p.title} loading="lazy" className="h-48 w-full object-cover transition duration-700 group-hover:scale-110" />
      <motion.span whileTap={{ scale: 1.4 }} onClick={save} role="button" aria-label="Favorite"
        className="absolute top-3 right-3 glass p-2 rounded-full"><Heart size={16} /></motion.span></div>
    <div className="p-4"><h3 className="font-semibold">{p.title}</h3><p className="opacity-70 text-sm">{p.city}, {p.country}</p>
      <div className="flex gap-4 text-sm mt-2 opacity-80"><span className="flex gap-1 items-center"><Star size={14} className="text-amber-400" />{p.rating}</span>
        <span className="flex gap-1 items-center"><BedDouble size={14} />{p.bedrooms}</span><span className="flex gap-1 items-center"><Users size={14} />{p.max_guests}</span></div>
      <p className="mt-2 font-bold text-amber-400">${p.price_per_night}<span className="opacity-60 font-normal text-sm"> / night</span></p></div></Link></Tilt>;
}
export function Nav() {
  const { token, role, dark, toggle, login } = useStore(), nav = useNavigate();
  const l = ({ isActive }: any) => "relative px-3 py-1 " + (isActive ? "font-semibold" : "opacity-70 hover:opacity-100");
  useEffect(() => { document.documentElement.classList.toggle("light", !dark); }, [dark]);
  return <header className="sticky top-3 z-30 mx-auto max-w-6xl px-3"><nav className="glass flex items-center gap-2 px-4 py-2">
    <Link to="/" className="flex items-center gap-2 font-bold text-lg mr-auto"><Home size={20} className="text-sky-400" />StayFinder</Link>
    <NavLink to="/" end className={l}>Home</NavLink><NavLink to="/explore" className={l}>Explore</NavLink>
    {token && <><NavLink to="/trips" className={l}>My trips</NavLink><NavLink to="/favorites" className={l}>Saved</NavLink>{role === "host" || role === "admin" ? <NavLink to="/host" className={l}>Host</NavLink> : null}<NavLink to="/messages" className={l}>Messages</NavLink><NavLink to="/notifications" className={l}>Alerts</NavLink><NavLink to="/assistant" className={l}>AI</NavLink>{role === "admin" ? <NavLink to="/admin" className={l}>Admin</NavLink> : null}</>}
    <motion.button whileTap={{ rotate: 180, scale: .8 }} onClick={toggle} aria-label="Toggle theme" className="p-2">{dark ? <Sun size={18} /> : <Moon size={18} />}</motion.button>
    {token ? <button className="btn" onClick={async () => { const refreshToken = useStore.getState().refreshToken; if (refreshToken) { try { await (await import("./api")).api("/auth/logout", { method: "POST", body: { refresh_token: refreshToken } }); } catch {} } login(null, null, null); nav("/"); }}>Log out{role === "host" ? " (host)" : ""}</button>
      : <><Link to="/auth" className="px-3 opacity-80">Log in</Link><Link to="/auth?mode=register" className="btn">Sign up</Link></>}
  </nav></header>;
}
export function Toast() {
  const t = useStore(s => s.toast);
  return <AnimatePresence>{t && <motion.div role="status" initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 60, opacity: 0 }}
    className="fixed bottom-6 left-1/2 -translate-x-1/2 glass px-5 py-3 z-50">{t}</motion.div>}</AnimatePresence>;
}
