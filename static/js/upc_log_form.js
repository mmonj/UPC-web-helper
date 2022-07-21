function handle_submit() {
    let upc = document.querySelector('#upc_value').value.trim();
    let store = document.querySelector('#store_value').value;
    let upc_length_error_node = document.querySelector('#upc-length-error');
    let store_error_node = document.querySelector('#store-error');

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

    if (store == 'forbidden-value') {
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

    store_encoded = encodeURIComponent(store);
    target_url = `/upc_log_final?upc=${upc}&store=${store_encoded}`;

    window.location.replace(target_url);
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

    console.log(`Check digit is ${res}, type: ${typeof(res)}`);

    return res;
}

function is_upc_valid(upc) {
    let check_digit = get_check_digit(upc);
    return check_digit == upc[upc.length - 1];
}

function blink_node(blink) {
    blink.style.opacity = 0;
    setTimeout(function() {
        blink.style.opacity = 1;
    }, 100);
}

function populate_dropdown() {
    let person_select_node = document.querySelector('#person-value');
    let stores_select_node = document.querySelector('#store_value');

    populate_dropdown_menu(stores_select_node, CATEGORIZED_STORES[person_select_node.value]);

    person_select_node.addEventListener( 'change', (event) => {
        let cat_ = person_select_node.value;
        populate_dropdown_menu(stores_select_node, CATEGORIZED_STORES[cat_]);
    } );
}

function make_dropdown_select2() {
    $(document).ready(function () {
    //change selectboxes to selectize mode to be searchable
       $("#store_value").select2();
    });
}
