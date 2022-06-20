"use strict";

$('#carousel-example').carousel({
  interval: 1500
})

$('#carousel-example').on('slide.bs.carousel', function (e) {
  /*
      CC 2.0 License Iatek LLC 2018 - Attribution required
  */
  var $e = $(e.relatedTarget);
  var idx = $e.index();
  var itemsPerSlide = 0;
  var totalItems = $('.carousel-item').length;

  // console.log('totalItems', totalItems);
  if (totalItems < 3){
    itemsPerSlide = 1;
  }
  else if (totalItems == 3){
    itemsPerSlide = 2;
  }
  else if (totalItems == 4){
    itemsPerSlide = 3;
  }
  else if (totalItems == 5){
    itemsPerSlide = 4;
  }
  else{
    itemsPerSlide = 5;
  }
  // console.log('itemsPerSlide', itemsPerSlide);
  if (idx >= totalItems-(itemsPerSlide-1)) {
      var it = itemsPerSlide - (totalItems - idx);
      for (var i=0; i<it; i++) {
          // append slides to end
          if (e.direction=="left") {
              $('.carousel-item').eq(i).appendTo('.carousel-inner');
          }
          else {
              $('.carousel-item').eq(0).appendTo('.carousel-inner');
          }
      }
  }
});

$(".carousel-item").click(function () {
  if ($(".carousel-item > img").hasClass("img-selected")) {
    $(".carousel-item > img").removeClass("img-selected");
  }
  $(this).children().first().addClass("img-selected");

  // let imgSrc = $(this).children().first().attr("src");
  let company_name = $(this).children().next().attr("value");
  let company_id = $(this).children().last().attr("value");
  $("input:text[name=company_name]").val(company_name);
  $("input:hidden[name=company_id]").val(company_id);
});

function validate_rfc(rfc, accept_generic = true) {
  const re = /^([A-ZÑ&]{3,4}) ?(?:- ?)?(\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])) ?(?:- ?)?([A-Z\d]{2})([A\d])$/;
  var valid = rfc.match(re);

  if (!valid) {
    return false;
  }
  //Separate the check digit from the rest of the RFC
  const check_digit = valid.pop();
  const rfc_without_digit = valid.slice(1).join("");
  const len = rfc_without_digit.length;
  //Get the expected digit
  const dictionary = "0123456789ABCDEFGHIJKLMN&OPQRSTUVWXYZ Ñ";
  const index = len + 1;
  let sum, expected_digit;

  if (len == 12) {
    sum = 0;
  }
  else {
    sum = 481; //Fit for legal entity
  }

  for (var i = 0; i < len; i++) {
    sum += dictionary.indexOf(rfc_without_digit.charAt(i)) * (index - i);
  }

  expected_digit = 11 - (sum % 11);

  if (expected_digit == 11) {
    expected_digit = 0;
  }
  else if (expected_digit == 10) {
    expected_digit = "A";
  }

  //Check digit matches expected digit? or is a Generic RFC (sales to general public)?
  if (check_digit != expected_digit && (!accept_generic || rfc_without_digit + check_digit != "XAXX010101000")) {
    return false;
  }
  else if (!accept_generic && rfc_without_digit + check_digit == "XEXX010101000") {
    return false;
  }

  return true;
}

function validate_input_rfc(event) {
  let rfc_input = document.getElementById('rfc_input');
  let rfc = rfc_input.value.trim().toUpperCase();
  let valid_rfc = validate_rfc(rfc);

  if (valid_rfc) {
    rfc_input.setCustomValidity("");
  } else {
    rfc_input.setCustomValidity("Campo no válido");
    event.preventDefault();
  }
}

function validate_input_image(event){
  let company_id = document.getElementsByName("company_id")[0].value;

  if (company_id == "" || company_id.length == 0) {
    event.preventDefault();
  }
}

function disable_send_button(){
  $(".submit_button").attr("disabled", true);
  $("#overlay").fadeIn(300);
}

function enable_submit_button(){
  $(".submit_button").attr("disabled", false);
  $("#overlay").fadeOut(300);
}

function add_order_to_session(form_data, data){
  delete form_data['csrf_token'];
  let orders = JSON.parse(localStorage.getItem('orders'));
  form_data.order_id = data.order_id;
  // form_data.client_id = data.client_id;
  form_data.is_ticket = data.is_ticket;
  orders.push(form_data);
  localStorage.setItem('orders', JSON.stringify(orders));
}

function send_form(){
  disable_send_button();

  let csrf_token = $("input[name=csrf_token]").val();
  let company_id = $("input[name=company_id]").val();
  let company_name = $("input[name=company_name]").val();
  let reference_number = $("input[name=reference_number]").val();
  let folio_number = $("input[name=folio_number]").val();
  let date = $("input[name=date]").val();
  let total = $("input[name=total]").val();
  let rfc = $("input[name=rfc]").val();

  let data_to_send = {
    'csrf_token': csrf_token,
    'company_id': company_id,
    'company_name': company_name,
    'reference_number': reference_number,
    'folio_number': folio_number,
    'date': date,
    'total': total,
    'rfc': rfc
  }

  // data_to_send = JSON.stringify(data_to_send)
  // console.log('tipo', typeof data_to_send)
  // console.log('data_to_send', data_to_send)

  $.ajax({
    type: "POST",
    url: "/invoicing/search",
    dataType : 'json',
    // contentType: "application/json",
    // contentType: "application/x-www-form-urlencoded",
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
      else{
        localStorage.setItem('orders', JSON.stringify([]));
        add_order_to_session(data_to_send, data);
        // localStorage.setItem('company_name', JSON.stringify(company_name));
        if (data.client_id) {
          window.location.href = "/invoicing/confirm_data?company_id=" + data.company_id + '&client_id=' + data.client_id;
        }else{
          window.location.href = "/invoicing/client_data?company_id=" + data.company_id;
        }
      }

      enable_submit_button();
    },

    error: function () {
      enable_submit_button();
      alert("Se produjeron errores, intente nuevamente");
    }

  });
}

$("#search_form").submit(function( event ) {
  validate_input_rfc(event);
  validate_input_image(event);
  event.preventDefault();
  send_form();
});

function delete_order(element){
  let index = $(element).attr('value');
  let orders = JSON.parse(localStorage.getItem('orders'));
  orders.splice(index, 1);
  localStorage.setItem('orders', JSON.stringify(orders));
  draw_table_body();
}

function draw_table_body(){
  disable_send_button();
  let orders = JSON.parse(localStorage.getItem('orders'));
  $("#tbody").html("");
  let table_body = ""

  if (orders.length){
    for (let index = 0; index < orders.length; index++) {
      table_body += `<tr>`;
        table_body += `<td class="text-center">${ orders[index].date }</td>`;
        table_body += `<td class="text-center">${ orders[index].reference_number }</td>`;
        table_body += `<td class="text-center">${ orders[index].folio_number }</td>`;
        table_body += `<td class="text-center">${ orders[index].total }</td>`;
        table_body += `<td class="text-center"><button type="button" class="btn btn-danger" value="${ index }" onClick="delete_order(this)">Eliminar</button></td>`;
      table_body += `</tr>`;

      document.getElementById("tbody").innerHTML = table_body;
    }
    enable_submit_button();
  }
  else{
    enable_submit_button();
    $('#no_orders').modal('show');
  }
}

function check_existence_orders(){
  let orders = JSON.parse(localStorage.getItem('orders'));
  if (!orders || !orders.length || orders === undefined){
    $('#no_orders').modal('show');
  }

  if (orders != null && orders && orders.length){
    $("input[name=rfc]").val(orders[0]['rfc']);
    $("input[name=company_name]").val(orders[0]['company_name']);
    $('#rfc_input').attr('readonly', true);
    draw_table_body();
  }
}

function remove_local_storage(){
  localStorage.removeItem('orders');
}

function start(){
  let pathname = window.location.pathname;
  invoicing_path = pathname.indexOf("/invoicing") > -1;
  invoicing_path_2 = pathname.indexOf("/invoicing/") > -1;
  client_data_path = pathname.indexOf("/invoicing/client_data") > -1;
  data_confirmation_path = pathname.indexOf("/invoicing/confirm_data") > -1;
  result_path = pathname.indexOf("/invoicing/result") > -1;

  if (client_data_path || data_confirmation_path){
    check_existence_orders();
  }

  if (invoicing_path && !invoicing_path_2){
    remove_local_storage();
  }

  if (result_path){
    let email = JSON.parse(localStorage.getItem('email'));
    $("input[name=email]").val(email);
  }
}

$(document).ready(function () {
  start();
});

$("#total").on({
  focus: function (event) {
    $(event.target).select();
  },
  keyup: function (event) {
    $(event.target).val(function (index, value) {
      return value
        .replace(/\D/g, "")
        .replace(/([0-9])([0-9]{2})$/, "$1.$2")
        .replace(/\B(?=(\d{3})+(?!\d)\.?)/g, ",");
    });
  },
});

// $("#reference_number").on({
//   focus: function (event) {
//     $(event.target).select();
//   },
//   keyup: function (event) {
//     $(event.target).val(function (index, value) {
//       return value
//         .replace(/\D/g, "")
//         .replace(/(\d{5})(\d{3})(\d{4})/, "$1-$2-$3");
//     });
//   },
// });

function only_numbers(e){
  key = (document.all) ? e.keyCode : e.which;

  if (key==8){
    return true;
  }

  patron =/[0-9]/;
  end_key = String.fromCharCode(key);
  return patron.test(end_key);
}

function to_upper_case(e) {
  e.value = e.value.toUpperCase();
}

function verify_duplicate_order(folio_number){
  let orders = JSON.parse(localStorage.getItem('orders'));
  for (let index = 0; index < orders.length; index++) {
    if (folio_number == orders[index]['folio_number']){
        return true;
        break;
    }
  }
  return false;
}

function validate_is_ticket(folio_number){
  return folio_number.startsWith('PTV-')
}

function validate_order_type(folio_number){
  let orders = JSON.parse(localStorage.getItem('orders'));
  let is_ticket = validate_is_ticket(folio_number);
  console.log('is_ticket', is_ticket);

  for (let index = 0; index < orders.length; index++) {
    if (is_ticket != orders[index]['is_ticket']){
        return false;
        break;
    }
  }
  return true;
}

function add_order(event){
  event.preventDefault();
  disable_send_button();
  let url_params = new URLSearchParams(window.location.search);

  let csrf_token = $("input[name=csrf_token]").val();
  let company_id = url_params.get('company_id');
  let company_name = $("input[name=company_name]").val();
  let reference_number = $("input[name=reference_number]").val();
  let folio_number = $("input[name=folio_number]").val();
  let date = $("input[name=date]").val();
  let total = $("input[name=total]").val();
  let rfc = $("input[name=rfc]").val();

  let data_to_send = {
    'csrf_token': csrf_token,
    'company_id': company_id,
    'company_name': company_name,
    'reference_number': reference_number,
    'folio_number': folio_number,
    'date': date,
    'total': total,
    'rfc': rfc
  }

  is_duplicate_order = verify_duplicate_order(folio_number);
  console.log('is_duplicate_order', is_duplicate_order);

  is_same_type_order = validate_order_type(folio_number);
  console.log('is_same_type_order', is_same_type_order);

  if (is_duplicate_order){
    $(".error_message").html('');
    $(".error_message").append('Orden duplicada<br/>');
    enable_submit_button();
  }

  if (!is_same_type_order){
    $(".error_message").html('');
    $(".error_message").append('No puede mezclar ordenes de tipo ventas y punto de venta.<br/>');
    enable_submit_button();
  }
  if(!is_duplicate_order && is_same_type_order){
    $.ajax({
      type: "POST",
      url: "/invoicing/add_order",
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
        else{
          add_order_to_session(data_to_send, data);
          draw_table_body();
          $(".error_message").html('');
          $("input[name=reference_number]").val('');
          $("input[name=folio_number]").val('');
          $("input[name=date]").val('');
          $("input[name=total]").val('');
          $('#add_modal').modal('hide');
        }

        enable_submit_button();
      },

      error: function () {
        enable_submit_button();
        alert("Se produjeron errores, intente nuevamente");
      }

    });
  }
}