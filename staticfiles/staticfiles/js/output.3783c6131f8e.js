class CeleryProgressBar{constructor(progressUrl,options){this.progressUrl=progressUrl;options=options||{};let progressBarId=options.progressBarId||"progress-bar";let progressBarMessage=options.progressBarMessageId||"progress-bar-message";this.progressBarElement=options.progressBarElement||document.getElementById(progressBarId);this.progressBarMessageElement=options.progressBarMessageElement||document.getElementById(progressBarMessage);this.onProgress=options.onProgress||this.onProgressDefault;this.onSuccess=options.onSuccess||this.onSuccessDefault;this.onError=options.onError||this.onErrorDefault;this.onTaskError=options.onTaskError||this.onTaskErrorDefault;this.onDataError=options.onDataError||this.onError;this.onRetry=options.onRetry||this.onRetryDefault;this.onIgnored=options.onIgnored||this.onIgnoredDefault;let resultElementId=options.resultElementId||"celery-result";this.resultElement=options.resultElement||document.getElementById(resultElementId);this.onResult=options.onResult||this.onResultDefault;this.onNetworkError=options.onNetworkError||this.onError;this.onHttpError=options.onHttpError||this.onError;this.pollInterval=options.pollInterval||500;let barColorsDefault={success:"#76ce60",error:"#dc4f63",progress:"#68a9ef",ignored:"#7a7a7a",};this.barColors=Object.assign({},barColorsDefault,options.barColors);let defaultMessages={waiting:"Waiting for task to start...",started:"Task started...",};this.messages=Object.assign({},defaultMessages,options.defaultMessages);}
onSuccessDefault(progressBarElement,progressBarMessageElement,result){result=this.getMessageDetails(result);if(progressBarElement){progressBarElement.style.backgroundColor=this.barColors.success;}
if(progressBarMessageElement){progressBarMessageElement.textContent="Success! "+result;}}
onResultDefault(resultElement,result){if(resultElement){resultElement.textContent=result;}}
onErrorDefault(progressBarElement,progressBarMessageElement,excMessage,data){progressBarElement.style.backgroundColor=this.barColors.error;excMessage=excMessage||"";progressBarMessageElement.textContent="Uh-Oh, something went wrong! "+excMessage;}
onTaskErrorDefault(progressBarElement,progressBarMessageElement,excMessage){let message=this.getMessageDetails(excMessage);this.onError(progressBarElement,progressBarMessageElement,message);}
onRetryDefault(progressBarElement,progressBarMessageElement,excMessage,retryWhen){retryWhen=new Date(retryWhen);let message="Retrying in "+
Math.round((retryWhen.getTime()-Date.now())/1000)+"s: "+
excMessage;this.onError(progressBarElement,progressBarMessageElement,message);}
onIgnoredDefault(progressBarElement,progressBarMessageElement,result){progressBarElement.style.backgroundColor=this.barColors.ignored;progressBarMessageElement.textContent=result||"Task result ignored!";}
onProgressDefault(progressBarElement,progressBarMessageElement,progress){progressBarElement.style.backgroundColor=this.barColors.progress;progressBarElement.style.width=progress.percent+"%";var description=progress.description||"";if(progress.current==0){if(progress.pending===true){progressBarMessageElement.textContent=this.messages.waiting;}else{progressBarMessageElement.textContent=this.messages.started;}}else{progressBarMessageElement.textContent=progress.current+" of "+
progress.total+" processed. "+
description;}}
getMessageDetails(result){if(this.resultElement){return"";}else{return result||"";}}
onData(data){let done=false;if(data.progress){this.onProgress(this.progressBarElement,this.progressBarMessageElement,data.progress);}
if(data.complete===true){done=true;if(data.success===true){this.onSuccess(this.progressBarElement,this.progressBarMessageElement,data.result);}else if(data.success===false){if(data.state==="RETRY"){this.onRetry(this.progressBarElement,this.progressBarMessageElement,data.result.message,data.result.when);done=false;delete data.result;}else{this.onTaskError(this.progressBarElement,this.progressBarMessageElement,data.result);}}else{if(data.state==="IGNORED"){this.onIgnored(this.progressBarElement,this.progressBarMessageElement,data.result);delete data.result;}else{done=undefined;this.onDataError(this.progressBarElement,this.progressBarMessageElement,"Data Error");}}
if(data.hasOwnProperty("result")){this.onResult(this.resultElement,data.result);}}else if(data.complete===undefined){done=undefined;this.onDataError(this.progressBarElement,this.progressBarMessageElement,"Data Error");}
return done;}
async connect(){let response;try{response=await fetch(this.progressUrl);}catch(networkError){this.onNetworkError(this.progressBarElement,this.progressBarMessageElement,"Network Error");throw networkError;}
if(response.status===200){let data;try{data=await response.json();}catch(parsingError){this.onDataError(this.progressBarElement,this.progressBarMessageElement,"Parsing Error");throw parsingError;}
const complete=this.onData(data);if(complete===false){setTimeout(this.connect.bind(this),this.pollInterval);}}else{this.onHttpError(this.progressBarElement,this.progressBarMessageElement,"HTTP Code "+response.status,response);}}
static initProgressBar(progressUrl,options){const bar=new this(progressUrl,options);bar.connect();}};let CSRF_TOKEN;let TOAST;let ACTIVE_TASKS=[];let multiviewDocs=document.querySelectorAll(".multiview-document");let docTables=document.querySelectorAll(".doc-table");let docPreviews=document.querySelectorAll(".doc-preview");multiviewDocs.forEach((el,index)=>{el.addEventListener("click",function(event){let targetID=event.currentTarget.id;multiviewDocs.forEach((el,index)=>{if(el.id==targetID){el.classList.add("active");}else{el.classList.remove("active");}});docTables.forEach((el,i)=>{if(el.id===`${targetID}-table`){el.classList.remove("d-none");}else{el.classList.add("d-none");}});docPreviews.forEach((el,i)=>{if(el.id===`${targetID}-preview`){el.classList.remove("d-none");}else{el.classList.add("d-none");}});},false);});let filterFolderOptions=(event)=>{let query=event.target.value.toLowerCase();console.log(`query=${query}`);let folderOptions=document.querySelectorAll(".folder-options button");folderOptions.forEach((el,i)=>{if(el.textContent.toLowerCase().includes(query)){el.classList.remove("d-none");}else{el.classList.add("d-none");}});};let importDriveFolderAsContainer=(folderId,folderName)=>{fetch("/documentcontainer/import-from-drive/",{method:"POST",body:JSON.stringify({folderId:folderId,folderName:folderName,}),headers:{"Content-Type":"application/json","X-CSRFToken":CSRF_TOKEN,},}).then((response)=>response.json()).then((data)=>{ACTIVE_TASKS.push(data.task_id);let progressUrl=`/task-status/${data.task_id}`;console.log(`data.task_id=${data.task_id}; progressUrl=${progressUrl}`);CeleryProgressBar.initProgressBar(progressUrl);});};let hideLoaderAfterMillisecondDelay=(delay)=>{setTimeout(()=>{try{document.querySelector(".loader").classList.add("d-none");}catch(err){}},delay);};let saveAllDocumentNotes=()=>{let docs=document.querySelectorAll(".multiview-document");let numDocs=docs.length;let counter=0;docs.forEach((el,i)=>{let docid=el.dataset.docid;saveDocumentNotes({docID:docid,showToast:false,}).then((response)=>{counter+=1;if(counter==numDocs){let toast=document.querySelector(".toast");toast.querySelector(".toast-bold").textContent="Success";toast.querySelector(".toast-when").textContent="Just Now";toast.querySelector(".toast-body").textContent=`Notes updated for all ${numDocs} documents`;TOAST.show();}});});};let saveDocumentNotes=async(props)=>{let docID=props.docID;let showToast=props.showToast;let data={pages:[...document.querySelectorAll(`#doc-${docID}-table tbody tr.tr-doc-page`),].map((el)=>{return{id:el.dataset.pageid,notes:el.querySelector("textarea").value,};}),};return fetch(`/document/${docID}/save-notes/`,{method:"POST",body:JSON.stringify(data),headers:{"Content-Type":"application/json","X-CSRFToken":CSRF_TOKEN,},}).then((response)=>response.json()).then((data)=>{if(showToast){let toast=document.querySelector(".toast");toast.querySelector(".toast-bold").textContent="Notes Updated";toast.querySelector(".toast-when").textContent="Just Now";toast.querySelector(".toast-body").textContent=data.result;TOAST.show();}});};let themifyTables=()=>{if(document.body.classList.contains("light-theme")){document.querySelectorAll(".doc-table").forEach((el,i)=>{el.classList.add("table-secondary");});}else{document.querySelectorAll(".doc-table").forEach((el,i)=>{el.classList.remove("table-secondary");});}};document.onreadystatechange=function(){if(document.readyState==="interactive"){var toastEl=document.querySelector(".toast");TOAST=new bootstrap.Toast(toastEl);try{document.querySelector(".tr-doc-page.table-active textarea").focus();themifyTables();}catch(error){}
let themeToggleSwitch=document.getElementById("theme-toggle-switch");themeToggleSwitch.addEventListener("change",function(){document.body.classList.toggle("light-theme");document.body.classList.toggle("dark-theme");fetch("/toggle-theme/",{method:"POST",body:JSON.stringify({current_theme:document.body.className,}),headers:{"Content-Type":"application/json","X-CSRFToken":CSRF_TOKEN,},}).then((response)=>{themifyTables();});});prepareTooltips();hideLoaderAfterMillisecondDelay(3000);}};let prepareTooltips=()=>{document.querySelectorAll("a[data-bs-toggle]").forEach((el,index)=>{let tooltip=new bootstrap.Tooltip(el);});document.querySelectorAll("button[data-bs-toggle]").forEach((el,index)=>{let tooltip=new bootstrap.Tooltip(el);});document.querySelectorAll("div[data-bs-toggle]").forEach((el,index)=>{let tooltip=new bootstrap.Tooltip(el);});};let updateCurrentPageForAllDocs=(newPageIndex)=>{document.querySelectorAll(".multiview-document").forEach((el,index)=>{el.dataset.currentpage=newPageIndex.toString();});};let showCurrentPageForAllDocs=(currentPageIndex)=>{document.querySelectorAll(".multiview-page").forEach((page)=>{if(page.dataset.pageindex==currentPageIndex.toString()){page.classList.remove("d-none");}else{page.classList.add("d-none");}});};let updateActiveTableRow=(currentPageIndex)=>{document.querySelectorAll(".tr-doc-page").forEach((trDocPage)=>{if(trDocPage.dataset.pageindex==currentPageIndex.toString()){trDocPage.classList.add("table-active");let notes=trDocPage.querySelector("textarea");notes.focus();notes.scrollIntoView();}else{trDocPage.classList.remove("table-active");}});};function multiviewPreviousPage(){let firstDocument=document.querySelector(".multiview-document");let currentPageIndex=firstDocument.dataset.currentpage;if(parseInt(currentPageIndex)-1>=1){currentPageIndex=Math.max(1,parseInt(currentPageIndex)-1);showCurrentPageForAllDocs(currentPageIndex);updateActiveTableRow(currentPageIndex);updateCurrentPageForAllDocs(currentPageIndex);}}
function multiviewNextPage(){let firstDocument=document.querySelector(".multiview-document");let currentPageIndex=firstDocument.dataset.currentpage;let maxPages=firstDocument.querySelectorAll(".multiview-page").length;if(parseInt(currentPageIndex)+1<=maxPages){currentPageIndex=Math.min(maxPages,parseInt(currentPageIndex)+1);showCurrentPageForAllDocs(currentPageIndex);updateActiveTableRow(currentPageIndex);updateCurrentPageForAllDocs(currentPageIndex);}}
let focusDocument=(direction)=>{let multiviewDocs=document.querySelectorAll(".multiview-document");let docTables=document.querySelectorAll(".doc-table");let docPreviews=document.querySelectorAll(".doc-preview");let currentDocIndex=document.querySelector(".multiview-document.active").dataset.docindex;let numDocTables=docTables.length;let newIndex;let condition;if(direction==="next"){newIndex=parseInt(currentDocIndex)+1;condition=newIndex<=numDocTables;}else if(direction==="previous"){newIndex=parseInt(currentDocIndex)-1;condition=newIndex>=1;}
if(condition){currentDocIndex=newIndex;multiviewDocs.forEach((el,index)=>{if(el.dataset.docindex==currentDocIndex){el.classList.add("active");}else{el.classList.remove("active");}});docTables.forEach((docTable,index)=>{if(docTable.dataset.docindex==currentDocIndex){docTable.classList.remove("d-none");}else{docTable.classList.add("d-none");}});docPreviews.forEach((docPreview,index)=>{if(docPreview.dataset.docindex==currentDocIndex){docPreview.classList.remove("d-none");}else{docPreview.classList.add("d-none");}});}};document.onkeydown=checkKey;function checkKey(e){e=e||window.event;if(e.keyCode=="37"){multiviewPreviousPage();}else if(e.keyCode=="39"){multiviewNextPage();}else if(e.keyCode=="38"){focusDocument("previous");}else if(e.keyCode=="40"){focusDocument("next");}};