import { Navigate, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Devices from './pages/Devices';
import DeviceView from './pages/DeviceView';
import NetworkMap from './pages/NetworkMap';

export default function App() {
  return (
    <div className="min-h-screen bg-midnight text-white">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,rgba(75,226,197,0.24),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(255,138,76,0.2),transparent_28%)]" />
      <div className="absolute inset-0 -z-10 bg-soc-grid bg-[size:48px_48px] opacity-20" />
      <Navbar />
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 pb-10 pt-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/devices" element={<Devices />} />
          <Route path="/devices/:deviceId" element={<DeviceView />} />
          <Route path="/network" element={<NetworkMap />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
