import { useEffect, useState } from "react";
import { Wifi, WifiOff, AlertTriangle, Pencil, Check, X } from "lucide-react";

export default function DashboardControlID() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingField, setEditingField] = useState(null);
  const [editingValue, setEditingValue] = useState("");

  const fetchDevices = () => {
    if (editingField) return; // evita atualização durante edição

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
    const interval = setInterval(fetchDevices, 10000); // 10 segundos
    return () => clearInterval(interval);
  }, [editingField]);

  const mapStatus = (status) => {
    if (status === "ONLINE")
      return { label: "Online", icon: Wifi, color: "bg-green-500" };
    if (status === "INSTAVEL")
      return { label: "Instável", icon: AlertTriangle, color: "bg-yellow-500" };
    return { label: "Offline", icon: WifiOff, color: "bg-red-500" };
  };

  const startEditing = (serial, field, currentValue) => {
    setEditingField({ serial, field });
    setEditingValue(currentValue);
  };

  const cancelEditing = () => {
    setEditingField(null);
    setEditingValue("");
  };

  const saveField = async (serial, field) => {
    try {
      const body =
        field === "serial"
          ? { new_serial: editingValue }
          : { [field]: editingValue };

      const response = await fetch(
        `http://localhost:5000/api/devices/${serial}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (response.ok) {
        setEditingField(null);
        setEditingValue("");
        fetchDevices();
      }
    } catch (error) {
      console.error("Erro ao salvar:", error);
    }
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
      <h1 className="text-3xl font-bold">
        Dashboard de Monitoramento – Control iD
      </h1>

      <div className="grid md:grid-cols-3 gap-6">
        {devices.map((d) => {
          const cfg = mapStatus(d.status);
          const Icon = cfg.icon;

          const isEditingSerial =
            editingField?.serial === d.serial &&
            editingField?.field === "serial";

          const isEditingIp =
            editingField?.serial === d.serial &&
            editingField?.field === "ip";

          return (
            <div
              key={d.serial}
              className="rounded-2xl shadow-xl bg-white p-5 space-y-3"
            >
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-800">
                  {d.cliente}
                </h2>
                <span
                  className={`text-white px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${cfg.color}`}
                >
                  <Icon size={14} /> {cfg.label}
                </span>
              </div>

              <div className="text-sm space-y-2">
                {/* SERIAL */}
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 font-medium">Serial:</span>

                  {isEditingSerial ? (
                    <div className="flex items-center gap-1">
                      <input
                        type="text"
                        value={editingValue}
                        onChange={(e) => setEditingValue(e.target.value)}
                        className="border rounded px-2 py-0.5 text-sm w-36"
                        autoFocus
                      />
                      <button
                        onClick={() => saveField(d.serial, "serial")}
                        className="text-green-600"
                      >
                        <Check size={16} />
                      </button>
                      <button
                        onClick={cancelEditing}
                        className="text-red-600"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1">
                      <span className="text-gray-600">{d.serial}</span>
                      <button
                        onClick={() =>
                          startEditing(d.serial, "serial", d.serial)
                        }
                        className="text-gray-400"
                      >
                        <Pencil size={14} />
                      </button>
                    </div>
                  )}
                </div>

                {/* IP */}
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 font-medium">IP:</span>

                  {isEditingIp ? (
                    <div className="flex items-center gap-1">
                      <input
                        type="text"
                        value={editingValue}
                        onChange={(e) => setEditingValue(e.target.value)}
                        className="border rounded px-2 py-0.5 text-sm w-32"
                        autoFocus
                      />
                      <button
                        onClick={() => saveField(d.serial, "ip")}
                        className="text-green-600"
                      >
                        <Check size={16} />
                      </button>
                      <button
                        onClick={cancelEditing}
                        className="text-red-600"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1">
                      <span className="text-blue-600">{d.ip}</span>
                      <button
                        onClick={() => startEditing(d.serial, "ip", d.ip)}
                        className="text-gray-400"
                      >
                        <Pencil size={14} />
                      </button>
                    </div>
                  )}
                </div>

                <p>
                  <span className="text-gray-500 font-medium">
                    Última comunicação:
                  </span>{" "}
                  <span className="text-blue-600">
                    {d.last_seen
                      ? new Date(d.last_seen).toLocaleString()
                      : "Nunca"}
                  </span>
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
