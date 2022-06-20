function close_no_orders_modal(){
  $('#no_tickets').modal('hide');
  window.location.href = "/invoicing";
}

function registration_form(event){
  event.preventDefault();

  let rfc = $("input[name=rfc]").val();
  let name = $("input[name=name]").val();
  let street = $("input[name=street]").val();
  let street2 = $("input[name=street2]").val();
  let city = $("input[name=city]").val();
  let zip = $("input[name=zip]").val();

  $(".rfc_verified").html(rfc);
  $(".name_verified").html(name);
  $(".address_verified").html(`${ street }, ${ street2 }, ${ city }, ${ zip }`);
  $('#verify_data').modal('show');
}

function send_registration_form(event){
  event.preventDefault();
  disable_send_button();
  let url_params = new URLSearchParams(window.location.search);

  let csrf_token = $("input[name=csrf_token]").val();
  let rfc = $("input[name=rfc]").val();
  let name = $("input[name=name]").val();
  let street = $("input[name=street]").val();
  let street2 = $("input[name=street2]").val();
  let city = $("input[name=city]").val();
  let zip = $("input[name=zip]").val();
  let email = $("input[name=email]").val();
  let company_id = url_params.get('company_id');
  let orders = localStorage.getItem('orders');

  let data_to_send = {
    'csrf_token': csrf_token,
    'rfc': rfc,
    'name': name,
    'street': street,
    'street2': street2,
    'city': city,
    'zip': zip,
    'email': email,
    'company_id': company_id,
    'orders': orders
  }

  $.ajax({
    type: "POST",
    url: "/invoicing/invoice",
    data: data_to_send,

    success: function (response) {
      let data = response.data;
      let errors = response.error_message;

      $(".error_message").html('');
      if (errors.length) {
        errors.forEach(element => {
          $(".error_message").append(element+ '<br/>');
        });
      }
      else if (data.attached_id) {
        localStorage.removeItem('tickets');
        $('#verify_data').modal('hide');
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