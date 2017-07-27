import os
import json
import urllib2
from bs4 import BeautifulSoup
import argparse
from isChord import isChordLine
from helpers import nameToID, idToData, dataToName

TEXT = 'txt'
JSON = 'json'
JSON_FOLDER = os.path.join(os.getcwd(), JSON)

class URLParser:
    def __init__(self, textFolder):
        self.textFolder = textFolder

    # URL of a song --> text file of a song
    def readURL(self, url):
        hdr = {'User-Agent': 'Mozilla/5.0'}
        req = urllib2.Request(url, headers = hdr)
        f = urllib2.urlopen(req)
        myfile = f.read()
        return myfile

    def toText(self, url):
        try:
            web_page = self.readURL(url)
            soup = BeautifulSoup(web_page, 'html.parser')

            # HTML markup for Ultimate Guitar website
            if 'ultimate-guitar' in url:
                data = soup.find('pre', {'class':'js-tab-content'}) # all of the lyrics and chords
                title = soup.find('h1').get_text()[:-7] # Wonderwall Chords
                artist = soup.find('div', {'class': 't_autor'}).find('a').get_text()

            # HTML markup for Ukutabs website
            if 'ukutabs' in url:
                # TO DO fix this
                # this is broken :(
                data = soup.findAll('pre', {'class': 'qoate-code'})[0]
                title = soup.find('span', {'class': 'stitlecolor'})
                artist = title.parent.parent.parent.findAll('tr')[1].find('a').get_text()
                title = title.get_text()

            fileName = dataToName(title, artist, TEXT)
            textFile = os.path.join(textFolder, fileName)
            print textFile
            with open(textFile, 'w') as outfile:
                outfile.write(data.get_text().encode('utf-8'))
            return fileName

        except urllib2.HTTPError :
            print("HTTPERROR!")
        except urllib2.URLError :
            print("URLERROR!")

    # All song URLs --> all text files of songs
    def allToText(self):
        f = open('urls.txt', 'r')
        lines = f.readlines()
        lines = [x.strip() for x in lines]
        for url in lines:
            self.toText(url)
class TextParser:
    def __init__(self, textFolder):
        self.textFolder = textFolder

    # Text file of a song --> JSON file of a song
    def toJSON(self, fileName):
         # Checks whether a line is a label
        def isLabel(line):
            return line.startswith('[') and line.endswith(']')

        textFile = os.path.join(textFolder, fileName)
        f = open(textFile, 'r')
        lines = f.readlines()
        lines = [x.rstrip() for x in lines]
        data = {}

        songID = nameToID(fileName)

        [title, artist] = idToData(songID)
        data['title'] = title
        data['artist'] = artist
        data['lines'] = []
        count = 0
        print title

        allChords = set()

        for i in xrange(len(lines)):
            l = lines[i]

            newLine = {}
            if(isLabel(lines[i])):
                newLine['label'] = lines[i]
                data['lines'].append(newLine)
            else:
                # Checks whether a line has chords
                if isChordLine(lines[i]):

                    newLine['lyrics'] = lines[i+1]
                    newLine['chord'] = lines[i]
                    newLine['count'] = count

                    for c in lines[i].split():
                        c = c.replace("#", "%23")
                        if "/" in c:
                            c = c.split("/")[0]
                        allChords.add(c)
                    count += 1
                    data['lines'].append(newLine)

        data['allChords'] = list(allChords)

        fileName = dataToName(title, artist, JSON)
        jsonFile = os.path.join(JSON_FOLDER, fileName)
        with open(jsonFile, 'w') as outfile:
            json.dump(data, outfile)

    # All song text files --> all JSON files of songs
    # toConvert = array of text file names that we want to convert
    # format = title - artist.txt
    # TO DO modify so that it actually has the full file names
    def allToJSON(self, toConvert):
        for fileName in toConvert:
            self.toJSON(fileName)
        self.getAllSongs()

    # Get all text files
    def getAllText(self):
        allText = []
        for fileName in os.listdir(textFolder):
            if fileName.endswith(TEXT):
                allText.append(fileName)
        return allText

    # Get modified files
    # return list of all modified text files
    def getAllModified(self):
        modifiedTextFile = "modified.txt"
        open(modifiedTextFile, 'w').close()
        os.system("git status -s >> %s" % modifiedTextFile)
        f = open(modifiedTextFile, 'r')
        lines = f.readlines()
        # remove new line character
        # also remove first 3 characters ' M ' or '?? '
        # remove quotes "
        lines = [x.strip('\n')[3:].replace('"', '') for x in lines]

        allModifiedText = []
        for l in lines:
            textFolder = 'text/'
            if l.startswith(textFolder) and l.endswith(TEXT):
                fileName = l[5:] #stripping out text/ extension
                allModifiedText.append(fileName)

        return allModifiedText

    # Get all songs
    def getAllSongs(self):
        allSongs = []
        for fileName in os.listdir(JSON_FOLDER):
            newSong = {}
            songID = nameToID(fileName)
            [title, artist] = idToData(songID)
            # tags = []

            newSong["id"] = songID
            newSong["label"] = title
            newSong["value"] = songID
            newSong["title"] = title
            newSong["artist"] = artist
            allSongs.append(newSong)
        with open('allSongs.json', 'w') as outfile:
            json.dump(allSongs, outfile)

if __name__ == "__main__":
    # Argument parsing is currently un-used
    # TO DO modify for use on the app's import feature
    parser = argparse.ArgumentParser(description="Add files")
    args = parser.parse_args()

    textFolder = os.path.join(os.getcwd(), 'text') # either 'text' or 'temp'

    urlParser = URLParser(textFolder)
    # urlParser.allToText()

    converter = TextParser(textFolder)

    modified = converter.getAllModified()
    converter.allToJSON(modified)
    # converter.getAllSongs()
