## **Sidebar:**

* **Portal**: Lists the folder directly under `xmlsource` in Perforce.  For help and dev guides, this corresponds to the portal where the content domain bundles are built. For example, the `/xmlsource/dev_guides/` folder contains content built to developer.salesforce.com.
* **Content Domain:** Lists the folders that contains a ditamap to be built. For example, the `/xmlsource/dev_guides/apex` folder.
* Blended Rank - the numerical position of a link on a page returned by Google when entering a search term. For example, if you enter

## Visualizations:

* [Shared Content](#shared-content-and-linked-content):  Shows the conrefs for bundle folder(s) in Perforce. For example, the `/xmlsource/dev_guides/` folder. Use this to examine how you are sharing content.
* [Linked Content](#shared-content-and-linked-content):  Shows the xrefs for a bundle folder(s).
* [Customer Search](#customer-search):
   * [Blended Rank](#blended-rank): Shows the search volume of terms, their position in Google search results, and the page customers were ultimately directed to. Use this to identify opportunities for SEO improvement.
   * [Blended Rank Change](#blended-rank-change): Shows the change in position for where a keyword is returned in Google search results. Use to see new terms and identify terms that are no longer being used as frequently.
   * [Combined Keywords](#combined-keywords): Shows keyword results from both H&T and developer.salesforce.com. Pick a general keyword to the different things that admins and developers are looking for.
* [Freshness](#freshness):  Allows you to view the freshness of files in a folder. This is the last time the file was modified on the client, before it was submitted to the Perforce server. So this is the last time a person touched the file. For information about multiple domains, see the **Comparison** menu Portal Freshness visualization.
* [Comparison](#comparison):
   * [Reference Treemap](#reference-treemap): Shows the relative number of conrefs or xrefs in a portal. Gives you a general idea of the difficulty of migrating content.
   * [Portal Freshness](#portal-fFreshness): Shows the last modified date for files across a portal.
* [Complex Questions](#complex-questions):  Allows you to filter by portal, content domain, and terms in node labels (file and folder name) or node ID (folder structure).


### Shared Content and Linked Content

These are both network visualizations which show the references between two files. Shared content shows conrefs and Linked Content shows xrefs.

#### Circle = Node
A circle is a node in the visualization. Each node is a separate Perforce file. The label under the node shows the parent folder and the file name. All nodes that are the same color are in the same parent folder.

#### Line
The lines between nodes are a reference from one node to another. This is either a conref or an xref.
The line color is the color of the node that is “reaching out” for the reference. For example, the Bulk V2 API - Query Get All Jobs file has a conref to a reference folder. The link is the same color as the Bulk V2 API node. Note: in some cases the line color is similar, due to a limited number of colors, but it is never identical. Zoom in and check the border color of the node to determine the line color.
The line thickness indicates the number of references between two files. If you want to see the exact number of references, check the Weight column in the data table under the visualization.

#### Data Table
The data table shown contains only the data shown in the visualization.

* Source - node ID for the file that that contains the xref or conref. The node ID is a concatenation of the file path for the file in Perforce and can be used to locate the file.
* Target- node ID for the file that that is the target of the xref or conref. The node ID is a concatenation of the file path for the file in Perforce and can be used to locate the file.
* Weight - the number of references between two files. For example, if there are three links from file A to file B, then the weight is 3.
* Ref - the type of reference: conref or xref.
* Group - the parent folder for the source node.
* Color - the color associated with the source node.
* Label - the label associated with the source node.
* TargetGroup - the parent folder for the target node.
* TargetColor - the color associated with the target node.
* TargetLabel - the label assocaited with the target node.

#### **Usage**

Use these visualizations to:

* Identify key pieces of content, that have multiple references. When you have limited resources, this can help you prioritize maintenance tasks.
* Understand how a customer can navigate your content. This can help you build better information scent, by making sure you’re linking effectively.
* Identify links that may break when you migrate content to a new portal.



### Customer Search

#### Blended Rank

Shows the search volume of terms, their position in Google search results, and the page customers were ultimately directed to. Use this to identify opportunities for SEO improvement.
Ideally, look for keywords related to your content with a high search volume and a high blended rank. This means that a lot of customers are searching for the keyword, but it’s

#### Blended Rank Change

Shows the change in position for where a keyword is returned in Google search results. Use to see new terms and identify terms that are no longer being used as frequently. These are largely bunched around positive and negative, since new content has a large positive change and older content has small negative change.

### Freshness

Shows the last date that a person changed a file before it was submitted to Perforce. Use this visualization to identify files that require maintenance or that are obsolete.

### Comparison

There are a few visualizations here:

#### Reference Treemap

Shows the relative number of conrefs and xrefs per file and folder in perforce. Use this visualization to understand the scope of changes required for migration and the

#### Portal Freshness

See the last modified date for all files in a top-level folder under xmlsource in Perforce. This can take some time to render, if it is a large number of files. The colors in the visualization distinguish bundle folders in the top-level folder.

### Complex Questions

Shows the references between files. You can filter by: portal (top-level folder), content domain (bundle folder), reference type, and keyword search.
The keyword search lets you pick between the label and the node ID. The node ID contains the file path for the file. The allows you to filter on folders you are responsible for or concepts that are common across Salesforce doc.
