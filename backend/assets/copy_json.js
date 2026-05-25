(function() {
  window.dash_clientside = window.dash_clientside || {};
  var noUpdate = window.dash_clientside.no_update;
  window.dash_clientside.copy_json_model = function(n_clicks, model) {
    if (n_clicks && model) {
      try {
        navigator.clipboard.writeText(model);
        return "Copiado!";
      } catch (e) {
        return "Erro ao copiar.";
      }
    }
    return noUpdate;
  };
})();
