General notes
=============

See https://dans-knaw.github.io/dans-datastation-tools/dev/

Manual test with deasy
======================

update_thematische_collecties
-----------------------------

Out of the box jumpoff pages don't refer to datasets.
Use the web interface and an admin account to create a jumpoff page for `easy-dataset:12`.
The validate button allows to enter plain HTML:

    <div class="jumpoffpage">
        <p class="jumpoffpage"><a
                href="http://persistent-identifier.nl/?identifier=urn:nbn:nl:ui:13-jpe-eqh">a12753</a> and <a
                href="https://doi.org/10.17026%2Fdans-zf5-xx5n">p</a><br/> and <a
                href="https://easy.dans.knaw.nl/ui/datasets/id/easy-dataset:255208">q</a><br> and <a
                href="http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-af-6wjo">x</a><br></br> and <a
                href="http://www.persistent-identifier.nl/?identifier=urn:nbn:nl:ui:13-yufi-k7">migrated</a> and <a
                href="http://www.talkofeurope.eu/">not a dataset</a>...
        </p>
    </div>

Use as input:

    name,EASY-dataset-id,type,comment,members
    Aeres Milieu,easy-dataset:9,organisatie,,
    bleekneusjes,"easy-dataset:10",organisatie,,
    Sweco,"easy-dataset:12,easy-dataset:22,easy-dataset:11",organisatie,,
    Odyssee onderzoeksprojecten,easy-dataset:34359,thema,,"easy-dataset:34099"

This tests a mix of (un)quoted, single/multiple dataset-ids in the CSV, existing/missing jumpoff-s,
and various types ok links: (un)encoded URLs, (not)migrated datasets, various types of IDs and non-datasets. 

* with 3 types of `<br>` html versus xhtml is supposed to be covered
  (this used to be a problem for easy-convert-bag-to-deposit)
  the real proof of the xhtml pudding is `dans-jumpoff:3931` on production for `easy-dataset:34359`
* `deasy` only produces jumpoff-s with a `HTML_MU` datastream. On production, possibly one of the jumpoff pages for 
  `easy-dataset:34359`, `easy-dataset:33834`, `easy-dataset:33895`, `easy-dataset:33976`, `easy-dataset:64608`
  returns data for the `TXT_MU` datastream instead:

    http://localhost:8080/fedora/objects/dans-jumpoff:NNN/datastreams/TXT_MU/content