function handle_submit() {
    let upc = document.querySelector('#upc_value').value;
    let store = document.querySelector('#store_value').value;
    let upc_length_error_node = document.querySelector('#upc-length-error');
    let store_error_node = document.querySelector('#store-error');

    if (is_bad_upc('#upc_value')) {
        upc_length_error_node.style.display = "block";
        return;
    }
    else {
        upc_length_error_node.style.display = "none";
    }

    if (store == 'forbidden-value') {
        store_error_node.style.display = 'block';
        return;
    }
    else {
        store_error_node.style.display = 'none';
    }

    store_encoded = encodeURIComponent(store);
    target_url = `/upc_log_final?upc=${upc}&store=${store_encoded}`;
    console.log(target_url);

    // window.location.replace(target_url);
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

function is_bad_upc(selector_) {
    return document.querySelector(selector_).value.length != 12;
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
