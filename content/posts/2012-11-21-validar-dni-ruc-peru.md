---
slug: validar-dni-ruc-peru
title: "Como Validar el DNI o el RUC de Perú en C#"
excerpt: "Una implementación (no es perfecta) para usando C# poder validar el número del DNI o del RUC de Perú."
date: 2012-11-21 00:00:00 +0200
lastmod: 2023-10-27 00:00:00 +0200
url: "/posts/validar-dni-ruc-peru/"
image:
    thumbnail: /images/2012-11-21-validar-dni-o-ruc-de-peru/thumbnail.webp
categories:
    - Legacy
    - Tutorial
    - C#
---

{{< notice type="warning" >}}
*Este tutorial es sobre una aproximación en C# para poder determinar si un número de DNI o de RUC del Parú es válido.*

*No es un algoritmo perfecto, de hecho puede que tenga *bugs*, con lo cual será tu responsabilidad si lo usas en un proyecto importante. La idea de esta publicación es ofrecer una primera aproximación (que en su momento me sirvió) para atender a este requerimiento. Es probable que hoy día exista un mecanismo mejor.*
{{< /notice >}}

En estos días me ha tocado trabajar en un proyecto que, como tantos otros hoy día, está pensado para un entorno empresarial globalizado.

Parte de las reglas de negocio del proyecto exige, como también es común en tantos otros proyectos, validar el documento de identidad correspondiente al cliente para el país al cual éste pertenece. Para el caso de países como España o Brasil existe amplia documentación y recursos referentes al algoritmo empleado para validar sus respectivos documentos de identidad.

Pero lamentablemente para Perú, uno de los países que tengo que gestionar, la cantidad y la calidad de la información disponible es decepcionante.

{{<figure src="/images/2012-11-21-validar-dni-o-ruc-de-peru/dni.png" alt="center-aligned-image" class="align-center" lightbox="false">}}{{</figure>}}

Por otro lado, al hablar de documentos de identidad en Perú, debemos distinguir entre el <a href="http://es.wikipedia.org/wiki/Documento_de_identidad#Per.C3.BA" target="_blank" rel="noopener">DNI</a> (Documento Único de Identidad) y el <a href="http://es.wikipedia.org/wiki/RUC" target="_blank" rel="noopener">RUC</a> (Registro Único de Contribuyente). El primero aplica a los ciudadanos en general y cuenta con un identificador conocido como CUI (Cédula Única de Identidad), mientras que el segundo aplica a empresas y comercios.

El siguiente algoritmo permite validar documentos de identidad peruanos (tanto DNI como RUC). Para el caso del DNI, es independiente que el CUI tenga como término de verificación un número o una letra.

```csharp
public static bool ValidateIdentificationDocumentPeru(string identificationDocument)
{
    if (!string.IsNullOrEmpty(identificationDocument))
    {
        int addition = 0;
        int[] hash = { 5, 4, 3, 2, 7, 6, 5, 4, 3, 2 };
        int identificationDocumentLength = identificationDocument.Length;

        string identificationComponent = identificationDocument.Substring(0, identificationDocumentLength - 1);

        int identificationComponentLength = identificationComponent.Length;

        int diff = hash.Length - identificationComponentLength;

        for (int i = identificationComponentLength - 1; i &amp;amp;gt;= 0; i--)
        {
            addition += (identificationComponent[i] - '0') * hash[i + diff];
        }

        addition = 11 - (addition % 11);

        if (addition == 11)
        {
            addition = 0;
        }
        else if (addition == 10)
        {
            addition = 1;
        }

        char last = char.ToUpperInvariant(identificationDocument[identificationDocumentLength - 1]);

        if (identificationDocumentLength == 11)
        {
            // The identification document corresponds to a RUC.
            return addition.Equals(last - '0');
        }
        else if (char.IsDigit(last))
        {
            // The identification document corresponds to a DNI with a number as verification digit.
            char[] hashNumbers = { '6', '7', '8', '9', '0', '1', '1', '2', '3', '4', '5' };
            return last.Equals(hashNumbers[addition]);
        }
        else if (char.IsLetter(last))
        {
            // The identification document corresponds to a DNI with a letter as verification digit.
            char[] hashLetters = { 'K', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J' };
            return last.Equals(hashLetters[addition]);
        }
    }

    return false;
}
```

Finalmente, el gobierno de Perú pone a disposición <a href="https://cel.reniec.gob.pe/valreg/valreg.do" target="_blank" rel="noopener">la siguiente herramienta</a> para verificar documentos de identidad; y esta <a href="http://www.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias" target="_blank" rel="noopener">otra herramienta</a> para validar RUC.

Espero que les sea de utilidad.
