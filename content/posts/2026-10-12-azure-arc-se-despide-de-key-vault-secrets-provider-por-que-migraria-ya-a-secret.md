---
title: 'Azure Arc se despide de Key Vault Secrets Provider: por qué yo migraría ya
  a Secret Store Extension'
date: '2026-10-12T06:39:20+00:00'
draft: true
slug: azure-arc-se-despide-de-key-vault-secrets-provider-por-que-migraria-ya-a-secret
description: La extensión Azure Key Vault Secrets Provider para Azure Arc Kubernetes
  se retira en 2027. Te explico qué cambia de verdad y cómo plantearía yo la migración
  a Secret Store Extension.
categories:
- Azure
- Arquitectura de Software
- Seguridad
tags:
- Azure Arc
- Kubernetes
- Azure Key Vault
- Seguridad
- Migración
image: /images/azure-arc-se-despide-de-key-vault-secrets-provider-por-que-migraria-ya-a-secret/cover.png
comments: true
ai:
  assisted: true
  article_type: business
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-10-12T06:39:20+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://azure.microsoft.com/updates?id=570313
    title: 'Retirement: Azure Key Vault Secrets Provider Extension for Azure Arc enabled
      Kubernetes clusters'
    published_date: '2026-10-09'
  - url: https://docs.microsoft.com/en-us/azure/azure-arc/kubernetes/secret-store-extension
    title: Use the Azure Key Vault Secret Store extension to sync secrets to the Kubernetes
      secret store for offline access in Azure Arc-enabled Kubernetes clusters - Azur…
    published_date: null
  - url: https://techcommunity.microsoft.com/t5/azure-arc-blog/ga-azure-key-vault-secrets-provider-extension-for-arc-enabled/ba-p/3389231
    title: 'GA: Azure Key Vault secrets provider extension for Arc enabled Kubernetes
      clusters | Microsoft Community Hub'
    published_date: null
---

Si tienes clústeres de Kubernetes conectados con Azure Arc y dependes de secretos servidos desde Azure Key Vault, yo no lo dejaría para el último momento. [Microsoft ha anunciado la retirada de Azure Key Vault Secrets Provider Extension para Azure Arc-enabled Kubernetes el 9 de octubre de 2027](https://azure.microsoft.com/updates?id=570313). Sobre el papel parece una fecha lejana. En la práctica, este tipo de cambios casi nunca duele por la sustitución técnica en sí, sino por todo lo que deja al descubierto: supuestos de conectividad, hábitos de despliegue, permisos excesivos y una arquitectura de secretos que quizá llevaba demasiado tiempo funcionando “porque sí”.

Mi lectura es bastante clara: **esto no va de cambiar una extensión por otra, sino de asumir un modelo operativo distinto**. Y si tu realidad está más cerca del híbrido, el edge o la conectividad irregular que del datacenter idealizado, la pregunta útil no es “¿puedo esperar hasta 2027?”, sino “¿qué dependencia exacta tengo hoy del acceso online y cuánto me costará moverme a un esquema sincronizado?”. Ahí está la conversación de verdad.

### Qué se retira exactamente y por qué importa

Lo que entra en retirada es la extensión de Azure Arc que permitía acceder a secretos de Azure Key Vault desde el clúster y montarlos en los pods. En el [anuncio de disponibilidad general del modelo original](https://techcommunity.microsoft.com/t5/azure-arc-blog/ga-azure-key-vault-secrets-provider-extension-for-arc-enabled/ba-p/3389231) se describía un flujo apoyado en el CSI driver y en el proveedor de Key Vault: cuando el pod arrancaba o se reiniciaba, se recuperaba el secreto y se montaba en un volumen `tmpfs` dentro del contenedor. La idea tenía bastante sentido. **Reducía la persistencia local del secreto** y encajaba muy bien cuando la conectividad con Azure era sólida y predecible.

{{< figure src="/images/azure-arc-se-despide-de-key-vault-secrets-provider-por-que-migraria-ya-a-secret/body-1.png" alt="Comparativa entre el modelo online y el modelo sincronizado de secretos en Azure Arc" caption="Dos modelos, dos implicaciones: menos persistencia local frente a más resiliencia offline." >}}{{< /figure >}}

El problema es que Azure Arc rara vez vive en un mundo homogéneo. Hay clústeres en fábricas, tiendas, oficinas remotas o ubicaciones donde la conectividad no es exactamente una promesa contractual (ni una experiencia relajante). Y ahí es donde la [documentación de Secret Store Extension](https://docs.microsoft.com/en-us/azure/azure-arc/kubernetes/secret-store-extension) deja bastante clara la dirección que Microsoft recomienda: sincronizar secretos desde Key Vault al almacén de secretos de Kubernetes para disponer de **acceso offline**.

Ese matiz cambia mucho más de lo que parece. Cambia el punto de dependencia, cambia dónde se materializa el riesgo y cambia también cómo deberías pensar la rotación, la auditoría y el endurecimiento del clúster. No es un simple relevo de componentes. Es otro contrato operativo.

### La diferencia que de verdad importa: online frente a sincronización local

Si me preguntas por la diferencia importante —la que condiciona decisiones, no presentaciones— yo la resumiría así:

- Con el modelo anterior, el secreto se obtenía desde Key Vault para el consumo del pod, con una dependencia fuerte de conectividad y de la cadena CSI/proveedor.
- Con Secret Store Extension, el secreto se sincroniza al `Secret` de Kubernetes y queda disponible localmente, incluso si el clúster entra en un estado semi-desconectado.

La propia [guía de Secret Store Extension](https://docs.microsoft.com/en-us/azure/azure-arc/kubernetes/secret-store-extension) lo dice sin rodeos: está pensada para clústeres fuera de Azure donde la conectividad con Key Vault puede no ser perfecta. Y añade algo que no conviene pasar por alto: SSE crea copias locales de los secretos en el almacén de Kubernetes. Es decir, ganas resiliencia operativa, pero a cambio asumes una responsabilidad mayor sobre la protección del dato dentro del clúster.

En otras palabras, **ganas continuidad offline, pero también aumentas la exigencia de disciplina en el plano local**. A mí ese intercambio me parece razonable en Azure Arc. Lo que no me parecería razonable es adoptar SSE pensando que “es básicamente lo mismo con otro nombre”. Porque no lo es. Y cuando se parte de esa premisa, los errores suelen aparecer donde más duele: seguridad, permisos y operación.

### Lo que yo revisaría antes de migrar

Antes de instalar nada, yo haría inventario. Pero inventario útil, no una hoja de cálculo ornamental que nadie vuelve a abrir. Empezaría por entender cómo se usa de verdad la extensión actual y qué patrones de consumo hay en las aplicaciones.

#### 1. Cómo consumen los secretos tus aplicaciones

No es lo mismo una aplicación que espera un volumen montado con archivos que otra que ya consume secretos de Kubernetes como variables de entorno o como volúmenes nativos. Como SSE sincroniza el secreto al almacén de Kubernetes, el impacto puede ser pequeño… o no tanto. Depende de cómo hayas estandarizado tus manifiestos, de si tienes convenciones claras y de cuánto acoplamiento hay al modelo anterior. **Aquí el riesgo no suele ser técnico, sino de consistencia**: varias aplicaciones resolviendo el mismo problema de cinco formas distintas.

#### 2. Qué requisitos de conectividad tienes de verdad

Si tu clúster tiene conexión excelente y continua con Azure, el modelo online tenía mucha lógica. Pero precisamente la [documentación de SSE](https://docs.microsoft.com/en-us/azure/azure-arc/kubernetes/secret-store-extension) lo recomienda para escenarios fuera de Azure donde la conectividad puede fallar. Yo revisaría incidentes reales y no supuestos amables: cortes, latencia, proxies corporativos, ventanas de mantenimiento, cadencias de reconexión y cualquier degradación que en un diagrama “no debería pasar”, pero pasa igual.

{{< figure src="/images/azure-arc-se-despide-de-key-vault-secrets-provider-por-que-migraria-ya-a-secret/body-2.png" alt="Flujo de sincronización de Secret Store Extension hacia Kubernetes" caption="SSE cambia el punto clave del diseño: el secreto pasa a vivir también dentro del cluster." >}}{{< /figure >}}

#### 3. Qué postura de seguridad tienes sobre secretos en Kubernetes

Para mí, este es el punto más serio. Si los secretos quedan almacenados en Kubernetes, el clúster deja de ser solo un consumidor de secretos y pasa a ser también su superficie de protección. La [documentación de Secret Store Extension](https://docs.microsoft.com/en-us/azure/azure-arc/kubernetes/secret-store-extension) menciona namespaces aislados, políticas RBAC y permisos limitados para el controlador de sincronización, y además recomienda [cifrar el almacén de secretos de Kubernetes](https://docs.microsoft.com/en-us/azure/azure-arc/kubernetes/secret-store-extension). Si tu plataforma no tiene una historia madura de hardening, auditoría y control de acceso, yo no haría la migración como una tarea puramente mecánica. Primero cerraría ese frente.

#### 4. Si estás pensando convivir con ambas extensiones

Yo sería muy conservador con eso. La [documentación oficial de SSE](https://docs.microsoft.com/en-us/azure/azure-arc/kubernetes/secret-store-extension) indica que no se recomienda ejecutar en paralelo la extensión online de Azure Key Vault Secrets Provider y SSE en el mismo clúster. Y a mí eso me suena a lo que realmente es: una migración pensada como reemplazo ordenado, no como convivencia indefinida “por si acaso”. El “por si acaso” en plataformas suele durar meses. O años. Y luego vienen las sorpresas.

### La hoja de ruta pragmática que yo seguiría

Sí, la retirada es en 2027. Pero yo dividiría el trabajo en fases pequeñas, verificables y con un resultado útil en cada paso. Lo importante aquí no es correr. Lo importante es no llegar tarde con deuda invisible.

### Fase 1: descubrimiento e inventario

Yo empezaría por una lista clara de clústeres Arc, namespaces, workloads y secretos dependientes. El objetivo no es solo saber qué existe, sino qué merece migración tal cual, qué requiere adaptación y qué revela un diseño mejorable.

```bash
az k8s-extension list \
  --cluster-type connectedClusters \
  --cluster-name MiClusterArcProduccion \
  --resource-group rg-plataforma-hibrida \
  --output table  # me interesa ver rápido qué extensiones siguen activas antes de planificar el reemplazo
```

Ese comando me gusta porque da visibilidad inmediata sobre las extensiones instaladas en un clúster Arc. Pero **el valor no está en ejecutarlo, sino en convertir su salida en decisiones**: qué dependencias siguen vivas, qué entornos están expuestos y dónde conviene empezar el piloto sin poner en riesgo un servicio crítico.

### Fase 2: piloto con Secret Store Extension

Después montaría un piloto en un clúster no crítico. No lo usaría para “demostrar que instala”, porque eso aporta muy poco. Lo usaría para validar tres cosas que sí importan:

- Que la sincronización desde Key Vault funciona con tu identidad y tus permisos reales;
- Que el secreto aparece en Kubernetes con la forma que tu aplicación espera;
- Que la rotación y la actualización encajan con tus tiempos operativos y tus procedimientos.

Aquí conviene recordar otro detalle importante de la [documentación de Secret Store Extension](https://docs.microsoft.com/en-us/azure/azure-arc/kubernetes/secret-store-extension): los secretos sincronizados pueden usarse como cualquier otro `Secret` de Kubernetes, por ejemplo montados como volumen o expuestos como variable de entorno. Esto simplifica mucho la integración con aplicaciones estándar. Pero también puede dar una falsa sensación de tranquilidad: como “ya es un `Secret` normal”, alguien puede olvidar que sigue siendo un activo sensible y que la pregunta clave pasa a ser quién puede leerlo, replicarlo o desplegarlo.

### Fase 3: endurecimiento del clúster

Antes de ampliar el cambio al resto de dominios, yo revisaría al menos esto:

- RBAC por namespace y por servicio.
- Cifrado del secret store de Kubernetes.
- Políticas de acceso a Key Vault y al mecanismo de sincronización.
- Procedimientos de rotación y revocación.
- Trazabilidad: quién lee, quién sincroniza, quién despliega.

{{< figure src="/images/azure-arc-se-despide-de-key-vault-secrets-provider-por-que-migraria-ya-a-secret/body-3.png" alt="Checklist visual de migración desde Key Vault Secrets Provider a Secret Store Extension" caption="La parte difícil no es instalar la nueva extensión, sino migrar con criterio operativo y de seguridad." >}}{{< /figure >}}

Si esta fase se trata como un apéndice, la migración puede salir bien desde el punto de vista técnico y mal desde el punto de vista arquitectónico. Y ya sabes cómo acaba eso: aparentemente todo funciona… hasta que deja de ser aceptable para auditoría, para operación o para ambos. **En seguridad, “ya lo endureceremos luego” suele ser una frase carísima**.

### Fase 4: migración progresiva por dominios

Yo movería primero workloads internos o de menor criticidad. Después, servicios con dependencias más sensibles. Y dejaría para el final las piezas más expuestas o más reguladas. No por miedo, sino por estrategia: cada dominio debería dejar una plantilla reutilizable de permisos, naming, namespaces, forma de consumo y controles. Si una migración no te deja un patrón repetible, te deja trabajo artesanal. Y el trabajo artesanal en plataforma no escala especialmente bien.

### Qué cambia para plataforma y qué cambia para aplicación

Para un equipo de plataforma, el cambio principal es de responsabilidad. Antes gran parte del foco estaba en la conectividad y en la cadena CSI hacia Key Vault. Ahora el foco pasa también a la custodia local del secreto en Kubernetes. Eso obliga a gobernar mejor el clúster, a revisar RBAC con más rigor y a tratar el almacén de secretos como un elemento crítico del diseño, no como una casilla de infraestructura.

Para un equipo de aplicación, en cambio, el cambio puede ser incluso beneficioso. Si una app ya trabaja bien con `Secret` de Kubernetes, el modelo es más natural y más alineado con patrones habituales del ecosistema. Hay menos piezas especiales en tiempo de ejecución, menos dependencia del momento exacto en que se resuelve el acceso remoto y más previsibilidad operacional.

Eso sí: que algo sea estándar no significa que sea automáticamente seguro. Un `Secret` de Kubernetes sigue siendo un dato sensible aunque su consumo sea cómodo. Si me preguntas dónde he visto más errores en este tipo de escenarios, yo no señalaría primero a la instalación de la extensión. Señalaría a permisos demasiado amplios, namespaces sin aislamiento real y ausencia de cifrado en el almacén de secretos. Ahí es donde se suelen esconder los problemas de verdad.

### Mi recomendación final

Yo empezaría ya, aunque solo sea para tener claridad. El [anuncio de retirada publicado por Microsoft](https://azure.microsoft.com/updates?id=570313) fija una fecha concreta —9 de octubre de 2027— y orienta a los clientes actuales a migrar a Azure Key Vault Secret Store Extension antes de entonces. Eso no implica precipitarse ni montar un proyecto épico. Implica no dejar que el calendario tape una dependencia arquitectónica que ya existe hoy.

{{< figure src="/images/azure-arc-se-despide-de-key-vault-secrets-provider-por-que-migraria-ya-a-secret/body-4.png" alt="Línea temporal de retirada y migración recomendada para Azure Arc" caption="Esperar a la fecha de retirada es la peor estrategia: la ventana útil es la de preparación previa." >}}{{< /figure >}}

Si usas Azure Arc en escenarios híbridos o edge, yo trataría esta retirada como una oportunidad para mejorar tu arquitectura de secretos, no solo como una tarea de mantenimiento. El beneficio real no está en “seguir soportado”. Está en salir con un modelo más explícito sobre conectividad, persistencia local, RBAC y operación semi-desconectada.

Y si tuviera que resumirlo en una sola frase, sería esta: **no esperes a 2027 para descubrir que no estabas migrando una extensión, sino tu forma de gestionar secretos en Azure Arc**.
