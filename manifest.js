const MYSUGYA_MANIFEST = [
  {
    id: "yoma",
    title: "Yoma",
    title_he: "יוֹמאָ",
    seder: "Moed",
    dafRange: { first: "2a", last: "88a" },
    totalDaf: 173,
    dataScript: "modules/yoma/learning_data.js",
    dataVersion: "12.3"
  }
];

(function syncFooterVersionFromManifest() {
  function currentVersion() {
    var params = new URLSearchParams(window.location.search);
    var moduleId = params.get("module") || (MYSUGYA_MANIFEST[0] && MYSUGYA_MANIFEST[0].id);
    var mod = MYSUGYA_MANIFEST.find(function(item) { return item.id === moduleId; }) || MYSUGYA_MANIFEST[0];
    return (mod && mod.dataVersion) || "";
  }

  function apply() {
    var footerVersion = document.querySelector(".app-footer > span:first-child");
    var version = currentVersion();
    if (footerVersion && version) footerVersion.textContent = "Version " + version;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", apply);
  } else {
    apply();
  }

  var observer = new MutationObserver(apply);
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
