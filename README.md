TODO:

* [X] Change the page code to a new .py file in the folder pages/
* [X] Check if sqlite is the better structure for this cloud solution [change to json]: every new patient will download his images and metadata [save as cache], and after saving push a json into aws s3, the same when loading [check if there is a json]
* [X] Review the diagnosis logic and the flow over the data during the labeling progress
* [ ] Set the cloud environment [jsons and images from aws s3]
* [X] Put the website on cloud with a streamlit account
* [X] get real data from patients [real list]
* [X] Add save button with log output

- [X] Check the load json to check previous labels + create a cache for images and labels
- [X] get rid of the dummie data
- [X] Fix the missing OCTs



LATER:

- [ ] Load always 2 patients in advance async
- [ ] Pointer para salvar o ultimo ponto de label
