import { useState } from "react";

const Card = ({ children }) => (
  <div className="bg-white rounded-2xl shadow-lg p-6">{children}</div>
);

const Input = ({ ...props }) => (
  <input
    {...props}
    className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-400"
  />
);

const Button = ({ children, ...props }) => (
  <button
    {...props}
    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
  >
    {children}
  </button>
);

export default function App() {
  const [zona, setZona] = useState("Ciudad de México");

  const riesgo = "Alto";
  const colorRiesgo =
    riesgo === "Alto"
      ? "bg-red-500"
      : riesgo === "Medio"
      ? "bg-yellow-400"
      : "bg-green-500";

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-100 to-blue-300 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-center text-gray-800 drop-shadow-lg">
          Predicción de Inundaciones - {zona}
        </h1>

        <div className="flex gap-2 justify-center">
          <Input
            placeholder="Buscar delegación o colonia..."
            onChange={(e) => setZona(e.target.value)}
          />
          <Button>Buscar</Button>
        </div>

        <Card>
          <h2 className="text-xl font-semibold mb-2">Nivel de Riesgo</h2>
          <div
            className={`text-white font-bold text-center py-3 rounded-lg ${colorRiesgo}`}
          >
            {riesgo}
          </div>
        </Card>

        <Card>
          <h2 className="text-xl font-semibold mb-2">Factores Relacionados</h2>
          <ul className="space-y-1 text-gray-700">
            <li>Lluvia pronosticada: 85 mm</li>
            <li>Temperatura: 21°C</li>
            <li>Nivel de agua en drenaje: 75%</li>
            <li>Zona urbana: {zona}</li>
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
  );
}
