import requests, json, time, sys, os

from io import StringIO, BytesIO

from lxml import etree
from lxml.etree import ParserError



from playwright.sync_api import sync_playwright

langs = ["German", "English", "Spanish", "French", "Italian", "Japanese"]

try:
    ENV_URL = os.environ['KOMGAURL']
except:
    ENV_URL = ""
try:
    ENV_EMAIL = os.environ['KOMGAEMAIL']
except:
    ENV_EMAIL = ""
try:
    ENV_PASS = os.environ['KOMGAPASSWORD']
except:
    ENV_PASS = ""
try:
    ENV_LANG = os.environ['LANGUAGE']
except:
    ENV_LANG = ""
try:
    ENV_MANGAS = os.environ['MANGAS']
except:
    ENV_MANGAS = "NONE"
try:
    ENV_PROGRESS = os.environ['KEEPPROGRESS']
    if(ENV_PROGRESS.lower() == "true"):
        ENV_PROGRESS = True
    else:
        ENV_PROGRESS = False
except:
    ENV_PROGRESS = False


if (ENV_URL == "" and ENV_EMAIL == "" and ENV_PASS == "" and ENV_LANG == ""):
    try:
        from config import *
    except ImportError:
        print("Failed to find config.py, does it exist?")
        sys.exit(1)
elif (ENV_URL != "" and ENV_EMAIL != "" and ENV_PASS != "" and ENV_LANG != ""):
    komgaurl = ENV_URL
    komgaemail = ENV_EMAIL
    komgapassword = ENV_PASS
    anisearchlang = ENV_LANG
    keepProgress = ENV_PROGRESS
    mangas = []
    if(ENV_MANGAS != "NONE"):
        for manga in ENV_MANGAS.split(","):
            if(manga[:1] == " "):
                manga = manga[1:]
            mangas.append(manga)
else:
    print("Looks like either you are trying to set the configuration using environment variables or you are using docker.")
    if(ENV_URL == ""):
        print("Missing Komga URL")
    if(ENV_EMAIL == ""):
        print("Missing Komga Email")
    if(ENV_PASS == ""):
        print("Missing Komga Password")
    if(ENV_LANG == ""):
        print("Missing Anisearch language")
    sys.exit(1)

if(anisearchlang not in langs):
    print("Invalid language, select one listed the README")
    sys.exit(1)


def getBaseURL():
    if(anisearchlang == "German"):
        return "https://www.anisearch.de/"
    if(anisearchlang == "English"):
        return "https://www.anisearch.com/"
    if(anisearchlang == "Spanish"):
        return "https://www.anisearch.es/"
    if(anisearchlang == "French"):
        return "https://www.anisearch.fr/"
    if(anisearchlang == "Italian"):
        return "https://www.anisearch.it/"
    if(anisearchlang == "Japanese"):
        return "https://www.anisearch.jp/"

def getFlagLanguage():
    if(anisearchlang == "German"):
        return "Deutsch"
    if(anisearchlang == "English"):
        return "English"
    if(anisearchlang == "Spanish"):
        return "Español"
    if(anisearchlang == "French"):
        return "Français"
    if(anisearchlang == "Italian"):
        return "Italiana"
    if(anisearchlang == "Japanese"):
        return "日本語"


summarySourceLang = [" Quelle: ", " Quelle:", "Quelle:", " Source: ", " Source:", "Source:"]
runningLang = ["Laufend", "Ongoing", "Corriente", "En cours", "In corso", "放送", "放送（連載）中"]
abandonedLang = ["Abgebrochen", "Aborted", "Cancelado", "Annulé", "Abbandonato", "打ち切り"]
endedLang = ["Abgeschlossen", "Completed", "Completado", "Terminé", "Completato", "完結"]
tagTexts = ["Hauptgenres", "Main genres", "Género principal", "Principaux genres", "Generi principali", "メインジャンル"]
noSummaryLang = ["Damit hilfst Du der gesamten deutschsprachigen Anime und Manga-Community", "We’re looking forward to your contributions", "Con esto ayudas a toda la comunidad de Anime y Manga", "Nous attendons avec impatience tes contributions", "Non vediamo l’ora di ricevere i tuoi contributi", "皆様からのご投稿をお待ちしております"]
blurbLang = ["Klappentext", "Blurb", "Texto de presentación", "Texte du rabat", "Testo della bandella"]

class metadata:
    def __init__(self):
            self.status = ""
            self.summary = ""
            self.publisher = ""
#            self.agerating = ""
            self.genres = "[]"
            self.tags = "[]"
            self.isvalid = False

def getURLfromSearch(query):
    url = getBaseURL() + "manga/index?text=" + query + "&smode=1&sort=voter&order=desc&quick-search=&char=all&q=true"


    resp = page.goto(url)
    content = page.content()
    new_url = resp.url
    status_code = resp.status

    if("quick-search=" not in new_url):
        print("Got instant redirect, correct series found")
        return new_url

    if(status_code != 200):
        print("Status code was " + str(status_code) + ", so skipping...")
        if(status_code == 403):
            print(content)
        return ""

    try:
        parser = etree.HTMLParser()
        html_dom = etree.HTML(content, parser)
    except ParserError as e:
        print(e)
    try:
        manga_url = html_dom.xpath("//*[@id=\"content-inner\"]/ul[2]/li[1]/a/@href")[0]
        return getBaseURL() + manga_url
    except:
        return ""

#out = open("out.txt", "w", encoding='utf-8')
#out.write(tree.tostring(tree.getroot()).content.decode(sys.stdout.encoding, errors='replace'))
#out.close()

#print(getURLfromSearch("adekan"))

def getMangaMetadata(query):
    print("Getting metadata for " + str(query))
    status = ""         #done
    summary = ""        #done
    publisher = ""      #done
#    agerating = ""
    genres = "[]"
    tags = "[]"

    data = metadata()

    URL = getURLfromSearch(query)
    if(URL == ""):
        print("No result found or error occured")
        return data

    time.sleep(1)

    resp = page.goto(URL)
    content = page.content()
    status_code = resp.status

    if(status_code != 200):
        print("return code was " + str(status_code) + ", skipping...")
        return data
    try:
        parser = etree.HTMLParser()
        html_dom = etree.HTML(content, parser)
    except ParserError as e:
        print(e)
        return data

    #getLangIndex
    index = 1
    rightIndex = -1
    langRunning = True
    while(langRunning):
        try:
            flag = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + str(index) + "]/div[1]/img/@title")[0]
            if(flag == getFlagLanguage()):
                rightIndex = index
                if (anisearchlang == "Japanese"):
                    statusIndex = 3
                    publisherIndex = 6
                else:
                    statusIndex = 2
                    publisherIndex = 5
#                print("Found correct Language, index is " + str(rightIndex))
                langRunning = False
                break
            index += 1
        except Exception as e:
            langRunning = False
            statusIndex = 3
            publisherIndex = 6
            break

    if(rightIndex == -1):
        print("Failed to find set language, using first language as fallback")
        rightIndex = 1

    rightIndex = str(rightIndex)

    #getStatus
    try:
        status = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + rightIndex + "]/div[" + str(statusIndex) + "]")[0].itertext()
        status = ''.join(status).split(": ")[1]
    except Exception as e:
        try:
            status = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[1]/div[3]")[0].itertext()
            status = ''.join(status).split(": ")[1]
        except Exception as e:
            print(e)
            print("Failed to get status")

    if(status != ""):
        if(status in runningLang):
            casestatus = "\"ONGOING\""
        elif(status in abandonedLang):
            casestatus = "\"ABANDONED\""
        elif(status in endedLang):
            casestatus = "\"ENDED\""
        else:
            casestatus = "\"ENDED\""
                
            
        data.status = casestatus


    #getSummary
    try:
        summary = html_dom.xpath("//*[@id=\"description\"]/div/div/div[1]")[0].itertext()
        summary = ''.join(summary)
        for t in tagTexts:
            if(t in summary):
                raise Exception
        for s in noSummaryLang:
            if(s in summary):
                raise Exception
    except Exception as e:
        engsum = ""
        langsum = ""
        sumindex = 1
        noavail = False
        while(True):
            try:
                summary = html_dom.xpath("//*[@id=\"description\"]/div/div/section/div[" + str(sumindex) + "]")[0].itertext()
                summary = ''.join(summary)
                sumlang = html_dom.xpath("//*[@id=\"description\"]/div/div/section/button[" + str(sumindex) + "]")[0].itertext()
                sumlang = ''.join(sumlang)
                for s in noSummaryLang:
                    if (s in summary):
                        print("No summary available for this language")
                        noavail = True
                        continue
                if (sumlang == getFlagLanguage() and noavail == False):
                    langsum = summary
                    break
                elif (sumlang == "English"):
                    engsum = summary
                    if(noavail):
                        break
                sumindex += 1
            except Exception as e:
                break

        if(langsum != ""):
            summary = langsum
        else:
            summary = engsum
    if(summary != ""):
        for b in blurbLang:
            if(b in summary.split(":")[0]):
                summary = summary[len(b):]

        summarylist = summary.split(":")[:-1]
        summary = ""
        for s in summarylist:
            summary += s
            summary += ":"

        if(summary[0:1] == ":"):
            summary = summary[1:]

        for sou in summarySourceLang:
            l = len(sou)
            if(summary[len(summary)-l:] == sou):
                summary = summary[:len(summary) - l]
                break

        data.summary = summary


    #getPublisher
    try:
        publisher = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + rightIndex + "]/div[" + str(publisherIndex) + "]")[0].itertext()
        publisher = ''.join(publisher)
    except Exception as e:
        try:
            publisher = html_dom.xpath("//*[@id=\"information\"]/div/ul/li[2]/ul/li[1]/div[6]")[0].itertext()
            publisher = ''.join(publisher)
        except Exception as e:
            print(e)
            print("Failed to get publisher")
    if(publisher != ""):
        publisher = publisher.split(": ")[1]
        data.publisher = publisher

    #Tags & Genres
    i = 1
    running = True
    genrelist = []
    taglist = []
    while(running):
        try:
            tag = html_dom.xpath("//*[@id=\"description\"]/div/div/ul/li[" + str(i) + "]")[0]
            tagstring = ''.join(tag.itertext())


            tagurl = html_dom.xpath("//*[@id=\"description\"]/div/div/ul/li[" + str(i) + "]/a/@href")[0]
            if("/genre/" in tagurl):
                if(tagstring not in genrelist):
                    genrelist.append(tagstring)
            else:
                if(tagstring not in taglist):
                    taglist.append(tagstring)
            i += 1
        except Exception as e:
#            print(e)
            running = False

    if(len(genrelist) > 0):
        genres = "["
        for idx, genre in enumerate(genrelist):
            if(idx != 0):
                genres += ",\n"
            genres += "\"" + genre + "\""
        genres += "]"

        data.genres = genres

    if(len(taglist) > 0):
        tags = "["
        for idx, tag in enumerate(taglist):
            if(idx != 0):
                tags += ",\n"
            tags += "\"" + tag + "\""
        tags += "]"

        data.tags = tags

    data.isvalid = True
    return data

p_context = sync_playwright()
p = p_context.__enter__()
browser = p.chromium.launch()
page = browser.new_page()
page.goto(getBaseURL())


print("Using user " + komgaemail)

x = requests.get(komgaurl + '/api/v1/series?size=50000', auth = (komgaemail, komgapassword))

json_string = json.loads(x.text)

seriesnum = 0
try:
    expected = json_string['numberOfElements']
except:
    print("Failed to get list of mangas, are the login infos correct?")
    sys.exit(1)

print("Series to do: ")
print(expected)

class failedtries():
    def __init__(self, id, name):
        self.id = id
        self.name = name

failed = []

progressfilename = "mangas.progress"

def addMangaProgress(seriesID):
    if(keepProgress == False):
        return
    progfile = open(progressfilename, "a+")
    progfile.write(str(seriesID) + "\n")
    progfile.close()


progresslist = []
if(keepProgress):
    print("Loading list of successfully updated mangas")
    try:
        with open(progressfilename) as file:
            progresslist = [line.rstrip() for line in file]
    except:
        print("Failed to load list of mangas")

failedfile = open("failed.txt", "w")
for series in json_string['content']:
    seriesnum += 1
    if(len(mangas) > 0):
        if(series['name'] not in mangas):
            continue
    print("Number: " + str(seriesnum) + "/" + str(expected))
    name = series['name']
    seriesID = series['id']
    if(str(seriesID) in progresslist):
        print("Manga " + str(name) + " was already updated, skipping...")
        continue
    print("Updating: " + str(name))
    md = getMangaMetadata(name)
    if(md.isvalid == False):
        print("----------------------------------------------------")
        print("Failed to update " + str(name) + ", trying again at the end")
        print("----------------------------------------------------")
        fail = failedtries(seriesID, name)
        failed.append(fail)
        failedfile.write(str(seriesID))
        failedfile.write(name)
        time.sleep(10)
        continue
    jsondata = """{
  "status": %s,
  "statusLock": true,
  "summary": "%s",
  "summaryLock": true,
  "publisher": "%s",
  "publisherLock": true,
  "genres": %s,
  "genresLock": true,
  "tags": %s,
  "tagsLock": true
}""" % (md.status, md.summary.replace('\n', '\\n'), md.publisher, md.genres, md.tags)
#% (md.status, md.summary.encode('ascii', 'ignore').decode("utf-8").replace('\n', '\\n'), md.publisher, md.genres, md.tags)
    pushdata = jsondata.replace("\n", "").replace("{  \\\"status\\\": ", "{\\\"status\\\":").replace(",  \\\"statusLock\\\": ", ",\\\"statusLock\\\":").replace(",  \\\"summary\\\": ", ",\\\"summary\\\":").replace(",  \\\"summaryLock\\\": ", ",\\\"summaryLock\\\":").replace("\n", "").replace("\r", "")
    print(pushdata)
    headers = {'Content-Type': 'application/json', 'accept': '*/*'}
    patch = requests.patch(komgaurl + "/api/v1/series/" + seriesID + "/metadata", data=str.encode(pushdata), auth = (komgaemail, komgapassword), headers=headers)
    if(patch.status_code == 204):
        print("----------------------------------------------------")
        print("Successfully updated " + str(name))
        print("----------------------------------------------------")
        addMangaProgress(seriesID)
        time.sleep(10)
    else:
        try:
            print("----------------------------------------------------")
            print("Failed to update " + str(name) + ", trying again at the end")
            print("----------------------------------------------------")
            print(patch)
            print(patch.text)
            failedfile.write(str(seriesID))
            failedfile.write(name)
            fail = failedtries(seriesID, name)
            failed.append(fail)
        except:
            pass

failedfile.close()

for f in failed:
    md = getMangaMetadata(f.name)
    if (md.isvalid == False):
        print("----------------------------------------------------")
        print("Failed again to update " + str(f.name) + ", not trying again")
        print("----------------------------------------------------")
        time.sleep(10)
        continue
    jsondata = """{
      "status": %s,
      "statusLock": true,
      "summary": "%s",
      "summaryLock": true,
      "publisher": "%s",
      "publisherLock": true,
      "genres": %s,
      "genresLock": true,
      "tags": %s,
      "tagsLock": true
    }""" % (md.status, md.summary.replace('\n', '\\n'), md.publisher, md.genres, md.tags)
    pushdata = jsondata.replace("\n", "").replace("{  \\\"status\\\": ", "{\\\"status\\\":").replace(",  \\\"statusLock\\\": ", ",\\\"statusLock\\\":").replace(",  \\\"summary\\\": ", ",\\\"summary\\\":").replace(",  \\\"summaryLock\\\": ", ",\\\"summaryLock\\\":").replace("\n", "").replace("\r", "")
    print(pushdata)
    headers = {'Content-Type': 'application/json', 'accept': '*/*'}
    patch = requests.patch(komgaurl + "/api/v1/series/" + seriesID + "/metadata", data=str.encode(pushdata), auth = (komgaemail, komgapassword), headers=headers)
    if(patch.status_code == 204):
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Successfully updated " + str(f.name))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
        addMangaProgress(seriesID)
        time.sleep(10)
    else:
        print("----------------------------------------------------")
        print("Failed again to update " + str(f.name) + ", not trying again")
        print("----------------------------------------------------")
        addMangaProgress(seriesID)
        time.sleep(10)
        continue