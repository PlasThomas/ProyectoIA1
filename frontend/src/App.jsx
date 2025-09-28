import { useState } from "react";

const Card = ({ children, className = "" }) => (
  <div
    className={`bg-white rounded-2xl shadow-lg p-6 w-full transition-transform duration-300 hover:shadow-xl hover:scale-[1.02] ${className}`}
  >
    {children}
  </div>
);

const Input = ({ ...props }) => (
  <input
    {...props}
    className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-400 shadow-sm"
  />
);

const Button = ({ children, ...props }) => (
  <button
    {...props}
    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-transform duration-200 hover:scale-[1.05] shadow-md"
  >
    {children}
  </button>
);

export default function App() {
  const [zona, setZona] = useState("Ciudad de México");

  const riesgo = "Bajo";
  const colorRiesgo =
    riesgo === "Alto"
      ? "bg-red-500"
      : riesgo === "Medio"
      ? "bg-yellow-400"
      : "bg-green-500";

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-100 to-blue-300 p-6 flex justify-center items-start">
      <div className="w-full max-w-6xl space-y-8">
        <h1 className="text-3xl font-bold text-gray-800 drop-shadow-lg text-center">
          Predicción de Inundaciones - {zona}
        </h1>

        <div className="flex gap-2 justify-center max-w-xl mx-auto">
          <Input
            placeholder="Buscar delegación o colonia..."
            onChange={(e) => setZona(e.target.value)}
          />
          <Button>Buscar</Button>
        </div>

        <div className="max-w-md mx-auto">
          <Card className="text-center">
            <h2 className="text-xl font-semibold mb-2">Nivel de Riesgo</h2>
            <div
              className={`text-white font-bold py-3 rounded-lg ${colorRiesgo}`}
            >
              {riesgo}
            </div>
          </Card>
        </div>

        <Card className="text-center">
          <h2 className="text-xl font-semibold mb-4">
            Imagen de la Ciudad de México
          </h2>
          <div className="flex items-center justify-center h-80 bg-gray-200 rounded-lg text-gray-600">
            📷 Aquí irá la imagen generada por IA
          </div>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <h2 className="text-xl font-semibold mb-2">Factores Relacionados</h2>
            <ul className="space-y-1 text-gray-700">
              <li>☔ Lluvia pronosticada: 85 mm</li>
              <li>🌡️ Temperatura: 21°C</li>
              <li>💧 Nivel de agua en drenaje: 75%</li>
              <li>🏙️ Zona urbana: {zona}</li>
            </ul>
          </Card>

          <Card>
            <h2 className="text-xl font-semibold mb-2">Recomendaciones</h2>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li>Evitar transitar por zonas bajas o túneles.</li>
              <li>Tener lista una ruta alterna de evacuación.</li>
              <li>Resguardar documentos y objetos de valor.</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
