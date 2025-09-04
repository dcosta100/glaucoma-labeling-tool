TODO:

* [X] Change the page code to a new .py file in the folder pages/
* [X] Check if sqlite is the better structure for this cloud solution [change to json]: every new patient will download his images and metadata [save as cache], and after saving push a json into aws s3, the same when loading [check if there is a json]
* [ ] Review the diagnosis logic and the flow over the data during the labeling progress
* [ ] Set the cloud environment [jsons and images from aws s3]
* [ ] Put the website on cloud with a paid streamlit account
* [X] get real data from patients [real list]
* [X] Add save button with log output



- Check the load json to check previous labels + create a cache for images and labels
- get rid of the dummie data
