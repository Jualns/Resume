window.onscroll = function() {
    updateProgressBar();
};

function updateProgressBar() {
    const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const progress = (scrollTop / scrollHeight) * 100;
    
    const progressBar = document.getElementById("progress-bar");
    console.log(progressBar); // Verifique se o elemento não é 'null'

    progressBar.style.width = progress + "%";
    console.log("Script carregado!");
}
