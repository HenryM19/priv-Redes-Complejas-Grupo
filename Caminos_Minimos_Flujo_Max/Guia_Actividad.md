UCUENCA
FACULTADDEINGENIERÍA
MÓDULODEREDESCOMPLEJAS—UNIVERSIDADDECUENCA
ACTIVIDADPRÁCTICAENPAREJAS
FLUJO
MÁXIMO
Ford-Fulkerson vs. Edmonds-Karp
CapítulodeOptimizaciónenRedes—ImplementacionesinteractivasenJulia
DOCUMENTOACADÉMICO—USOENCLASE
FabiánAstudillo-Salinas—LaUquevivelaeducación
Cuenca—Ecuador 14dejuliode2026

Índice
1 InformaciónGeneraldelaActividad 2
1.1 Fichadelaactividad . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
1.2 Objetivosdeaprendizaje . . . . . . . . . . . . . . . . . . . . . . . . . 2
2 FundamentoTeórico 4
2.1 Elproblemadeflujomáximo . . . . . . . . . . . . . . . . . . . . . . . 4
2.2 Ford-FulkersonyEdmonds-Karp . . . . . . . . . . . . . . . . . . . . . . 4
3 PreparacióndelEntorno 5
3.1 Obtencióndelcódigo . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
3.2 Estructuradelcódigobase . . . . . . . . . . . . . . . . . . . . . . . . 5
4 DesarrollodelaActividad 7
4.1 Parte1—Exploraciónguiada(2puntos) . . . . . . . . . . . . . . . . . 7
4.2 Parte2—Elexperimentozigzag(3puntos) . . . . . . . . . . . . . . . . 7
4.3 Parte3—Supropiared(3puntos) . . . . . . . . . . . . . . . . . . . . 8
4.4 Parte4—Análisiscomparativo(2puntos) . . . . . . . . . . . . . . . . 9
5 Entregables,RúbricayCondiciones 11
5.1 Entregables . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
5.2 Rúbricadeevaluación . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
1

Capítulo 1
| Información     | General   | de la Actividad |
| --------------- | --------- | --------------- |
| 1.1 Ficha de la | actividad |                 |
Cuadro1:Fichageneraldelaactividad
| Campo     | Detalle                                 |     |
| --------- | --------------------------------------- | --- |
| Módulo    | RedesComplejas                          |     |
| Capítulo  | Optimizaciónenredes                     |     |
| Tema      | Flujomáximo:Ford-FulkersonyEdmonds-Karp |     |
| Modalidad | Trabajoenparejas                        |     |
Duraciónestimada 1sesióndelaboratorio(2horas)+trabajoautónomo
Julia(≥1.9)conPlots.jlyPluto
Lenguaje
Repositorio
https://github.com/fabianastudillo/ComplexNetw
orks
| Códigobase | optimization/ford-fulkerson/yoptimization/edm |     |
| ---------- | --------------------------------------------- | --- |
onds-karp/
| Entregable    | InformePDF+códigoJulia+animacionesGIF   |     |
| ------------- | --------------------------------------- | --- |
| Entrega       | Unasemanadespuésdelasesióndelaboratorio |     |
| 1.2 Objetivos | de aprendizaje                          |     |
INFO-CIRCLE
Objetivogeneral
Comprender, mediante experimentación con implementaciones interactivas en
Julia, las ventajas, desventajas, similitudes y diferencias entre el algoritmo de
Ford-Fulkerson (búsqueda de caminosaumentantescon DFS) y su refinamiento
Edmonds-Karp(búsquedaconBFS),enelcontextodelproblemadeflujomáximo
enredescomplejas.
Alfinalizarlaactividad,cadaparejaserácapazde:
1. Explicarlosconceptosdereddeflujo,redresidual,caminoaumentante,cuellode
botellaycortemínimo.
2. EjecutarymodificarlasimplementacionesenJuliadeambosalgoritmos,interpre-
tandosusanimacionespasoapaso.
2

ACTIVIDAD:FLUJOMÁXIMO UNIVERSIDADDECUENCA
3. Comparar experimentalmente el número de iteraciones y las longitudes de los
caminosaumentantesdecadamétodo.
4. Argumentarcuándolaeleccióndelcaminoaumentanteesdeterminanteparala
eficienciaylaterminacióndelalgoritmo.
5. Relacionarelteoremamax-flowmin-cut conproblemasderedescomplejas:robus-
tez,conectividadydeteccióndecuellosdebotella.
Exclamation-Triangle Integridadacadémica
Eltrabajosedesarrollaenparejasycadaparejadebeentregaruninformepropio.
Sepermitediscutirideasentreparejas,peronocompartirtexto,códigomodificado
niresultados.Todomaterialexternoutilizadodebecitarsecorrectamente.
3

Capítulo 2
Fundamento Teórico
2.1 El problema de flujo máximo
UnareddeflujoesungrafodirigidoG = (V,E)conunafuncióndecapacidadc(u,v) ≥ 0,
unnodofuentesyunnodosumiderot.Unflujoesunafunciónf(u,v)querespetalas
capacidades(f(u,v) ≤ c(u,v))yconservaelflujoen losnodosintermedios(todolo
queentrasale).Elproblemadeflujomáximoconsisteenmaximizarelvalor|f|quesale
desyllegaat.
Laherramientacentraldeambosalgoritmoseslaredresidual:dadounflujof,la
capacidadresiduales
r(u,v) = c(u,v)−f(u,v),
dondelosarcosderetroceso(conc(u,v) = 0perof(v,u) > 0)permitencancelar flujo
enviadopreviamente.Uncaminoaumentanteesuncaminodesatenlaredresidual;
sucuellodebotella∆eslamínimacapacidadresidualalolargodelcamino.
2.2 Ford-Fulkerson y Edmonds-Karp
ElmétododeFord-Fulkerson(1956)repiteunciclosimple:mientrasexistauncamino
aumentanteenlaredresidual,aumentarelflujoen∆alolargodeél.Elmétodono
especificacómoencontrarelcamino;laimplementacióndelrepositoriousaDFSparala
varianteclásica(metodo=:dfs).
El algoritmo de Edmonds-Karp (1972) es la especialización que busca el camino
aumentantesiempreconBFS,esdecir,elcaminoconmenosarcos.Estecambioapa-
rentementemenortieneconsecuenciasprofundasqueustedesverificaránexperimen-
talmenteenestaactividad.
SEARCH Preguntaguíadelaactividad
Siambosalgoritmosejecutanelmismociclodeaumentoylleganalmismoflujo
máximo,¿porquélaformadeelegir elcaminoaumentantecambialagarantíade
terminación y la complejidad de O(E · |f∗|) a O(V · E2)? Toda la actividad está
diseñadaparaquepuedanresponderestapreguntaconevidenciaexperimental
propia.
Alterminarcualquieradelosdosalgoritmos,elconjuntoSdenodosalcanzablesdes-
desenlaredresidualdefineelcortemínimo(S,V \S),cuyacapacidadesexactamente
elflujomáximo(teoremamax-flowmin-cut).
4

Capítulo 3
| Preparación   | del        | Entorno |     |     |     |
| ------------- | ---------- | ------- | --- | --- | --- |
| 3.1 Obtención | del código |         |     |     |     |
1 git clone https://github.com/fabianastudillo/ComplexNetworks.git
cd ComplexNetworks/optimization/ford-fulkerson
2
| julia --project=. | -e 'using | Pkg; Pkg.instantiate()' |     |     |     |
| ----------------- | --------- | ----------------------- | --- | --- | --- |
3
4 cd ../edmonds-karp
| julia --project=. | -e 'using | Pkg; Pkg.instantiate()' |     |     |     |
| ----------------- | --------- | ----------------------- | --- | --- | --- |
5
Listing3.1:Clonacióndelrepositorioeinstalacióndedependencias
| 3.2 Estructura | del código | base |     |     |     |
| -------------- | ---------- | ---- | --- | --- | --- |
Cuadro2:Archivosprincipalesdelcódigobase
| Archivo |     | Contenido |     |     |     |
| ------- | --- | --------- | --- | --- | --- |
ford-fulkerson/ford_fulkerso
|     |     | Algoritmo | con búsqueda | BFS | o DFS |
| --- | --- | --------- | ------------ | --- | ----- |
n.jl
|     |     | (metodo=:bfs | / :dfs),        | corte mínimo, | dibu-     |
| --- | --- | ------------ | --------------- | ------------- | --------- |
|     |     | jo de        | la red de flujo | y de la red   | residual, |
animaciónGIFymodointeractivo.
RedclásicadeCormenetal.(CLRS,flujomáximo
ford-fulkerson/ejemplo1.jl
23):trazaenconsolaygeneracióndeGIF.
edmonds-karp/edmonds_karp.jl Edmonds-KarpconregistrodenivelesBFS,ani-
|     |     | macióndelaondaBFS |     | capaporcapaytablade |     |
| --- | --- | ----------------- | --- | ------------------- | --- |
longitudesdecaminosaumentantes.
edmonds-karp/ejemplo1.jl RedCLRS+redzigzagconarcotrampadecapa-
cidad1.
*/notebook_pluto.jl Notebooks Pluto interactivos con sliders para
recorrerlasiteraciones.
CLIPBOARD-CHECK
Tresformasdeexplorarlosalgoritmos
1. Consola:julia --project=. ejemplo1.jlimprimelatrazaygeneralosGIF.
2. Modo interactivo: desde el REPL, ford_fulkerson_interactivo(red, s,
t)oedmonds_karp_interactivo(red, s, t)avanzanfotogramaafotogra-
5

ACTIVIDAD:FLUJOMÁXIMO UNIVERSIDADDECUENCA
macon[Enter]—idealparadiscutirenparejaquéocurriráenelsiguiente
pasoantesdeverlo.
3. NotebookPluto:Pluto.run()yabrirnotebook_pluto.jlparaexperimentar
consliders.
6

| Capítulo   | 4         |                 |        |            |
| ---------- | --------- | --------------- | ------ | ---------- |
| Desarrollo |           | de la Actividad |        |            |
| 4.1        | Parte 1 — | Exploración     | guiada | (2 puntos) |
Ejecuten de ambos proyectos y recorran las ejecuciones con el modo
ejemplo1.jl
interactivo.Respondanenelinforme:
1. ParalaredCLRS,tabulenporiteración:caminoaumentante,longitud(númerode
arcos),cuellodebotella∆yflujoacumulado,paraBFSyparaDFSporseparado.
2. Identifiquenenlasanimacionesunaiteracióndondeelcaminoaumentanteuseun
arcoderetroceso(punteadonaranja).Expliquenconsuspalabrasquéflujoseestá
cancelandoyporquéelresultadosiguesiendoválido.
3. En la animación de Edmonds-Karp, observen la onda BFS: ¿qué representa el
númerodanotadobajocadanodo?¿Porquéelcaminoresaltadosiempretiene
exactamented(t)arcos?
4. Comparenelúltimofotogramadeambosalgoritmos:¿elcortemínimoeselmismo?
¿Elflujomáximoeselmismo?¿Losflujosarcoporarcosonlosmismos?Expliquen
cadarespuesta.
| 4.2 | Parte 2 | — El experimento | zigzag | (3 puntos) |
| --- | ------- | ---------------- | ------ | ---------- |
Laredzigzagtieneunarcotrampau → v decapacidad1entredosrutasdecapacidad
M.Enteoría,unFord-Fulkersonquesiempreeligieraelcaminoqueatraviesaesearco
| necesitaría2M |     | iteraciones. |     |     |
| ------------- | --- | ------------ | --- | --- |
include("ford_fulkerson.jl")
1
2
3 M = 1000
| Cz = | zeros(Int, | 4, 4) |     |     |
| ---- | ---------- | ----- | --- | --- |
4
| Cz[1,2] | = M; Cz[1,3] | = M # | →su, →sv |     |
| ------- | ------------ | ----- | -------- | --- |
5
| 6 Cz[2,3] | = 1 # →uv    | (arco trampa) |          |     |
| --------- | ------------ | ------------- | -------- | --- |
| Cz[2,4]   | = M; Cz[3,4] | = M #         | →ut, →vt |     |
7
| red_z | = RedFlujo(Cz, | ["s","u","v","t"], |     |     |
| ----- | -------------- | ------------------ | --- | --- |
8
| 9   | [(0.0,1.0),(1.2,2.0),(1.2,0.0),(2.4,1.0)]) |     |     |     |
| --- | ------------------------------------------ | --- | --- | --- |
10
| # Comparar | ambos | métodos: |     |     |
| ---------- | ----- | -------- | --- | --- |
11
| 12 ford_fulkerson(red_z, |     | 1, 4; | metodo=:dfs) |     |
| ------------------------ | --- | ----- | ------------ | --- |
| 13 ford_fulkerson(red_z, |     | 1, 4; | metodo=:bfs) |     |
Listing4.1:Redzigzagenelproyectoford-fulkerson(ejecutardesdeesacarpeta)
7

ACTIVIDAD:FLUJOMÁXIMO UNIVERSIDADDECUENCA
1. EjecutenambosmétodosparaM ∈ {10,100,1000,10000}ytabulenelnúmerode
iteracionesyloscaminosusadosencadacaso.
2. ¿La implementación DFSdelrepositorio alcanza el peor caso teórico de 2M ite-
raciones? Analicen el orden de exploración de la función buscar_camino_dfs y
expliquenporqué seobservaelnúmerodeiteracionesobtenido.
3. ProponganyjustifiquenunamodificacióndelordendeexploracióndelaDFS(por
ejemplo,invertirelordendelosvecinos)queempeoresucomportamientoenesta
red.Impleméntenlayreportenelefecto.
4. ¿PorquéEdmonds-KarpesinmuneaesteproblemasinimportarelvalordeM?
Relacionensurespuestaconlalongituddeloscaminos.
Exclamation-circle ElcasopatológicoquemotivaaEdmonds-Karp
Con capacidades enteras, Ford-Fulkerson siempre termina, pero su número de
iteracionespuededependerdelvalor delascapacidades,nosolodeltamañodel
grafo. Con capacidadesirracionalesexiste una red(Zwick, 1995) en la que Ford-
Fulkersonconmalaeleccióndecaminosnoterminanuncaynisiquieraconverge
alflujomáximo.Edmonds-Karpeliminaambosproblemas:sucotaO(V ·E2)es
independientedelascapacidades.
4.3 Parte 3 —Su propia red (3 puntos)
Cadaparejadebediseñarunareddeflujooriginalquecumpla:
• Almenos8nodosy12arcos,conposicioneslegibles.
• Almenosunpardearcosantiparalelos(u → vyv → u).
• Quealmenosunaejecución(BFSoDFS)useunarcoderetrocesoenalgúncamino
aumentante.
• QueelnúmerodeiteracionesdeBFSyDFSseadiferente.
Consured:ejecutenambosalgoritmos,generenlasanimacionesGIFconlasfun-
ciones animar_ford_fulkersony animar_edmonds_karp,verifiquen a mano elcorte
mínimoreportado(sumenlascapacidadesdelasaristasdelcorte)einclúyanlotodoen
elinforme.
INFO-CIRCLE Sugerencia
Diseñenprimerolaredenpapelpensandodóndequierenqueaparezcaelcuellode
botella,yluegoajustencapacidadeshastaprovocarloscomportamientospedidos.
Documentenenelinformelosintentosfallidos:elprocesodediseñotambiénse
evalúa.
8

ACTIVIDAD:FLUJOMÁXIMO UNIVERSIDADDECUENCA
4.4 Parte 4 — Análisis comparativo (2 puntos)
Conlaevidenciadelaspartes1–3,completenlatabla3yrespondanlaspreguntasde
discusión.
Cuadro3:Tablacomparativaacompletarporlapareja
Criterio Ford-Fulkerson(DFS) Edmonds-Karp(BFS)
Estrategiade
búsquedadelcamino
aumentante
Complejidadteórica
¿Terminacon
capacidades
irracionales?
Iteracionesobservadas
(redCLRS)
Iteracionesobservadas
(zigzag,M = 104)
Longitudesdelos
caminosaumentantes
Sensibilidadalvalorde
lascapacidades
Flujomáximoobtenido
Cortemínimoobtenido
Preguntasdediscusión(respondanconargumentosyevidencia):
1. Similitudes:¿quécompartenexactamenteambosalgoritmos(invariantes,estruc-
turadelciclo,resultadofinal)?¿Quéteoremagarantizaqueamboslleganalmismo
valordeflujo?
2. Diferencias:enEdmonds-Karplaslongitudesdeloscaminosaumentantesnunca
decrecen(verifíquenloensustablas).¿Secumpleesapropiedadensusejecuciones
conDFS?¿QuépapeljuegaestapropiedadenlademostracióndelacotaO(V ·E2)?
3. Ventajasydesventajas:¿existealgúnescenariodondelavarianteDFSpuedaser
preferibleenlapráctica(porejemplo,memoria,simplicidad,redesconestructura
conocida)?Justifiquen.
4. Redescomplejas:propongandosaplicacionesdelflujomáximo/cortemínimo
enelanálisisderedescomplejas(porejemplo:robustezdeunareddecomunica-
cionesantefallas,capacidaddeunaredeléctricaodetransporte,detecciónde
9

ACTIVIDAD:FLUJOMÁXIMO UNIVERSIDADDECUENCA
comunidadesvíacortes).Paraunadeellas,indiquenquérepresentaríans,tylas
capacidades.
10

Capítulo 5
| Entregables, | Rúbrica | y Condiciones |     |     |     |
| ------------ | ------- | ------------- | --- | --- | --- |
5.1 Entregables
1. Informe PDF (máximo 12 páginas sin contar anexos) con las tablas, respuestas,
capturasdelasanimacionesyanálisisdelaspartes1–4.Debeincluirnombresy
correosinstitucionalesdeambosintegrantes.
2. CódigoJulia:losarchivoscreadosomodificados(redpropia,DFSmodificadadela
| parte2),ejecutablesconjulia |     | --project=.. |     |     |     |
| --------------------------- | --- | ------------ | --- | --- | --- |
3. Animaciones:losGIFdelaredpropiageneradosconambosalgoritmos.
| 5.2 Rúbrica de | evaluación |     |     |     |     |
| -------------- | ---------- | --- | --- | --- | --- |
Cuadro4:Rúbricadeevaluación(sobre10puntos)
| Componente               |     | Criteriodecalidad             |          |              | Puntos |
| ------------------------ | --- | ----------------------------- | -------- | ------------ | ------ |
| Parte1—Exploraciónguiada |     | Tablascompletasycorrectas;ex- |          |              | 2      |
|                          |     | plicación                     | clara de | los arcos de |        |
retrocesoydelaondaBFS.
| Parte2—Experimentozigzag |     | Medicionesparaloscuatrovalo- |     |     | 3   |
| ------------------------ | --- | ---------------------------- | --- | --- | --- |
resdeM;análisisdelordende
exploración;modificacióndela
DFSimplementadayexplicada.
| Parte3—Redpropia |     | Redquecumpleloscuatrorequi- |     |     | 3   |
| ---------------- | --- | --------------------------- | --- | --- | --- |
sitos;cortemínimoverificadoa
mano;animacionesincluidas.
| Parte4—Análisiscomparativo |     | Tabla      | comparativa  | completa; | 2   |
| -------------------------- | --- | ---------- | ------------ | --------- | --- |
|                            |     | respuestas | argumentadas | con       |     |
evidenciaexperimentalpropia.
|     |     |     |     | Total | 10  |
| --- | --- | --- | --- | ----- | --- |
Exclamation-Triangle Penalizaciones
Informesquenocompilenlasafirmacionesconevidenciapropia(tablas,capturas,
código),ocódigoquenoejecuteconjulia --project=.,perderánhastael50%
delpuntajedelcomponentecorrespondiente.Laentregatardíasepenalizasegún
11

ACTIVIDAD:FLUJOMÁXIMO UNIVERSIDADDECUENCA
elreglamentodelmódulo.
CLIPBOARD-CHECK Criteriodeexcelencia
Lasmejoresparejasnoselimitanareportarnúmeros:explicanporquéocurren.Un
informesobresalienteconectacadaobservaciónexperimentalconelargumento
teóricocorrespondiente(lemadelongitudesnodecrecientes,teoremamax-flow
min-cut,dependenciade|f∗|enlacotadeFord-Fulkerson).
12