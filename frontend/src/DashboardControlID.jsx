import { useEffect, useState } from "react";
import { Wifi, WifiOff, AlertTriangle } from "lucide-react";

export default function DashboardControlID() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDevices = () => {
    fetch("http://localhost:5000/api/devices")
      .then((res) => res.json())
      .then((data) => {
        setDevices(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchDevices();
    const interval = setInterval(fetchDevices, 15000);
    return () => clearInterval(interval);
  }, []);

  const mapStatus = (status) => {
    if (status === "ONLINE")
      return { label: "Online", icon: Wifi, color: "bg-green-500" };
    if (status === "INSTAVEL")
      return { label: "Instável", icon: AlertTriangle, color: "bg-yellow-500" };
    return { label: "Offline", icon: WifiOff, color: "bg-red-500" };
  };

  if (loading) {
    return (
      <div className="p-6 text-xl font-semibold">
        Carregando dispositivos...
      </div>
    );
  }

  if (devices.length === 0) {
    return (
      <div className="p-6 text-xl text-gray-500">
        Nenhum dispositivo cadastrado
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 min-h-screen bg-gray-100">
      <h1 className="text-3xl font-bold">Dashboard de Monitoramento – Control iD</h1>

      <div className="grid md:grid-cols-3 gap-6">
        {devices.map((d) => {
          const cfg = mapStatus(d.status);
          const Icon = cfg.icon;

          return (
            <div
              key={d.serial}
              className="rounded-2xl shadow-xl bg-white p-5 space-y-3"
            >
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-800">{d.cliente}</h2>
                <span
                  className={`text-white px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 cursor-pointer transition-colors ${cfg.color} hover:bg-gray-700`}
                >
                  <Icon size={14} /> {cfg.label}
                </span>
              </div>

              <div className="text-sm space-y-1">
                <p><span className="text-gray-500 font-medium">Serial:</span> <span className="text-gray-600">{d.serial}</span></p>
                <p><span className="text-gray-500 font-medium">IP:</span> <span className="text-blue-600">{d.ip}</span></p>
                <p>
                  <span className="text-gray-500 font-medium">Última comunicação:</span>{" "}
                  <span className="text-blue-600">{d.last_seen ? new Date(d.last_seen).toLocaleString() : "Nunca"}</span>
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
