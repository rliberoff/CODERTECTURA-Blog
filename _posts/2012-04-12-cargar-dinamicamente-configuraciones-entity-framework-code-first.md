---
title: "Cargar Dinámicamente Configuraciones de Entidades en Entity Framework y Code-First"
excerpt: "***Legacy*** - Una de las cosas que hace poderoso a este framework y que en particular a mi me encanta es la posibilidad de definir y configurar todo el repositorio de datos (la base de datos per se) completamente desde código fuente gestionado, un enfoque que se conoce como Code-First."
date: 2012-04-12 00:00:00 +0200
last_modified_at: 2023-10-27 00:00:00 +0200
layout: post
permalink: /posts/ef-cargar-dinamicamente-configuraciones-de-entidades
image:
    path: /images/2012-04-12-cargar-dinamicamente-configuraciones-entity-framework-code-first/header.webp
    thumbnail: /images/2012-04-12-cargar-dinamicamente-configuraciones-entity-framework-code-first/thumbnail.webp
categories:
    - Legacy
    - Tutorial
    - C#
    - Entity Framework
---

{% capture notice-text %}
Este tutorial es sobre una versión antigua (legacy) de Entity Framework, por lo cual muy probablemente este código esté obsoleto y no sea una buena idea usarlo en tus proyectos. Lo mantengo en este blog como un recuerdo de mi recorrido profesional y técnico.
{% endcapture %}

<div class="notice--danger" style="font-size: small; font-weight: bold;">
  {{ notice-text | markdownify }}
</div>

En estos días he estado muy activo empleando la nueva versión del <a href="http://msdn.microsoft.com/en-us/data/ef.aspx" target="_blank" rel="noopener">Entity Framework</a> de Microsoft.
Una de las cosas que hace poderoso a este *framework* y que en particular a mi me encanta es la posibilidad de definir y configurar todo el repositorio de datos (la base de datos *per se*) completamente desde código fuente gestionado, un enfoque que se conoce como `Code-First`.

A través de `Code-First` es posible definir las clases <a href="http://en.wikipedia.org/wiki/Plain_Old_CLR_Object" target="_blank" rel="noopener">POCO</a> y también *configuradores* (clases que bien heradan de <a href="http://msdn.microsoft.com/en-us/library/gg696117(v=vs.103)" target="_blank" rel="noopener">`EntityTypeConfiguration`</a> o de <a href="http://msdn.microsoft.com/en-us/library/gg696149(v=vs.103)" target="_blank" rel="noopener">`ComplexTypeConfiguration`</a>) y que nos permiten definir las restricciones sobre el modelo (como claves primarias y no nulidades) o los nombres de las tablas y sus columnas.

La parte interesante es que en modelos grandes y complejos un desarrollo termina llenándose de muchos *configuradores* que deben ser agregados al modelo en el momento de su creación (lo cual ocurre durante el evento <a href="http://msdn.microsoft.com/en-us/library/system.data.entity.dbcontext.onmodelcreating(v=vs.103).aspx" target="_blank" rel="noopener">`OnModelCreating`</a> de la clase <a href="http://msdn.microsoft.com/en-us/library/system.data.entity.dbcontext(v=vs.103).aspx" target="_blank" rel="noopener">`DbContext`</a>) y que termina incrementando dos factores muy poco positivos de un código: la <a href="http://en.wikipedia.org/wiki/Cyclomatic_complexity" target="_blank" rel="noopener">complejidad ciclomática</a> y el <a href="http://en.wikipedia.org/wiki/Coupling_(computer_programming)" target="_blank" rel="noopener">acoplamiento de clases</a>, ambos elementos que son reportados por el Visual Studio a través del Code Analyzer como una violación a la regla <a target="http://msdn.microsoft.com/en-us/library/bb397994.aspx">CA1506</a>.

Para evitar esto, lo ideal seria encontrar un mecanismo para cargar los *configuradores* de forma dinámica, pero el problema es que el método `Add` para el <a href="http://msdn.microsoft.com/en-us/library/system.data.entity.dbmodelbuilder(v=vs.103).aspx" target="_blank" rel="noopener">`ModelBuilder`</a> que se emplea para cargarlos no admite como parámetro una clase base o genérica que pudiera ayudarnos a través de herencia, sino que explícitamente sólo acepta un `EntityTypeConfiguration` o un `ComplexTypeConfiguration`.

Por suerte, la plataforma .NET y el lenguaje C# cuentan con una palabra que logra salvar la patria: <a href="http://msdn.microsoft.com/en-us/library/dd264741.aspx" target="_blank" rel="noopener">`dynamic`</a>; que se encargará de indicar al compilador que no haga validaciones del tipo de dato/objeto que se está pasando como parámetro al método y que más bien este tipo de verificaciones se practiquen en tiempo de ejecución, es decir, que el compilador confíe en que nosotros como desarrolladores sabemos lo que estamos haciendo.

Así, el primer paso sería utilizar `Reflection` sobre nuestro ensamblado, que como ya está cargado en memoria durante la ejecución del evento `OnModelCreating`, no impactará (negativamente) en el desempeño de nuestro aplicativo.

```csharp
/// <summary>
/// Method calleded when the model for a derived context has been initialized, but before the model has
/// been locked down and used to initialize the context.
/// </summary>
/// <param name=&amp;quot;modelBuilder&amp;quot;>The builder that defines the model for the context being created.</param>
protected override void OnModelCreating(DbModelBuilder modelBuilder)
{
    if (modelBuilder != null)
    {
        IEnumerable<Type> entityTypeConfigurationTypes = Assembly.GetExecutingAssembly().GetTypes().Where(type => 
            !type.IsAbstract
            && (type.BaseType.GetGenericTypeDefinition() == typeof(EntityTypeConfiguration) || type.BaseType.GetGenericTypeDefinition() == typeof(ComplexTypeConfiguration)));

        foreach (Type type in entityTypeConfigurationTypes)
        {
            // The 'Add' method of the DbModelBuilder accepts both &amp;quot;ComplexTypeConfiguration<TComplexType>&amp;quot; or &amp;quot;EntityTypeConfiguration<TEntityType>&amp;quot;.
            // At first glance, the type of configurator is not know during compile time.
            // The dynamic type enables the operations in which it occurs to bypass compile-time type checking, in other words,
            // types are not resolved or checked by the compiler; instead, these operations are resolved at run time (when the explicit configuration
            // type is known).
            // Reference: http://msdn.microsoft.com/en-us/library/dd264741.aspx
            dynamic entityTypeConfigurationInstance = Activator.CreateInstance(type);
            modelBuilder.Configurations.Add(entityTypeConfigurationInstance);
        }
    }
}
```

De esta manera incluso podemos modificar el acceso a las clases de configuración como `internal`. Sin embargo será entonces necesario ignorar el *warning* <a href="http://msdn.microsoft.com/en-us/library/ms182265.aspx" target="_blank" rel="noopener">CA1812</a> del Code Analyzer (la cual podemos suprimir de forma segura ya que sabemos que sí son consumidas por `Reflection`).

**Actualización 21/01/2013**: En la nueva versión del Entity Framework, la 6.0, encontraremos en la clase <a href="http://msdn.microsoft.com/en-us/library/system.data.entity.modelconfiguration.configuration.configurationregistrar(v=vs.103).aspx" target="_blank" rel="noopener">ConfigurationRegistrar</a> un nuevo método llamado `AddFromAssembly` que nos permitirá hacer exactamente lo que se describe en este artículo. La clase `ConfigurationRegistrar` habitualmente la accedemos desde el método del evento <a href="http://msdn.microsoft.com/en-us/library/system.data.entity.dbcontext.onmodelcreating(v=vs.103).aspx" target="_blank" rel="noopener">`OnModelCreating`</a> a través de la propiedad <a href="http://msdn.microsoft.com/en-us/library/system.data.entity.dbmodelbuilder.configurations(v=vs.103).aspx" target="_blank" rel="noopener">`Configurations`</a>.

##### Referencias

- <a href="http://msdn.microsoft.com/en-us/library/dd264736.aspx" target="_blank" rel="noopener">Using Type dynamic (C# Programming Guide).</a>
