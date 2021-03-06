let CSRF_TOKEN;
let TOAST;
let ACTIVE_TASKS = [];

let multiviewDocs = document.querySelectorAll(".multiview-document");
let docTables = document.querySelectorAll(".doc-table");
let docPreviews = document.querySelectorAll(".doc-preview");

multiviewDocs.forEach((el, index) => {
  el.addEventListener(
    "click",
    function (event) {
      let targetID = event.currentTarget.id;
      multiviewDocs.forEach((el, index) => {
        if (el.id == targetID) {
          el.classList.add("active");
        } else {
          el.classList.remove("active");
        }
      });
      docTables.forEach((el, i) => {
        if (el.id === `${targetID}-table`) {
          el.classList.remove("d-none");
        } else {
          el.classList.add("d-none");
        }
      });
      docPreviews.forEach((el, i) => {
        if (el.id === `${targetID}-preview`) {
          el.classList.remove("d-none");
        } else {
          el.classList.add("d-none");
        }
      });
    },
    false
  );
});

let filterFolderOptions = (event) => {
  let query = event.target.value.toLowerCase();
  console.log(`query=${query}`);
  let folderOptions = document.querySelectorAll(".folder-options button");
  folderOptions.forEach((el, i) => {
    if (el.textContent.toLowerCase().includes(query)) {
      el.classList.remove("d-none");
    } else {
      el.classList.add("d-none");
    }
  });
};

let googleDriveImportLoadingScreen = {
  show: () => {
    document
      .querySelector(".google-drive-loading-screen")
      .classList.remove("d-none");
  },
  hide: () => {
    document
      .querySelector(".google-drive-loading-screen")
      .classList.add("d-none");
  },
};

let importDriveFolderAsContainer = (folderId, folderName) => {
  // display loading screen for Google Drive import here
  googleDriveImportLoadingScreen.show();
  // display loading screen for Google Drive import here
  fetch("/documentcontainer/import-from-drive/", {
    method: "POST",
    body: JSON.stringify({
      folderId: folderId,
      folderName: folderName,
    }),
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": CSRF_TOKEN,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      setTimeout(() => {
        location.href = "/dash";
      }, 3000);
    });
};

document.addEventListener("DOMContentLoaded", function () {
  // active task list included in master template; this monitors progress of each
  // task if any are present; this allows notification to populate in top nav
  // if any of them complete
  document.querySelectorAll("li.active-task-id").forEach((el, i) => {
    console.log(`monitoring progress of ${el.dataset.taskId}`);
    monitorProgress(el.dataset.taskId);
  });

  initTaskStatusPage(); // won't do anything if not on tasks.html page
});

let notifyUserTaskComplete = (data) => {
  // data: {'state': 'SUCCESS', 'complete': True, 'success': True, 'progress': {'pending': False, 'current': 100, 'total': 100, 'percent': 100}, 'result': 'success'}
  document.querySelector(".notification-description").textContent = 1; //data.result;
  document.querySelector(".notification-badge").classList.remove("d-none");
};

let initTaskStatusPage = () => {
  // initialize all of the progress bars on the tasks.html (task status view) page
  document
    .querySelectorAll(".task-status-page .tasks-accordion .task-id")
    .forEach((el, i) => {
      let task_id = el.dataset.taskId;
      // create a progress bar for a given task id on the task-status view page
      CeleryProgressBar.initProgressBar(`/task-status/${task_id}`, {
        pollInterval: 1500,
        progressBarId: `progress-bar-${task_id}`,
        progressBarMessageId: `progress-bar-message-${task_id}`,
      });
    });
};

let monitorProgress = (task_id) => {
  let progressUrl = `/task-status/${task_id}`;
  let complete = false;
  let monitorIntervalId = setInterval(() => {
    fetch(progressUrl)
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        // structure: {'state': 'SUCCESS', 'complete': True, 'success': True, 'progress': {'pending': False, 'current': 100, 'total': 100, 'percent': 100}, 'result': 'success'}
        if (data.complete) {
          notifyUserTaskComplete(data);
          // stop monitoring; it's done
          clearInterval(monitorIntervalId);
        }
      });
  }, 1500);
};

let hideLoaderAfterMillisecondDelay = (delay) => {
  setTimeout(() => {
    try {
      document.querySelector(".loader").classList.add("d-none");
    } catch (err) {}
  }, delay);
};

let saveAllDocumentNotes = () => {
  let docs = document.querySelectorAll(".multiview-document");
  let numDocs = docs.length;
  let counter = 0;
  docs.forEach((el, i) => {
    let docid = el.dataset.docid;
    saveDocumentNotes({
      docID: docid,
      showToast: false, // don't show toast for every single document
    }).then((response) => {
      counter += 1;
      // show toast when done
      if (counter == numDocs) {
        let toast = document.querySelector(".toast");
        toast.querySelector(".toast-bold").textContent = "Success";
        toast.querySelector(".toast-when").textContent = "Just Now";
        toast.querySelector(
          ".toast-body"
        ).textContent = `Notes updated for all ${numDocs} documents`;
        TOAST.show();
      }
    });
  });
};

let saveDocumentNotes = async (props) => {
  let docID = props.docID;
  let showToast = props.showToast;
  // build JSON object representing all notes for this document
  let data = {
    pages: [
      ...document.querySelectorAll(`#doc-${docID}-table tbody tr.tr-doc-page`),
    ].map((el) => {
      return {
        id: el.dataset.pageid,
        notes: el.querySelector("textarea").value,
      };
    }),
  };
  return fetch(`/document/${docID}/save-notes/`, {
    method: "POST",
    body: JSON.stringify(data),
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": CSRF_TOKEN,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (showToast) {
        let toast = document.querySelector(".toast");
        toast.querySelector(".toast-bold").textContent = "Notes Updated";
        toast.querySelector(".toast-when").textContent = "Just Now";
        toast.querySelector(".toast-body").textContent = data.result;
        TOAST.show(); // the Toast object corresponding to the above HTML element
      }
    });
};
let themifyTables = () => {
  if (document.body.classList.contains("light-theme")) {
    document.querySelectorAll(".doc-table").forEach((el, i) => {
      el.classList.add("table-secondary");
    });
  } else {
    document.querySelectorAll(".doc-table").forEach((el, i) => {
      el.classList.remove("table-secondary");
    });
  }
};
document.onreadystatechange = function () {
  if (document.readyState === "interactive") {
    var toastEl = document.querySelector(".toast");
    TOAST = new bootstrap.Toast(toastEl);

    // autofocus the currently active notes textarea
    try {
      document.querySelector(".tr-doc-page.table-active textarea").focus();
      themifyTables();
    } catch (error) {}

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
          "Content-Type": "application/json",
          "X-CSRFToken": CSRF_TOKEN,
        },
      }).then((response) => {
        themifyTables();
      });
    });
    prepareTooltips();
    hideLoaderAfterMillisecondDelay(3000);
  }
};

let prepareTooltips = () => {
  document
    .querySelectorAll("a[data-bs-toggle='tooltip']")
    .forEach((el, index) => {
      let tooltip = new bootstrap.Tooltip(el);
    });
  document
    .querySelectorAll("button[data-bs-toggle='tooltip']")
    .forEach((el, index) => {
      let tooltip = new bootstrap.Tooltip(el);
    });
  document
    .querySelectorAll("div[data-bs-toggle='tooltip']")
    .forEach((el, index) => {
      let tooltip = new bootstrap.Tooltip(el);
    });
};
let updateCurrentPageForAllDocs = (newPageIndex) => {
  document.querySelectorAll(".multiview-document").forEach((el, index) => {
    el.dataset.currentpage = newPageIndex.toString();
  });
};

let showCurrentPageForAllDocs = (currentPageIndex) => {
  document.querySelectorAll(".multiview-page").forEach((page) => {
    if (page.dataset.pageindex == currentPageIndex.toString()) {
      page.classList.remove("d-none");
    } else {
      page.classList.add("d-none");
    }
  });
};

let updateActiveTableRow = (currentPageIndex) => {
  document.querySelectorAll(".tr-doc-page").forEach((trDocPage) => {
    if (trDocPage.dataset.pageindex == currentPageIndex.toString()) {
      trDocPage.classList.add("table-active");
      let notes = trDocPage.querySelector("textarea");
      notes.focus();
      //notes.scrollIntoView(); bad UX
    } else {
      trDocPage.classList.remove("table-active");
    }
  });
};

function multiviewPreviousPage() {
  let firstDocument = document.querySelector(".multiview-document");
  let currentPageIndex = firstDocument.dataset.currentpage;
  if (parseInt(currentPageIndex) - 1 >= 1) {
    currentPageIndex = Math.max(1, parseInt(currentPageIndex) - 1);
    showCurrentPageForAllDocs(currentPageIndex);
    updateActiveTableRow(currentPageIndex);
    updateCurrentPageForAllDocs(currentPageIndex);
  }
}
function multiviewNextPage() {
  let firstDocument = document.querySelector(".multiview-document");
  let currentPageIndex = firstDocument.dataset.currentpage;
  let maxPages = firstDocument.querySelectorAll(".multiview-page").length;
  if (parseInt(currentPageIndex) + 1 <= maxPages) {
    currentPageIndex = Math.min(maxPages, parseInt(currentPageIndex) + 1);
    showCurrentPageForAllDocs(currentPageIndex);
    updateActiveTableRow(currentPageIndex);
    updateCurrentPageForAllDocs(currentPageIndex);
  }
}

let focusDocument = (direction) => {
  let multiviewDocs = document.querySelectorAll(".multiview-document");
  let docTables = document.querySelectorAll(".doc-table");
  let docPreviews = document.querySelectorAll(".doc-preview");
  let currentDocIndex = document.querySelector(".multiview-document.active")
    .dataset.docindex;
  let numDocTables = docTables.length;
  let newIndex;
  let condition;
  if (direction === "next") {
    newIndex = parseInt(currentDocIndex) + 1;
    condition = newIndex <= numDocTables;
  } else if (direction === "previous") {
    newIndex = parseInt(currentDocIndex) - 1;
    condition = newIndex >= 1;
  }
  if (condition) {
    currentDocIndex = newIndex;
    multiviewDocs.forEach((el, index) => {
      if (el.dataset.docindex == currentDocIndex) {
        el.classList.add("active");
      } else {
        el.classList.remove("active");
      }
    });
    docTables.forEach((docTable, index) => {
      if (docTable.dataset.docindex == currentDocIndex) {
        docTable.classList.remove("d-none");
      } else {
        docTable.classList.add("d-none");
      }
    });
    docPreviews.forEach((docPreview, index) => {
      if (docPreview.dataset.docindex == currentDocIndex) {
        docPreview.classList.remove("d-none");
      } else {
        docPreview.classList.add("d-none");
      }
    });
  }
};
document.onkeydown = checkKey;
function checkKey(e) {
  e = e || window.event;
  if (e.keyCode == "37") {
    // left arrow
    multiviewPreviousPage();
  } else if (e.keyCode == "39") {
    // right arrow
    multiviewNextPage();
  } else if (e.keyCode == "38") {
    // up, bring previous document into focus
    focusDocument("previous");
  } else if (e.keyCode == "40") {
    //down, bring next document into focus
    focusDocument("next");
  }
}
