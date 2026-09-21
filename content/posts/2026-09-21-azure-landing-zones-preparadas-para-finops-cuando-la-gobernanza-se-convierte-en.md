---
title: 'Azure Landing Zones preparadas para FinOps: cuando la gobernanza se convierte
  en control de costes'
date: '2026-09-21T12:12:29+00:00'
draft: true
slug: azure-landing-zones-preparadas-para-finops-cuando-la-gobernanza-se-convierte-en
description: Te explico cómo planteo una Azure Landing Zone para que la gobernanza
  también sirva como sistema de control de costes desde el primer día.
categories:
- Azure
- Arquitectura de Software
- FinOps
tags:
- Azure Landing Zones
- FinOps
- Gobernanza
- Azure Policy
- Cost Management
- Bicep
image: /images/azure-landing-zones-preparadas-para-finops-cuando-la-gobernanza-se-convierte-en/cover.png
comments: true
ai:
  assisted: true
  article_type: technical
  model: gpt-5.4
  prompt_version: 2026-08-21.1
  generated_at: '2026-09-21T12:12:29+00:00'
  reviewed_by: ''
  review_status: pending
  disclosure: Borrador asistido por IA; revisado por una persona antes de su publicación.
  sources:
  - url: https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/finops-ready-azure-landing-zone-part-2/ba-p/4555727
    title: FinOps-Ready Azure Landing Zone - Part 2
    published_date: '2026-09-18'
  - url: https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone
    title: What is an Azure landing zone? - Cloud Adoption Framework
    published_date: null
  - url: https://learn.microsoft.com/en-us/azure/well-architected/cost-optimization/set-spending-guardrails
    title: Architecture strategies for setting spending guardrails - Microsoft Azure
      Well-Architected Framework | Microsoft Learn
    published_date: null
---

Si diseñas una *landing zone* pensando solo en seguridad, redes y cumplimiento, para mí te falta una pieza crítica: el coste. Cada vez tengo más claro que **FinOps no debería llegar después de la plataforma**, como una capa reactiva de informes, sustos y recortes, sino formar parte de la arquitectura desde el minuto uno. En Azure, eso significa usar la jerarquía de *management groups*, las suscripciones, Azure Policy y los guardrails operativos como un sistema que haga más difícil gastar mal y más fácil atribuir, vigilar y corregir.

La propia [definición de Azure landing zone en Cloud Adoption Framework](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone) ya apunta en esa dirección: una base preparada para gobernar, securizar y escalar entornos multi-suscripción. Y si además lees las [recomendaciones de *spending guardrails* del Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/cost-optimization/set-spending-guardrails), el mensaje es todavía más directo: controles de acceso, políticas, límites y automatización de plataforma. Mi tesis aquí es sencilla: **una landing zone madura ya es, en gran medida, tu sistema de control de costes**.

### El cambio mental: de gobierno “administrativo” a gobierno “económico”

Durante años se ha tratado la gobernanza como algo casi burocrático: *naming*, tags, RBAC, regiones permitidas y poco más. Todo eso está bien, claro. El problema es que se queda corto en cuanto el gasto empieza a crecer, aparecen varias unidades de negocio y nadie sabe muy bien quién paga qué ni quién puede tomar decisiones cuando algo se dispara.

En mi experiencia, el salto de verdad ocurre cuando cada decisión de plataforma responde también a tres preguntas muy terrenales: quién paga, quién decide y quién responde cuando el coste se desvía. Parece una obviedad, pero no lo es. He visto demasiados entornos “bien gobernados” en lo técnico y completamente borrosos en lo económico.

El artículo [«FinOps-Ready Azure Landing Zone - Part 2»](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/finops-ready-azure-landing-zone-part-2/ba-p/4555727) lo explica muy bien al separar la visibilidad a nivel de recurso de la visibilidad a nivel de aplicación. Azure te dice cuánto cuesta un recurso; el problema real en una empresa es saber qué aplicación representa, qué unidad de negocio la financia, qué equipo la opera y qué dependencias arrastra. Si eso no está modelado en la landing zone, FinOps llega tarde y, peor aún, llega a ciegas.

{{< figure src="/images/azure-landing-zones-preparadas-para-finops-cuando-la-gobernanza-se-convierte-en/body-1.png" alt="Diagrama del modelo operativo FinOps en una landing zone" caption="La landing zone se vuelve FinOps-ready cuando jerarquía, políticas, visibilidad y automatización trabajan como un único sistema." >}}{{< /figure >}}

Por eso yo suelo pensar una landing zone en cuatro planos conectados:

- **Jerarquía organizativa**: *management groups* y suscripciones alineados con responsabilidad financiera.
- **Gobernanza preventiva**: políticas que niegan o auditan configuraciones costosas o inatribuidas.
- **Gobernanza detectiva**: presupuestos, alertas y análisis centralizado.
- **Gobernanza correctiva**: automatización para apagar, etiquetar, bloquear o escalar revisiones.

Si una de esas capas falta, para mí no tienes FinOps embebido. Tienes, como mucho, observación de costes.

### Cómo mapear la landing zone al modelo operativo de FinOps

La [arquitectura de landing zones de Azure](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone) distingue entre *platform landing zones* y *application landing zones*. Esa separación me parece especialmente útil para FinOps porque permite decidir qué costes son compartidos y cuáles son atribuibles a una carga concreta sin mezclar señales desde el principio.

Yo lo mapearía así:

- **Management groups** para aplicar políticas de coste por dominio organizativo: producción, no producción, *sandbox*, datos, IA, etc.
- **Suscripciones** como frontera financiera y operativa cuando necesites aislar presupuesto, *ownership* o ciclo de vida.
- **Resource groups** como unidad táctica de despliegue, no como frontera principal de gobierno económico.
- **Tags obligatorias** para llevar el coste hasta aplicación, entorno, centro de coste y propietario.

Un ejemplo razonable podría ser este:

- `Mg-platform`: conectividad, identidad, observabilidad y servicios compartidos.
- `Mg-corp-prod`: cargas productivas corporativas.
- `Mg-corp-nonprod`: desarrollo, test y preproducción.
- `Mg-sandbox`: experimentación con límites más estrictos.

Aquí la clave no es “ordenar” Azure porque sí. La clave es que **cada nivel te permita tomar decisiones económicas distintas**. *Sandbox* puede tener SKUs limitados y regiones reducidas. *Nonprod* puede exigir apagado nocturno o recursos efímeros. Producción puede aceptar compromisos de gasto, pero con *ownership* cristalino. Dicho de otra forma: la jerarquía no solo organiza, también condiciona el comportamiento financiero.

### Antes de empezar

Para reproducir el ejemplo de este artículo, yo asumiría este punto de partida:

- Una suscripción de Azure activa.
- Permisos suficientes para crear *resource groups* y asignar políticas. Idealmente, `Owner` o `Contributor` + `Resource Policy Contributor` en la suscripción donde vas a probar.
- [Azure CLI](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone) instalada, versión **2.75 o superior**.
- [Bicep CLI integrada en Azure CLI](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone) o soporte de `az deployment sub create` con ficheros `.bicep`.
- Una sesión iniciada con `az login` y la suscripción seleccionada.

Yo comprobaría versión y contexto con esto:

```bash
az version --query '"azure-cli"' -o tsv
az account show --query '{subscription:name, id:id, tenantId:tenantId}' -o table
```

Con eso ves enseguida si estás en la suscripción correcta antes de desplegar nada (que parece una tontería, hasta que no lo es).

### Paso 1: crear una base mínima gobernable con Bicep

Voy a montar un ejemplo pequeño, pero útil: un *resource group* para una carga, una política que obligue a llevar ciertas tags y una asignación a nivel de suscripción. No es una *enterprise-scale landing zone* completa, pero sí reproduce el patrón que luego escalarías a *management groups*.

Guarda este archivo como `main.bicep`. Está pensado para desplegarse en **Bicep sobre Azure Resource Manager** con **Azure CLI 2.75+**.

```bicep
targetScope = 'subscription'

@description('Ubicación del resource group de ejemplo')
param location string = 'westeurope'

@description('Nombre del resource group de la carga')
param workloadRgName string = 'rg-app-payments-prod-we'

resource workloadRg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: workloadRgName
  location: location
  tags: {
    Application: 'payments-api'
    Environment: 'prod'
    CostCenter: 'FIN-042'
    Owner: 'team-payments'
  }
}

resource requireCostCenterTagDef 'Microsoft.Authorization/policyDefinitions@2021-06-01' = {
  name: 'require-costcenter-tag'
  properties: {
    policyType: 'Custom'
    mode: 'Indexed' // Limito la evaluación a recursos con tags para evitar ruido innecesario
    displayName: 'Require CostCenter tag on resources'
    description: 'Denies resource creation when the CostCenter tag is missing.'
    policyRule: {
      if: {
        allOf: [
          {
            field: 'type'
            notEquals: 'Microsoft.Resources/subscriptions/resourceGroups'
          }
          {
            field: 'tags[CostCenter]'
            exists: false
          }
        ]
      }
      then: {
        effect: 'deny'
      }
    }
  }
}

resource requireOwnerTagDef 'Microsoft.Authorization/policyDefinitions@2021-06-01' = {
  name: 'require-owner-tag'
  properties: {
    policyType: 'Custom'
    mode: 'Indexed'
    displayName: 'Require Owner tag on resources'
    description: 'Denies resource creation when the Owner tag is missing.'
    policyRule: {
      if: {
        allOf: [
          {
            field: 'type'
            notEquals: 'Microsoft.Resources/subscriptions/resourceGroups'
          }
          {
            field: 'tags[Owner]'
            exists: false
          }
        ]
      }
      then: {
        effect: 'deny'
      }
    }
  }
}

resource assignCostCenter 'Microsoft.Authorization/policyAssignments@2022-06-01' = {
  name: 'assign-require-costcenter-tag'
  properties: {
    displayName: 'Assign require CostCenter tag'
    policyDefinitionId: requireCostCenterTagDef.id
  }
}

resource assignOwner 'Microsoft.Authorization/policyAssignments@2022-06-01' = {
  name: 'assign-require-owner-tag'
  properties: {
    displayName: 'Assign require Owner tag'
    policyDefinitionId: requireOwnerTagDef.id
  }
}
```

Despliega el archivo así:

```bash
az deployment sub create \
  --location westeurope \
  --name lz-finops-baseline \
  --template-file main.bicep \
  --query properties.provisioningState -o tsv
```

Si todo va bien, verás `Succeeded`. Y lo importante no es el *Succeeded* en sí, claro; lo importante es que ya tienes una primera línea de defensa para evitar gasto huérfano.

### Paso 2: verificar que la gobernanza bloquea gasto inatribuible

Aquí viene la parte que a mí más me interesa demostrar: que la política no es decorativa. Voy a intentar crear una cuenta de almacenamiento sin las tags requeridas. Si la landing zone está bien planteada, el despliegue debe fallar.

Primero crea un archivo `bad-storage.json` para **ARM template deployment con Azure CLI 2.75+**:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "resources": [
    {
      "type": "Microsoft.Storage/storageAccounts",
      "apiVersion": "2023-05-01",
      "name": "stfinopsguardrail001",
      "location": "westeurope",
      "sku": {
        "name": "Standard_LRS"
      },
      "kind": "StorageV2",
      "properties": {}
    }
  ]
}
```

Lanza el despliegue en el *resource group* creado antes:

```bash
az deployment group create \
  --resource-group rg-app-payments-prod-we \
  --name verify-deny-missing-tags \
  --template-file bad-storage.json \
  --query error.code -o tsv
```

Lo esperable aquí es un error `RequestDisallowedByPolicy` o equivalente, indicando que falta la tag `CostCenter` o `Owner`. Y sí, en este caso el error es una buena noticia.

**No quiero descubrir el coste huérfano al final de mes; quiero impedirlo en el momento de creación.** Esa es la diferencia entre vigilar gasto y diseñar una plataforma que ya incorpora disciplina económica.

{{< figure src="/images/azure-landing-zones-preparadas-para-finops-cuando-la-gobernanza-se-convierte-en/body-2.png" alt="Flujo de denegación por Azure Policy al faltar etiquetas de coste" caption="Un guardrail útil no avisa tarde: bloquea la creación de recursos que nacerían sin contexto financiero." >}}{{< /figure >}}

### Paso 3: crear un recurso válido y comprobar que pasa el guardrail

Ahora repito la prueba, pero cumpliendo las reglas. Guarda este archivo como `good-storage.json`:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "resources": [
    {
      "type": "Microsoft.Storage/storageAccounts",
      "apiVersion": "2023-05-01",
      "name": "stfinopsguardrail002",
      "location": "westeurope",
      "tags": {
        "CostCenter": "FIN-042",
        "Owner": "team-payments",
        "Application": "payments-api",
        "Environment": "prod"
      },
      "sku": {
        "name": "Standard_LRS"
      },
      "kind": "StorageV2",
      "properties": {}
    }
  ]
}
```

Despliega de nuevo:

```bash
az deployment group create \
  --resource-group rg-app-payments-prod-we \
  --name verify-allowed-tagged-resource \
  --template-file good-storage.json \
  --query properties.provisioningState -o tsv
```

Aquí deberías obtener `Succeeded` y ver la cuenta `stfinopsguardrail002` en el *resource group*.

Puedes comprobar las tags así:

```bash
az resource show \
  --resource-group rg-app-payments-prod-we \
  --name stfinopsguardrail002 \
  --resource-type Microsoft.Storage/storageAccounts \
  --query tags -o json
```

Y deberías ver algo equivalente a esto:

```json
{
  "Application": "payments-api",
  "CostCenter": "FIN-042",
  "Environment": "prod",
  "Owner": "team-payments"
}
```

### Qué guardrails de coste metería yo en la landing zone desde el día uno

Las [guías de *spending guardrails* de Azure Well-Architected](https://learn.microsoft.com/en-us/azure/well-architected/cost-optimization/set-spending-guardrails) hablan de *release gates*, *governance policies*, límites de recursos y controles de acceso. Traducido a una landing zone real, yo empezaría por decisiones bastante concretas:

1. **Tags obligatorias y útiles**, no una taxonomía ornamental. Si nadie usa una tag para una decisión financiera u operativa, probablemente sobra.
2. **Regiones permitidas**. Limitar geografía también limita combinaciones de precio, dispersión y complejidad.
3. **Catálogo de SKUs permitidos por entorno**. En *sandbox* y *nonprod*, esto reduce mucho el sobredimensionamiento por defecto.
4. **Separación de suscripciones por responsabilidad financiera**. No todo merece su propia suscripción, pero mezclar dominios sin *ownership* claro suele salir caro.
5. **Políticas de expiración o revisión para entornos efímeros**, especialmente en innovación, datos e IA.
6. **Observabilidad centralizada** para unir coste, inventario y contexto de aplicación, justo en la línea que plantea el artículo sobre [landing zones preparadas para FinOps](https://techcommunity.microsoft.com/t5/azure-infrastructure-blog/finops-ready-azure-landing-zone-part-2/ba-p/4555727).

### Lo que mucha gente subestima: la relación entre ownership y coste

Cuando un recurso no tiene propietario, tampoco tiene una historia de negocio clara. Y cuando no tiene historia de negocio, nadie lo apaga, nadie lo redimensiona y nadie discute en serio si debía existir. Por eso insisto tanto en que las tags no son un simple *check* de compliance: son la base para conversación, *accountability* y automatización.

Aquí es donde la separación entre monitorización de recurso y monitorización de aplicación se vuelve decisiva. Un App Service barato puede depender de una base de datos costosa, una cola, un Key Vault y varios componentes de red. Si la landing zone no te ayuda a agrupar eso por aplicación, el análisis financiero se fragmenta en piezas que no cuentan la historia completa.

**El coste verdaderamente relevante no es el del recurso aislado, sino el del servicio que entregas.** Y si la plataforma no te da ese contexto, luego intentas reconstruirlo con hojas de cálculo, reuniones eternas y bastante sufrimiento innecesario.

### Un diseño práctico de suscripciones para no mezclar señales

Si me preguntas por una hoja de ruta sensata, yo iría por aquí:

- Una o varias suscripciones de plataforma para conectividad, identidad, seguridad y observabilidad compartida.
- Suscripciones de *workload* separadas al menos por producción y no producción cuando el coste o el riesgo lo justifiquen.
- *Sandboxes* acotados, con políticas más estrictas y revisión frecuente.
- Asignaciones de Policy heredadas desde *management groups*, evitando replicar reglas manualmente en cada suscripción.

No hace falta empezar con una jerarquía gigantesca ni con un diseño de manual perfecto. Lo que sí hace falta es que la estructura soporte preguntas reales: qué gasta producción, qué gasta I+D, qué parte corresponde a plataforma compartida, qué parte pertenece a un producto concreto y quién puede decidir optimizaciones sin abrir un debate arqueológico cada mes.

### Errores que yo evitaría desde el primer sprint

Hay varios antipatrones que veo repetirse con demasiada frecuencia:

- Crear la landing zone y dejar FinOps para una “fase 2”.
- Meter tags obligatorias, pero sin proceso para mantener su vocabulario y su calidad.
- Usar una única suscripción para todo porque al principio “es más simple”.
- Confiar en *dashboards* de coste sin controles preventivos.
- Hacer *governance* manual en vez de automatizada con IaC y Policy.

El problema de todos ellos es el mismo: desplazan el control al momento más caro, que es cuando el gasto ya ha ocurrido. Y una vez has llegado ahí, optimizar sigue siendo posible, claro, pero ya estás jugando en defensa.

### Mi conclusión

Yo ya no separo arquitectura de plataforma y disciplina FinOps. Una [Azure landing zone bien planteada](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone) incorpora muchas de las decisiones que luego determinan si puedes gobernar el gasto con precisión o si solo vas a reaccionar tarde. Y cuando combinas esa base con [guardrails de gasto bien definidos](https://learn.microsoft.com/en-us/azure/well-architected/cost-optimization/set-spending-guardrails), la gobernanza deja de ser un catálogo de restricciones para convertirse en algo bastante más útil: un sistema operativo económico para tu nube.

Si tú construyes plataforma en Azure, mi recomendación es muy clara: empieza por la jerarquía, la atribución y las Policies que impiden el gasto opaco. Lo demás —*dashboards*, optimizaciones, compromisos de consumo y automatización más avanzada— funciona muchísimo mejor cuando esa base ya existe.

Y como puedes ver, aquí no hay magia. Hay diseño intencional, guardrails bien puestos y una idea bastante simple detrás: gastar mejor también es arquitectura.
