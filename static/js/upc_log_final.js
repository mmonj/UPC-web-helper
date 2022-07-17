function submit_upc_removal() {
    let xhr = new XMLHttpRequest();
    let url = "/direct_update";
    let upc_removal_data = {
        'action': 'remove',
        'upc': upc_number,
        'store': store_name
    };

    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // console.log(xhr.responseText);
            document.querySelector('#hidden-label').style.display = 'block';
        }
    };
    let data = JSON.stringify(upc_removal_data);
    xhr.send(data);
}

function submit_reset_store_and_upc_remove() {
    target_url = `/upc_log_form?upc=${upc_number}&store=${store_name}&reset-store=true&remove-upc=true`;
    window.location.replace(target_url);
}

function handle_add_new_upc() {
    document.querySelector('#manually-add-upc-button-div').style.display = "none";
    document.querySelector('#add-upc-input-div').style.display = "block";

    document.querySelector('#remove-upc').style.display = "none";
    document.querySelector('#reset-and-remove').style.display = "none";

    document.querySelector('#hidden-label').style.display = "none";
}

function is_upc_valid(upc_input_node, upc_error_node) {
    let check_digit = get_check_digit(upc_input_node.value);
    let upc_value = upc_input_node.value;

    if (upc_value.length === 11) {
        upc_error_node.innerText = `Error. UPC number must be 12 digits, you have ${upc_value.length}.\n\nHowever, `
            + `if these are the first ${upc_value.length} digits of the UPC number, the check digit (last digit) would `
            + `be ${check_digit}.\n\nRemember that Clrx, KC, GM, COS, and Lav UPC numbers will start with a 0, and Yasso with an 8`;
        upc_error_node.style.color = "red";
        upc_error_node.style.display = "block";
        blink_node('#upc-length-error');

        return false;
    }
    else if (upc_value.length !== 12) {
        upc_error_node.innerText = `Error. UPC number must be 12 digits, you have ${upc_value.length}`;
        upc_error_node.style.color = "red";
        upc_error_node.style.display = "block";
        blink_node('#upc-length-error');

        return false;
    }
    else if ( upc_value[upc_value.length - 1] != get_check_digit( upc_value ) ) {
        let upc_value_11 = upc_value.slice(0, 11);
        upc_error_node.innerText = "Error. You've input an invalid UPC number";
        upc_error_node.style.color = "red";
        upc_error_node.style.display = "block";
        blink_node('#upc-length-error');

        return false;
    }

    return true;
}

function submit_add_new_upc() {
    let upc_input_node = document.querySelector('#add-upc-input');
    let upc_error_node = document.querySelector('#upc-length-error');

    if (!is_upc_valid(upc_input_node, upc_error_node)) {
        return;
    }

    let xhr = new XMLHttpRequest();
    let url = "/direct_update";
    let payload_data = {
        'action': 'add',
        'upc': upc_input_node.value,
        'store': store_name
    };

    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // console.log(xhr.responseText);
            upc_error_node.innerText = `${upc_input_node.value} has successfully been submitted & logged`;
            upc_error_node.style.color = "#88b04b";
            upc_error_node.style.display = "block";
            blink_node('#upc-length-error');
        }
    };
    let data = JSON.stringify(payload_data);
    xhr.send(data);
}

function submit_remove_manually_typed_upc() {
    let upc_input_node = document.querySelector('#add-upc-input');
    let upc_error_node = document.querySelector('#upc-length-error');

    if (!is_upc_valid(upc_input_node, upc_error_node)) {
        return;
    }


    let xhr = new XMLHttpRequest();
    let url = "/direct_update";
    let payload_data = {
        'action': 'remove',
        'upc': upc_input_node.value,
        'store': store_name
    };

    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // console.log(xhr.responseText);
            upc_error_node.innerText = `${upc_input_node.value} has successfully been removed from the scan log`;
            upc_error_node.style.color = "#88b04b";
            upc_error_node.style.display = "block";
            blink_node('#upc-length-error');
        }
    };
    let data = JSON.stringify(payload_data);
    xhr.send(data);
}

function blink_node(id_val) {
    var blink = document.querySelector(id_val);
    blink.style.opacity = 0;
    setTimeout(function() {
        blink.style.opacity = 1;
    }, 100);
}

function get_check_digit(input) {
    if (input.length != 11 && input.length != 12) {
        return null;
    }

    if (input.length == 12) {
        input = input.slice(0, 11);
    }

    let array = input.split('').reverse();

    let total = 0;
    let i = 1;
    array.forEach(number => {
        number = parseInt(number);
        if (i % 2 === 0) {
            total = total + number;
        }
        else {
            total = total + (number * 3);
        }
        i++;
    });

    let res = (Math.ceil(total / 10) * 10) - total;

    console.log(`Check digit is ${res}, type: ${typeof(res)}`);

    return res;
}
