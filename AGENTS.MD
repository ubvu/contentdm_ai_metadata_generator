ContentDM AI - additional metadata generator for historical images in the Content DM system.
The VU and many other museumns and archives use ContentDM to describe the historical images of their collection. We want to interconnect the images across all archives to search over, using linked data. But due to personnel shortage this activity is stalled.
I am asked to build an app that is able to automatically add metadata to pictures from our Content DM system https://vu.contentdm.oclc.org/ (this can be changed in the config file)
This is to help our volunteers making rich descriptions, so that content can be more easy be found an reused throughout the semantic web using linked data. 
Content DM is based on linked data. more about content dm system can be found here: https://www.oclc.org/en/contentdm.html
I want the app to use linked-data and Named Entity Recognition (NER) principles for describing the features and elements on the picture for the 'object description' metadata, and if text is detected, it needs to try to extract the text written on he picture for the 'transcript' metadata.
I imagine that the app is build as a Streamlit app.
I imagine that the app shows on the site of https://vu.contentdm.oclc.org/ on the left frame that for 80% width, and on the right pane 20% width with the metadata extraction activity pane.
When the user is browsing to a details page (where /id/ appears in the url), for example https://vu.contentdm.oclc.org/digital/collection/vko/id/347/rec/1, the right pane will become "active", where the current metadata can be found, and where there is a button to process the picture to generate more metadata.
To get the picture and the metadata, the source of the html page cannot be used due to security restrictions. therefore you need to use the api. for this example to get the item metadata use https://vu.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmGetItemInfo/vko/347/json and to get the image metadata use 
https://vu.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmGetImageInfo/vko/347/json this returns the file name of the image in a path (for example {
    "filename": "/cdm/sites/21033/data/vko/image/348.jp2",) you need in the next api call
 to get the image object use the file name in combination with the collection alias in the follwong api call https://vu.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmGetStreamingFile/vko/348.jp2/xml
For the complete api documentation see: https://help.oclc.org/Metadata_Services/CONTENTdm/Advanced_website_customization/API_Reference/CONTENTdm_API/CONTENTdm_Server_API_Functions_dmwebservices
Use this image to process using your image recognition AI models.
Show the user in a expandable log view what you are doing/processing.
Add in the second half of the right pane  in the section 'transcript' the additional transcribed text from the image, and in the section 'object description a textual description of what the AI model has seen, plus a list of linked data named entities including the uri pointers. https://en.wikipedia.org/wiki/Named-entity_recognition
Add a save button, that stores the additional generated information on the server in a csv file. add a export button to export / download the csv locally. add a "export all" button to generate a zip file to download all the csv files on the server.

Q&A
Q: What types of pictures are you working with in your ContentDM system? (historical photos, documents, artwork, etc.) 
	A: historical photos and artwork
Q: What specific metadata fields do you want the app to automatically populate? (title, description, subject tags, dates, locations, people, etc.) 
	A: all of those.
Q: How should volunteers interact with the app? Do you want them to upload images one by one, or process batches of images? 
	A: no, browse and select a photo from the index of our content dm system (use the API to get the metadata and objects. )
Q: What level of volunteer review do you want? Should the app generate suggestions that volunteers can approve/edit, or automatically add metadata that volunteers can later modify? 
	A: generate additional metadata that volunteers can use by copy-pasting, save or export, tso that they can add this later in their edit interface of contentdm.
Q: Do you have access credentials for your ContentDM system, or should the app work with exported images and then provide metadata that can be imported back? 
	A: viewing the html and using the API is public. no credentials needed. The volunteers use a different edit interface later on, where they enter the generated metdata manually.
Q: What's your preferred workflow - should this be a web application where volunteers log in and process images, or something else? 
	A: no login, just use the same view as the content dm website in a frame, but in a sidebar they can press "auto generate additional metadata" where additional metadata is generated based on the pictures in the current view of the website.

Development requirements & housekeeping
The code of this app is published on GitHub, so add a readme.md describing the project, and how to setup the streamlit application locally by cloning the repository and deploy as a docker container. also include a config.yaml and a template config.example.yaml to put the api keys of for example the LLM services that are used, and the baseurl of the content dm system to work on, in our case https://vu.contentdm.oclc.org/  Also add a .gitignore file that includes the config.yaml file to prevent from uploading api keys to a git repo. Also add MIT license and a CFF citation file format for attributing the creator Maurice Vanderfeesten https://orcid.org/0000-0001-6397-4759

Q&A
Q: AI Services: Which AI services would you prefer for the image analysis and NER? (e.g., OpenAI GPT-4 Vision, Google Vision API, Azure Cognitive Services, or open-source alternatives like spaCy for NER)
	A: Use Open Source alternatives than can run locally or in the same a docker container as the streamlit app.
Q: Linked Data Sources: Which specific linked data vocabularies/ontologies should the app use for generating URIs? (e.g., Getty Art & Architecture Thesaurus, Library of Congress Subject Headings, Wikidata, DBpedia)
	A: use Wikidata and DBpedia
Q: Metadata Fields: You mentioned "all of those" for metadata fields - should the app focus on the standard Dublin Core fields that ContentDM typically uses, or do you have a specific metadata schema in mind?
	A: Dublin core fields that represent the description, and the subjects.
Q: Processing Scope: Should the app process images one at a time when a user clicks the button, or would you like batch processing capabilities for multiple images in a collection?
	A: at first one at the time, to see the workings. if all goes well, the user can click on a button to generate metadata for the whole collection. Also showing the log and processing status of the collection. to get all the records in a collection see the dmQueryTotalRecs documentation. 
Q: Data Storage: For the CSV export functionality, should each processed image create a separate CSV file, or should all processed metadata be stored in a single CSV file per session/collection?
	A: Each processed image creates a separate csv file combining the record id and image file name as filename for the csv data file. Put the csv files in a folder using the collection alias as folder name. Use json data package standard for bundeling the csv collection (read more about this here: https://datapackage.org/standard/data-package/ ) also define the CSV table dialect https://datapackage.org/standard/table-dialect/ and the table schema of the csv files https://datapackage.org/standard/table-schema/ . Us this to to bundle the collection of csv files, readme.md and json in a zip for export. 