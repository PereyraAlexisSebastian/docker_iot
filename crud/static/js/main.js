
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
const linkTema = document.getElementById('tema-css');

const urlClaro = "https://bootswatch.com/5/cosmo/bootstrap.min.css";
const urlOscuro = "https://bootswatch.com/5/darkly/bootstrap.min.css";

if (localStorage.getItem('tema') === 'oscuro') {
    linkTema.setAttribute('href', urlOscuro);
} else {
    linkTema.setAttribute('href', urlClaro);
}

const opcionesTema = document.querySelectorAll('.btn-tema-select');


opcionesTema.forEach(opcion => {
    opcion.addEventListener('click', function(evento) {
        evento.preventDefault();

        const temaElegido = this.getAttribute('data-tema');

        if (temaElegido === 'oscuro') {
            linkTema.setAttribute('href', urlOscuro);
            localStorage.setItem('tema', 'oscuro');
        } else {
            linkTema.setAttribute('href', urlClaro);
            localStorage.setItem('tema', 'claro');
        }
    });
});