var CSRF_TOKEN;
document.onreadystatechange = function () {
  if (document.readyState === "interactive") {
    let themeToggleSwitch = document.getElementById("theme-toggle-switch");
    themeToggleSwitch.addEventListener("change", function () {
      document.body.classList.toggle("light-theme");
      document.body.classList.toggle("dark-theme");
      fetch("/toggle-theme/", {
        method: "POST",
        body: JSON.stringify({
          current_theme: document.body.className,
        }),
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
        },
      }).then((response) => console.log(response));
    });
  }
};
