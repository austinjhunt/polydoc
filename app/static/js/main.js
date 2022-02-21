document.onreadystatechange = function () {
  if (document.readyState === "interactive") {
    let themeToggleSwitch = document.getElementById("theme-toggle-switch");
    themeToggleSwitch.addEventListener("change", function () {
      document.body.classList.toggle("light-theme");
      document.body.classList.toggle("dark-theme");
    });
  }
};
