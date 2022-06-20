function send_client_confirmation_data_form(){
  disable_send_button();
  let url_params = new URLSearchParams(window.location.search);

  let csrf_token = $("input[name=csrf_token]").val();
  let client_id = url_params.get('client_id');
  let company_id = url_params.get('company_id');
  let street = $("input[name=street]").val();
  let street2 = $("input[name=street2]").val();
  let city = $("input[name=city]").val();
  let state_id = $("#state_id").val();
  let zip = $("input[name=zip]").val();
  let country_id = $("#country_id").val();
  let email = $("input[name=email]").val();
  let orders = localStorage.getItem('orders');

  let data_to_send = {
    'csrf_token': csrf_token,
    'client_id': client_id,
    'company_id': company_id,
    'street': street,
    'street2': street2,
    'city': city,
    'state_id': state_id,
    'zip': zip,
    'country_id': country_id,
    'email': email,
    'orders': orders
  }

  $.ajax({
    type: "POST",
    url: "/invoicing/invoice",
    data: data_to_send,

    success: function (response) {
      let data = response.data;
      let errors = response.error_message;

      $(".error_message2").html('');
      if (errors.length) {
        errors.forEach(element => {
          $(".error_message2").append(element+ '<br/>');
        });
      }
      else if (data.attached_id) {
        localStorage.removeItem('orders');
        localStorage.setItem('email', JSON.stringify(email));
        window.location.href = "/invoicing/result?company_id=" + company_id + '&attached_id=' + data.attached_id + '&uuid=' + data.uuid;
      }

      enable_submit_button();
    },

    error: function () {
      enable_submit_button();
      alert("Se produjeron errores, intente nuevamente");
    }

  });
}

$("#country_id").on("change", function () {
  let country_id = $("#country_id").val();
  $("#state_id").html("");
  $('#state_id').append($('<option>', { value: "", text: "" }));

  if (country_id != "") {
    $.ajax({
      type: "GET",
      url: "/invoicing/get_states_by_country",
      data: {
        'country_id': country_id,
      },
      success: function (response) {
        for(let i=0; i < response.data.length; i++){
          $('#state_id').append($('<option>', { value: response.data[i].id, text: response.data[i].name }));
        }
      },
      error: function () {
        alert("No se ha podido obtener los estados");
      }
    });
  }
});

$("#update_data_form").submit(function( event ) {
  event.preventDefault();
  send_client_confirmation_data_form();
});