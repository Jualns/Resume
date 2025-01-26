window.onscroll = function() {
    updateProgressBar();
};

function updateProgressBar() {
    const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const progress = (scrollTop / scrollHeight) * 100;
    
    document.getElementById("progress-bar").style.width = progress + "%";
    console.log("Script carregado!");
}
