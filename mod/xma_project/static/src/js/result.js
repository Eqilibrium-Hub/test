function send_email_form(){
  disable_send_button();
  let url_params = new URLSearchParams(window.location.search);

  let csrf_token = $("input[name=csrf_token]").val();
  let email = $("input[name=email]").val();
  let company_id = url_params.get('company_id');
  let attached_id = url_params.get('attached_id');
  let uuid = url_params.get('uuid');

  let data_to_send = {
    'csrf_token': csrf_token,
    'email': email,
    'company_id': company_id,
    'attached_id': attached_id,
    'uuid': uuid
  }

  $.ajax({
    type: "POST",
    url: "/invoicing/send_mail",
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

      else if (data.success) {
          $(".success").html('Archivos enviados exitosamente');
      }

      enable_submit_button();
    },

    error: function () {
      enable_submit_button();
      alert("Se produjeron errores, intente nuevamente");
    }

  });
}

$("#send_email_form").submit(function(event) {
  event.preventDefault();
  send_email_form();
});

function print_pdf_file(file_type){
  disable_send_button();
  let url_params = new URLSearchParams(window.location.search);

  let csrf_token = $("input[name=csrf_token]").val();
  let company_id = url_params.get('company_id');
  let attached_id = url_params.get('attached_id');
  let uuid = url_params.get('uuid');

  let data_to_send = {
    'csrf_token': csrf_token,
    'company_id': company_id,
    'attached_id': attached_id,
    'uuid': uuid,
    'file_type': file_type
  }

  $.ajax({
    type: "POST",
    url: "/invoicing/print_pdf_file",
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
      else if (data.url) {
        window.location.href = data.url;
      }

      enable_submit_button();
    },

    error: function () {
      enable_submit_button();
      alert("Se produjeron errores, intente nuevamente");
    }

  });
}

$("#print_pdf_file").click(function(event) {
  print_pdf_file('pdf');
});

$("#print_xml_file").click(function(event) {
  print_pdf_file('xml');
});