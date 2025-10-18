import { useState, useEffect } from "react";

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

const Select = ({ children, ...props }) => (
  <select
    {...props}
    className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-400 shadow-sm"
  >
    {children}
  </select>
);

export default function App() {
  const [alcaldiaSeleccionada, setAlcaldiaSeleccionada] = useState("");
  const [periodoSeleccionado, setPeriodoSeleccionado] = useState(24);
  const [alcaldias, setAlcaldias] = useState([]);
  const [datosPrediccion, setDatosPrediccion] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [busqueda, setBusqueda] = useState("");
  const [error, setError] = useState("");

  // Mapeo de alcaldías a imágenes (basado en el orden de tu API)
  const mapeoImagenes = {
    "Xochimilco": "1.png",
    "Benito Juarez": "2.png", 
    "Tlahuac": "3.png",
    "Tlalpan": "4.png",
    "Alvaro Obregon": "5.png",
    "Iztapalapa": "6.png",
    "Iztacalco": "7.png",
    "Gustavo A. Madero": "8.png",
    "Coyoacan": "9.png",
    "La Magdalena Contreras": "10.png",
    "Azcapotzalco": "11.png",
    "Cuauhtemoc": "12.png",
    "Miguel Hidalgo": "13.png",
    "Milpa Alta": "14.png",
    "Cuajimalpa de Morelos": "15.png",
    "Venustiano Carranza": "16.png"
  };

  // Cargar lista de alcaldías al iniciar
  useEffect(() => {
    cargarAlcaldias();
  }, []);

  const cargarAlcaldias = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/v1/alcaldias");
      const data = await response.json();
      setAlcaldias(data.alcaldias);
    } catch (error) {
      console.error("Error cargando alcaldías:", error);
      setError("Error conectando con la API");
    }
  };

  const buscarPrediccion = async () => {
    if (!alcaldiaSeleccionada) return;
    
    setCargando(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/predict/${encodeURIComponent(alcaldiaSeleccionada)}?periodo=${periodoSeleccionado}`
      );
      const data = await response.json();
      setDatosPrediccion(data);
    } catch (error) {
      console.error("Error obteniendo predicción:", error);
      alert("Error al obtener la predicción");
    } finally {
      setCargando(false);
    }
  };

  // Obtener la imagen correspondiente a la alcaldía seleccionada
  const obtenerImagenAlcaldia = (alcaldiaNombre) => {
    return mapeoImagenes[alcaldiaNombre] || "default.png";
  };

  // Filtrar alcaldías basado en la búsqueda
  const alcaldiasFiltradas = alcaldias.filter(alcaldia =>
    alcaldia.toLowerCase().includes(busqueda.toLowerCase())
  );

  // Determinar color del riesgo
  const getColorRiesgo = (nivelRiesgo) => {
    switch (nivelRiesgo?.toLowerCase()) {
      case "alto": return "bg-red-500";
      case "medio": return "bg-yellow-400";
      case "bajo": return "bg-green-500";
      default: return "bg-gray-400";
    }
  };

  // Obtener la clave correcta de las predicciones según el periodo
  const obtenerPredicciones = () => {
    const clavePrediccion = `${periodoSeleccionado}_horas`;
    return datosPrediccion?.predicciones?.[clavePrediccion] || datosPrediccion?.predicciones?.["24_horas"];
  };

  const predicciones = obtenerPredicciones();

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-100 to-blue-300 p-6 flex justify-center items-start">
      <div className="w-full max-w-6xl space-y-8">
        <h1 className="text-3xl font-bold text-gray-800 drop-shadow-lg text-center">
          Predicción de Inundaciones - CDMX
        </h1>

        {/* Controles de búsqueda */}
        <div className="flex flex-col gap-4 justify-center max-w-2xl mx-auto">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Selector de alcaldía */}
            <Select
              value={alcaldiaSeleccionada}
              onChange={(e) => setAlcaldiaSeleccionada(e.target.value)}
            >
              <option value="">Selecciona una alcaldía</option>
              {alcaldiasFiltradas.map((alcaldia) => (
                <option key={alcaldia} value={alcaldia}>
                  {alcaldia}
                </option>
              ))}
            </Select>

            {/* Selector de periodo - ACTUALIZADO */}
            <Select
              value={periodoSeleccionado}
              onChange={(e) => {
                setPeriodoSeleccionado(parseInt(e.target.value));
                setDatosPrediccion(null); // Limpia datos anteriores
              }}
            >
              <option value={24}>Pronóstico 24 horas</option>
              <option value={48}>Pronóstico 48 horas</option>
            </Select>
          </div>

          <Button 
            onClick={buscarPrediccion} 
            disabled={cargando || !alcaldiaSeleccionada}
            className="w-full"
          >
            {cargando ? "Cargando..." : `Buscar Predicción (${periodoSeleccionado}h)`}
          </Button>
        </div>

        {datosPrediccion && (
          <>
            {/* Tarjeta de Nivel de Riesgo */}
            <div className="max-w-md mx-auto">
              <Card className="text-center">
                <h2 className="text-xl font-semibold mb-2">
                  Nivel de Riesgo - {periodoSeleccionado}h
                </h2>
                <div
                  className={`text-white font-bold py-3 rounded-lg ${getColorRiesgo(
                    predicciones?.nivel_riesgo
                  )}`}
                >
                  {predicciones?.nivel_riesgo || "No disponible"}
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  Lluvia pronosticada: {predicciones?.lluvia_total_mm || 0} mm
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Período analizado: {periodoSeleccionado} horas
                </p>
              </Card>
            </div>

            {/* Imagen de la Alcaldía */}
            <Card className="text-center">
              <h2 className="text-xl font-semibold mb-4">
                {datosPrediccion.alcaldia} - Análisis de Riesgo ({periodoSeleccionado}h)
              </h2>
              <div className="flex flex-col items-center justify-center">
                <img 
                  src={`/img/${obtenerImagenAlcaldia(datosPrediccion.alcaldia)}`}
                  alt={`Mapa de riesgo para ${datosPrediccion.alcaldia}`}
                  className="max-w-full h-auto max-h-80 rounded-lg shadow-md border-2 border-gray-200"
                  onError={(e) => {
                    e.target.src = "/img/default.png";
                  }}
                />
                <p className="text-sm text-gray-600 mt-2">
                  Mapa de riesgo para {datosPrediccion.alcaldia}
                </p>
              </div>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Factores de Riesgo */}
              <Card>
                <h2 className="text-xl font-semibold mb-2">Factores de Riesgo</h2>
                <ul className="space-y-2 text-gray-700">
                  {datosPrediccion.analisis_contextual?.factores_riesgo?.map((factor, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-red-500 mr-2">•</span>
                      {factor}
                    </li>
                  ))}
                </ul>
                
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <h3 className="font-semibold text-blue-800 mb-1">Explicación:</h3>
                  <p className="text-sm text-blue-700">
                    {datosPrediccion.analisis_contextual?.explicacion_corta}
                  </p>
                </div>
              </Card>

              {/* Recomendaciones */}
              <Card>
                <h2 className="text-xl font-semibold mb-2">Recomendaciones</h2>
                <ul className="space-y-2 text-gray-700">
                  {datosPrediccion.analisis_contextual?.recomendaciones?.map((recomendacion, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="break-words whitespace-normal">
                        {recomendacion.replace(/_/g, ' ')}
                      </span>
                    </li>
                  ))}
                </ul>

                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <h3 className="font-semibold text-gray-700 mb-1">Fuente de datos:</h3>
                  <p className="text-sm text-gray-600">
                    Clima: {datosPrediccion.datos_utilizados?.fuente_clima} | 
                    Análisis: {datosPrediccion.datos_utilizados?.modo_analisis} |
                    Período: {datosPrediccion.datos_utilizados?.periodo_analizado || `${periodoSeleccionado}h`}
                  </p>
                </div>
              </Card>
            </div>

            {/* Información Adicional */}
            <Card>
              <h2 className="text-xl font-semibold mb-3">Resumen de la Situación</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {predicciones?.lluvia_total_mm || 0} mm
                  </div>
                  <div className="text-sm text-blue-500">Lluvia en {periodoSeleccionado}h</div>
                </div>
                <div className="p-3 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {datosPrediccion.analisis_contextual?.factores_riesgo?.length || 0}
                  </div>
                  <div className="text-sm text-orange-500">Factores de riesgo</div>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {datosPrediccion.analisis_contextual?.recomendaciones?.length || 0}
                  </div>
                  <div className="text-sm text-green-500">Recomendaciones</div>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {periodoSeleccionado}h
                  </div>
                  <div className="text-sm text-purple-500">Período analizado</div>
                </div>
              </div>
            </Card>
          </>
        )}

        {!datosPrediccion && !cargando && (
          <Card className="text-center py-12">
            <div className="text-gray-500 text-lg">
              Selecciona una alcaldía, elige el período y haz clic en "Buscar" para ver la predicción
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}