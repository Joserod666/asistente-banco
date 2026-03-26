(function() {
  window.BancoChat = {
    init: function(options) {
      options = options || {};
      var containerId = options.container || 'banco-chat';
      var width = options.width || '100%';
      var height = options.height || '600px';
      var theme = options.theme || 'light';
      var apiUrl = options.apiUrl || 'http://127.0.0.1:8000';
      var baseUrl = options.baseUrl || window.location.origin;

      var container = document.getElementById(containerId);
      if (!container) {
        container = document.querySelector(containerId);
      }
      if (!container) {
        console.error('BancoChat: Contenedor no encontrado: ' + containerId);
        return;
      }

      var iframe = document.createElement('iframe');
      iframe.src = baseUrl + '/?apiUrl=' + encodeURIComponent(apiUrl) + '&theme=' + theme;
      iframe.style.border = 'none';
      iframe.style.width = width;
      iframe.style.height = height;
      iframe.style.display = 'block';
      iframe.setAttribute('title', 'Asistente Virtual Banco de Bogotá');

      container.innerHTML = '';
      container.appendChild(iframe);
    }
  };
})();
