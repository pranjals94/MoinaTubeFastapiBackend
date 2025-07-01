made for local storage as a server for playing videos within the local network , and for the android tv.

make a shared folder for all the video files, inside the shared create sub folders, directly dumping a video file to it wont play.

the back end folder contains the start.sh that is used to start the server using supervisor

the server runs on ubuntu server OS with ftp server and ssh installed

npm run build the front end and coppy all the build files to the static folder
when deploying remove the cors permission in the python main,

when uploading via ftp clients like filezilla, the filenames that contains characters like hindi, smilies , multiplication sign(x) not * , will produce encode error while saving the thumbnails files, becoz these characters cannot be encoded properly by the ftp client which is seen as endode error in the ubuntu os.
