var CSRF_TOKEN;
var TOAST;
document.onreadystatechange = function () {
  if (document.readyState === "interactive") {
    var toastEl = document.querySelector(".toast");
    TOAST = new bootstrap.Toast(toastEl);

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
      })
        .then((response) => response.json())
        .then((response) => console.log(response));
    });
  }
};

function multiviewPreviousPage() {
  let firstDocument = document.querySelectorAll(".multiview-document")[0];
  let currentPageIndex = firstDocument.dataset.currentpage;
  if (parseInt(currentPageIndex) - 1 >= 1) {
    document.querySelectorAll(".multiview-page").forEach((page) => {
      if (page.dataset.pageindex == currentPageIndex) {
        page.classList.add("d-none");
      } else if (
        page.dataset.pageindex == (parseInt(currentPageIndex) - 1).toString()
      ) {
        page.classList.remove("d-none");
      }
    });
    currentPageIndex = Math.max(1, parseInt(currentPageIndex) - 1);
    firstDocument.dataset.currentpage = currentPageIndex.toString();
  }
}
function multiviewNextPage() {
  let firstDocument = document.querySelectorAll(".multiview-document")[0];
  let currentPageIndex = firstDocument.dataset.currentpage;
  let maxPages = firstDocument.querySelectorAll(".multiview-page").length;
  if (parseInt(currentPageIndex) + 1 <= maxPages) {
    document.querySelectorAll(".multiview-page").forEach((page) => {
      if (page.dataset.pageindex == currentPageIndex) {
        page.classList.add("d-none");
      } else if (
        page.dataset.pageindex == (parseInt(currentPageIndex) + 1).toString()
      ) {
        page.classList.remove("d-none");
      }
    });
    currentPageIndex = Math.min(maxPages, parseInt(currentPageIndex) + 1);
    firstDocument.dataset.currentpage = currentPageIndex.toString();
  }
}

document.onkeydown = checkKey;
function checkKey(e) {
  e = e || window.event;
  if (e.keyCode == "37") {
    // left arrow
    multiviewPreviousPage();
  } else if (e.keyCode == "39") {
    // right arrow
    multiviewNextPage();
  }
}
