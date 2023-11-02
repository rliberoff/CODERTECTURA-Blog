---
title: "Reading multiple files from ORACLE using PL\\SQL"
excerpt: "Some time ago I was involved in a very important project for China where We used ORACLE 11g as database server with a very important but simple requirement: read the content of a set of plain text files that will be available in a public folder, parse their content and insert them into a known set of tables using a 100% PL\\SQL solution. No C++ or anything external from ORACLE could be used. <br><br>This post explains how We did it!"
date: 2011-11-02 00:00:00 +0200
last_modified_at: 2023-11-01 00:00:00 +0200
layout: post
permalink: /posts/oracle-read-multiple-files-using-only-pl-sql
image:
    path: /images/2008-03-07-realizaciones-o-de-cuando-me-fui-de-venezuela/header.avif
    thumbnail: /images/2008-03-07-realizaciones-o-de-cuando-me-fui-de-venezuela/thumbnail.avif
categories:
    - Legacy    
    - Tutorial
    - English
    - Oracle
---
ORACLE is not my favorite database manager. It feels outdated, old, complicated and slow (specially because all the available software is made on JAVA, except [TOAD](https://www.quest.com/products/toad-for-oracle/){:target="_blank"} which is a very nice tool).

It is quite annoying that some task that We may consider advanced in database management and programming are quite easy to do by other database software like Microsoft SQL Server 2005/2008, but in ORACLE are terribly complicated, obscure and taking a lot of time.

Some time ago I was involved in a very important project for China where sadly We have to use ORACLE 11g as database server. We have a very important but simple requirement: read the content of a set of plain text files that will be available in a public folder, parse their content and insert it into a known set of tables using a 100% PL\SQL solution (***no*** C++ or anything external from ORACLE could be used).

As you may know, there is a very solid stored procedures package in ORACLE called `UTL_FILE` which contains functions to read and write text files, as long as the name and extension of the file is known when invoking those functions.

And then problems started… because the name of the files that We are going to read are not known, they contain a date and time component as part of their name (for example: `MyFile_20101015_1045.txt`) but such name’s components are not known at any given time.

So, from the requirements We face two challenges:

1. Since the exact file name is not known, We could not use the functions available in the `UTL_FILE`.
2. The solution must be completely and exclusively written in pure PL\SQL.

Luckily there is a hidden functionality in ORACLE’s `SYS` schema, in the `DBMS_BACKUP_RESTORE` package called `SearchFiles` available out of the box (which means that no additional installation of special stuff is required to have it). The mentioned package is used by ORACLE when restoring a backup (automatically or manually).

The `SearchFiles` function takes a file name pattern and creates a list of those files that match it (recursively considering any sub directories) and storing the result in a temporary table called `X$KRBMSFT` (which belongs to the family of those handily `$x` tables).

So, with this knowledge, We have new challenges:

1. Isolate the `SYS` schema to warrant the security of it (nobody should access this schema).
2. Retrieve the data stored in the table from outside the `SYS` schema.
3. Process the data using the `UTL_FILE` package.

The following diagram depicts the design of this solution:

![center-aligned-image](/images/2011-11-02-reading-multiple-files-from-oracle-using-pl-sql/1.png){: .align-center .image-border}

We can solve challenges 1 and 2 creating a stored procedure which We will call `ListFiles`, and storing it in a new package under the `SYS` schema. This stored procedure will be a proxy or gateway to invoke the `SearchFiles` procedure. The values of the `X$KRBMSFT` table will be returned as a cursor, so the consumers of this stored procedure will no require access privileges to it. The script is as follows:

```sql
create or replace PACKAGE EXT_UTILS AS
    TYPE cur_output IS REF CURSOR;
    PROCEDURE ListFiles(p_dir_pattern IN VARCHAR2,
                        cur_out OUT cur_output);
END EXT_UTILS;
 
create or replace PACKAGE BODY EXT_UTILS AS
 
PROCEDURE ListFiles(p_dir_pattern IN VARCHAR2, 
                    cur_out OUT cur_output) AS
v_ns VARCHAR2(200);
v_select VARCHAR2(200);
v_dir_pattern VARCHAR2(1024);
 
BEGIN
 
    v_dir_pattern := p_dir_pattern;
 
    -- Change LIKE clause to match file pattern or format specification.
    -- The LIKE condition should match files with the next file name format: “NamePrefix_20100812_1312.txt”.
    v_select := 'SELECT FNAME_KRBMSFT FROM X$KRBMSFT WHERE UPPER(FNAME_KRBMSFT) LIKE UPPER("%NamePrefix!_________!_____.txt") ESCAPE "!"';
    SYS.DBMS_BACKUP_RESTORE.searchFiles(v_dir_pattern, v_ns);
    OPEN cur_out FOR v_select;
 
END;
 
END EXT_UTILS;
```

Then We will grant execute permissions to our schema to execute this new package only. In other words, our schema will be able to see and execute the `ListFiles` stored procedure from `SYS`, but will not see or be able to invoke with anything else form there. Since the `EXT_FILES` does not expose anything from the `SYS` side rather then its own implementation, security is warranted.

```sql
-- In the real life, <user> will be our schema.
GRANT EXECUTE ON EXT_UTILS TO <user>;
```

After you invoke the `EXT_UTILS.ListFiles` stored procedure, you’ll receive a cursor with the name, extension and complete path to the files you need to work with, which you can pass as argument to the stored procedures of the `UTL_FILE` package.

**PROS**: this approach is flexible and reliable as a 100% PL\SQL solution with good performance. It leverage on existent ORACLE stored procedures and packages. Also, this solution works for ORACLE 10g.

**CONS**: this solution requires some work to be done as `SYS`. Some maintainability could be lost since some work requires the intervention of the database administrators (even when the creation of the `EXT_FILES` package will be done only once). Appropriate privileges for execution must be granted to your schema for the new `EXT_UTILS` package. Finally, in order to use the `ULT_FILE` package, `SYS` must grant create and drop `directory` objects privileges to your schema.

**WARNING**: As `x$krbmsft` is an in memory table, it is recommended to take precautions. Calling the `SearchFiles` procedure on a directory with too many sub directories and files that match the given pattern has the potential to consume large amounts of memory.

Hope it helps someone.

##### References

- [Christopher Poole’s Oracle Database Consultancy PL/SQL Tips](http://www.chrispoole.co.uk/tips/plsqltip2.htm){:target="_blank"}
