---
slug: minify-javascript-and-css-for-web-application-from-visual-studio
title: "Minify JavaScript and CSS files when publishing Web Applications from Visual Studio"
excerpt: "One of the best practices to speed up a web site or web application is to minify JavaScript and CSS files; which as a secondary effect, not only reduces the size of those files but also makes them harder to read (something helpful to prevent the stealing of your ideas and efforts)."
date: 2012-02-02 00:00:00 +0200
lastmod: 2023-11-01 00:00:00 +0200
url: "/posts/minify-javascript-and-css-for-web-application-from-visual-studio/"
image:
    path: /images/2012-02-02-minify-javascript-css-web-applications-visual-studio/header.jpg
    thumbnail: /images/2012-02-02-minify-javascript-css-web-applications-visual-studio/thumbnail.jpg
categories:
    - Legacy
    - English
    - Tutorial
    - JavaScript
    - CSS
    - Visual Studio
---
One of the best practices to speed up a web site or web application is to minify JavaScript and CSS files; which as a secondary effect, not only reduces the size of those files but also makes them harder to read (something helpful to prevent the stealing of your ideas and efforts).

### Intro

You may think that actually this is not very helpful since using external JavaScript and CSS files in the real world generally produces faster pages because they will be cached by the browser. However, if their size is big, you may improve the first request load time by reducing their size.

Minification is the practice of removing unnecessary characters from code to reduce its size thereby improving load times. When code is minified all comments are removed, as well as unneeded white space characters (like newlines or tabs). This improves response time performance because the size of the downloaded file is reduced.

There are many tools to minify JavaScript and CSS files, like for example:

- <a href="http://crockford.com/javascript/jsmin" target="_blank" rel="noopener noreferrer">JSMin</a>
- <a href="http://developer.yahoo.com/yui/compressor/" target="_blank" rel="noopener noreferrer">YUI Compressor</a>
- <a href="http://ajaxmin.codeplex.com/" target="_blank" rel="noopener noreferrer">Microsoft Ajax Minifier</a>

I'm a Microsoft .NET professional, so in this and future post, I will going to focus only on Microsoft's Ajax Minifier tool.

#### The proper time to minify

It is not advisable to minify your web application's JavaScript and CSS files during developing time; it should be done on deployment or publish (for testing or any other purpose) time.

But then, how to minify those files without affecting the original source code in the solution when deploying it?

The answer is quite easy: we must use MSBuild in the web application project file to configure the Microsoft Ajax Minifier to be executed as a task when publishing in 'Release' mode.

#### The steps to minify

The first step is to unload the web application project by right-clicking on it and choose the option «Unload Project». Once unloaded, right-click it again and choose the «Edit *<web_app_project_name>*.csproj» option, which will open the XML editor of the Visual Studio with the project's configuration.

What I usually do, is to go to the end of the file and then add the following line just before the closing `Project` tag:

```xml
<UsingTask TaskName="AjaxMin" AssemblyFile="$(SolutionDir)Lib\AjaxMinTask.dll" />
<PropertyGroup>
    <ResGenDependsOn>
        CompressJsAndCss;
        $(ResGenDependsOn)
    </ResGenDependsOn>
</PropertyGroup>
```

Please note the `PropertyGroup` tag. It describes the property activity to perform and its dependency with the generation of resources. This is very important to specify.

I prefer the `UsingTask` tag instead of the `Import` tag because I work with a lot of people who may have installed the Microsoft Ajax Minifier in different versions or locations that me (or not having it installed at all). So we distribute the solution’s `dll`s inside a `Lib` subfolder, that is also under source control. With this mechanism, every body uses the same `dll`s in the same version and referenced from the same location.

It is very important to take into account that you will need to have the `AjaxMinTask.dll` and also the `AjaxMin.dll` in the same location.

The next step is to create a custom target with the following lines:

```xml
<Target Name="CompressJsAndCss" AfterTargets="CopyAllFilesToSingleFolderForPackage" Condition="'$(Configuration)'=='Release'">
...
</Target>
```

The new target is called `CompressJsAndCss` and will be executed when publishing a web application just after the `CopyAllFilesToSingleFolderForPackage` target, which is responsible of copying (or materialize in-memory files) the project files into your `obj` folder (specifically the folder specified by `_PackageTempDir`) in preparation for a publish.

Next, we need to gather the files suitable to be minified, in this case, JavaScript and CSS files. To do so, just add the following lines to the custom target:

```xml
<ItemGroup>
    <JS Include="$(_PackageTempDir)\**\*.js" Exclude="$(_PackageTempDir)\**\*.min.js" />
    <CSS Include="$(_PackageTempDir)\**\*.css" Exclude="$(_PackageTempDir)\**\*.min.css" />
</ItemGroup>
```

As you can see, we’re creating a set of all available JavaScript and CSS files in the `_PackageTempDir` folder (where the `CopyAllFilesToSingleFolderForPackage` put the files for the publication) but excluding those with extension `.min.js` or `.min.css` which are already minified (usually jQuery files).

Finally, we must call the Microsoft Ajax Minifier task in order to minify the gathered files with the following lines:

```xml
<AjaxMin JsKnownGlobalNames="jQuery,$" JsSourceFiles="@(JS)" 
         JsSourceExtensionPattern="\.js$" JsTargetExtension=".js"
         CssSourceFiles="@(CSS)" CssSourceExtensionPattern="\.css$" 
         CssTargetExtension=".css" />
```

Note that we’re informing the Microsoft Ajax Minifier to respect the `jQuery` and `$` literals on the JavaScript files since they are well know global names that must not be modified in the minify process.

At the end, we should have the following added configuration:

```xml
<!-- Minify all JavaScript and CSS files that are present on this web application when publish in release. -->
<UsingTask TaskName="AjaxMin" AssemblyFile="$(SolutionDir)Lib\AjaxMinTask.dll" />

<!-- This target will run after the files are copied to PackageTmp folder (usually 'obj\Release\Package\PackageTmp') -->
<Target Name="CompressJsAndCss" AfterTargets="CopyAllFilesToSingleFolderForPackage" Condition="'$(Configuration)'=='Release'">
<ItemGroup>
    <JS Include="$(_PackageTempDir)\**\*.js" Exclude="$(_PackageTempDir)\**\*.min.js" />
    <CSS Include="$(_PackageTempDir)\**\*.css" Exclude="$(_PackageTempDir)\**\*.min.css" />
</ItemGroup>
<Message Text="Compressing JavaScript and CSS files..." Importance="high" />
<AjaxMin JsKnownGlobalNames="jQuery,$" JsSourceFiles="@(JS)" 
         JsSourceExtensionPattern="\.js$" JsTargetExtension=".js"
         CssSourceFiles="@(CSS)" CssSourceExtensionPattern="\.css$" 
         CssTargetExtension=".css" />
</Target>
```

So what is left to do is to save the `csproj` file, close it and right-click on it from the Solution Explorer and choose the «Reload Project» option in order to load it again in the solution.

Now when we go to publish the web application (and in ‘Release’ mode) our custom target will be evaluated just after the `CopyAllFilesToSingleFolderForPackage` target, and all JavaScript and CSS files will be minified without affecting the original ones.

##### References

- <a href="http://en.wikipedia.org/wiki/Minification_(programming)" target="_blank" rel="noopener noreferrer">Wikipedia: Minification (programming)</a>
- <a href="http://yhoo.it/R35J" target="_blank" rel="noopener noreferrer">Yahoo’s Best Practices for Speeding Up Your Web Site</a>
