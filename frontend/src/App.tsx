import { Routes, Route, useLocation, Navigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Nav, Orbs, Toast } from "./ui"; import { useStore } from "./store";
import { HomePage, ExplorePage, PropertyPage, AuthPage, TripsPage, FavoritesPage, HostPage, AssistantPage, MessagesPage, AdminPage, VerifyEmailPage, ForgotPasswordPage, NotificationsPage, PaymentSuccessPage } from "./pages";

export default function App() {
  const loc = useLocation(), token = useStore(s => s.token);
  return <><Orbs /><Nav /><AnimatePresence mode="wait"><motion.main key={loc.pathname} initial={{ opacity: 0, y: 16, filter: "blur(6px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }} exit={{ opacity: 0 }} transition={{ duration: .35 }}>
    <Routes location={loc}><Route path="/" element={<HomePage />} /><Route path="/explore" element={<ExplorePage />} /><Route path="/property/:id" element={<PropertyPage />} />
      <Route path="/auth" element={<AuthPage />} /><Route path="/verify-email" element={<VerifyEmailPage />} /><Route path="/forgot-password" element={<ForgotPasswordPage />} /><Route path="/reset-password" element={<ForgotPasswordPage />} /><Route path="/payment/success" element={<PaymentSuccessPage />} /><Route path="/notifications" element={token ? <NotificationsPage /> : <Navigate to="/auth" />} />
      <Route path="/trips" element={token ? <TripsPage /> : <Navigate to="/auth" />} />
      <Route path="/favorites" element={token ? <FavoritesPage /> : <Navigate to="/auth" />} />
      <Route path="/host" element={token ? <HostPage /> : <Navigate to="/auth" />} />
      <Route path="/assistant" element={token ? <AssistantPage /> : <Navigate to="/auth" />} />
      <Route path="/messages" element={token ? <MessagesPage /> : <Navigate to="/auth" />} />
      <Route path="/admin" element={token ? <AdminPage /> : <Navigate to="/auth" />} /></Routes></motion.main></AnimatePresence><Toast /></>;
}
