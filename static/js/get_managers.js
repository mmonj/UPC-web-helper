var STORES_DATA = null;

function init_store_data() {
    let promises_ = [
        get_json('static/data/categorized_store_listings.json')
    ];

    Promise.all(promises_).then(data => {
        STORES_DATA = data[0];
        update_managers_info_form();
    })
}

function update_managers_info_form() {
    let body_div = document.querySelector('#stores-container');
    body_div.innerHTML = '';

    let employee_name = document.querySelector('#person-dropdown').value;
    let store_list = STORES_DATA[employee_name];

    for (let store_name of store_list) {
        let new_fieldset = get_new_fieldset(store_name);
        body_div.appendChild(new_fieldset);
    }
}

async function get_json(url) {
  const resp = await fetch(url);
  const _data = await resp.json();

  return _data;
}

function get_new_fieldset(store_name) {
    let new_fieldset = document.createElement('fieldset');
    new_fieldset.setAttribute('class', 'store-info');

    let new_label = document.createElement('label');
    // new_label.setAttribute('class', 'store-name');
    new_label.setAttribute('name', 'store-name');
    new_label.innerText = store_name;

    let [first_name, last_name] = STORES_DATA['All Stores'][store_name]['manager_names'];

    let new_input1 = document.createElement('input');
    new_input1.setAttribute('type', 'text');
    new_input1.setAttribute('placeholder', 'First Name');
    new_input1.setAttribute('class', 'first-name');
    new_input1.setAttribute('name', 'first-name');
    new_input1.value = first_name;

    let new_input2 = document.createElement('input');
    new_input2.setAttribute('type', 'text');
    new_input2.setAttribute('placeholder', 'Last Name');
    new_input2.setAttribute('class', 'last-name');
    new_input2.setAttribute('name', 'last-name')
    new_input2.value = last_name;

    if (first_name === '' && last_name === '') {
        new_fieldset.style.backgroundColor = '#e1a1a130';
    }

    new_fieldset.appendChild(new_label);
    new_fieldset.appendChild( document.createElement('br') );

    new_fieldset.appendChild(new_input1);
    let error_div = document.createElement('div'); error_div.setAttribute('class', 'error-msg');
    new_fieldset.appendChild(error_div);

    new_fieldset.appendChild(new_input2);
    error_div = document.createElement('div'); error_div.setAttribute('class', 'error-msg');

    new_fieldset.appendChild(error_div);

    return new_fieldset;
}

function update_submit_button_style(submit_node) {
    submit_node.disabled = true;
    submit_node.style.background = 'grey';
    submit_node.innerText = 'Submitting...';
}

function init_eventlisteners() {
    let form = document.querySelector('#manager_form');

    form.addEventListener('submit', (e) => {
        // e.preventDefault();
        let is_prevented = false;
        let store_nodes = document.querySelectorAll('.store-info');

        for (let store_node of store_nodes) {
            if ( !is_inputs_consistent(store_node) ) {
                console.log('preventing default');
                e.preventDefault();
                is_prevented = true;
            }
        }

        let first_error_node = document.querySelector('.error-active');
        if (first_error_node != null) {
            first_error_node.scrollIntoView();
        }

        let submit_node = (e.target || e.srcElement).querySelector('button[type="submit"]');

        if (!is_prevented) {
            update_submit_button_style(submit_node);
        }
    })
}

function is_inputs_consistent(store_node) {
    let first_name_node = store_node.querySelector('.first-name');
    let last_name_node = store_node.querySelector('.last-name');

    let first_name = first_name_node.value.trim();
    let last_name = last_name_node.value.trim();

    if (first_name === '' && last_name === '') {
        // console.log('is consistent')
        return true;
    }
    else if ( first_name !== '' && last_name !== '' ) {
        clear_error(first_name_node);
        clear_error(last_name_node);
        return true;
    }

    if (first_name === '') {
        set_error(first_name_node, 'First name is needed');
    }
    else {
        clear_error(first_name_node);
    }

    if (last_name === '') {
        set_error(last_name_node, 'Last name is needed')
    }
    else {
        clear_error(last_name_node);
    }

    first_name_node.parentElement.classList.add('error');

    return false;
}

function clear_error(input_node) {
    input_node.nextElementSibling.innerText = '';
    input_node.classList.remove('error-active');
}

function set_error(input_node, msg) {
    input_node.nextElementSibling.innerText = msg;
    input_node.classList.add('error-active');
}
