import { useEffect } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Landing from './pages/Landing';
import Devices from './pages/Devices';
import DeviceInvestigation from './pages/DeviceInvestigation';
import NetworkMap from './pages/NetworkMap';

export default function App() {
  useEffect(() => {
    document.documentElement.dataset.theme = 'dark';
    document.documentElement.style.colorScheme = 'dark';
  }, []);

  return (
    <div className="app-shell min-h-screen">
      <div className="app-glow absolute inset-0 -z-10" />
      <div className="app-grid absolute inset-0 -z-10 bg-[size:48px_48px] opacity-60" />
      <Navbar />
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 pb-10 pt-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/devices" element={<Devices />} />
          <Route path="/devices/:deviceId" element={<DeviceInvestigation />} />
          <Route path="/network" element={<NetworkMap />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
