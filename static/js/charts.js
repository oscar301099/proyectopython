document.addEventListener('DOMContentLoaded', function() {
  // Configurar fechas por defecto
  const today = new Date();
  const oneMonthAgo = new Date();
  oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
  
  document.getElementById('start-date').valueAsDate = oneMonthAgo;
  document.getElementById('end-date').valueAsDate = today;
  
  // Inicializar gráficos
  let gananciasChart = initChart('gananciasChart', 'Ganancias', 'rgba(54, 162, 235, 0.2)', 'rgba(54, 162, 235, 1)');
  let gastosChart = initChart('gastosChart', 'Gastos', 'rgba(255, 99, 132, 0.2)', 'rgba(255, 99, 132, 1)');
  let predictionChart = initPredictionChart('predictionChart');
  
  // Cargar datos iniciales
  loadData();
  
  // Event listeners
  document.getElementById('refresh-button').addEventListener('click', function() {
      loadData();
      document.getElementById('status-message').textContent = 'Datos actualizados...';
  });
  
  document.getElementById('chart-type').addEventListener('change', loadData);
  document.getElementById('start-date').addEventListener('change', loadData);
  document.getElementById('end-date').addEventListener('change', loadData);
  
  document.getElementById('predict-button').addEventListener('click', function() {
      generatePredictions();
  });
  
  // Función para inicializar un gráfico básico
  function initChart(canvasId, label, bgColor, borderColor) {
      const ctx = document.getElementById(canvasId).getContext('2d');
      return new Chart(ctx, {
          type: 'line',
          data: {
              labels: [],
              datasets: [{
                  label: label,
                  data: [],
                  backgroundColor: bgColor,
                  borderColor: borderColor,
                  borderWidth: 1,
                  tension: 0.1
              }]
          },
          options: {
              responsive: true,
              plugins: {
                  legend: {
                      position: 'top',
                  },
                  tooltip: {
                      mode: 'index',
                      intersect: false,
                  }
              },
              scales: {
                  x: {
                      type: 'time',
                      time: {
                          unit: 'day'
                      }
                  },
                  y: {
                      beginAtZero: true
                  }
              }
          }
      });
  }
  
  // Función para inicializar el gráfico de predicción
  function initPredictionChart(canvasId) {
      const ctx = document.getElementById(canvasId).getContext('2d');
      return new Chart(ctx, {
          type: 'line',
          data: {
              labels: [],
              datasets: [
                  {
                      label: 'Ganancias Reales',
                      data: [],
                      borderColor: 'rgba(54, 162, 235, 1)',
                      backgroundColor: 'rgba(54, 162, 235, 0.2)',
                      borderWidth: 2
                  },
                  {
                      label: 'Ganancias Predichas',
                      data: [],
                      borderColor: 'rgba(54, 162, 235, 1)',
                      backgroundColor: 'rgba(54, 162, 235, 0.2)',
                      borderWidth: 2,
                      borderDash: [5, 5]
                  },
                  {
                      label: 'Gastos Reales',
                      data: [],
                      borderColor: 'rgba(255, 99, 132, 1)',
                      backgroundColor: 'rgba(255, 99, 132, 0.2)',
                      borderWidth: 2
                  },
                  {
                      label: 'Gastos Predichos',
                      data: [],
                      borderColor: 'rgba(255, 99, 132, 1)',
                      backgroundColor: 'rgba(255, 99, 132, 0.2)',
                      borderWidth: 2,
                      borderDash: [5, 5]
                  }
              ]
          },
          options: {
              responsive: true,
              plugins: {
                  legend: {
                      position: 'top',
                  },
                  tooltip: {
                      mode: 'index',
                      intersect: false,
                  },
                  annotation: {
                      annotations: {
                          line1: {
                              type: 'line',
                              yMin: 0,
                              yMax: 0,
                              borderColor: 'rgb(255, 99, 132)',
                              borderWidth: 2,
                              borderDash: [4, 4],
                              label: {
                                  content: 'Hoy',
                                  enabled: true,
                                  position: 'top'
                              }
                          }
                      }
                  }
              },
              scales: {
                  x: {
                      type: 'time',
                      time: {
                          unit: 'day'
                      }
                  },
                  y: {
                      beginAtZero: true
                  }
              }
          }
      });
  }
  
  // Función para cargar datos - VERSIÓN CORREGIDA
  function loadData() {
    const chartType = document.getElementById('chart-type').value;
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;

    // Mostrar indicador de carga
    document.getElementById('status-message').textContent = 'Cargando datos...';
    
    fetch(`/get_data?chart_type=${chartType}&start_date=${startDate}&end_date=${endDate}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        // Validación básica de la estructura de datos
        if (!data || (typeof data !== 'object')) {
          throw new Error('Formato de datos inválido');
        }

        // Manejo robusto de ganancias
        if (data.ganancias) {
          try {
            // Asegurar que tenemos arrays válidos
            const gananciasLabels = Array.isArray(data.ganancias.labels) ? data.ganancias.labels : [];
            const gananciasData = Array.isArray(data.ganancias.data) ? data.ganancias.data : [];
            
            // Normalizar datos (convertir a números y manejar valores faltantes)
            const normalizedGananciasData = gananciasData.map(d => {
              const num = Number(d);
              return isNaN(num) ? 0 : num;
            });
            
            // Emparejar labels con datos (tomar el mínimo de ambos)
            const minLength = Math.min(gananciasLabels.length, normalizedGananciasData.length);
            const pairedGananciasLabels = gananciasLabels.slice(0, minLength);
            const pairedGananciasData = normalizedGananciasData.slice(0, minLength);
            
            // Actualizar gráfico
            gananciasChart.data.labels = pairedGananciasLabels;
            gananciasChart.data.datasets[0].data = pairedGananciasData;
            gananciasChart.update();
            
            document.getElementById('status-message').textContent = 
              `Ganancias: ${pairedGananciasData.length} registros válidos`;
            
            if (gananciasLabels.length !== normalizedGananciasData.length) {
              console.warn(`Ganancias: Se esperaban ${gananciasLabels.length} labels pero hay ${normalizedGananciasData.length} datos. Usando ${minLength} puntos.`);
            }
          } catch (e) {
            console.error('Error procesando datos de ganancias:', e);
          }
        }

        // Manejo robusto de gastos
        if (data.gastos) {
          try {
            // Asegurar que tenemos arrays válidos
            const gastosLabels = Array.isArray(data.gastos.labels) ? data.gastos.labels : [];
            const gastosData = Array.isArray(data.gastos.data) ? data.gastos.data : [];
            
            // Normalizar datos (convertir a números y manejar valores faltantes)
            const normalizedGastosData = gastosData.map(d => {
              const num = Number(d);
              return isNaN(num) ? 0 : num;
            });
            
            // Si no hay labels, crear unos genéricos basados en el índice
            const finalGastosLabels = gastosLabels.length > 0 ? 
              gastosLabels.slice(0, normalizedGastosData.length) : 
              Array.from({length: normalizedGastosData.length}, (_, i) => `Dato ${i+1}`);
            
            // Actualizar gráfico
            gastosChart.data.labels = finalGastosLabels;
            gastosChart.data.datasets[0].data = normalizedGastosData;
            gastosChart.update();
            
            document.getElementById('status-message').textContent += 
              ` | Gastos: ${normalizedGastosData.length} registros`;
            
            if (gastosLabels.length > 0 && gastosLabels.length !== normalizedGastosData.length) {
              console.warn(`Gastos: Se esperaban ${gastosLabels.length} labels pero hay ${normalizedGastosData.length} datos. Usando ${Math.min(gastosLabels.length, normalizedGastosData.length)} puntos.`);
            }
          } catch (e) {
            console.error('Error procesando datos de gastos:', e);
          }
        }
      })
      .catch(error => {
        console.error('Error:', error);
        document.getElementById('status-message').textContent = 'Error al cargar datos: ' + error.message;
      });
  }

  // Función para generar predicciones
  function generatePredictions() {
      const modelType = document.getElementById('model-type').value;
      const predictionDays = document.getElementById('prediction-days').value;
      const predictionPeriod = document.getElementById('prediction-period').value;
      
      // Mostrar indicador de carga
      document.getElementById('prediction-metrics').innerHTML = '<p>Generando predicciones...</p>';
      
      fetch(`/get_predictions?model_type=${modelType}&prediction_days=${predictionDays}&prediction_period=${predictionPeriod}`)
          .then(response => {
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
          })
          .then(data => {
              if (!data) {
                  throw new Error('No se recibieron datos de predicción');
              }
              
              // Validación y normalización de datos de predicción
              try {
                // Ganancias reales
                const gananciasRealLabels = Array.isArray(data.ganancias?.real?.labels) ? data.ganancias.real.labels : [];
                const gananciasRealData = Array.isArray(data.ganancias?.real?.data) ? 
                  data.ganancias.real.data.map(d => Number(d)) : [];
                
                // Ganancias predichas
                const gananciasPredictedLabels = Array.isArray(data.ganancias?.predicted?.labels) ? 
                  data.ganancias.predicted.labels : [];
                const gananciasPredictedData = Array.isArray(data.ganancias?.predicted?.data) ? 
                  data.ganancias.predicted.data.map(d => Number(d)) : [];
                
                // Gastos reales
                const gastosRealData = Array.isArray(data.gastos?.real?.data) ? 
                  data.gastos.real.data.map(d => Number(d)) : [];
                
                // Gastos predichos
                const gastosPredictedData = Array.isArray(data.gastos?.predicted?.data) ? 
                  data.gastos.predicted.data.map(d => Number(d)) : [];
                
                // Actualizar gráfico de predicción
                predictionChart.data.labels = [
                    ...gananciasRealLabels,
                    ...gananciasPredictedLabels
                ];
                
                predictionChart.data.datasets[0].data = [
                    ...gananciasRealData,
                    ...Array(gananciasPredictedLabels.length).fill(null)
                ];
                
                predictionChart.data.datasets[1].data = [
                    ...Array(gananciasRealLabels.length).fill(null),
                    ...gananciasPredictedData
                ];
                
                predictionChart.data.datasets[2].data = [
                    ...gastosRealData,
                    ...Array(gastosPredictedData.length).fill(null)
                ];
                
                predictionChart.data.datasets[3].data = [
                    ...Array(gastosRealData.length).fill(null),
                    ...gastosPredictedData
                ];
                
                predictionChart.update();
                
                // Mostrar métricas
                let metricsHTML = '<h5>Métricas de Predicción</h5>';
                
                if (data.metrics?.ganancias?.r2 !== undefined && data.metrics?.ganancias?.mae !== undefined) {
                    metricsHTML += `
                        <p><strong>Ganancias:</strong> 
                        R² = ${Number(data.metrics.ganancias.r2).toFixed(3)}, 
                        MAE = ${Number(data.metrics.ganancias.mae).toFixed(2)}</p>
                    `;
                }
                
                if (data.metrics?.gastos?.r2 !== undefined && data.metrics?.gastos?.mae !== undefined) {
                    metricsHTML += `
                        <p><strong>Gastos:</strong> 
                        R² = ${Number(data.metrics.gastos.r2).toFixed(3)}, 
                        MAE = ${Number(data.metrics.gastos.mae).toFixed(2)}</p>
                    `;
                }
                
                if (modelType === 'moving_avg') {
                    metricsHTML += '<p>Modelo de promedio móvil: métricas no aplicables</p>';
                }
                
                document.getElementById('prediction-metrics').innerHTML = metricsHTML;
              } catch (e) {
                throw new Error('Error procesando datos de predicción: ' + e.message);
              }
          })
          .catch(error => {
              console.error('Error:', error);
              document.getElementById('prediction-metrics').innerHTML = 
                  `<div class="alert alert-danger">Error al generar predicciones: ${error.message}</div>`;
          });
  }
});