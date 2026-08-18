/* Service worker do GerLauNR10 Campo.
   Guarda a pagina em cache para que o aplicativo abra sem sinal -- situacao
   normal numa subestacao ou galpao. Como o index.html e autocontido (estilos,
   scripts, icones e manifest embutidos), basta cachear a propria pagina. */
const CACHE = "nr10-campo-v1";
const ARQUIVOS = ["./", "./index.html"];

self.addEventListener("install", ev => {
  ev.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ARQUIVOS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", ev => {
  ev.waitUntil(
    caches.keys()
      .then(chaves => Promise.all(chaves.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", ev => {
  if (ev.request.method !== "GET") return;
  // Rede primeiro, cache como reserva: assim uma versao nova publicada no
  // GitHub Pages chega ao aparelho, sem perder o funcionamento offline.
  ev.respondWith(
    fetch(ev.request)
      .then(resp => {
        const copia = resp.clone();
        caches.open(CACHE).then(c => c.put(ev.request, copia)).catch(() => {});
        return resp;
      })
      .catch(() => caches.match(ev.request).then(r => r || caches.match("./index.html")))
  );
});
