function populate_store_options() {
    let person_select_node = document.getElementById('person-dropdown');
    let store_select_node = document.getElementById('store-dropdown');
    $(store_select_node).select2();

    replace_store_options(store_select_node, person_select_node.value);

    person_select_node.addEventListener( 'change', (event) => {
        replace_store_options(store_select_node, person_select_node.value);
    } );
}

function replace_store_options(select_node, name) {
    // clear select node; remove all its children nodes
    let stores = CATEGORIZED_STORES[name];
    select_node.innerHTML = '';

    // add disabled option to act as header for options dropdown
    let option_node = document.createElement("option");
    option_node.textContent = 'Search';
    option_node.value = "forbidden-value";
    option_node.selected = true;
    option_node.disabled = true;
    select_node.appendChild(option_node);

    for(let store of stores) {
        option_node = document.createElement("option");
        option_node.textContent = store;
        option_node.value = store;
        select_node.appendChild(option_node);
    }
}

function toggle_to_submitting_mode() {
    document.getElementById('m1-store-picker').classList.add('hidden');
    document.getElementById('m2-currently-submitting').classList.remove('hidden');
}

function toggle_to_submission_successful_mode() {
    document.getElementById('m2-currently-submitting').classList.add('hidden');
    document.getElementById('m3-submission-successful').classList.remove('hidden');
}

function toggle_to_start_mode() {
    document.getElementById('upc-removal-successful').classList.add('hidden');

    document.getElementById('m3-submission-successful').classList.add('hidden');
    document.getElementById('m1-store-picker').classList.remove('hidden');
}

function toggle_to_manual_mode() {
    document.getElementById('upc-removal-successful').classList.add('hidden');

    document.getElementById('m3-submission-successful').classList.add('hidden');
    document.getElementById('m4-manual-buttons').classList.remove('hidden');
    document.getElementById('manual-store-name').textContent = window.previously_submitted_store_name;
}

function handle_scan_submit() {
    let upc_number = document.getElementById('upc-number').value.trim();
    let store_node = document.getElementById('store-dropdown');
    let upc_error_node = document.getElementById('upc-error');
    let store_error_node = document.getElementById('store-error');

    let is_form_bad = false;
    let validity_info = get_upc_validity(upc_number);
    handle_error(validity_info, upc_error_node);
    if (!validity_info.is_valid) {
        console.log('handle_scan_submit: invalid UPC number');
        blink_node(upc_error_node);
        is_form_bad = true;
    }

    validity_info = get_store_validity(store_node);
    handle_error(validity_info, store_error_node);
    if (!validity_info.is_valid) {
        console.log('handle_scan_submit: invalid store');
        blink_node(store_error_node);
        is_form_bad = true;
    }

    if (is_form_bad) {
        return;
    }

    console.log('handle_scan_submit: form check completed');
    submit_upc(upc_number, store_node.value);
}

function submit_upc(upc_number, store_name) {
    if (!is_upc_valid(upc_number)) {
        console.log('submit_upc: invalid UPC');
        return;
    }

    let data = {
        'action': 'add',
        'upc': upc_number,
        'store': store_name
    };

    console.log(`submit_upc: attempting to POST data: UPC "${upc_number}" for store "${store_name}"`);
    toggle_to_submitting_mode();

    let action_on_success = function() {
        console.log('POST successful');

        update_scan_confirmation(upc_number, store_name);
        toggle_to_submission_successful_mode();
        update_cookies(data);
        
        window.previously_submitted_upc = upc_number;
        window.previously_submitted_store_name = store_name;
    }

    post_data(data, action_on_success);
}

function update_scan_confirmation(upc_number, store_name) {
    document.getElementById('upc-submitted').textContent = upc_number;
    document.getElementById('store-name-submitted').textContent = store_name;
}

function handle_upc_removal() {
    let payload_data = {
        'action': 'remove',
        'upc': window.previously_submitted_upc,
        'store': window.previously_submitted_store_name
    };

    let action_on_success = function() {
        let upc_removal_successful_node = document.getElementById('upc-removal-successful');
        upc_removal_successful_node.classList.remove('hidden');
        blink_node(upc_removal_successful_node);

        console.log('UPC removal successful');
        update_cookies(payload_data);
    }

    post_data(payload_data, action_on_success);
}

function handle_reset_store_and_upc_remove() {
    let payload_data = {
        'action': 'remove',
        'store_reset': true,
        'upc': window.previously_submitted_upc,
        'store': window.previously_submitted_store_name
    };

    let action_on_success = function() {
        update_cookies(payload_data);
        toggle_to_start_mode();
    }

    post_data(payload_data, action_on_success);
}

function handle_reset_store() {
    let data = {
        'store_reset': true,
        'store': window.previously_submitted_store_name
    };

    update_cookies(data);
    toggle_to_start_mode();
}

function handle_action_manual_upc(action) {
    let upc_number = document.getElementById('manual-upc-number').value.trim();
    let upc_error_node = document.getElementById('manual-action-error');
    let upc_success_node = document.getElementById('manual-action-successful');

    let validity_info = get_upc_validity(upc_number);
    handle_error(validity_info, upc_error_node, upc_success_node);
    if (!validity_info.is_valid) {
        console.log('handle_add_manual_upc: invalid UPC number');
        blink_node(upc_error_node);
        return;
    }

    let payload_data = {
        'action': action,
        'upc': upc_number,
        'store': window.previously_submitted_store_name
    };

    let action_on_success = function() {
        console.log(`Successfully POSTed "${action}" action for ${upc_number}`);
        update_cookies(payload_data);
        
        upc_success_node.classList.remove('hidden');
        blink_node(upc_success_node);
    }

    post_data(payload_data, action_on_success);
}

function get_upc_validity(upc_number) {
    let validity_info = {
        is_valid: true, 
        error_message: ''
    };

    let check_digit = get_check_digit(upc_number);
    if (check_digit == null) {
        validity_info.error_message = `UPC number must be 12 digits, you have ${upc_number.length}`;
        validity_info.is_valid = false;
    }
    else if (upc_number.length === 11) {
        validity_info.error_message = `UPC number must be 12 digits, but if these are the first 11 digits the check digit would be ${check_digit}`;
        validity_info.is_valid = false;
    }
    else if ( upc_number[upc_number.length - 1] != get_check_digit( upc_number ) ) {
        validity_info.error_message = `Invalid UPC number. Expected ${check_digit} as the check digit`;
        validity_info.is_valid = false;
    }

    return validity_info;
}

function get_store_validity(store_node) {
    let validity_info = {
        is_valid: true, 
        error_message: ''
    };

    if (store_node.value === 'forbidden-value') {
        validity_info.is_valid = false;
        validity_info.error_message = 'You must choose a store';
    }

    return validity_info;
}

function get_check_digit(input) {
    if (input.length !== 11 && input.length !== 12) {
        return null;
    }
    else if (input.length === 12) {
        input = input.slice(0, 11);
    }

    let sum = 0;
    for (let i = 0; i < input.length; ++i) {
      if (i % 2 === 0) sum += 3 * parseInt(input[i]);
      else sum += parseInt(input[i]);
    }

    return Math.ceil(sum / 10) * 10 - sum;
}

function is_upc_valid(upc_number) {
    let check_digit = get_check_digit(upc_number);
    return upc_number.length === 12 && check_digit == upc_number[upc_number.length - 1];
}

function handle_error(validity_info, error_node, success_node) {
    if (validity_info.is_valid) {
        error_node.classList.add('hidden');
        return;
    }

    error_node.classList.remove('hidden');
    error_node.textContent = validity_info.error_message;
    if (success_node) {
        success_node.classList.add('hidden');
    }
}

function blink_node(node) {
    node.classList.remove('blink');
    setTimeout(() => {
        node.classList.add('blink');
    }, 250);
}

function update_cookies(data) {
    document.cookie = `previous_store=${data.store}; expires=Fri, 31 Dec 3999 23:59:59 GMT`;

    if ( data['store_reset'] ) {
        document.cookie = `previous_unix_log_time=0; expires=Fri, 31 Dec 3999 23:59:59 GMT`;
    }
    else {
        document.cookie = `previous_unix_log_time=${ Math.floor(Date.now() / 1000) }; expires=Fri, 31 Dec 3999 23:59:59 GMT`;
    }
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

    xhr.send( JSON.stringify(payload_data) );
}
