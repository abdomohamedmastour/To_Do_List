const getValue = (form, name) => (form.elements[name] ? form.elements[name].value : "");

const validators = {
  register(form) {
    const errors = [];
    const name = getValue(form, "name").trim();
    const email = getValue(form, "email").trim();
    const password = getValue(form, "password");
    const confirm = getValue(form, "confirm_password");
    if (!name) errors.push("Name is required");
    else if (name.length > 100) errors.push("Name is too long (100 characters at most)");
    if (!email) errors.push("Email is required");
    else if (email.length > 255) errors.push("Email is too long (255 characters at most)");
    if (!password) errors.push("Password is required");
    else if (new TextEncoder().encode(password).length > 72) errors.push("Password is too long (72 bytes at most)");
    if (!confirm) errors.push("Confirm password is required");
    else if (password && password !== confirm) errors.push("Passwords do not match");
    return errors;
  },
  login(form) {
    const errors = [];
    if (!getValue(form, "email").trim()) errors.push("Email is required");
    if (!getValue(form, "password")) errors.push("Password is required");
    return errors;
  },
  todo(form) {
    const title = getValue(form, "title").trim();
    if (!title) return ["Title is required"];
    if (title.length > 200) return ["Title is too long (200 characters at most)"];
    return [];
  },
};

function showErrors(form, errors) {
  const box = form.querySelector(".js-errors");
  box.innerHTML = "";
  if (!errors.length) return;
  const alertBox = document.createElement("div");
  alertBox.className = "alert alert-danger py-2 mt-2 mb-0";
  alertBox.setAttribute("role", "alert");
  const list = document.createElement("ul");
  list.className = "mb-0 ps-3";
  errors.forEach((message) => {
    const item = document.createElement("li");
    item.textContent = message;
    list.appendChild(item);
  });
  alertBox.appendChild(list);
  box.appendChild(alertBox);
}

document.querySelectorAll("form[data-validate]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const errors = validators[form.dataset.validate](form);
    showErrors(form, errors);
    if (errors.length) event.preventDefault();
  });
});

document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});