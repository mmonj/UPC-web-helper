function toggle_modal() {
    let store_picker_node = document.querySelector('#m1-store-picker');
    let submission_successful_node = document.querySelector('#m2-submission-successful');
    let currently_submitting_node = document.querySelector('#m2-currently-submitting');

    store_picker_node.style.display = (store_picker_node.style.display === "none" ? "block" : "none");
    if (store_picker_node.style.display == 'none') {
        currently_submitting_node.style.display = 'block';
    }
    else {
        submission_successful_node.style.display = 'none';
        currently_submitting_node.style.display = 'none';
    }
}

function toggle_from_submitting_to_success() {
    let currently_submitting_node = document.querySelector('#m2-currently-submitting');
    let submission_successful_node = document.querySelector('#m2-submission-successful');

    currently_submitting_node.style.display = 'none';
    submission_successful_node.style.display = 'block';
}

function handle_submit() {
    let upc = document.querySelector('#upc_value').value.trim();
    let store_name = document.querySelector('#store-value').value;
    let upc_length_error_node = document.querySelector('#upc-length-error');
    let store_error_node = document.querySelector('#store-error-message');

    is_return = false;

    if (upc.length != 12) {
        upc_length_error_node.style.display = "block";
        blink_node(upc_length_error_node);
        set_upc_error_msg(upc_length_error_node, `Error. UPC number must be 12 digits, you have ${upc.length}`);
        is_return = true;
    }
    else if (!is_upc_valid(upc)) {
        upc_length_error_node.style.display = "block";
        blink_node(upc_length_error_node);
        set_upc_error_msg(upc_length_error_node, 'Error. The submitted UPC is invalid.');
        is_return = true;
    }
    else {
        upc_length_error_node.style.display = "none";
    }

    if (store_name == 'forbidden-value') {
        store_error_node.style.display = 'block';
        blink_node(store_error_node);
        is_return = true;
    }
    else {
        store_error_node.style.display = 'none';
    }

    if (is_return) {
        return;
    }

    submit_upc(upc, store_name);
    // xhr submit code here
}

function submit_upc(upc, store_name) {
    if (!is_upc_valid(upc)) {
        console.log('"submit_upc" says: Invalid UPC');
        return;
    }

    let payload_data = {
        'action': 'add',
        'upc': upc,
        'store': store_name
    };

    toggle_modal();
    let action_on_success = function() {
        update_scan_confirmation(`Saved ${upc}\n\n${store_name}`);
        toggle_from_submitting_to_success()
    }

    // alert('Mock-Main-Submit');
    post_data(payload_data, action_on_success);
}

function set_upc_error_msg(upc_length_error_node, error_msg) {
    upc_length_error_node.querySelector('p').innerHTML = error_msg;
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

    // console.log(`Check digit is ${res}, type: ${typeof(res)}`);

    return res;
}

function is_upc_valid(upc) {
    if (upc.length != 12) {
        return false;
    }

    let check_digit = get_check_digit(upc);
    return check_digit == upc[upc.length - 1];
}

function blink_node(node_) {
    node_.style.opacity = 0;
    setTimeout(function() {
        node_.style.opacity = 1;
    }, 100);
}

function make_dropdown_select2() {
    $(document).ready(function () {
    //change selectboxes to selectize mode to be searchable
       $("#store-value").select2();
    });
}

function populate_dropdown() {
    let person_select_node = document.querySelector('#person-value');
    let stores_select_node = document.querySelector('#store-value');

    populate_dropdown_menu(stores_select_node, CATEGORIZED_STORES[person_select_node.value]);

    person_select_node.addEventListener( 'change', (event) => {
        let cat_ = person_select_node.value;
        populate_dropdown_menu(stores_select_node, CATEGORIZED_STORES[cat_]);
    } );
}

function populate_dropdown_menu(select_node, option_values_list) {
    // clear select node; remove all its children nodes
    select_node.innerHTML = '';

    // add disabled option to act as header for options dropdown
    let option_node = document.createElement("option");
    option_node.textContent = 'Search';
    option_node.value = "forbidden-value";
    option_node.selected = true;
    option_node.disabled = true;
    select_node.appendChild(option_node);

    for(let store of option_values_list) {
        option_node = document.createElement("option");
        option_node.textContent = store;
        option_node.value = store;
        select_node.appendChild(option_node);
    }
}

function update_scan_confirmation(new_msg) {
    document.querySelector('#m-upc-saved-message').innerText = new_msg;

    // if (scan_complete) {
    //     toggle_currently_submitting_modal();
    //     document.querySelector('#m-upc-saved-message').innerText = new_msg;
    //     document.querySelector('#m2-submission-successful').style.display = 'block';
    // }
    // else {
    //     document.querySelector('#m2-submission-successful').style.display = 'none';
    //     toggle_currently_submitting_modal();
    // }


    // if (scan_successful_node.style.display === 'block') {
    //     document.querySelector('.scan-confirmation-header').style.display = 'none';
    //     document.querySelector('#m-upc-saved-message').innerText = 'Submitting...';
    // }
    // else {
    //     document.querySelector('.scan-confirmation-header').style.display = 'none';
    //     document.querySelector('#m-upc-saved-message').innerText = new_text;
    // }
}

// function toggle_currently_submitting_modal() {
//     let m1 = document.querySelector('#m1-store-picker');
//     let m2 = document.querySelector('#m2-submission-successful');

//     if (m1.style.display == 'block' || m2.style.display == 'block') {
//         document.querySelector('#m2-currently-submitting').style.display = 'none';
//     }
//     else {
//         document.querySelector('#m2-currently-submitting').style.display = 'block';
//     }
// }

function handle_manually_add_new_upc() {
    document.querySelector('#m2-submission-successful').style.display = "none";
    document.querySelector('#m3-manual-buttons').style.display = "block";
}

function get_store_to_submit() {
    return (PREVIOUS_STORE != null ? PREVIOUS_STORE : document.querySelector('#store-value').value);
}

function submit_add_manual_upc() {
    let upc_input_node = document.querySelector('#input-add-upc-manual');
    let upc_error_node = document.querySelector('#upc-length-error-modal');

    if (!is_upc_valid_from_modal_input(upc_input_node, upc_error_node)) {
        return;
    }

    upc_error_node.innerText = "Submitting...";
    upc_error_node.style.color = "black";
    upc_error_node.style.display = "block";

    let payload_data = {
        'action': 'add',
        'upc': upc_input_node.value,
        'store': get_store_to_submit()
    };

    let action_on_success = function() {
        upc_error_node.innerText = `${upc_input_node.value} has successfully been submitted & logged`;
        upc_error_node.style.color = "#88b04b";
        upc_error_node.style.display = "block";
        blink_node(upc_error_node);
    }

    // alert('Mocking Add-UPC');
    post_data(payload_data, action_on_success);
}

function submit_remove_manual_upc() {
    let upc_input_node = document.querySelector('#input-add-upc-manual');
    let upc_error_node = document.querySelector('#upc-length-error-modal');

    if (!is_upc_valid_from_modal_input(upc_input_node, upc_error_node)) {
        return;
    }

    upc_error_node.innerText = "Removing...";
    upc_error_node.style.color = "black";
    upc_error_node.style.display = "block";

    let payload_data = {
        'action': 'remove',
        'upc': upc_input_node.value,
        'store': get_store_to_submit()
    };

    let action_on_success = function() {
        upc_error_node.innerText = `${upc_input_node.value} has been removed from the scan log`;
        upc_error_node.style.color = "red";
        upc_error_node.style.display = "block";
        blink_node(upc_error_node);
    }

    // alert('Mocking Remove-UPC');
    post_data(payload_data, action_on_success);
}

function submit_upc_removal() {
    let upc_input_node = document.querySelector('#upc_value');

    let payload_data = {
        'action': 'remove',
        'upc': upc_input_node.value,
        'store': get_store_to_submit()
    };

    let action_on_success = function() {
        document.querySelector('#upc-removed-label').style.display = 'block';
    }

    // alert('Mocking Remove-UPC');
    post_data(payload_data, action_on_success);
}

function submit_reset_store_and_upc_remove() {
    let upc_input_node = document.querySelector('#upc_value');

    let payload_data = {
        'action': 'remove',
        'store_reset': true,
        'upc': upc_input_node.value,
        'store': get_store_to_submit()
    };

    let action_on_success = function() {
        document.querySelector('#upc-removed-label').style.display = 'none';

        toggle_modal();
        update_scan_confirmation('');
    }

    // alert('Mock-reset-store-and-remove-upc');
    post_data(payload_data, action_on_success);
}

function post_data(payload_data, action_on_success) {
    let url = "/direct_update";
    let xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            action_on_success();
        }
    };
    let str_payload = JSON.stringify(payload_data);
    xhr.send(str_payload);
}

function is_upc_valid_from_modal_input(upc_input_node, upc_error_node) {
    let upc_value = upc_input_node.value;
    let check_digit = get_check_digit(upc_value);

    if (upc_value.length === 11) {
        upc_error_node.innerText = `Error. UPC number must be 12 digits, you have ${upc_value.length}.\n\nHowever, `
            + `if these are the first ${upc_value.length} digits of the UPC number, the check digit (last digit) would `
            + `be ${check_digit}.\n\nRemember that Clrx, KC, GM, COS, and Lav UPC numbers will start with a 0, and Yasso with an 8`;
        upc_error_node.style.color = "red";
        upc_error_node.style.display = "block";
        blink_node(upc_error_node);

        return false;
    }
    else if (upc_value.length !== 12) {
        upc_error_node.innerText = `Error. UPC number must be 12 digits, you have ${upc_value.length}`;
        upc_error_node.style.color = "red";
        upc_error_node.style.display = "block";
        blink_node(upc_error_node);

        return false;
    }
    else if ( upc_value[upc_value.length - 1] != get_check_digit( upc_value ) ) {
        let upc_value_11 = upc_value.slice(0, 11);
        upc_error_node.innerText = "Error. You've input an invalid UPC number";
        upc_error_node.style.color = "red";
        upc_error_node.style.display = "block";
        blink_node(upc_error_node);

        return false;
    }

    return true;
}
