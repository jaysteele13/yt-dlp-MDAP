MDAP 
Music Downloading Automated Pipeline

# How will work:


The main yt-dlp command we wil use will be:

yt-dlp --verbose --extract-audio --audio-quality 0 --embed-metadata "{URL}"

(This will return a verbose message in the CLI)

HOW TO GET ALBUM NAME FROM VERBOSE MESSAGE
[download] Downloading playlist: Album - Taking My Side - look for in json '[download] Downloading playlist: Album - [Album_Name]' new line is tyhe end of the artist name.

HOW TO GET ARTIST NAME FROM VERBOSE MESSAGE
To get the artist we should look in this verbose comment for '-metadata 'artist=[artist_name]' Should be exact enough. ' should be the end of the artist name 



# flow

Setup Dir will be preset for 'Music/temp'

When temporarily downloading we will make a directory given the current timestamp

Paste in Link should be Album, if not select song category. 

[ALBUM Category]
- Once finished downloading to temp dir. We should be able to extract the Album and Artist name
- Prompt if these are correct if so extract and we will move these songs into newly corrected album. Have edit mode if these are wrong.
- Hit extract and updated notion (This will configured later). If all successful we will return a log of files and album added (Also delete timestamp dir).

[SONG Category]
- We can extract the Artist and from the song metadata the same way as album.
- Prompt if the artist is right then
- If directory exist / make one if it doesn't move the newly song downloaded there and remove the timestamp drectory.
- We will also call out to notion and make the type 'Song' Rather than 'Album'



#### Optional add on
Have a Side menu to show verbose message. If messages mess up have an i - so we can change the regex to filter for the album or Artist name if verbose mode syntax ever changes