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
  
  // Función para cargar datos
  function loadData() {
      const chartType = document.getElementById('chart-type').value;
      const startDate = document.getElementById('start-date').value;
      const endDate = document.getElementById('end-date').value;
      
      fetch(`/get_data?chart_type=${chartType}&start_date=${startDate}&end_date=${endDate}`)
          .then(response => response.json())
          .then(data => {
              // Actualizar gráfico de ganancias
              if (data.ganancias.labels.length > 0) {
                  gananciasChart.data.labels = data.ganancias.labels;
                  gananciasChart.data.datasets[0].data = data.ganancias.data;
                  gananciasChart.update();
                  
                  // Actualizar mensaje de estado
                  document.getElementById('status-message').textContent = 
                      `Ganancias: ${data.ganancias.data.length} registros`;
              }
              
              // Actualizar gráfico de gastos
              if (data.gastos.labels.length > 0) {
                  gastosChart.data.labels = data.gastos.labels;
                  gastosChart.data.datasets[0].data = data.gastos.data;
                  gastosChart.update();
                  
                  // Actualizar mensaje de estado
                  document.getElementById('status-message').textContent += 
                      ` | Gastos: ${data.gastos.data.length} registros`;
              }
          })
          .catch(error => {
              console.error('Error:', error);
              document.getElementById('status-message').textContent = 'Error al cargar datos';
          });
  }
  
  // Función para generar predicciones
  function generatePredictions() {
      const modelType = document.getElementById('model-type').value;
      const predictionDays = document.getElementById('prediction-days').value;
      const predictionPeriod = document.getElementById('prediction-period').value;
      
      fetch(`/get_predictions?model_type=${modelType}&prediction_days=${predictionDays}&prediction_period=${predictionPeriod}`)
          .then(response => response.json())
          .then(data => {
              if (!data) {
                  throw new Error('No se recibieron datos de predicción');
              }
              
              // Actualizar gráfico de predicción
              predictionChart.data.labels = [
                  ...data.ganancias.real.labels,
                  ...data.ganancias.predicted.labels
              ];
              
              predictionChart.data.datasets[0].data = [
                  ...data.ganancias.real.data,
                  ...Array(data.ganancias.predicted.labels.length).fill(null)
              ];
              
              predictionChart.data.datasets[1].data = [
                  ...Array(data.ganancias.real.labels.length).fill(null),
                  ...data.ganancias.predicted.data
              ];
              
              predictionChart.data.datasets[2].data = [
                  ...data.gastos.real.data,
                  ...Array(data.gastos.predicted.labels.length).fill(null)
              ];
              
              predictionChart.data.datasets[3].data = [
                  ...Array(data.gastos.real.labels.length).fill(null),
                  ...data.gastos.predicted.data
              ];
              
              predictionChart.update();
              
              // Mostrar métricas
              let metricsHTML = '<h5>Métricas de Predicción</h5>';
              
              if (data.metrics.ganancias.r2 !== null) {
                  metricsHTML += `
                      <p><strong>Ganancias:</strong> 
                      R² = ${data.metrics.ganancias.r2.toFixed(3)}, 
                      MAE = ${data.metrics.ganancias.mae.toFixed(2)}</p>
                  `;
              }
              
              if (data.metrics.gastos.r2 !== null) {
                  metricsHTML += `
                      <p><strong>Gastos:</strong> 
                      R² = ${data.metrics.gastos.r2.toFixed(3)}, 
                      MAE = ${data.metrics.gastos.mae.toFixed(2)}</p>
                  `;
              }
              
              if (modelType === 'moving_avg') {
                  metricsHTML += '<p>Modelo de promedio móvil: métricas no aplicables</p>';
              }
              
              document.getElementById('prediction-metrics').innerHTML = metricsHTML;
          })
          .catch(error => {
              console.error('Error:', error);
              document.getElementById('prediction-metrics').innerHTML = 
                  `<div class="alert alert-danger">Error al generar predicciones: ${error.message}</div>`;
          });
  }
});