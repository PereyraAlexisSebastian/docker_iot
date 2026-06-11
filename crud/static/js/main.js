
const btnDelete= document.querySelectorAll('.btn-borrar');
if(btnDelete) {
  const btnArray = Array.from(btnDelete);
  btnArray.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if(!confirm('¿Está seguro de querer borrar?')){
        e.preventDefault();
      }
    });
  })
}
//el boton
const linkTema = document.getElementById('tema-css');
const botonTema = document.getElementById('btn-tema');

// Las URLs de los temas claro y oscuro
const urlClaro = "https://bootswatch.com/5/cosmo/bootstrap.min.css";
const urlOscuro = "https://bootswatch.com/5/darkly/bootstrap.min.css";

// se revisa la memori
if (localStorage.getItem('tema') === 'oscuro') {
    linkTema.setAttribute('href', urlOscuro);
    botonTema.textContent = '☀️ Modo Claro';
} else {
    linkTema.setAttribute('href', urlClaro);
}

// 4. Escuchamos el clic del botón
botonTema.addEventListener('click', function() {
    //donde se cambia el tema 
    if (linkTema.getAttribute('href') === urlClaro) {
        linkTema.setAttribute('href', urlOscuro);
        localStorage.setItem('tema', 'oscuro'); 
        botonTema.textContent = '☀️ Modo Claro';
        
    } else {
        linkTema.setAttribute('href', urlClaro);
        localStorage.setItem('tema', 'claro');
        botonTema.textContent = '🌙 Modo Oscuro';
    }
});